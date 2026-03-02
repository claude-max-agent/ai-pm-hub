"""
スプリントレポート自動生成

指定スプリントの進捗を集計して日本語ナラティブレポートを生成する。

使い方:
  python pm_agent/sprint_report.py --sprint "Sprint 1"
  python pm_agent/sprint_report.py --sprint "Sprint 1" --discord
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mock_jira.client import MockJiraClient


SPRINT_REPORT_PROMPT = """あなたはAI PMアシスタントです。以下のスプリントデータをもとに週次レポートを日本語で生成してください。

## スプリント情報
スプリント名: {sprint_name}
期間: {start} 〜 {end}
目標: {goal}

## 進捗データ
- 完了チケット数: {closed_count}件
- 残オープン数: {open_count}件
- ブロック中: {blocked_count}件
- 完了率: {completion_rate:.1f}%

## チーム別状況
{team_breakdown}

## 出力形式
以下の形式で生成してください:

**📊 スプリントレポート: {sprint_name}**
**期間:** {start} 〜 {end}
**目標:** {goal}

### 進捗サマリー
{進捗の全体評価と完了率}

### チーム別ハイライト
{各チームの主要な進捗・懸念点}

### リスク・ブロッカー
{ブロック中のチケットや期限リスク}

### 次スプリントへの引き継ぎ
{未完了チケットの方針}
"""


def generate_sprint_report(sprint_name: str, notify_discord: bool = False):
    client = MockJiraClient()

    # スプリント全体の状況
    sprint = client.get_sprint_status(sprint_name)
    print(f"スプリント: {sprint_name}")
    print(f"  完了: {sprint.closed_count}件 / 全体: {sprint.open_count + sprint.closed_count}件 ({sprint.completion_rate:.1f}%)")
    print(f"  ブロック中: {sprint.blocked_count}件")

    # チーム別内訳
    team_ids = ["dev-a", "dev-b", "dev-c", "tester", "operator", "legal"]
    team_breakdown = ""
    for team_id in team_ids:
        in_prog = client.search(status="in-progress", team=team_id, sprint=sprint_name)
        blocked = client.search(status="blocked", team=team_id, sprint=sprint_name)
        done = client.search(status="done", team=team_id, sprint=sprint_name, state="closed")
        if in_prog or blocked or done:
            team_breakdown += f"\n**{team_id}**: 完了{len(done)}件 / 進行中{len(in_prog)}件 / ブロック{len(blocked)}件\n"
            for t in blocked:
                team_breakdown += f"  - ⚠ PROJ-{t.number}: {t.title}\n"

    try:
        import anthropic
        api_client = anthropic.Anthropic()
        prompt = SPRINT_REPORT_PROMPT.format(
            sprint_name=sprint_name,
            start=sprint.start,
            end=sprint.end,
            goal=sprint.goal,
            closed_count=sprint.closed_count,
            open_count=sprint.open_count,
            blocked_count=sprint.blocked_count,
            completion_rate=sprint.completion_rate,
            team_breakdown=team_breakdown if team_breakdown else "データなし",
        )
        response = api_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        report = response.content[0].text.strip()
    except ImportError:
        report = f"**📊 スプリントレポート: {sprint_name}**\n\n完了率: {sprint.completion_rate:.1f}%\n\n{team_breakdown}\n\n*(anthropicパッケージ未インストール)*"
    except Exception as e:
        report = f"**📊 スプリントレポート: {sprint_name}**\n\nエラー: {e}"

    print("\n" + "="*60)
    print(report)
    print("="*60)

    if notify_discord:
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        if webhook_url:
            import urllib.request, json
            data = json.dumps({"content": report[:2000]}).encode("utf-8")
            req = urllib.request.Request(
                webhook_url,
                data=data,
                headers={"Content-Type": "application/json; charset=utf-8"},
                method="POST"
            )
            urllib.request.urlopen(req)
            print("Discord通知を送信しました")
        else:
            print("DISCORD_WEBHOOK_URL が未設定のため通知をスキップ")


def main():
    parser = argparse.ArgumentParser(description="スプリントレポート生成")
    parser.add_argument("--sprint", required=True, help='例: "Sprint 1"')
    parser.add_argument("--discord", action="store_true", help="Discord通知を送信")
    args = parser.parse_args()
    generate_sprint_report(args.sprint, notify_discord=args.discord)


if __name__ == "__main__":
    main()
