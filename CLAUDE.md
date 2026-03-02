# ai-pm-hub

AI駆動プロジェクト管理システム - Claude × GitHub Issues による Mock Jira PM自動化

## プロジェクト概要

このリポジトリは **AI駆動PM（Project Management）の練習システム** です。
実際のJiraの代わりに GitHub Issues + Labels + Milestones を「Mock Jira」として使い、
ClaudeがPM業務（チケットトリアージ・進捗管理・レポート生成）を自動化します。

## チーム構成

| チーム | ラベル | 役割 |
|--------|--------|------|
| 開発チームA | `team/dev-a` | 領域A担当（フロントエンド等） |
| 開発チームB | `team/dev-b` | 領域B担当（バックエンド等） |
| 開発チームC | `team/dev-c` | 領域C担当（インフラ等） |
| テスターチーム | `team/tester` | QA・テスト全般 |
| オペレーターチーム | `team/operator` | 設定値決定・一部テスト |
| 法務チーム | `team/legal` | 法的確認・承認 |

## ラベル体系

### ステータス（Jiraワークフロー互換）
```
status/backlog → status/todo → status/in-progress → status/in-review → status/done
                                                   → status/blocked
```

### 優先度
- `priority/critical`: ブロッカー・最優先対応
- `priority/high`: 高優先度
- `priority/medium`: 中優先度（デフォルト）
- `priority/low`: 低優先度

### タイプ
- `type/feature`: 機能追加
- `type/bug`: バグ修正
- `type/task`: タスク（実装を伴わない作業）
- `type/legal-review`: 法務確認が必要
- `type/spike`: 調査・検証

## スプリント構成（2ヶ月 = 4スプリント）

| Milestone | 期間 | 目的 |
|-----------|------|------|
| Sprint 1 | 〜2026-03-16 | セットアップ・初期実装 |
| Sprint 2 | 〜2026-03-30 | コア機能実装 |
| Sprint 3 | 〜2026-04-13 | テスト・法務確認 |
| Sprint 4 | 〜2026-04-27 | 仕上げ・リリース準備 |

## Claudeへの主要指示

### チケットトリアージ
新しいIssueを見て、適切なラベル（チーム・優先度・タイプ・ステータス）を付与し、
スプリントのMilestoneを設定する。担当チームが不明な場合はコメントで確認する。

### 朝会サマリー生成
```bash
python pm_agent/standup.py
```
全チームの `status/in-progress` と `status/blocked` のIssueをまとめ、
チーム別の進捗サマリーを日本語で生成してDiscordに通知する。

### スプリントレポート生成
```bash
python pm_agent/sprint_report.py --sprint "Sprint 1"
```
指定スプリントのIssue一覧から完了率・ブロッカー・残課題を集計し、
日本語ナラティブレポートを生成する。

### ステータス変更
IssueのステータスラベルをJiraのトランジションと同様に変更する:
```python
from mock_jira.client import MockJiraClient
client = MockJiraClient()
client.transition_issue(issue_number=5, new_status="in-progress")
```

## API操作パターン

### GitHub APIの使い方
このリポジトリでは `gh` CLIまたは `mock_jira/client.py` 経由でGitHub Issues APIを操作する。

```bash
# 特定チームのIn-Progress IssueをJQL風に検索
gh issue list --label "team/dev-a,status/in-progress" --json number,title,assignees

# 新規Issue作成（Jiraチケット作成相当）
gh issue create --title "タイトル" --label "team/dev-a,priority/medium,type/feature,status/todo" --milestone "Sprint 1"

# ステータス変更（ラベル操作）
gh issue edit 5 --remove-label "status/todo" --add-label "status/in-progress"
```

## 開発ガイドライン

- **GitHub Actionsは現在未設定**（Admin承認待ち）
- **Mock Jira** の実装は `mock_jira/client.py` にカプセル化
  - 将来のJira本番移行時はこのファイルのみ変更
- スクリプトは手動実行またはcronで定期実行

## ディレクトリ構成

```
ai-pm-hub/
├── CLAUDE.md              # このファイル
├── README.md
├── mock_jira/             # Mock Jira実装
│   ├── __init__.py
│   ├── client.py          # GitHub Issues APIをJira風にラップ
│   ├── models.py          # データ構造定義
│   └── labels.yaml        # ラベル定義マスタ
├── pm_agent/              # PM自動化スクリプト
│   ├── __init__.py
│   ├── standup.py         # 朝会サマリー生成
│   ├── sprint_report.py   # スプリントレポート生成
│   └── triage.py          # チケット自動トリアージ
├── prompts/               # Claudeプロンプトテンプレート
│   ├── triage.md
│   ├── standup.md
│   └── sprint_report.md
├── config/
│   ├── teams.yaml         # チーム定義
│   └── project.yaml       # プロジェクト設定
└── docs/
    ├── setup.md
    └── workflow.md
```
