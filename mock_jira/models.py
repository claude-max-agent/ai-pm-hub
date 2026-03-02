"""Mock Jira データモデル定義"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class JiraTicket:
    """Jiraチケット相当（GitHub Issue対応）"""
    number: int                       # GitHub Issue番号 = Jiraチケット番号
    key: str                          # 例: "PROJ-5" (PROJ = リポジトリ名プレフィックス)
    title: str
    body: str
    status: str                       # backlog/todo/in-progress/in-review/done/blocked
    priority: str                     # critical/high/medium/low
    ticket_type: str                  # feature/bug/task/legal-review/spike
    team: str                         # dev-a/dev-b/dev-c/tester/operator/legal
    sprint: Optional[str]             # "Sprint 1" 等
    assignees: list[str] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)
    url: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Sprint:
    """スプリント情報"""
    number: int
    title: str                        # "Sprint 1"
    start: str                        # "2026-03-02"
    end: str                          # "2026-03-16"
    goal: str
    open_count: int = 0
    closed_count: int = 0
    blocked_count: int = 0

    @property
    def completion_rate(self) -> float:
        total = self.open_count + self.closed_count
        if total == 0:
            return 0.0
        return self.closed_count / total * 100


@dataclass
class TeamStatus:
    """チームの現在の状態"""
    team_id: str
    team_name: str
    in_progress: list[JiraTicket] = field(default_factory=list)
    blocked: list[JiraTicket] = field(default_factory=list)
    done_today: list[JiraTicket] = field(default_factory=list)
