"""
Mock Jira Client - GitHub Issues API を Jira 互換インターフェースでラップする

将来 Jira 本番移行時はこのファイルのみ差し替えればOK。
外部からは JiraTicket / Sprint データ構造のみを扱う。
"""
import json
import os
import subprocess
from typing import Optional
from .models import JiraTicket, Sprint, TeamStatus


# ラベルのプレフィックス定義
STATUS_PREFIX = "status/"
PRIORITY_PREFIX = "priority/"
TEAM_PREFIX = "team/"
TYPE_PREFIX = "type/"

REPO = os.getenv("GITHUB_REPO", "claude-max-agent/ai-pm-hub")


def _gh(*args) -> dict | list:
    """gh CLI を呼び出して JSON を返す"""
    result = subprocess.run(
        ["gh"] + list(args),
        capture_output=True, text=True, check=True
    )
    return json.loads(result.stdout)


def _extract_label(labels: list[str], prefix: str) -> str:
    """ラベルリストから指定プレフィックスの値を取り出す"""
    for label in labels:
        if label.startswith(prefix):
            return label[len(prefix):]
    return ""


def _issue_to_ticket(issue: dict) -> JiraTicket:
    """GitHub Issue dict を JiraTicket に変換"""
    labels = [lb["name"] for lb in issue.get("labels", [])]
    milestone = issue.get("milestone") or {}
    return JiraTicket(
        number=issue["number"],
        key=f"PROJ-{issue['number']}",
        title=issue["title"],
        body=issue.get("body") or "",
        status=_extract_label(labels, STATUS_PREFIX) or "backlog",
        priority=_extract_label(labels, PRIORITY_PREFIX) or "medium",
        ticket_type=_extract_label(labels, TYPE_PREFIX) or "task",
        team=_extract_label(labels, TEAM_PREFIX),
        sprint=milestone.get("title"),
        assignees=[a["login"] for a in issue.get("assignees", [])],
        labels=labels,
        url=issue.get("html_url", ""),
        created_at=issue.get("created_at"),
        updated_at=issue.get("updated_at"),
    )


