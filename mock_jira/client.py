"""
Jira Client - Jira REST API v3 を使用した実装

外部インターフェース（クラス名・メソッドシグネチャ）は MockJiraClient のまま維持する。
pm_agent/ のスクリプトはこのファイルの変更なしに動作する。
"""
import os
from typing import Optional

import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

from .models import JiraTicket, Sprint, TeamStatus

# .env ファイルから認証情報を読み込む
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

JIRA_BASE_URL = os.environ.get("JIRA_BASE_URL", "https://koshifuruzono.atlassian.net")
JIRA_EMAIL = os.environ.get("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN", "")
JIRA_PROJECT_KEY = os.environ.get("JIRA_PROJECT_KEY", "JZZG")

# ラベルのプレフィックス定義（GitHub Issues 時代との互換性維持）
STATUS_PREFIX = "status/"
PRIORITY_PREFIX = "priority/"
TEAM_PREFIX = "team/"
TYPE_PREFIX = "type/"

# Jira ステータスカテゴリ → 内部ステータス マッピング
# statusCategory.key を使用（言語に依存しない）
STATUS_CATEGORY_MAP = {
    "new": "todo",          # To Do
    "indeterminate": "in-progress",  # 進行中 / In Progress
    "done": "done",         # 完了 / Done
}

# 内部ステータス → Jira トランジション ID マッピング
# JZZG プロジェクトのトランジション ID（GET /rest/api/3/issue/{key}/transitions で確認済み）
STATUS_TO_TRANSITION = {
    "todo": "11",
    "in-progress": "21",
    "done": "31",
}

# Jira issuetype.name → 内部 ticket_type マッピング
ISSUETYPE_MAP = {
    "タスク": "task",
    "バグ": "bug",
    "ストーリー": "feature",
    "エピック": "feature",
    "サブタスク": "task",
    # 英語名のフォールバック
    "Task": "task",
    "Bug": "bug",
    "Story": "feature",
    "Epic": "feature",
    "Subtask": "task",
}

# 内部 ticket_type → Jira issuetype ID マッピング
TICKETTYPE_TO_ISSUETYPE_ID = {
    "task": "10001",
    "bug": "10002",
    "feature": "10003",
    "spike": "10001",
    "legal-review": "10001",
}


def _make_auth() -> HTTPBasicAuth:
    """Basic Auth オブジェクトを生成する"""
    return HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)


def _make_headers() -> dict:
    """共通 HTTPヘッダーを生成する"""
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _adf_to_text(description) -> str:
    """Atlassian Document Format (ADF) をプレーンテキストに変換する"""
    if description is None:
        return ""
    if isinstance(description, str):
        return description

    # ADF は dict 形式
    parts = []
    content = description.get("content", [])
    for block in content:
        for inline in block.get("content", []):
            if inline.get("type") == "text":
                parts.append(inline.get("text", ""))
        parts.append("\n")
    return "".join(parts).strip()


def _text_to_adf(text: str) -> dict:
    """プレーンテキストを ADF 形式に変換する"""
    if not text:
        return {
            "type": "doc",
            "version": 1,
            "content": [],
        }
    paragraphs = []
    for line in text.split("\n\n"):
        line = line.strip()
        if line:
            paragraphs.append({
                "type": "paragraph",
                "content": [{"type": "text", "text": line}],
            })
    if not paragraphs:
        paragraphs.append({
            "type": "paragraph",
            "content": [{"type": "text", "text": text}],
        })
    return {
        "type": "doc",
        "version": 1,
        "content": paragraphs,
    }


def _extract_label(labels: list[str], prefix: str) -> str:
    """ラベルリストから指定プレフィックスの値を取り出す"""
    for label in labels:
        if label.startswith(prefix):
            return label[len(prefix):]
    return ""


