import hmac
import hashlib

import pytest

from app.github.schemas import (
    PROpenEvent,
    PRSyncEvent,
    IssueCommentEvent,
    InstallationEvent,
    UnknownEvent,
)
from app.github.webhook import (
    verify_signature,
    parse_event,
    extract_pr_identifiers,
)


SECRET = "test_webhook_secret"


def _sign(payload: bytes, secret: str = SECRET) -> str:
    return "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


@pytest.fixture
def mock_config_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.config import get_config
    cfg = get_config()
    monkeypatch.setattr(cfg, "GITHUB_WEBHOOK_SECRET", SECRET)


class TestVerifySignature:
    def test_valid_signature(self, mock_config_secret: None) -> None:
        payload = b'{"action":"opened"}'
        sig = _sign(payload)
        assert verify_signature(payload, sig) is True

    def test_invalid_signature(self, mock_config_secret: None) -> None:
        payload = b'{"action":"opened"}'
        sig = _sign(payload, "wrong_secret")
        assert verify_signature(payload, sig) is False

    def test_tampered_payload(self, mock_config_secret: None) -> None:
        payload = b'{"action":"opened"}'
        sig = _sign(payload)
        assert verify_signature(b'{"action":"reopened"}', sig) is False

    def test_empty_signature(self, mock_config_secret: None) -> None:
        payload = b'{"action":"opened"}'
        assert verify_signature(payload, "") is False

    def test_timing_safe_comparison(self, mock_config_secret: None) -> None:
        payload = b'{"action":"opened"}'
        sig = _sign(payload)
        assert verify_signature(payload, sig) is True
        bad_sig = sig[:-5] + "00000"
        assert verify_signature(payload, bad_sig) is False


class TestParseEvent:
    def test_parse_ping(self) -> None:
        evt = parse_event("ping", {"zen": "test"})
        assert isinstance(evt, UnknownEvent)
        assert evt.event_type == "ping"

    def test_parse_pr_opened(self) -> None:
        payload = {
            "action": "opened",
            "repository": {
                "name": "test-repo",
                "owner": {"login": "testuser"},
            },
            "pull_request": {"number": 1},
            "sender": {"login": "dev1"},
        }
        evt = parse_event("pull_request", payload)
        assert isinstance(evt, PROpenEvent)
        assert evt.owner == "testuser"
        assert evt.repo == "test-repo"
        assert evt.pr_number == 1
        assert evt.sender == "dev1"

    def test_parse_pr_reopened(self) -> None:
        payload = {
            "action": "reopened",
            "repository": {"name": "r", "owner": {"login": "o"}},
            "pull_request": {"number": 2},
            "sender": {"login": "d"},
        }
        evt = parse_event("pull_request", payload)
        assert isinstance(evt, PROpenEvent)
        assert evt.pr_number == 2

    def test_parse_pr_synchronize(self) -> None:
        payload = {
            "action": "synchronize",
            "repository": {"name": "r", "owner": {"login": "o"}},
            "pull_request": {"number": 3},
            "sender": {"login": "d"},
        }
        evt = parse_event("pull_request", payload)
        assert isinstance(evt, PRSyncEvent)
        assert evt.pr_number == 3

    def test_parse_pr_other_action(self) -> None:
        payload = {
            "action": "closed",
            "repository": {"name": "r", "owner": {"login": "o"}},
            "pull_request": {"number": 4},
        }
        evt = parse_event("pull_request", payload)
        assert isinstance(evt, UnknownEvent)

    def test_parse_issue_comment(self) -> None:
        payload = {
            "action": "created",
            "repository": {"name": "r", "owner": {"login": "o"}},
            "issue": {"pull_request": {"url": "https://api.github.com/repos/o/r/pulls/5"}},
            "comment": {"body": "/review", "id": 42},
            "sender": {"login": "reviewer"},
        }
        evt = parse_event("issue_comment", payload)
        assert isinstance(evt, IssueCommentEvent)
        assert evt.comment_body == "/review"
        assert evt.comment_id == 42
        assert evt.pr_number == 5

    def test_parse_issue_comment_no_pr(self) -> None:
        payload = {
            "action": "created",
            "repository": {"name": "r", "owner": {"login": "o"}},
            "issue": {},
            "comment": {"body": "regular issue comment"},
            "sender": {"login": "user"},
        }
        evt = parse_event("issue_comment", payload)
        assert isinstance(evt, IssueCommentEvent)
        assert evt.pr_number == 0

    def test_parse_installation(self) -> None:
        payload = {
            "action": "created",
            "installation": {"id": 999},
            "sender": {"login": "admin"},
        }
        evt = parse_event("installation", payload)
        assert isinstance(evt, InstallationEvent)
        assert evt.installation_id == 999

    def test_parse_installation_repositories(self) -> None:
        payload = {
            "action": "added",
            "installation": {"id": 888},
            "sender": {"login": "admin"},
        }
        evt = parse_event("installation_repositories", payload)
        assert isinstance(evt, InstallationEvent)
        assert evt.installation_id == 888

    def test_parse_unknown_event_type(self) -> None:
        evt = parse_event("push", {"ref": "refs/heads/main"})
        assert isinstance(evt, UnknownEvent)
        assert evt.event_type == "push"


class TestExtractPrIdentifiers:
    def test_from_pr_open_event(self) -> None:
        evt = PROpenEvent(
            event_type="pull_request", raw_payload={},
            owner="myowner", repo="myrepo", pr_number=42,
            action="opened",
        )
        owner, repo, pr = extract_pr_identifiers(evt)
        assert owner == "myowner"
        assert repo == "myrepo"
        assert pr == 42

    def test_from_issue_comment_event(self) -> None:
        evt = IssueCommentEvent(
            event_type="issue_comment", raw_payload={},
            owner="o", repo="r", pr_number=99,
            comment_body="/review",
        )
        owner, repo, pr = extract_pr_identifiers(evt)
        assert (owner, repo, pr) == ("o", "r", 99)

    def test_from_unknown_event(self) -> None:
        evt = UnknownEvent(event_type="unknown", raw_payload={})
        owner, repo, pr = extract_pr_identifiers(evt)
        assert owner == ""
        assert repo == ""
        assert pr == 0
