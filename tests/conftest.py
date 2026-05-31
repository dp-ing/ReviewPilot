from collections.abc import Generator

import pytest

pytest_plugins: list[str] = []


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "e2e: end-to-end test requiring real API credentials")
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.models import Base
from app.models.repository import Repository
from app.models.pull_request import PullRequest
from app.models.review_record import ReviewRecord, ReviewStatus
from app.models.review_issue import ReviewIssue
from app.models.user import User
from app.models.repo_config import RepoConfig


@pytest.fixture
def temp_db() -> Generator[Session, None, None]:
    """Create a temporary SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_repository(temp_db: Session) -> Repository:
    repo = Repository(
        github_repo_id=12345,
        name="test-repo",
        full_name="testuser/test-repo",
        owner="testuser",
        html_url="https://github.com/testuser/test-repo",
        default_branch="main",
        language="Python",
    )
    temp_db.add(repo)
    temp_db.commit()
    temp_db.refresh(repo)
    return repo


@pytest.fixture
def sample_pr(temp_db: Session, sample_repository: Repository) -> PullRequest:
    pr = PullRequest(
        repository_id=sample_repository.id,
        pr_number=1,
        title="Test PR",
        body="A test pull request",
        author="testuser",
        head_sha="abc123",
        base_sha="def456",
        head_branch="feature/test",
        base_branch="main",
    )
    temp_db.add(pr)
    temp_db.commit()
    temp_db.refresh(pr)
    return pr


@pytest.fixture
def sample_review(temp_db: Session, sample_pr: PullRequest) -> ReviewRecord:
    review = ReviewRecord(
        pull_request_id=sample_pr.id,
        status=ReviewStatus.PENDING,
        triggered_by="auto",
    )
    temp_db.add(review)
    temp_db.commit()
    temp_db.refresh(review)
    return review


@pytest.fixture
def sample_issue(temp_db: Session, sample_review: ReviewRecord) -> ReviewIssue:
    issue = ReviewIssue(
        review_record_id=sample_review.id,
        file_path="src/main.py",
        line_start=10,
        line_end=15,
        severity="warning",
        category="security",
        rule_id="python-sql-concat",
        title="SQL Injection Risk",
        description="Potential SQL injection via string concatenation",
        suggestion="Use parameterized queries",
        confidence=0.85,
        source="ast",
    )
    temp_db.add(issue)
    temp_db.commit()
    temp_db.refresh(issue)
    return issue


@pytest.fixture
def sample_user(temp_db: Session) -> User:
    user = User(
        github_user_id=67890,
        login="reviewer",
        avatar_url="https://avatars.example.com/u/67890",
        is_admin=False,
    )
    temp_db.add(user)
    temp_db.commit()
    temp_db.refresh(user)
    return user


@pytest.fixture
def sample_repo_config(temp_db: Session, sample_repository: Repository) -> RepoConfig:
    cfg = RepoConfig(
        repository_id=sample_repository.id,
        auto_review=True,
        enabled_categories=["security", "logic"],
        ignore_patterns=["**/test_*.py", "**/migrations/**"],
        ignore_rule_ids=["python-complexity"],
        review_language="zh-CN",
    )
    temp_db.add(cfg)
    temp_db.commit()
    temp_db.refresh(cfg)
    return cfg


@pytest.fixture
def mock_config(monkeypatch: pytest.MonkeyPatch) -> Settings:
    """Override configuration with test values."""
    test_config = Settings(
        GITHUB_APP_ID="test_app_id",
        GITHUB_APP_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----",
        GITHUB_WEBHOOK_SECRET="test_secret",
        GITHUB_CLIENT_ID="test_client_id",
        GITHUB_CLIENT_SECRET="test_client_secret",
        AI_API_KEY="test_ai_key",
        AI_API_BASE="https://api.test.com/v1",
        AI_DEFAULT_MODEL="test-model-fast",
        AI_STRONG_MODEL="test-model-strong",
        DATABASE_URL="sqlite:///:memory:",
        APP_HOST="127.0.0.1",
        APP_PORT=9999,
        LOG_LEVEL="DEBUG",
        SECRET_KEY="test_secret_key",
    )
    monkeypatch.setattr("app.core.config.get_config", lambda: test_config)
    return test_config
