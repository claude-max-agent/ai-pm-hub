# ai-pm-hub

AI駆動プロジェクト管理システム - Claude × GitHub Issues による PM自動化練習システム

## 概要

実際のJiraの代わりに **GitHub Issues + Labels + Milestones** を「Mock Jira」として使い、
Claude AI がPM業務（チケットトリアージ・進捗管理・レポート生成）を自動化します。

将来的に本番Jiraへ移行する際は `mock_jira/client.py` のみ差し替えればOK。

## チーム構成

| チーム | 人数 | 役割 |
|--------|------|------|
| 開発チームA | 3-4人 | フロントエンド・UI |
| 開発チームB | 3-4人 | バックエンド・API |
| 開発チームC | 3-4人 | インフラ・データ基盤 |
| テスターチーム | 3-4人 | QA・テスト全般 |
| オペレーターチーム | 3-4人 | 設定値決定・運用テスト |
| 法務チーム | 3-4人 | 法的確認・リスク管理 |

## セットアップ

```bash
# 1. リポジトリクローン
git clone https://github.com/claude-max-agent/ai-pm-hub.git
cd ai-pm-hub

# 2. 依存パッケージインストール
pip install anthropic pyyaml

# 3. 環境変数設定（任意: Discord通知を使う場合）
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

## 使い方

### チケットトリアージ（自動ラベル割り当て）

```bash
# 特定Issueをトリアージ
python pm_agent/triage.py --issue 5

# シミュレーション（実際の変更なし）
python pm_agent/triage.py --issue 5 --dry-run

# 未割り当て全件を一括トリアージ
python pm_agent/triage.py --all-unassigned
```

### 朝会サマリー生成

```bash
python pm_agent/standup.py
python pm_agent/standup.py --discord  # Discord通知付き
```

### スプリントレポート生成

```bash
python pm_agent/sprint_report.py --sprint "Sprint 1"
python pm_agent/sprint_report.py --sprint "Sprint 1" --discord
```

### GitHub CLIで直接操作（JQL相当）

```bash
# 開発チームAの進行中チケット
gh issue list --label "team/dev-a,status/in-progress" --json number,title

# 法務チームの未着手チケット
gh issue list --label "team/legal,status/todo"

# ブロック中の全チケット
gh issue list --label "status/blocked"

# Sprint 1のチケット一覧
gh issue list --milestone "Sprint 1"
```

## ラベル体系

```
チーム:    team/dev-a  team/dev-b  team/dev-c  team/tester  team/operator  team/legal
ステータス: status/backlog → todo → in-progress → in-review → done
                                                → blocked
優先度:    priority/critical  high  medium  low
タイプ:    type/feature  bug  task  legal-review  spike
```

## Mock Jira API

```python
from mock_jira.client import MockJiraClient

client = MockJiraClient()

# チケット作成
ticket = client.create_ticket(
    title="ユーザー認証機能の実装",
    body="詳細説明...",
    team="dev-b",
    ticket_type="feature",
    priority="high",
    sprint="Sprint 1",
)

# ステータス変更
client.transition_issue(ticket.number, "in-progress")

# スプリント進捗確認
sprint = client.get_sprint_status("Sprint 1")
print(f"完了率: {sprint.completion_rate:.1f}%")

# チーム状況確認
status = client.get_team_status("dev-a")
```

## スプリント計画

| Sprint | 期間 | 目標 |
|--------|------|------|
| Sprint 1 | 2026-03-02 〜 03-16 | セットアップ・初期実装 |
| Sprint 2 | 2026-03-17 〜 03-30 | コア機能実装 |
| Sprint 3 | 2026-03-31 〜 04-13 | テスト・法務確認 |
| Sprint 4 | 2026-04-14 〜 04-27 | 仕上げ・リリース準備 |

## 参考: claude-agent-hub

このリポジトリの設計は [claude-agent-hub](https://github.com/claude-max-agent/claude-agent-hub) を参考にしています。
