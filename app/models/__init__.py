from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.models.repository import Repository  # noqa: E402
from app.models.pull_request import PullRequest  # noqa: E402
from app.models.review_record import ReviewRecord  # noqa: E402
from app.models.review_issue import ReviewIssue  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.repo_config import RepoConfig  # noqa: E402

__all__ = [
    "Base",
    "Repository",
    "PullRequest",
    "ReviewRecord",
    "ReviewIssue",
    "User",
    "RepoConfig",
]