def _issue_to_ticket(issue: dict) -> JiraTicket:
    """Jira Issue dict を JiraTicket に変換する"""
    fields = issue.get("fields", {})
    labels = fields.get("labels", [])

    # ステータス: Jira の statusCategory.key を使って変換し、blocked ラベルで上書き
    status_category_key = (
        fields.get("status", {})
        .get("statusCategory", {})
        .get("key", "new")
    )
    status = STATUS_CATEGORY_MAP.get(status_category_key, "todo")
    if "blocked" in labels:
        status = "blocked"

    # ラベルから team, priority, type を取り出す（GitHub Issues 互換）
    team = _extract_label(labels, TEAM_PREFIX)
    priority_from_label = _extract_label(labels, PRIORITY_PREFIX)
    type_from_label = _extract_label(labels, TYPE_PREFIX)

    # priority: ラベルを優先し、なければ Jira priority フィールドを使用
    if priority_from_label:
        priority = priority_from_label
    else:
        jira_priority_name = fields.get("priority", {}) or {}
        priority_name = jira_priority_name.get("name", "Medium").lower()
        priority_map = {
            "highest": "critical",
            "high": "high",
            "medium": "medium",
            "low": "low",
            "lowest": "low",
        }
        priority = priority_map.get(priority_name, "medium")

    # ticket_type: type/ ラベルを優先し、なければ issuetype.name を使用
    if type_from_label:
        ticket_type = type_from_label
    else:
        issuetype_name = (fields.get("issuetype") or {}).get("name", "タスク")
        ticket_type = ISSUETYPE_MAP.get(issuetype_name, "task")

    # sprint: fixVersions を sprint のプロキシとして使用
    fix_versions = fields.get("fixVersions", []) or []
    sprint = fix_versions[0]["name"] if fix_versions else None

    # key から number を取り出す（例: "JZZG-5" → 5）
    key = issue.get("key", "")
    try:
        number = int(key.split("-")[-1])
    except (ValueError, IndexError):
        number = 0

    # assignees: Jira は単一 assignee（リストで返す）
    assignee = fields.get("assignee")
    assignees = [assignee["displayName"]] if assignee else []

    return JiraTicket(
        number=number,
        key=key,
        title=fields.get("summary", ""),
        body=_adf_to_text(fields.get("description")),
        status=status,
        priority=priority,
        ticket_type=ticket_type,
        team=team,
        sprint=sprint,
        assignees=assignees,
        labels=labels,
        url=f"{JIRA_BASE_URL}/browse/{key}",
        created_at=fields.get("created"),
        updated_at=fields.get("updated"),
    )


