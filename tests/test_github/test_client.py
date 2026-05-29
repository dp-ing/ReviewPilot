from unittest.mock import MagicMock

from app.github.client import GitHubClient
from app.github.schemas import FileChange, PRDetail, RepoStructure


class TestGitHubClientInit:
    def test_init_stores_installation_id(self) -> None:
        client = GitHubClient(installation_id=12345)
        assert client._installation_id == 12345
        assert client._token is None

    def test_init_with_different_installation_id(self) -> None:
        client = GitHubClient(installation_id=99999)
        assert client._installation_id == 99999


def _make_client(installation_id: int = 1) -> tuple[GitHubClient, MagicMock]:
    """Create a GitHubClient with a mocked _github property."""
    client = GitHubClient(installation_id=installation_id)
    mock_gh = MagicMock()
    client._gh = mock_gh
    return client, mock_gh


class TestGitHubClientGetPR:
    def test_get_pr_basic(self) -> None:
        client, mock_gh = _make_client()

        mock_user = MagicMock()
        mock_user.login = "testdev"

        mock_pr = MagicMock()
        mock_pr.id = 100
        mock_pr.number = 5
        mock_pr.title = "Test PR"
        mock_pr.body = "PR body text"
        mock_pr.user = mock_user
        mock_pr.head.sha = "head_sha_123"
        mock_pr.base.sha = "base_sha_456"
        mock_pr.head.ref = "feature/branch"
        mock_pr.base.ref = "main"
        mock_pr.diff_url = "https://github.com/o/r/pull/5.diff"

        mock_repo = MagicMock()
        mock_repo.get_pull.return_value = mock_pr
        mock_gh.get_repo.return_value = mock_repo

        result = client.get_pr("owner1", "repo1", 5)

        mock_gh.get_repo.assert_called_once_with("owner1/repo1")
        mock_repo.get_pull.assert_called_once_with(5)

        assert isinstance(result, PRDetail)
        assert result.pr_id == 100
        assert result.number == 5
        assert result.title == "Test PR"
        assert result.body == "PR body text"
        assert result.author == "testdev"
        assert result.head_sha == "head_sha_123"
        assert result.base_sha == "base_sha_456"


class TestGitHubClientGetPRFiles:
    def test_get_pr_files(self) -> None:
        client, mock_gh = _make_client()

        mock_file = MagicMock()
        mock_file.filename = "src/main.py"
        mock_file.status = "modified"
        mock_file.patch = "@@ -1,3 +1,5 @@"
        mock_file.previous_filename = None
        mock_file.additions = 5
        mock_file.deletions = 1
        mock_file.changes = 6

        mock_pr = MagicMock()
        mock_pr.get_files.return_value = [mock_file]

        mock_repo = MagicMock()
        mock_repo.get_pull.return_value = mock_pr
        mock_gh.get_repo.return_value = mock_repo

        result = client.get_pr_files("o", "r", 1)

        assert len(result) == 1
        assert isinstance(result[0], FileChange)
        assert result[0].filename == "src/main.py"
        assert result[0].status == "modified"
        assert result[0].patch == "@@ -1,3 +1,5 @@"
        assert result[0].additions == 5
        assert result[0].deletions == 1
        assert result[0].changes == 6


class TestGitHubClientGetFileContent:
    def test_get_file_content(self) -> None:
        client, mock_gh = _make_client()

        mock_content = MagicMock()
        mock_content.decoded_content = b"print('hello')"

        mock_repo = MagicMock()
        mock_repo.get_contents.return_value = mock_content
        mock_gh.get_repo.return_value = mock_repo

        content = client.get_file_content("o", "r", "main", "src/app.py")
        assert content == "print('hello')"
        mock_repo.get_contents.assert_called_once_with("src/app.py", ref="main")


class TestGitHubClientGetRepoStructure:
    def test_get_repo_structure_flat(self) -> None:
        client, mock_gh = _make_client()

        mock_file = MagicMock()
        mock_file.name = "main.py"
        mock_file.type = "file"

        mock_repo = MagicMock()
        mock_repo.get_contents.return_value = [mock_file]
        mock_gh.get_repo.return_value = mock_repo

        result = client.get_repo_structure("o", "r", "main")

        assert isinstance(result, RepoStructure)
        assert "main.py" in result.tree
        mock_repo.get_contents.assert_called_once_with("", ref="main")


class TestGitHubClientCreateComments:
    def test_create_review_comment(self) -> None:
        client, mock_gh = _make_client()

        mock_comment = MagicMock()
        mock_comment.id = 42

        mock_pr = MagicMock()
        mock_pr.create_review_comment.return_value = mock_comment

        mock_commit = MagicMock()
        mock_repo = MagicMock()
        mock_repo.get_commit.return_value = mock_commit
        mock_repo.get_pull.return_value = mock_pr
        mock_gh.get_repo.return_value = mock_repo

        comment_id = client.create_review_comment(
            "o", "r", 1, "abc123", "src/main.py", 10, "RIGHT", "Nice code!"
        )

        assert comment_id == 42
        mock_pr.create_review_comment.assert_called_once_with(
            body="Nice code!",
            commit=mock_commit,
            path="src/main.py",
            line=10,
            side="RIGHT",
        )

    def test_create_issue_comment(self) -> None:
        client, mock_gh = _make_client()

        mock_comment = MagicMock()
        mock_comment.id = 100

        mock_issue = MagicMock()
        mock_issue.create_comment.return_value = mock_comment

        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue
        mock_gh.get_repo.return_value = mock_repo

        comment_id = client.create_issue_comment("o", "r", 1, "Great PR!")
        assert comment_id == 100
        mock_issue.create_comment.assert_called_once_with(body="Great PR!")

    def test_create_review(self) -> None:
        client, mock_gh = _make_client()

        mock_review = MagicMock()
        mock_review.id = 200

        mock_commit = MagicMock()
        mock_pr = MagicMock()
        mock_pr.create_review.return_value = mock_review

        mock_repo = MagicMock()
        mock_repo.get_commit.return_value = mock_commit
        mock_repo.get_pull.return_value = mock_pr
        mock_gh.get_repo.return_value = mock_repo

        review_comments = [
            {"path": "a.py", "position": 1, "body": "Issue 1"},
            {"path": "b.py", "position": 3, "body": "Issue 2"},
        ]

        review_id = client.create_review(
            "o", "r", 1, "abc123", "Review summary", review_comments
        )

        assert review_id == 200
        mock_pr.create_review.assert_called_once_with(
            commit=mock_commit,
            body="Review summary",
            event="COMMENT",
            comments=review_comments,
        )


class TestGitHubClientCollaborators:
    def test_list_repo_collaborators(self) -> None:
        client, mock_gh = _make_client()

        mock_collab = MagicMock()
        mock_collab.login = "dev1"
        mock_collab.id = 111

        mock_repo = MagicMock()
        mock_repo.get_collaborators.return_value = [mock_collab]
        mock_gh.get_repo.return_value = mock_repo

        result = client.list_repo_collaborators("o", "r")

        assert len(result) == 1
        assert result[0]["login"] == "dev1"
        assert result[0]["id"] == 111
