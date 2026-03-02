"""
仮想シミュレーション時計

Jiraのタイムスタンプは実際の登録日時で固定されるため、
シミュレーション内の「仮想日時」を別途管理し、
チケット本文・コメントに明示的に埋め込む方式を取る。

仮想日時の管理:
  simulation/state.yaml の virtual_date を参照・更新する

使い方:
  from simulation.clock import SimClock
  clock = SimClock()
  print(clock.today)           # "2026-03-05"
  clock.advance(days=3)        # 3日進める
  clock.set_date("2026-03-10") # 特定日付に設定
"""
import os
import yaml
from datetime import date, datetime, timedelta
from pathlib import Path

STATE_FILE = Path(__file__).parent / "state.yaml"


class SimClock:
    """シミュレーション仮想時計"""

    def __init__(self):
        self._state = self._load()

    def _load(self) -> dict:
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                return yaml.safe_load(f) or {}
        return {"virtual_date": "2026-03-02", "sprint": "Sprint 1", "day_in_sprint": 1}

    def _save(self):
        with open(STATE_FILE, "w") as f:
            yaml.dump(self._state, f, allow_unicode=True)

    @property
    def today(self) -> str:
        """仮想現在日付 (YYYY-MM-DD)"""
        return self._state.get("virtual_date", "2026-03-02")

    @property
    def today_date(self) -> date:
        return datetime.strptime(self.today, "%Y-%m-%d").date()

    @property
    def sprint(self) -> str:
        """現在のスプリント名"""
        return self._state.get("sprint", "Sprint 1")

    @property
    def day_in_sprint(self) -> int:
        """スプリント開始からの日数"""
        return self._state.get("day_in_sprint", 1)

    def advance(self, days: int = 1):
        """仮想時計を N 日進める"""
        current = self.today_date
        new_date = current + timedelta(days=days)
        self._state["virtual_date"] = new_date.strftime("%Y-%m-%d")
        self._state["day_in_sprint"] = self._state.get("day_in_sprint", 1) + days
        self._save()
        print(f"⏰ 仮想日時: {current} → {new_date.strftime('%Y-%m-%d')} (+{days}日)")

    def set_date(self, date_str: str, sprint: str = None, day_in_sprint: int = None):
        """仮想日時を指定日付に設定"""
        self._state["virtual_date"] = date_str
        if sprint:
            self._state["sprint"] = sprint
        if day_in_sprint is not None:
            self._state["day_in_sprint"] = day_in_sprint
        self._save()
        print(f"⏰ 仮想日時を {date_str} に設定")

    def timestamp_label(self) -> str:
        """チケット本文・コメントに埋め込む仮想タイムスタンプラベル"""
        return f"[🕐 仮想日時: {self.today} / {self.sprint} Day {self.day_in_sprint}]"

    def status(self) -> str:
        return (
            f"仮想日時: {self.today}\n"
            f"スプリント: {self.sprint}\n"
            f"経過日数: Day {self.day_in_sprint}"
        )
