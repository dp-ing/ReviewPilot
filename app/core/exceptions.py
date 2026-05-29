from __future__ import annotations


class ReviewPilotException(Exception):
    def __init__(self, message: str, detail: str | None = None) -> None:
        self.message = message
        self.detail = detail
        super().__init__(message)


class ConfigError(ReviewPilotException):
    pass


class GitHubAPIError(ReviewPilotException):
    pass


class WebhookVerifyError(ReviewPilotException):
    pass


class AIProviderError(ReviewPilotException):
    pass


class AnalysisError(ReviewPilotException):
    pass


class PRTooLargeError(ReviewPilotException):
    pass


class ASTParseError(ReviewPilotException):
    pass


class NotFoundError(ReviewPilotException):
    pass


class PermissionDeniedError(ReviewPilotException):
    pass