class MockJiraClient:
    """Jira 互換クライアント（GitHub Issues バックエンド）"""

    def __init__(self, repo: str = REPO):
        self.repo = repo

    # ── チケット検索 ────────────────────────────────────────────

    def search(
        self,
        status: Optional[str] = None,
        team: Optional[str] = None,
        sprint: Optional[str] = None,
        priority: Optional[str] = None,
        state: str = "open",
    ) -> list[JiraTicket]:
        """JQL 相当のフィルタ検索"""
        labels = []
        if status:
            labels.append(f"{STATUS_PREFIX}{status}")
        if team:
            labels.append(f"{TEAM_PREFIX}{team}")
        if priority:
            labels.append(f"{PRIORITY_PREFIX}{priority}")

        args = [
            "issue", "list",
            "--repo", self.repo,
            "--state", state,
            "--json", "number,title,body,labels,milestone,assignees,html_url,createdAt,updatedAt",
            "--limit", "100",
        ]
        if labels:
            args += ["--label", ",".join(labels)]

        issues = _gh(*args)
        tickets = [_issue_to_ticket(i) for i in issues]

        # スプリントフィルタ（ミルストーンはラベルと別管理）
        if sprint:
            tickets = [t for t in tickets if t.sprint == sprint]

        return tickets

    def get_ticket(self, issue_number: int) -> JiraTicket:
        """Issue番号でチケットを取得"""
        issue = _gh(
            "issue", "view", str(issue_number),
            "--repo", self.repo,
            "--json", "number,title,body,labels,milestone,assignees,html_url,createdAt,updatedAt",
        )
        return _issue_to_ticket(issue)

    # ── チケット作成・更新 ──────────────────────────────────────

    def create_ticket(
        self,
        title: str,
        body: str,
        team: str,
        ticket_type: str = "task",
        priority: str = "medium",
        sprint: Optional[str] = None,
        status: str = "todo",
    ) -> JiraTicket:
        """新規チケット作成（Jira: Create Issue 相当）"""
        labels = [
            f"{TEAM_PREFIX}{team}",
            f"{TYPE_PREFIX}{ticket_type}",
            f"{PRIORITY_PREFIX}{priority}",
            f"{STATUS_PREFIX}{status}",
        ]
        args = [
            "issue", "create",
            "--repo", self.repo,
            "--title", title,
            "--body", body,
            "--label", ",".join(labels),
        ]
        if sprint:
            args += ["--milestone", sprint]

        result = subprocess.run(
            ["gh"] + args,
            capture_output=True, text=True, check=True
        )
        # 作成されたURLからIssue番号を抽出
        url = result.stdout.strip()
        issue_number = int(url.split("/")[-1])
        return self.get_ticket(issue_number)

    def transition_issue(self, issue_number: int, new_status: str) -> JiraTicket:
        """ステータス変更（Jira: Transition Issue 相当）"""
        ticket = self.get_ticket(issue_number)

        # 既存のstatusラベルを除去して新しいものを追加
        old_status_label = f"{STATUS_PREFIX}{ticket.status}"
        new_status_label = f"{STATUS_PREFIX}{new_status}"

        subprocess.run([
            "gh", "issue", "edit", str(issue_number),
            "--repo", self.repo,
            "--remove-label", old_status_label,
            "--add-label", new_status_label,
        ], capture_output=True, check=True)

        return self.get_ticket(issue_number)

    def assign_team(self, issue_number: int, team: str) -> JiraTicket:
        """チーム割り当て"""
        ticket = self.get_ticket(issue_number)

        # 既存のteamラベルを除去
        for existing_label in ticket.labels:
            if existing_label.startswith(TEAM_PREFIX):
                subprocess.run([
                    "gh", "issue", "edit", str(issue_number),
                    "--repo", self.repo,
                    "--remove-label", existing_label,
                ], capture_output=True, check=True)

        subprocess.run([
            "gh", "issue", "edit", str(issue_number),
            "--repo", self.repo,
            "--add-label", f"{TEAM_PREFIX}{team}",
        ], capture_output=True, check=True)

        return self.get_ticket(issue_number)

    def add_comment(self, issue_number: int, body: str):
        """コメント追加（Jira: Add Comment 相当）"""
        subprocess.run([
            "gh", "issue", "comment", str(issue_number),
            "--repo", self.repo,
            "--body", body,
        ], capture_output=True, check=True)

    # ── スプリント情報 ──────────────────────────────────────────

    def get_sprint_status(self, sprint_name: str) -> Sprint:
        """スプリント進捗情報を取得"""
        open_tickets = self.search(sprint=sprint_name, state="open")
        closed_tickets = self.search(sprint=sprint_name, state="closed")
        blocked_tickets = [t for t in open_tickets if t.status == "blocked"]

        # config から sprint 情報を読む
        import yaml, pathlib
        config_path = pathlib.Path(__file__).parent.parent / "config" / "project.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)

        sprint_config = next(
            (s for s in config["sprints"] if s["milestone"] == sprint_name),
            {"number": 0, "start": "", "end": "", "goal": ""}
        )

        sprint = Sprint(
            number=sprint_config["number"],
            title=sprint_name,
            start=sprint_config["start"],
            end=sprint_config["end"],
            goal=sprint_config["goal"],
            open_count=len(open_tickets),
            closed_count=len(closed_tickets),
            blocked_count=len(blocked_tickets),
        )
        return sprint

    def get_team_status(self, team_id: str) -> TeamStatus:
        """チームの現在状態を取得"""
        import yaml, pathlib
        config_path = pathlib.Path(__file__).parent.parent / "config" / "teams.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)

        team_config = next(
            (t for t in config["teams"] if t["id"] == team_id),
            {"name": team_id}
        )

        in_progress = self.search(status="in-progress", team=team_id)
        blocked = self.search(status="blocked", team=team_id)
        done = self.search(status="done", team=team_id, state="closed")

        return TeamStatus(
            team_id=team_id,
            team_name=team_config.get("name", team_id),
            in_progress=in_progress,
            blocked=blocked,
            done_today=done,
        )
