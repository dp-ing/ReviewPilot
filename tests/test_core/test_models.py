from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from app.models.repository import Repository
from app.models.pull_request import PullRequest
from app.models.review_record import ReviewRecord, ReviewStatus
from app.models.review_issue import ReviewIssue
from app.models.user import User
from app.models.repo_config import RepoConfig


class TestRepositoryModel:
    def test_create_repository(self, temp_db: Session) -> None:
        repo = Repository(
            github_repo_id=11111,
            name="my-repo",
            full_name="owner/my-repo",
            owner="owner",
            html_url="https://github.com/owner/my-repo",
        )
        temp_db.add(repo)
        temp_db.commit()
        temp_db.refresh(repo)

        assert repo.id is not None
        assert repo.github_repo_id == 11111
        assert repo.name == "my-repo"
        assert repo.full_name == "owner/my-repo"
        assert repo.default_branch == "main"
        assert repo.created_at is not None

    def test_github_repo_id_must_be_unique(self, temp_db: Session) -> None:
        repo1 = Repository(
            github_repo_id=22222,
            name="repo1",
            full_name="owner/repo1",
            owner="owner",
            html_url="https://github.com/owner/repo1",
        )
        repo2 = Repository(
            github_repo_id=22222,
            name="repo2",
            full_name="owner/repo2",
            owner="owner",
            html_url="https://github.com/owner/repo2",
        )
        temp_db.add(repo1)
        temp_db.commit()
        temp_db.add(repo2)
        with pytest.raises(Exception):
            temp_db.commit()

    def test_read_repository(self, temp_db: Session, sample_repository: Repository) -> None:
        repo = temp_db.query(Repository).filter_by(id=sample_repository.id).first()
        assert repo is not None
        assert repo.name == sample_repository.name
        assert repo.github_repo_id == sample_repository.github_repo_id

    def test_update_repository(self, temp_db: Session, sample_repository: Repository) -> None:
        sample_repository.language = "Java"
        temp_db.commit()
        temp_db.refresh(sample_repository)
        assert sample_repository.language == "Java"

    def test_delete_repository(self, temp_db: Session) -> None:
        repo = Repository(
            github_repo_id=33333,
            name="delete-me",
            full_name="owner/delete-me",
            owner="owner",
            html_url="https://github.com/owner/delete-me",
        )
        temp_db.add(repo)
        temp_db.commit()
        temp_db.delete(repo)
        temp_db.commit()
        result = temp_db.query(Repository).filter_by(github_repo_id=33333).first()
        assert result is None

    def test_optional_language_field(self, temp_db: Session) -> None:
        repo = Repository(
            github_repo_id=44444,
            name="no-lang",
            full_name="owner/no-lang",
            owner="owner",
            html_url="https://github.com/owner/no-lang",
        )
        temp_db.add(repo)
        temp_db.commit()
        assert repo.language is None


class TestPullRequestModel:
    def test_create_pull_request(self, temp_db: Session, sample_repository: Repository) -> None:
        pr = PullRequest(
            repository_id=sample_repository.id,
            pr_number=2,
            title="New Feature",
            body="Adds new functionality",
            author="dev",
            head_sha="abc456",
            base_sha="def789",
            head_branch="feature/new",
            base_branch="main",
        )
        temp_db.add(pr)
        temp_db.commit()
        temp_db.refresh(pr)

        assert pr.id is not None
        assert pr.pr_number == 2
        assert pr.title == "New Feature"
        assert pr.repository_id == sample_repository.id
        assert pr.created_at is not None

    def test_pr_belongs_to_repository(
        self, temp_db: Session, sample_pr: PullRequest, sample_repository: Repository
    ) -> None:
        assert sample_pr.repository is not None
        assert sample_pr.repository.id == sample_repository.id
        assert sample_pr.repository.name == "test-repo"

    def test_pr_body_is_optional(self, temp_db: Session, sample_repository: Repository) -> None:
        pr = PullRequest(
            repository_id=sample_repository.id,
            pr_number=3,
            title="No Body PR",
            author="dev",
            head_sha="111",
            base_sha="222",
            head_branch="fix/bug",
            base_branch="main",
        )
        temp_db.add(pr)
        temp_db.commit()
        assert pr.body is None

    def test_cascade_delete_pr_deletes_reviews(
        self, temp_db: Session, sample_pr: PullRequest, sample_review: ReviewRecord
    ) -> None:
        review_id = sample_review.id
        temp_db.delete(sample_pr)
        temp_db.commit()
        result = temp_db.query(ReviewRecord).filter_by(id=review_id).first()
        assert result is None


