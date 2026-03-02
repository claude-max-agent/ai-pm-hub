"""
朝会サマリー自動生成

全チームの in-progress / blocked チケットをまとめて日本語サマリーを生成する。
Discord通知または標準出力に出力する。

使い方:
  python pm_agent/standup.py
  python pm_agent/standup.py --discord
"""
import argparse
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mock_jira.client import MockJiraClient


STANDUP_PROMPT = """あなたはAI PMアシスタントです。以下の情報をもとに朝会サマリーを日本語で生成してください。

## 本日の日付
{today}

## 各チームの状況
{team_status}

## 出力形式
以下の形式で簡潔にまとめてください:

**🌅 朝会サマリー {today}**

{各チームのサマリー（進行中・ブロッカー・完了）}

**⚠️ 要注意事項**
{ブロッカーや期限リスクがある場合のみ記述}
"""


def generate_standup(notify_discord: bool = False):
    client = MockJiraClient()

    # チームIDリスト
    team_ids = ["dev-a", "dev-b", "dev-c", "tester", "operator", "legal"]
    team_status_text = ""

    for team_id in team_ids:
        status = client.get_team_status(team_id)
        in_progress_titles = [f"- PROJ-{t.number}: {t.title}" for t in status.in_progress]
        blocked_titles = [f"- ⚠ PROJ-{t.number}: {t.title}" for t in status.blocked]

        team_status_text += f"\n### {status.team_name}\n"
        if in_progress_titles:
            team_status_text += "進行中:\n" + "\n".join(in_progress_titles) + "\n"
        else:
            team_status_text += "進行中: なし\n"
        if blocked_titles:
            team_status_text += "ブロック中:\n" + "\n".join(blocked_titles) + "\n"

    today = date.today().strftime("%Y-%m-%d")

    try:
        import anthropic
        api_client = anthropic.Anthropic()
        prompt = STANDUP_PROMPT.format(
            today=today,
            team_status=team_status_text
        )
        response = api_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        summary = response.content[0].text.strip()
    except ImportError:
        summary = f"**🌅 朝会サマリー {today}**\n\n{team_status_text}\n\n*(anthropicパッケージ未インストールのため生成失敗)*"
    except Exception as e:
        summary = f"**🌅 朝会サマリー {today}**\n\n{team_status_text}\n\nエラー: {e}"

    print(summary)

    if notify_discord:
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        if webhook_url:
            import urllib.request
            data = {"content": summary[:2000]}.encode("utf-8")
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
    parser = argparse.ArgumentParser(description="朝会サマリー生成")
    parser.add_argument("--discord", action="store_true", help="Discord通知を送信")
    args = parser.parse_args()
    generate_standup(notify_discord=args.discord)


if __name__ == "__main__":
    main()
