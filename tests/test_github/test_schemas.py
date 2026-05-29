from app.github.schemas import (
    FileChange,
    PRDetail,
    RepoStructure,
    PROpenEvent,
    PRSyncEvent,
    IssueCommentEvent,
    InstallationEvent,
    UnknownEvent,
    BaseWebhookEvent,
)


class TestFileChange:
    def test_basic_file_change(self) -> None:
        fc = FileChange(filename="src/app.py", status="modified", patch="@@ -1,3 +1,4 @@")
        assert fc.filename == "src/app.py"
        assert fc.status == "modified"
        assert fc.patch == "@@ -1,3 +1,4 @@"
        assert fc.previous_filename is None
        assert fc.additions == 0

    def test_renamed_file(self) -> None:
        fc = FileChange(
            filename="src/new.py",
            status="renamed",
            previous_filename="src/old.py",
            additions=10,
            deletions=5,
            changes=15,
        )
        assert fc.previous_filename == "src/old.py"
        assert fc.additions == 10
        assert fc.deletions == 5

    def test_default_values(self) -> None:
        fc = FileChange(filename="test.py", status="added")
        assert fc.patch is None
        assert fc.previous_filename is None
        assert fc.additions == 0
        assert fc.deletions == 0
        assert fc.changes == 0


class TestPRDetail:
    def test_basic_pr_detail(self) -> None:
        pr = PRDetail(
            pr_id=100,
            number=1,
            title="Fix bug",
            body="Fixes issue #42",
            author="dev",
            head_sha="abc",
            base_sha="def",
            head_branch="fix/bug",
            base_branch="main",
        )
        assert pr.pr_id == 100
        assert pr.number == 1
        assert pr.title == "Fix bug"
        assert pr.head_sha == "abc"
        assert pr.files == []

    def test_pr_with_files(self) -> None:
        files = [FileChange(filename="a.py", status="modified")]
        pr = PRDetail(
            pr_id=200, number=2, title="Feature", body=None,
            author="dev", head_sha="111", base_sha="222",
            head_branch="feat/x", base_branch="main",
            files=files,
        )
        assert len(pr.files) == 1
        assert pr.files[0].filename == "a.py"
        assert pr.body is None


class TestRepoStructure:
    def test_default_empty(self) -> None:
        rs = RepoStructure()
        assert rs.tree == []
        assert rs.config_files == {}
        assert rs.dependency_files == {}

    def test_with_data(self) -> None:
        rs = RepoStructure(
            tree=["src/", "src/main.py", "requirements.txt"],
            config_files={"pyproject.toml": "[tool.black]"},
            dependency_files={"requirements.txt": "fastapi>=0.110.0"},
        )
        assert len(rs.tree) == 3
        assert "pyproject.toml" in rs.config_files


class TestWebhookEvents:
    def test_pr_open_event(self) -> None:
        evt = PROpenEvent(
            event_type="pull_request",
            raw_payload={"action": "opened"},
            owner="testowner",
            repo="testrepo",
            pr_number=5,
            action="opened",
            sender="user1",
        )
        assert evt.owner == "testowner"
        assert evt.repo == "testrepo"
        assert evt.pr_number == 5
        assert evt.action == "opened"

    def test_pr_sync_event(self) -> None:
        evt = PRSyncEvent(
            event_type="pull_request",
            raw_payload={"action": "synchronize"},
            owner="owner1",
            repo="repo1",
            pr_number=10,
            action="synchronize",
        )
        assert evt.owner == "owner1"
        assert evt.pr_number == 10

    def test_issue_comment_event(self) -> None:
        evt = IssueCommentEvent(
            event_type="issue_comment",
            raw_payload={},
            owner="owner",
            repo="repo",
            pr_number=3,
            comment_body="/review",
            comment_id=100,
            sender="reviewer",
        )
        assert evt.comment_body == "/review"
        assert evt.comment_id == 100
        assert evt.sender == "reviewer"

    def test_installation_event(self) -> None:
        evt = InstallationEvent(
            event_type="installation",
            raw_payload={},
            action="created",
            installation_id=123,
            sender="admin",
        )
        assert evt.installation_id == 123
        assert evt.action == "created"

    def test_unknown_event(self) -> None:
        evt = UnknownEvent(event_type="unknown_type", raw_payload={})
        assert evt.event_type == "unknown_type"

    def test_base_event_defaults(self) -> None:
        evt = BaseWebhookEvent(event_type="test", raw_payload={})
        assert evt.owner == ""
        assert evt.repo == ""
        assert evt.pr_number == 0