class TestReviewRecordModel:
    def test_create_review_record(self, temp_db: Session, sample_pr: PullRequest) -> None:
        review = ReviewRecord(
            pull_request_id=sample_pr.id,
            status=ReviewStatus.PENDING,
        )
        temp_db.add(review)
        temp_db.commit()
        temp_db.refresh(review)

        assert review.id is not None
        assert review.status == ReviewStatus.PENDING
        assert review.critical_count == 0
        assert review.warning_count == 0
        assert review.suggestion_count == 0
        assert review.total_issues == 0

    def test_review_status_enum(self, temp_db: Session, sample_pr: PullRequest) -> None:
        review = ReviewRecord(
            pull_request_id=sample_pr.id,
            status=ReviewStatus.COMPLETED,
            summary="Review completed successfully",
            critical_count=2,
            warning_count=5,
            suggestion_count=3,
            total_issues=10,
        )
        temp_db.add(review)
        temp_db.commit()

        assert review.status == ReviewStatus.COMPLETED
        assert review.status.value == "completed"
        assert review.summary == "Review completed successfully"
        assert review.critical_count == 2
        assert review.warning_count == 5

    def test_review_status_values(self) -> None:
        assert ReviewStatus.PENDING.value == "pending"
        assert ReviewStatus.COMPLETED.value == "completed"
        assert ReviewStatus.FAILED.value == "failed"

    def test_failed_review_with_error(self, temp_db: Session, sample_pr: PullRequest) -> None:
        review = ReviewRecord(
            pull_request_id=sample_pr.id,
            status=ReviewStatus.FAILED,
            error_message="AI provider timeout",
        )
        temp_db.add(review)
        temp_db.commit()

        assert review.status == ReviewStatus.FAILED
        assert review.error_message == "AI provider timeout"

    def test_review_belongs_to_pr(
        self, temp_db: Session, sample_review: ReviewRecord, sample_pr: PullRequest
    ) -> None:
        assert sample_review.pull_request is not None
        assert sample_review.pull_request.id == sample_pr.id

    def test_triggered_by_field(self, temp_db: Session, sample_pr: PullRequest) -> None:
        for trigger in ("auto", "webhook", "/review command", None):
            review = ReviewRecord(
                pull_request_id=sample_pr.id,
                triggered_by=trigger,
            )
            temp_db.add(review)
            temp_db.commit()
            assert review.triggered_by == trigger


class TestReviewIssueModel:
    def test_create_review_issue(
        self, temp_db: Session, sample_review: ReviewRecord
    ) -> None:
        issue = ReviewIssue(
            review_record_id=sample_review.id,
            file_path="app/main.py",
            line_start=5,
            line_end=10,
            severity="critical",
            category="security",
            rule_id="python-exec-eval",
            title="Exec call detected",
            description="Using exec() is dangerous",
            suggestion="Remove exec() call",
            confidence=0.95,
            source="ast",
        )
        temp_db.add(issue)
        temp_db.commit()
        temp_db.refresh(issue)

        assert issue.id is not None
        assert issue.severity == "critical"
        assert issue.category == "security"
        assert issue.confidence == 0.95
        assert issue.source == "ast"

    def test_suggestion_diff_json_field(
        self, temp_db: Session, sample_review: ReviewRecord
    ) -> None:
        suggestion = {
            "old": "cursor.execute(f'SELECT * FROM users WHERE id = {uid}')",
            "new": "cursor.execute('SELECT * FROM users WHERE id = ?', (uid,))",
        }
        issue = ReviewIssue(
            review_record_id=sample_review.id,
            file_path="app/db.py",
            line_start=20,
            line_end=20,
            severity="warning",
            category="security",
            rule_id="python-sql-concat",
            title="SQL Injection",
            description="String concatenation in SQL",
            suggestion="Use parameterized queries",
            suggestion_diff=suggestion,
        )
        temp_db.add(issue)
        temp_db.commit()
        temp_db.refresh(issue)

        assert issue.suggestion_diff == suggestion
        assert issue.suggestion_diff["old"] == suggestion["old"]
        assert issue.suggestion_diff["new"] == suggestion["new"]

    def test_optional_suggestion_diff(self, temp_db: Session, sample_review: ReviewRecord) -> None:
        issue = ReviewIssue(
            review_record_id=sample_review.id,
            file_path="app/main.py",
            line_start=1,
            line_end=1,
            severity="suggestion",
            category="style",
            title="Style issue",
            description="Line too long",
        )
        temp_db.add(issue)
        temp_db.commit()
        assert issue.suggestion_diff is None
        assert issue.suggestion is None

    def test_issue_belongs_to_review(
        self, temp_db: Session, sample_issue: ReviewIssue, sample_review: ReviewRecord
    ) -> None:
        assert sample_issue.review_record is not None
        assert sample_issue.review_record.id == sample_review.id

    def test_default_source_is_ai(self, temp_db: Session, sample_review: ReviewRecord) -> None:
        issue = ReviewIssue(
            review_record_id=sample_review.id,
            file_path="src/test.py",
            line_start=1,
            line_end=1,
            severity="suggestion",
            category="style",
            title="Test",
            description="Test",
        )
        temp_db.add(issue)
        temp_db.commit()
        assert issue.source == "ai"

    def test_default_confidence_is_zero(
        self, temp_db: Session, sample_review: ReviewRecord
    ) -> None:
        issue = ReviewIssue(
            review_record_id=sample_review.id,
            file_path="src/test.py",
            line_start=1,
            line_end=1,
            severity="suggestion",
            category="style",
            title="Test",
            description="Test",
        )
        temp_db.add(issue)
        temp_db.commit()
        assert issue.confidence == 0.0


