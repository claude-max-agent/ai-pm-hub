"""
Sprint 1 シナリオチケット自動作成スクリプト

team-scenario.yaml のシナリオに基づき、
リアルな開発チームの Sprint 1 チケットを Jira に一括作成する。

使い方:
  python simulation/create_sprint1_tickets.py
  python simulation/create_sprint1_tickets.py --dry-run
"""
import argparse
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mock_jira.client import MockJiraClient

SPRINT = "Sprint 1"

# Sprint 1 チケット定義
# 各チームの初期実装タスク＋リアルなシナリオを含む
TICKETS = [
    # ─── 開発チームA (フロントエンド) ───────────────────────────
    {
        "title": "ログイン画面UI実装",
        "body": "メールアドレス・パスワードによるログインフォームをReactで実装する。バリデーション付き。\n\n担当: アリス",
        "team": "dev-a",
        "ticket_type": "feature",
        "priority": "high",
        "sprint": SPRINT,
        "labels_extra": ["assignee/alice"],
    },
    {
        "title": "ダッシュボード画面の基本レイアウト実装",
        "body": "ログイン後のダッシュボード画面。グラフ・テーブルコンポーネントの骨格を作る。\n\n担当: ボブ",
        "team": "dev-a",
        "ticket_type": "feature",
        "priority": "high",
        "sprint": SPRINT,
        "labels_extra": ["assignee/bob"],
    },
    {
        "title": "ユーザー設定画面の実装",
        "body": "プロフィール編集・パスワード変更・通知設定ページを実装する。\n\n担当: チャーリー\n\n※ 締め切り: Sprint 1終了まで（2026-03-16）",
        "team": "dev-a",
        "ticket_type": "feature",
        "priority": "medium",
        "sprint": SPRINT,
        "labels_extra": ["assignee/charlie"],
    },
    {
        "title": "エラーハンドリングコンポーネントの作成",
        "body": "APIエラー時・ネットワークエラー時の共通エラー表示コンポーネント。\n\n担当: ダナ（シンプルなUIコンポーネントなので担当可能）",
        "team": "dev-a",
        "ticket_type": "feature",
        "priority": "medium",
        "sprint": SPRINT,
        "labels_extra": ["assignee/dana"],
    },
    {
        "title": "ログイン画面のモバイル対応（レスポンシブ）",
        "body": "ログイン画面をスマートフォン表示に対応する。\n\n担当: ダナ",
        "team": "dev-a",
        "ticket_type": "feature",
        "priority": "low",
        "sprint": SPRINT,
        "labels_extra": ["assignee/dana"],
    },

    # ─── 開発チームB (バックエンド) ─────────────────────────────
    {
        "title": "認証APIエンドポイント実装（JWT）",
        "body": "POST /auth/login, POST /auth/logout, POST /auth/refresh の3エンドポイントをGoで実装。JWT認証。\n\n担当: イブ",
        "team": "dev-b",
        "ticket_type": "feature",
        "priority": "high",
        "sprint": SPRINT,
        "labels_extra": ["assignee/eve"],
    },
    {
        "title": "ユーザーCRUD APIの実装",
        "body": "GET/POST/PUT/DELETE /users エンドポイント。PostgreSQLとの接続含む。\n\n担当: フランク",
        "team": "dev-b",
        "ticket_type": "feature",
        "priority": "high",
        "sprint": SPRINT,
        "labels_extra": ["assignee/frank"],
    },
    {
        "title": "APIドキュメント（OpenAPI）の整備",
        "body": "全APIエンドポイントのOpenAPI 3.0ドキュメントを作成する。Swaggerで確認できるようにする。\n\n担当: グレース（ドキュメント作業）",
        "team": "dev-b",
        "ticket_type": "task",
        "priority": "medium",
        "sprint": SPRINT,
        "labels_extra": ["assignee/grace"],
    },
    {
        "title": "データベースマイグレーションスクリプトの作成",
        "body": "初期スキーマのマイグレーションファイルを作成する。users, sessions テーブル。\n\n担当: ヒロ",
        "team": "dev-b",
        "ticket_type": "task",
        "priority": "high",
        "sprint": SPRINT,
        "labels_extra": ["assignee/hiro"],
    },
    {
        "title": "レート制限（Rate Limiting）の実装",
        "body": "APIへの過剰リクエストを防ぐためのレート制限をミドルウェアとして実装する。\n\n担当: イブ（セキュリティ系はイブが適任）",
        "team": "dev-b",
        "ticket_type": "feature",
        "priority": "medium",
        "sprint": SPRINT,
        "labels_extra": ["assignee/eve"],
    },

    # ─── 開発チームC (インフラ) ──────────────────────────────────
    {
        "title": "開発環境のDocker Compose構築",
        "body": "ローカル開発環境をDocker Composeで統一する。フロント・バックエンド・DB・Redisを含む。\n\n担当: イバン",
        "team": "dev-c",
        "ticket_type": "task",
        "priority": "high",
        "sprint": SPRINT,
        "labels_extra": ["assignee/ivan"],
    },
    {
        "title": "ステージング環境の構築（AWS）",
        "body": "AWSにステージング環境を構築する。ECS/RDS/ALBの設定。\n\n担当: イバン",
        "team": "dev-c",
        "ticket_type": "task",
        "priority": "high",
        "sprint": SPRINT,
        "labels_extra": ["assignee/ivan"],
    },
    {
        "title": "CI パイプライン設定（GitHub Actions）",
        "body": "プッシュ時にビルド・テストが自動実行されるGitHub Actions workflowを作成する。\n\n担当: ジュリア",
        "team": "dev-c",
        "ticket_type": "task",
        "priority": "high",
        "sprint": SPRINT,
        "labels_extra": ["assignee/julia"],
    },
    {
        "title": "本番環境用セキュリティグループ設定",
        "body": "本番AWSのセキュリティグループを最小権限原則で設定する。ポート開放の精査。\n\n担当: ケン（手順書通りの作業）\n\n⚠️ PMメモ: 設定後の確認を必ずイバンにレビューさせること",
        "team": "dev-c",
        "ticket_type": "task",
        "priority": "medium",
        "sprint": SPRINT,
        "labels_extra": ["assignee/ken"],
    },
]


def create_tickets(dry_run: bool = False):
    client = MockJiraClient()

    print(f"Sprint 1 シナリオチケット作成 ({'dry-run' if dry_run else '実行'})")
    print(f"作成予定: {len(TICKETS)}件\n")

    created = []
    for i, ticket_def in enumerate(TICKETS, 1):
        title = ticket_def["title"]
        print(f"[{i}/{len(TICKETS)}] {title}")

        if dry_run:
            print(f"  → (dry-run スキップ)")
            continue

        try:
            ticket = client.create_ticket(
                title=ticket_def["title"],
                body=ticket_def["body"],
                team=ticket_def["team"],
                ticket_type=ticket_def["ticket_type"],
                priority=ticket_def["priority"],
                sprint=ticket_def.get("sprint"),
                status="todo",
            )
            print(f"  → 作成: {ticket.key} ({ticket.team})")
            created.append(ticket)
            time.sleep(0.5)  # Jira API レート制限対策
        except Exception as e:
            print(f"  → エラー: {e}")

    if not dry_run:
        print(f"\n完了: {len(created)}件作成")
        print(f"\nJiraで確認: https://koshifuruzono.atlassian.net/jira/software/projects/JZZG/boards")


def main():
    parser = argparse.ArgumentParser(description="Sprint 1 シナリオチケット作成")
    parser.add_argument("--dry-run", action="store_true", help="作成をシミュレートのみ")
    args = parser.parse_args()
    create_tickets(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
