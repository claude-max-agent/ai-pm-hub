"""
チケット自動トリアージ

新規Issueを解析してClaudeがチーム・優先度・タイプ・スプリントを自動割り当てする。

使い方:
  python pm_agent/triage.py --issue 5
  python pm_agent/triage.py --all-unassigned
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mock_jira.client import MockJiraClient


TRIAGE_PROMPT = """あなたはAI PMアシスタントです。以下のGitHub Issueをトリアージしてください。

## Issue情報
タイトル: {title}
本文:
{body}

## チーム一覧
- dev-a: 開発チームA（フロントエンド・UI）
- dev-b: 開発チームB（バックエンド・API）
- dev-c: 開発チームC（インフラ・データ基盤）
- tester: テスターチーム（QA・テスト全般）
- operator: オペレーターチーム（設定値決定・運用テスト）
- legal: 法務チーム（法的確認・リスク管理）

## 判断してください
以下のJSON形式で回答してください:
{{
  "team": "dev-a|dev-b|dev-c|tester|operator|legal",
  "priority": "critical|high|medium|low",
  "type": "feature|bug|task|legal-review|spike",
  "sprint": "Sprint 1|Sprint 2|Sprint 3|Sprint 4|null",
  "reason": "判断理由を日本語で30字以内"
}}
"""


def triage_issue(issue_number: int, dry_run: bool = False):
    client = MockJiraClient()
    ticket = client.get_ticket(issue_number)

    print(f"トリアージ対象: PROJ-{ticket.number} [{ticket.title}]")

    # 既にチームが割り当て済みならスキップ
    if ticket.team and not dry_run:
        print(f"  → 既にチーム割り当て済み ({ticket.team})、スキップ")
        return

    # Claude APIでトリアージ
    try:
        import anthropic
        api_client = anthropic.Anthropic()
        prompt = TRIAGE_PROMPT.format(
            title=ticket.title,
            body=ticket.body[:2000] if ticket.body else "(本文なし)"
        )
        response = api_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )
        result_text = response.content[0].text.strip()

        # JSONを抽出
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        triage = json.loads(result_text)
        print(f"  トリアージ結果: {triage}")

        if dry_run:
            print("  (dry-run: 実際の変更はしません)")
            return

        # ラベル付与
        labels_to_add = [
            f"team/{triage['team']}",
            f"priority/{triage['priority']}",
            f"type/{triage['type']}",
            "status/todo",
        ]
        cmd = [
            "gh", "issue", "edit", str(issue_number),
            "--repo", client.repo,
            "--add-label", ",".join(labels_to_add),
        ]
        if triage.get("sprint"):
            cmd += ["--milestone", triage["sprint"]]
        subprocess.run(cmd, check=True)

        # トリアージコメントを追加
        comment = (
            f"🤖 **自動トリアージ完了**\n\n"
            f"- チーム: `{triage['team']}`\n"
            f"- 優先度: `{triage['priority']}`\n"
            f"- タイプ: `{triage['type']}`\n"
            f"- スプリント: `{triage.get('sprint', '未割り当て')}`\n\n"
            f"**判断理由:** {triage['reason']}"
        )
        client.add_comment(issue_number, comment)
        print(f"  → トリアージ完了!")

    except ImportError:
        print("  ⚠ anthropic パッケージが未インストールです: pip install anthropic")
        print("  手動トリアージが必要です")
    except Exception as e:
        print(f"  ⚠ トリアージエラー: {e}")


def main():
    parser = argparse.ArgumentParser(description="チケット自動トリアージ")
    parser.add_argument("--issue", type=int, help="トリアージするIssue番号")
    parser.add_argument("--all-unassigned", action="store_true", help="未割り当て全件をトリアージ")
    parser.add_argument("--dry-run", action="store_true", help="変更をしないシミュレーション")
    args = parser.parse_args()

    if args.issue:
        triage_issue(args.issue, dry_run=args.dry_run)
    elif args.all_unassigned:
        client = MockJiraClient()
        # チームラベルなしのオープンIssueを検索
        import subprocess, json
        result = subprocess.run([
            "gh", "issue", "list",
            "--repo", client.repo,
            "--state", "open",
            "--json", "number,labels,title",
            "--limit", "50",
        ], capture_output=True, text=True, check=True)
        issues = json.loads(result.stdout)
        unassigned = [
            i for i in issues
            if not any(lb["name"].startswith("team/") for lb in i["labels"])
        ]
        print(f"未割り当てIssue: {len(unassigned)}件")
        for issue in unassigned:
            triage_issue(issue["number"], dry_run=args.dry_run)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