class TestUserModel:
    def test_create_user(self, temp_db: Session) -> None:
        user = User(
            github_user_id=99999,
            login="testuser",
            avatar_url="https://avatars.example.com/u/99999",
        )
        temp_db.add(user)
        temp_db.commit()
        temp_db.refresh(user)

        assert user.id is not None
        assert user.github_user_id == 99999
        assert user.login == "testuser"
        assert user.is_admin is False
        assert user.created_at is not None

    def test_github_user_id_is_unique(self, temp_db: Session) -> None:
        user1 = User(github_user_id=88888, login="user1")
        user2 = User(github_user_id=88888, login="user2")
        temp_db.add(user1)
        temp_db.commit()
        temp_db.add(user2)
        with pytest.raises(Exception):
            temp_db.commit()

    def test_admin_flag(self, temp_db: Session) -> None:
        user = User(github_user_id=77777, login="admin", is_admin=True)
        temp_db.add(user)
        temp_db.commit()
        assert user.is_admin is True

    def test_optional_fields(self, temp_db: Session) -> None:
        user = User(github_user_id=66666, login="minimal")
        temp_db.add(user)
        temp_db.commit()
        assert user.avatar_url is None
        assert user.last_login_at is None

    def test_last_login_at(self, temp_db: Session, sample_user: User) -> None:
        now = datetime.utcnow()
        sample_user.last_login_at = now
        temp_db.commit()
        temp_db.refresh(sample_user)
        assert sample_user.last_login_at == now


class TestRepoConfigModel:
    def test_create_repo_config(
        self, temp_db: Session, sample_repository: Repository
    ) -> None:
        cfg = RepoConfig(
            repository_id=sample_repository.id,
            auto_review=True,
            review_language="zh-CN",
        )
        temp_db.add(cfg)
        temp_db.commit()
        temp_db.refresh(cfg)

        assert cfg.id is not None
        assert cfg.auto_review is True
        assert cfg.review_language == "zh-CN"
        assert cfg.max_files_per_review == 50
        assert cfg.confidence_threshold == 0.6

    def test_repo_config_unique_per_repository(
        self, temp_db: Session, sample_repository: Repository
    ) -> None:
        cfg1 = RepoConfig(repository_id=sample_repository.id)
        cfg2 = RepoConfig(repository_id=sample_repository.id)
        temp_db.add(cfg1)
        temp_db.commit()
        temp_db.add(cfg2)
        with pytest.raises(Exception):
            temp_db.commit()

    def test_json_list_fields(self, temp_db: Session, sample_repo_config: RepoConfig) -> None:
        cfg = sample_repo_config
        assert isinstance(cfg.enabled_categories, list)
        assert "security" in cfg.enabled_categories
        assert isinstance(cfg.ignore_patterns, list)
        assert "**/test_*.py" in cfg.ignore_patterns

    def test_config_belongs_to_repository(
        self, temp_db: Session, sample_repo_config: RepoConfig, sample_repository: Repository
    ) -> None:
        assert sample_repo_config.repository is not None
        assert sample_repo_config.repository.id == sample_repository.id

    def test_default_values(self, temp_db: Session, sample_repository: Repository) -> None:
        cfg = RepoConfig(repository_id=sample_repository.id)
        temp_db.add(cfg)
        temp_db.commit()

        assert cfg.auto_review is True
        assert cfg.review_language == "zh-CN"
        assert cfg.max_files_per_review == 50
        assert cfg.confidence_threshold == 0.6
        assert cfg.enabled_categories is None
        assert cfg.ignore_patterns is None
        assert cfg.ignore_rule_ids is None

    def test_update_config(self, temp_db: Session, sample_repo_config: RepoConfig) -> None:
        sample_repo_config.auto_review = False
        sample_repo_config.enabled_categories = ["performance"]
        temp_db.commit()
        temp_db.refresh(sample_repo_config)

        assert sample_repo_config.auto_review is False
        assert sample_repo_config.enabled_categories == ["performance"]