class MockJiraClient:
    """Jira 互換クライアント（Jira REST API v3 バックエンド）

    クラス名・メソッドシグネチャは GitHub Issues 版と完全互換。
    """

    def __init__(self, repo: str = ""):
        # repo 引数は後方互換性のために残す（使用しない）
        self.base_url = JIRA_BASE_URL
        self.project_key = JIRA_PROJECT_KEY
        self.auth = _make_auth()
        self.headers = _make_headers()

    def _get(self, path: str, params: dict = None) -> dict:
        """GET リクエストを送信し JSON を返す"""
        resp = requests.get(
            f"{self.base_url}{path}",
            params=params,
            auth=self.auth,
            headers=self.headers,
        )
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, json_body: dict) -> dict:
        """POST リクエストを送信し JSON を返す"""
        resp = requests.post(
            f"{self.base_url}{path}",
            json=json_body,
            auth=self.auth,
            headers=self.headers,
        )
        resp.raise_for_status()
        if resp.status_code == 204 or not resp.content:
            return {}
        return resp.json()

    def _put(self, path: str, json_body: dict) -> dict:
        """PUT リクエストを送信し JSON を返す"""
        resp = requests.put(
            f"{self.base_url}{path}",
            json=json_body,
            auth=self.auth,
            headers=self.headers,
        )
        resp.raise_for_status()
        if resp.status_code == 204 or not resp.content:
            return {}
        return resp.json()

    # ── チケット検索 ────────────────────────────────────────────

    def search(
        self,
        status: Optional[str] = None,
        team: Optional[str] = None,
        sprint: Optional[str] = None,
        priority: Optional[str] = None,
        state: str = "open",
    ) -> list[JiraTicket]:
        """JQL を使ったフィルタ検索（GitHub Issues 版の search() 互換）"""
        jql_parts = [f"project = {self.project_key}"]

        # state: "open" → 未完了、"closed" → 完了
        if state == "open":
            jql_parts.append('statusCategory != Done')
        elif state == "closed":
            jql_parts.append('statusCategory = Done')

        # ラベルフィルタ
        if team:
            jql_parts.append(f'labels = "{TEAM_PREFIX}{team}"')
        if priority:
            jql_parts.append(f'labels = "{PRIORITY_PREFIX}{priority}"')

        # status: blocked はラベルで、それ以外は statusCategory で検索
        if status:
            if status == "blocked":
                jql_parts.append('labels = "blocked"')
            elif status == "todo":
                jql_parts.append('statusCategory = "To Do"')
            elif status == "in-progress":
                jql_parts.append('statusCategory = "In Progress"')
            elif status == "done":
                jql_parts.append('statusCategory = Done')
            else:
                # status/ ラベルによるフォールバック
                jql_parts.append(f'labels = "{STATUS_PREFIX}{status}"')

        jql = " AND ".join(jql_parts) + " ORDER BY created DESC"

        result = self._post(
            "/rest/api/3/search/jql",
            {
                "jql": jql,
                "maxResults": 100,
                "fields": [
                    "summary", "description", "status", "issuetype",
                    "labels", "assignee", "priority", "fixVersions",
                    "created", "updated",
                ],
            },
        )

        issues = result.get("issues", [])
        tickets = [_issue_to_ticket(i) for i in issues]

        # sprint フィルタ（fixVersions ベース）
        if sprint:
            tickets = [t for t in tickets if t.sprint == sprint]

        return tickets

    def get_ticket(self, issue_number: int) -> JiraTicket:
        """チケット番号でチケットを取得（GitHub Issues 版の get_ticket() 互換）"""
        key = f"{self.project_key}-{issue_number}"
        issue = self._get(f"/rest/api/3/issue/{key}")
        return _issue_to_ticket(issue)

    def get_ticket_by_key(self, issue_key: str) -> JiraTicket:
        """Jira キー（例: JZZG-5）でチケットを取得"""
        issue = self._get(f"/rest/api/3/issue/{issue_key}")
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
        ]
        # status が blocked の場合はラベルを追加
        if status == "blocked":
            labels.append("blocked")

        issuetype_id = TICKETTYPE_TO_ISSUETYPE_ID.get(ticket_type, "10001")

        fields: dict = {
            "project": {"key": self.project_key},
            "summary": title,
            "issuetype": {"id": issuetype_id},
            "description": _text_to_adf(body),
            "labels": labels,
        }

        # sprint のプロキシとして fixVersions を使用
        if sprint:
            fields["fixVersions"] = [{"name": sprint}]

        result = self._post("/rest/api/3/issue", {"fields": fields})
        created_key = result.get("key", "")

        # status が todo 以外の場合はトランジションを実行
        if status and status not in ("todo", "blocked") and status in STATUS_TO_TRANSITION:
            try:
                transition_id = STATUS_TO_TRANSITION[status]
                self._post(
                    f"/rest/api/3/issue/{created_key}/transitions",
                    {"transition": {"id": transition_id}},
                )
            except Exception:
                pass  # トランジション失敗は無視

        # 番号を key から取り出して get_ticket を呼ぶ
        try:
            number = int(created_key.split("-")[-1])
        except (ValueError, IndexError):
            number = 0
        return self.get_ticket(number)

    def transition_issue(self, issue_number: int, new_status: str) -> JiraTicket:
        """ステータス変更（Jira: Transition Issue 相当）"""
        key = f"{self.project_key}-{issue_number}"

        if new_status == "blocked":
            # blocked は Jira ステータスではなくラベルで管理
            ticket = self.get_ticket(issue_number)
            existing_labels = list(ticket.labels)
            if "blocked" not in existing_labels:
                existing_labels.append("blocked")
            self._put(
                f"/rest/api/3/issue/{key}",
                {"fields": {"labels": existing_labels}},
            )
        else:
            # ラベルから "blocked" を除去
            ticket = self.get_ticket(issue_number)
            existing_labels = [lb for lb in ticket.labels if lb != "blocked"]
            self._put(
                f"/rest/api/3/issue/{key}",
                {"fields": {"labels": existing_labels}},
            )

            # Jira トランジションを実行
            transition_id = STATUS_TO_TRANSITION.get(new_status)
            if transition_id:
                self._post(
                    f"/rest/api/3/issue/{key}/transitions",
                    {"transition": {"id": transition_id}},
                )

        return self.get_ticket(issue_number)

    def assign_team(self, issue_number: int, team: str) -> JiraTicket:
        """チーム割り当て（ラベルを更新）"""
        key = f"{self.project_key}-{issue_number}"
        ticket = self.get_ticket(issue_number)

        # 既存の team/ ラベルを除去して新しいものを追加
        labels = [lb for lb in ticket.labels if not lb.startswith(TEAM_PREFIX)]
        labels.append(f"{TEAM_PREFIX}{team}")

        self._put(
            f"/rest/api/3/issue/{key}",
            {"fields": {"labels": labels}},
        )
        return self.get_ticket(issue_number)

    def add_comment(self, issue_number: int, body: str) -> None:
        """コメント追加（Jira: Add Comment 相当）"""
        key = f"{self.project_key}-{issue_number}"
        self._post(
            f"/rest/api/3/issue/{key}/comment",
            {"body": _text_to_adf(body)},
        )

    # ── スプリント情報 ──────────────────────────────────────────

    def get_sprint_status(self, sprint_name: str) -> Sprint:
        """スプリント進捗情報を取得"""
        open_tickets = self.search(sprint=sprint_name, state="open")
        closed_tickets = self.search(sprint=sprint_name, state="closed")
        blocked_tickets = [t for t in open_tickets if t.status == "blocked"]

        import yaml
        import pathlib
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
        import yaml
        import pathlib
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
