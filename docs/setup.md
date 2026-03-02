# セットアップガイド

## 前提条件

- Python 3.11+
- GitHub CLI (`gh`) がインストール済みでログイン済み
- Anthropic API Key（チケットトリアージ・レポート生成に使用）

## インストール手順

```bash
# 1. リポジトリクローン
git clone https://github.com/claude-max-agent/ai-pm-hub.git
cd ai-pm-hub

# 2. 依存パッケージ
pip install anthropic pyyaml

# 3. 環境変数設定
export ANTHROPIC_API_KEY="sk-ant-..."
# Discord通知を使う場合
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."

# 4. GitHub CLIのログイン確認
gh auth status
```

## 動作確認

```bash
# リポジトリのIssue一覧を確認
gh issue list --repo claude-max-agent/ai-pm-hub

# ラベル一覧を確認
gh api repos/claude-max-agent/ai-pm-hub/labels --jq '.[].name'

# マイルストーン（スプリント）一覧を確認
gh api repos/claude-max-agent/ai-pm-hub/milestones --jq '.[].title'
```

## テスト用Issueの作成

```bash
# サンプルチケットを作成してトリアージをテスト
gh issue create \
  --repo claude-max-agent/ai-pm-hub \
  --title "ユーザーログイン機能の実装" \
  --body "メールアドレスとパスワードによるログイン機能。JWT認証を使用する。"

# 作成されたIssue番号を確認して自動トリアージ
python pm_agent/triage.py --issue <番号>
```

## よくある問題

### `gh: command not found`
GitHub CLI のインストールが必要: https://cli.github.com/

### `anthropic` パッケージが未インストール
```bash
pip install anthropic
```
インストールなしでも `mock_jira/client.py` は動作するが、
AI生成機能（トリアージ・レポート）は手動対応が必要。
