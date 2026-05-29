import pytest

from app.core.exceptions import (
    ReviewPilotException,
    ConfigError,
    GitHubAPIError,
    WebhookVerifyError,
    AIProviderError,
    AnalysisError,
    PRTooLargeError,
    ASTParseError,
    NotFoundError,
    PermissionDeniedError,
)


class TestReviewPilotException:
    def test_basic_exception(self) -> None:
        exc = ReviewPilotException("test message")
        assert exc.message == "test message"
        assert exc.detail is None
        assert str(exc) == "test message"

    def test_with_detail(self) -> None:
        exc = ReviewPilotException("test message", detail="extra info")
        assert exc.message == "test message"
        assert exc.detail == "extra info"

    def test_is_exception_subclass(self) -> None:
        exc = ReviewPilotException("test")
        assert isinstance(exc, Exception)


class TestExceptionHierarchy:
    @pytest.mark.parametrize("exc_class,exc_name", [
        (ConfigError, "ConfigError"),
        (GitHubAPIError, "GitHubAPIError"),
        (WebhookVerifyError, "WebhookVerifyError"),
        (AIProviderError, "AIProviderError"),
        (AnalysisError, "AnalysisError"),
        (PRTooLargeError, "PRTooLargeError"),
        (ASTParseError, "ASTParseError"),
        (NotFoundError, "NotFoundError"),
        (PermissionDeniedError, "PermissionDeniedError"),
    ])
    def test_all_inherit_from_base(self, exc_class: type, exc_name: str) -> None:
        exc = exc_class("test message")
        assert isinstance(exc, ReviewPilotException)
        assert isinstance(exc, Exception)

    @pytest.mark.parametrize("exc_class,exc_name", [
        (ConfigError, "ConfigError"),
        (GitHubAPIError, "GitHubAPIError"),
    ])
    def test_exception_with_detail(self, exc_class: type, exc_name: str) -> None:
        exc = exc_class("error message", detail="detailed info")
        assert exc.message == "error message"
        assert exc.detail == "detailed info"
