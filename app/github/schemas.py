from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class FileChange:
    filename: str
    status: str  # added, modified, removed, renamed
    patch: Optional[str] = None
    previous_filename: Optional[str] = None
    additions: int = 0
    deletions: int = 0
    changes: int = 0


@dataclass
class PRDetail:
    pr_id: int
    number: int
    title: str
    body: Optional[str]
    author: str
    head_sha: str
    base_sha: str
    head_branch: str
    base_branch: str
    files: list[FileChange] = field(default_factory=list)
    diff_url: Optional[str] = None


@dataclass
class RepoStructure:
    tree: list[str] = field(default_factory=list)
    config_files: dict[str, str] = field(default_factory=dict)
    dependency_files: dict[str, str] = field(default_factory=dict)


# ---- Webhook Events ----

@dataclass
class BaseWebhookEvent:
    event_type: str
    raw_payload: dict[str, Any]

    @property
    def owner(self) -> str:
        return ""

    @property
    def repo(self) -> str:
        return ""

    @property
    def pr_number(self) -> int:
        return 0


@dataclass
class PROpenEvent(BaseWebhookEvent):
    owner: str = ""
    repo: str = ""
    pr_number: int = 0
    action: str = ""
    sender: str = ""


@dataclass
class PRSyncEvent(BaseWebhookEvent):
    owner: str = ""
    repo: str = ""
    pr_number: int = 0
    action: str = ""
    sender: str = ""


@dataclass
class IssueCommentEvent(BaseWebhookEvent):
    owner: str = ""
    repo: str = ""
    pr_number: int = 0
    comment_body: str = ""
    comment_id: int = 0
    sender: str = ""


@dataclass
class InstallationEvent(BaseWebhookEvent):
    action: str = ""
    installation_id: int = 0
    sender: str = ""


@dataclass
class UnknownEvent(BaseWebhookEvent):
    pass
