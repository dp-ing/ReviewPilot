from __future__ import annotations

import time
from typing import Any, Optional

import httpx
from github import Github, Auth
from github.GithubException import GithubException
from github.ContentFile import ContentFile
from github.Repository import Repository as GhRepository
from jose import jwt  # type: ignore[import-untyped]

from app.core.config import get_config
from app.core.exceptions import GitHubAPIError
from app.github.schemas import FileChange, PRDetail, RepoStructure


class GitHubClient:
    """GitHub API client using GitHub App installation tokens."""

    def __init__(self, installation_id: int) -> None:
        self._installation_id = installation_id
        self._config = get_config()
        self._token: Optional[str] = None
        self._token_expires_at: float = 0.0
        self._gh: Optional[Github] = None

    def _generate_jwt(self) -> str:
        now = int(time.time())
        payload = {
            "iat": now - 60,
            "exp": now + 600,
            "iss": self._config.GITHUB_APP_ID,
        }
        token: str = jwt.encode(payload, self._config.GITHUB_APP_PRIVATE_KEY, algorithm="RS256")
        return token

    def _get_token(self) -> str:
        now = time.time()
        if self._token and now < self._token_expires_at - 300:
            return self._token

        jwt_token = self._generate_jwt()
        url = (
            f"https://api.github.com/app/installations/{self._installation_id}/access_tokens"
        )

        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {jwt_token}",
                        "Accept": "application/vnd.github.v3+json",
                    },
                )
                resp.raise_for_status()
                data: dict[str, Any] = resp.json()

            self._token = data["token"]
            self._token_expires_at = now + 3600
            self._gh = Github(auth=Auth.Token(self._token))
            return self._token
        except httpx.HTTPStatusError as e:
            raise GitHubAPIError(
                f"Failed to get installation token: {e.response.status_code}",
                detail=str(e),
            )
        except Exception as e:
            raise GitHubAPIError(f"Failed to get installation token: {e}", detail=str(e))

    @property
    def _github(self) -> Github:
        if self._gh is None:
            self._get_token()
        assert self._gh is not None
        return self._gh

    def get_pr(self, owner: str, repo: str, pr_number: int) -> PRDetail:
        try:
            gh_repo = self._github.get_repo(f"{owner}/{repo}")
            gh_pr = gh_repo.get_pull(pr_number)

            return PRDetail(
                pr_id=gh_pr.id,
                number=gh_pr.number,
                title=gh_pr.title,
                body=gh_pr.body,
                author=gh_pr.user.login if gh_pr.user else "unknown",
                head_sha=gh_pr.head.sha,
                base_sha=gh_pr.base.sha,
                head_branch=gh_pr.head.ref,
                base_branch=gh_pr.base.ref,
                diff_url=gh_pr.diff_url,
            )
        except GithubException as e:
            raise GitHubAPIError(
                f"Failed to get PR {owner}/{repo}#{pr_number}: {e.status}",
                detail=str(e),
            )

    def get_pr_files(self, owner: str, repo: str, pr_number: int) -> list[FileChange]:
        try:
            gh_repo = self._github.get_repo(f"{owner}/{repo}")
            gh_pr = gh_repo.get_pull(pr_number)
            files = gh_pr.get_files()

            result: list[FileChange] = []
            for f in files:
                result.append(
                    FileChange(
                        filename=f.filename,
                        status=f.status,
                        patch=f.patch,
                        previous_filename=f.previous_filename,
                        additions=f.additions,
                        deletions=f.deletions,
                        changes=f.changes,
                    )
                )
            return result
        except GithubException as e:
            raise GitHubAPIError(
                f"Failed to get PR files {owner}/{repo}#{pr_number}: {e.status}",
                detail=str(e),
            )

    def get_file_content(self, owner: str, repo: str, ref: str, path: str) -> str:
        try:
            gh_repo = self._github.get_repo(f"{owner}/{repo}")
            content = gh_repo.get_contents(path, ref=ref)
            if isinstance(content, list):
                raise GitHubAPIError(f"Path {path} is a directory, not a file")
            return content.decoded_content.decode("utf-8")
        except GithubException as e:
            raise GitHubAPIError(
                f"Failed to get file {owner}/{repo}/{path}@{ref}: {e.status}",
                detail=str(e),
            )

    def get_repo_structure(self, owner: str, repo: str, ref: str) -> RepoStructure:
        try:
            gh_repo = self._github.get_repo(f"{owner}/{repo}")
            contents = gh_repo.get_contents("", ref=ref)

            tree: list[str] = []
            config_files: dict[str, str] = {}
            dependency_files: dict[str, str] = {}

            self._traverse_contents(gh_repo, contents, "", ref, tree, config_files, dependency_files, 0)

            return RepoStructure(
                tree=tree,
                config_files=config_files,
                dependency_files=dependency_files,
            )
        except GithubException as e:
            raise GitHubAPIError(
                f"Failed to get repo structure {owner}/{repo}: {e.status}",
                detail=str(e),
            )

    def _traverse_contents(
        self,
        gh_repo: GhRepository,
        contents: list[ContentFile] | ContentFile,
        prefix: str,
        ref: str,
        tree: list[str],
        config_files: dict[str, str],
        dependency_files: dict[str, str],
        depth: int,
    ) -> None:
        if depth > 5:
            return

        known_configs = {
            ".github/workflows/", ".github/dependabot.yml",
            "setup.cfg", "pyproject.toml", "pom.xml", "build.gradle",
            "package.json", "go.mod", "Cargo.toml", "Makefile",
        }
        known_deps = {
            "requirements.txt", "Pipfile", "Pipfile.lock",
            "pom.xml", "build.gradle", "package.json", "package-lock.json",
            "go.mod", "go.sum", "Cargo.toml", "Cargo.lock",
        }

        items: list[ContentFile] = (
            contents if isinstance(contents, list) else [contents]
        )

        for item in items:
            path = f"{prefix}{item.name}" if not prefix else f"{prefix}/{item.name}"
            if item.type == "dir":
                tree.append(f"{path}/")
                try:
                    sub = gh_repo.get_contents(path, ref=ref)
                    self._traverse_contents(gh_repo, sub, path, ref, tree, config_files, dependency_files, depth + 1)
                except Exception:
                    pass
            else:
                tree.append(path)
                is_config = path in known_configs or any(path.startswith(c) for c in known_configs)
                is_dep = path in known_deps or any(d in path for d in known_deps)
                if is_config:
                    try:
                        file_content = gh_repo.get_contents(path, ref=ref)
                        if not isinstance(file_content, list):
                            config_files[path] = file_content.decoded_content.decode("utf-8")
                    except Exception:
                        pass
                if is_dep:
                    try:
                        file_content = gh_repo.get_contents(path, ref=ref)
                        if not isinstance(file_content, list):
                            dependency_files[path] = file_content.decoded_content.decode("utf-8")
                    except Exception:
                        pass

    def create_review_comment(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        commit_id: str,
        path: str,
        line: int,
        side: str,
        body: str,
    ) -> int:
        try:
            gh_repo = self._github.get_repo(f"{owner}/{repo}")
            gh_pr = gh_repo.get_pull(pr_number)
            comment = gh_pr.create_review_comment(
                body=body,
                commit=gh_repo.get_commit(commit_id),
                path=path,
                line=line,
                side=side,
            )
            return comment.id
        except GithubException as e:
            raise GitHubAPIError(
                f"Failed to create review comment on {owner}/{repo}#{pr_number}: {e.status}",
                detail=str(e),
            )

    def create_issue_comment(self, owner: str, repo: str, pr_number: int, body: str) -> int:
        try:
            gh_repo = self._github.get_repo(f"{owner}/{repo}")
            gh_issue = gh_repo.get_issue(number=pr_number)
            comment = gh_issue.create_comment(body=body)
            return comment.id
        except GithubException as e:
            raise GitHubAPIError(
                f"Failed to create issue comment on {owner}/{repo}#{pr_number}: {e.status}",
                detail=str(e),
            )

    def create_review(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        commit_id: str,
        body: str,
        comments: list[dict[str, Any]],
    ) -> int:
        try:
            gh_repo = self._github.get_repo(f"{owner}/{repo}")
            gh_pr = gh_repo.get_pull(pr_number)
            review = gh_pr.create_review(
                commit=gh_repo.get_commit(commit_id),
                body=body,
                event="COMMENT",
                comments=comments,  # type: ignore[arg-type]
            )
            return review.id
        except GithubException as e:
            raise GitHubAPIError(
                f"Failed to create review on {owner}/{repo}#{pr_number}: {e.status}",
                detail=str(e),
            )

    def list_repo_collaborators(self, owner: str, repo: str) -> list[dict[str, Any]]:
        try:
            gh_repo = self._github.get_repo(f"{owner}/{repo}")
            collaborators = gh_repo.get_collaborators()
            return [
                {"login": c.login, "id": c.id, "permissions": {}}
                for c in collaborators
            ]
        except GithubException as e:
            raise GitHubAPIError(
                f"Failed to list collaborators for {owner}/{repo}: {e.status}",
                detail=str(e),
            )
