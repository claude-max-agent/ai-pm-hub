"""
Sprint 1 シミュレーション実行スクリプト

シナリオ定義 (team-scenario.yaml) に基づき、
Sprint 1 の14日間を仮想的に進行させる。

イベントタイムライン:
  Day 1  (Mar 2): キックオフ。高パフォーマーが即開始。
  Day 3  (Mar 4): 中堅メンバーが着手。
  Day 5  (Mar 6): アリスが初タスク完了。ダナが遅れて着手。
  Day 7  (Mar 8): 中間チェック。リスク検出を実行。
  Day 10 (Mar 11): 複数完了。ダナPR初回差し戻し。
  Day 12 (Mar 13): RS-001 チャーリー突然ブロック報告。RS-002 ダナPR2回目差し戻し。
  Day 14 (Mar 16): スプリント終了。10/14完了 (71%)。

使い方:
  python simulation/run_sprint1.py
  python simulation/run_sprint1.py --from-day 7  # Day7から再開
"""
import argparse
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mock_jira.client import MockJiraClient
from simulation.clock import SimClock

client = MockJiraClient()
clock = SimClock()


def ts(msg: str = "") -> str:
    """仮想タイムスタンプラベル付きメッセージを返す"""
    label = clock.timestamp_label()
    return f"{label}\n{msg}" if msg else label


def log(msg: str):
    print(f"[Day {clock.day_in_sprint:2d} / {clock.today}] {msg}")


def transition(issue_num: int, new_status: str, comment: str = ""):
    try:
        client.transition_issue(issue_num, new_status)
        if comment:
            client.add_comment(issue_num, ts(comment))
        log(f"  JZZG-{issue_num} → {new_status}" + (f" ({comment[:40]}...)" if len(comment) > 40 else f" ({comment})" if comment else ""))
    except Exception as e:
        log(f"  ⚠ JZZG-{issue_num} エラー: {e}")


def comment(issue_num: int, msg: str):
    try:
        client.add_comment(issue_num, ts(msg))
        log(f"  JZZG-{issue_num} コメント追加")
    except Exception as e:
        log(f"  ⚠ JZZG-{issue_num} コメントエラー: {e}")


def separator(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ─────────────────────────────────────────────────────────────
# Day 1 (2026-03-02): スプリントキックオフ
# ─────────────────────────────────────────────────────────────
def day1():
    separator("Day 1 - Sprint 1 キックオフ (2026-03-02)")
    clock.set_date("2026-03-02", sprint="Sprint 1", day_in_sprint=1)

    log("高パフォーマーが即日着手 —")
    # アリス: JZZG-5 ログイン画面UI実装
    transition(5, "in-progress", "アリス: 設計着手。コンポーネント構成を確認中。")
    # イブ: JZZG-10 認証API
    transition(10, "in-progress", "イブ: JWT実装方針を確認。ライブラリ選定完了。")
    # イバン: JZZG-15 Docker Compose
    transition(15, "in-progress", "イバン: 既存構成を確認。docker-compose.yml 作成開始。")

    time.sleep(0.3)
    log("キックオフ完了。高パフォーマー3名が即日着手。")


# ─────────────────────────────────────────────────────────────
# Day 3 (2026-03-04): 中堅メンバーが着手
# ─────────────────────────────────────────────────────────────
def day3():
    separator("Day 3 - 中堅メンバー着手 (2026-03-04)")
    clock.set_date("2026-03-04", sprint="Sprint 1", day_in_sprint=3)

    # ボブ: JZZG-6
    transition(6, "in-progress", "ボブ: ダッシュボードレイアウトの着手。Figma確認中。")
    # フランク: JZZG-11
    transition(11, "in-progress", "フランク: ユーザーCRUD API。DBスキーマをヒロと確認。")
    # ヒロ: JZZG-13
    transition(13, "in-progress", "ヒロ: DBマイグレーション。usersテーブル定義から開始。")
    # ジュリア: JZZG-17
    transition(17, "in-progress", "ジュリア: GitHub Actions workflow。サンプルを参考に作成開始。")

    log("チャーリー・ダナ・グレース・ケンはまだTodo。PMメモ: チャーリーの動向を要観察。")
    time.sleep(0.3)


# ─────────────────────────────────────────────────────────────
# Day 5 (2026-03-06): アリス初タスク完了。ダナ遅れて着手。
# ─────────────────────────────────────────────────────────────
def day5():
    separator("Day 5 - アリス完了・ダナ着手 (2026-03-06)")
    clock.set_date("2026-03-06", sprint="Sprint 1", day_in_sprint=5)

    # アリス: JZZG-5 完了
    transition(5, "done", "アリス: ログイン画面完成。バリデーション・レスポンシブ対応済み。PRマージ。")
    # イバン: JZZG-15 完了
    transition(15, "done", "イバン: Docker Compose完成。全サービス起動確認済み。")

    # ダナがようやく着手（遅い）
    transition(8, "in-progress", "ダナ: やっと着手。エラーコンポーネントの設計から始める。")

    # ケン: JZZG-18 着手
    transition(18, "in-progress", "ケン: セキュリティグループ設定。AWSコンソールで作業開始。\nPMメモ: イバンのレビューを必ず依頼すること。")

    # チャーリー: まだTodo（Day5で無更新）
    log("チャーリー (JZZG-7): Day5でもTodo。4日間更新なし。PMが確認する必要あり。")
    comment(7, "PMより: チャーリー、進捗はいかがでしょうか？何か困っていることがあれば教えてください。")
    # チャーリーの返信（遅くて短い典型的な反応）
    time.sleep(0.5)
    comment(7, "チャーリー: まだ設計中です。来週には進めます。（PMメモ: 具体性なし）")

    time.sleep(0.3)


# ─────────────────────────────────────────────────────────────
# Day 7 (2026-03-08): 中間チェック
# ─────────────────────────────────────────────────────────────
def day7():
    separator("Day 7 - 中間チェック・リスク検出 (2026-03-08)")
    clock.set_date("2026-03-08", sprint="Sprint 1", day_in_sprint=7)

    # イブ: JZZG-10 完了
    transition(10, "done", "イブ: JWT認証API完成。ユニットテスト込みでPRマージ。")
    # ヒロ: JZZG-13 完了
    transition(13, "done", "ヒロ: DBマイグレーション完成。sessions, usersテーブル作成確認済み。")
    # グレース: JZZG-12 ようやく着手
    transition(12, "in-progress", "グレース: APIドキュメント作成を開始。（PMメモ: 予定より3日遅れ）")

    # ケン: JZZG-18 完了（初の設定作業は問題なし）
    transition(18, "done", "ケン: セキュリティグループ設定完了。イバンレビュー済み。問題なし。\nPMメモ: 今回はイバンのレビューが機能した。")

    # イバン: JZZG-16 着手
    transition(16, "in-progress", "イバン: ステージング環境構築。ECS/RDS設定開始。")
    # アリス: 次のタスクへ (JZZG-14 レート制限)
    transition(14, "in-progress", "アリス: ログイン画面完了。次にレート制限実装に着手。")

    log("\n--- 中間サマリー (Day 7) ---")
    log("✅ 完了: JZZG-5, 10, 13, 15, 18 (5件)")
    log("🔄 進行中: JZZG-6, 7(未), 8, 11, 12, 14, 16, 17")
    log("⚠ 要注意: チャーリー(JZZG-7) Day7でもTodo")
    log("⚠ 要注意: グレース(JZZG-12) 3日遅れで着手")

    log("\n--- AIリスク検出 実行 ---")
    log("  pm-risk-detect → チャーリー: delay_risk (7日無更新)")
    log("  pm-risk-detect → グレース: delay_risk (着手3日遅れ)")
    log("  pm-risk-detect → ダナ: quality_risk (新人・初PR未提出)")
    log("  残り7日で 9件In-Progress → スコープ縮小リスクあり")

    # PMアクション記録
    comment(7, f"PMアクション{ts()}: リスク検出でdelay_flagが立った。明日1on1 MTG設定。ブロックがあれば即報告するよう再確認する。")


# ─────────────────────────────────────────────────────────────
# Day 9 (2026-03-10): 1on1とその結果
# ─────────────────────────────────────────────────────────────
def day9():
    separator("Day 9 - チャーリー1on1 (2026-03-10)")
    clock.set_date("2026-03-10", sprint="Sprint 1", day_in_sprint=9)

    # ボブ: JZZG-6 完了
    transition(6, "done", "ボブ: ダッシュボードレイアウト完成。グラフ・テーブルコンポーネント骨格実装済み。")
    # ジュリア: JZZG-17 完了
    transition(17, "done", "ジュリア: CIパイプライン設定完了。push時にbuild+test自動実行を確認。")
    # フランク: JZZG-11 完了
    transition(11, "done", "フランク: ユーザーCRUD API完成。GET/POST/PUT/DELETE全て動作確認済み。")

    # チャーリー1on1の結果
    comment(7, "チャーリー1on1 MTG記録 " + ts() + ":\n\n実は「ユーザー設定画面に必要なAPI仕様が確定していない」と言っていた。\n本人が確認せずに放置していた。\n\n→ PMアクション: イブに仕様確認を依頼。チャーリーには「APIなしでできるUI部分から着手するよう」指示。")

    # チャーリー: ようやく着手
    transition(7, "in-progress", "チャーリー: UI部分のみ先行着手。API依存部分は保留。（Day9、遅い）")

    # ダナ: PR提出
    comment(8, "ダナ: エラーコンポーネントのPR提出 " + ts())

    time.sleep(0.3)


# ─────────────────────────────────────────────────────────────
# Day 10 (2026-03-11): ダナPR差し戻し
# ─────────────────────────────────────────────────────────────
def day10():
    separator("Day 10 - ダナPR差し戻し・進捗加速 (2026-03-11)")
    clock.set_date("2026-03-11", sprint="Sprint 1", day_in_sprint=10)

    # イバン: JZZG-16 完了
    transition(16, "done", "イバン: ステージング環境構築完了。ECS/RDS/ALB設定済み。動作確認OK。")

    # ダナ: PR差し戻し (1回目)
    comment(8,
        "アリス (コードレビュー) " + ts() + ":\n\n"
        "差し戻し (1回目)。以下の問題:\n"
        "1. エラーメッセージがハードコーディングされている (i18n対応必要)\n"
        "2. エラーの種類ごとに表示を分けていない\n"
        "3. テストコードなし\n\n"
        "修正してから再提出してください。"
    )
    log("ダナ (JZZG-8): PR差し戻し1回目。アリスから3点指摘。")

    # グレース: まだ遅い
    comment(12, "グレース進捗 " + ts() + ": エンドポイントの一覧は作成。説明文はまだ途中。予定より遅れている。")
    log("グレース (JZZG-12): Day10で半分も完成していない。")

    time.sleep(0.3)


# ─────────────────────────────────────────────────────────────
# Day 12 (2026-03-13): RS-001 チャーリーブロック / RS-002 ダナ2回目差し戻し
# ─────────────────────────────────────────────────────────────
def day12():
    separator("Day 12 - RS-001 & RS-002 発動！ (2026-03-13)")
    clock.set_date("2026-03-13", sprint="Sprint 1", day_in_sprint=12)

    log("🚨 RS-001: チャーリーが突然ブロックを報告")
    transition(7, "blocked",
        "チャーリー (緊急報告) " + ts() + ":\n\n"
        "API仕様が未定のため、設定フォームが実装できない。\n"
        "パスワード変更APIのレスポンス形式が確定していない。\n\n"
        "残り2日なのに今更報告。スプリント内完了は困難な状況。"
    )

    log("🚨 RS-002: ダナのPRが2回目も差し戻し")
    comment(8,
        "アリス (コードレビュー 2回目) " + ts() + ":\n\n"
        "差し戻し (2回目)。i18n対応はされたが:\n"
        "1. エラー分類ロジックにバグあり (network errorとserver errorが混在)\n"
        "2. テストコードが不完全 (ハッピーパスのみ)\n"
        "3. コンポーネント名がスタイルガイドに沿っていない\n\n"
        "PMへ: ダナにペアプログラミングのサポートが必要と思われます。"
    )

    log("\n--- PMアクション (Day 12) ---")
    log("  1. アリスにダナとのペアプロを依頼")
    log("  2. イブにチャーリーのAPI仕様を優先確認依頼")
    log("  3. JZZG-7 をスプリント繰り越し候補として記録")

    # PMアクション記録
    comment(7,
        "PMアクション " + ts() + ":\n\n"
        "【スコープ判断】JZZG-7 はSprint 2に繰り越し。\n"
        "理由: API仕様未確定のためスプリント内完了不可能。\n\n"
        "【根本原因】チャーリーが7日間ブロックを放置した。\n"
        "Day5にPMが確認した際に「設計中」と答えたが、実際には不明点があった。\n\n"
        "【再発防止】デイリーチェックイン（Slack更新）を義務化する。"
    )
    comment(8,
        "PMアクション " + ts() + ":\n\n"
        "アリスにダナとのペアプロを依頼。\n"
        "明日(Day 13)午前中に2時間セッション設定。\n\n"
        "ダナへ: PRを一度クローズして、アリスとペアで作り直す方針。"
    )

    # ダナのPRをリセット（ペアプロ準備）
    comment(8, "ダナ: 了解しました。明日アリスと一緒に進めます。" + ts())

    # アリスとイブが追加作業
    comment(14, "アリス " + ts() + ": レート制限の実装中。ダナサポートと並行。")
    comment(10, "イブ " + ts() + ": チャーリーのAPI仕様確認。パスワード変更APIのレスポンスを明日までに確定する。")

    time.sleep(0.3)


# ─────────────────────────────────────────────────────────────
# Day 13 (2026-03-14): ペアプロ・API仕様確定
# ─────────────────────────────────────────────────────────────
def day13():
    separator("Day 13 - ペアプロ・API仕様確定 (2026-03-14)")
    clock.set_date("2026-03-14", sprint="Sprint 1", day_in_sprint=13)

    # イブがAPI仕様を確定 → チャーリーのブロック解除
    comment(7,
        "イブ (API仕様確定) " + ts() + ":\n\n"
        "パスワード変更APIのレスポンス形式を確定:\n"
        "```\n{ \"success\": bool, \"message\": string }\n```\n\n"
        "チャーリー、これで実装できます。"
    )
    # チャーリーはブロック解除されたが残り1日
    transition(7, "in-progress",
        "チャーリー: イブからAPI仕様連絡。\n実装再開。ただし残り1日のため全機能は難しい。" + ts()
    )

    # ダナとアリスのペアプロ結果
    comment(8,
        "アリス: ダナとペアプロ完了 " + ts() + "。\n\n"
        "バグ修正・テスト追加・命名規則修正完了。\n3回目のPR提出予定。"
    )
    time.sleep(0.5)
    transition(8, "done",
        "ダナ + アリス (ペアプロ) " + ts() + ": エラーハンドリングコンポーネント完成。\n"
        "3回のレビューサイクルを経て完成。テストカバレッジ 87%。"
    )

    # グレース: まだ未完了
    comment(12, "グレース " + ts() + ": ドキュメント作業継続中。明日中に終わらせる予定。")

    # アリス: JZZG-14 完了
    transition(14, "done",
        "アリス: レート制限実装完了。ミドルウェアとして組み込み。\nダナサポートと並行したが期限内完了。" + ts()
    )

    time.sleep(0.3)


# ─────────────────────────────────────────────────────────────
# Day 14 (2026-03-16): スプリント終了
# ─────────────────────────────────────────────────────────────
def day14():
    separator("Day 14 - Sprint 1 終了 (2026-03-16)")
    clock.set_date("2026-03-16", sprint="Sprint 1", day_in_sprint=14)

    # チャーリー: 一部実装のみ完了（スプリント内未完）
    comment(7,
        "チャーリー (Sprint 1 最終日) " + ts() + ":\n\n"
        "プロフィール編集UIのみ実装完了。\n"
        "パスワード変更・通知設定はSprint 2に繰り越し。\n"
        "（PMメモ: もし初日から着手していれば完了していた内容）"
    )
    transition(7, "blocked",  # 繰り越しのためblocked維持
        "Sprint 1 繰り越し: API依存部分が未完了。Sprint 2に持ち越し。" + ts()
    )

    # グレース: 未完了
    comment(12,
        "グレース (Sprint 1 最終日) " + ts() + ":\n\n"
        "60%完成。残りの認証・ユーザー系エンドポイントはSprint 2に繰り越し。\n"
        "（PMメモ: Day7から着手していれば完了していた量）"
    )

    # JZZG-9 (ダナのモバイル対応) は未着手
    comment(9,
        "Sprint 1 繰り越し " + ts() + ":\n\n"
        "ダナのJZZG-8サポートに時間がかかったため未着手。\n"
        "Sprint 2に持ち越し。優先度lowなので問題は小さい。"
    )

    log("\n" + "="*60)
    log("  Sprint 1 終了サマリー")
    log("="*60)
    log("✅ 完了 (10件): JZZG-5, 6, 8, 10, 11, 13, 14, 15, 16, 17, 18")
    log("   ※ JZZG-18はDay7完了カウント済み")
    log("❌ 繰り越し (3件): JZZG-7(チャーリー), JZZG-9(ダナ), JZZG-12(グレース)")
    log("📊 完了率: 71% (10/14)")
    log("")
    log("🔴 問題発生: RS-001 (チャーリー遅延ブロック) ✅解消")
    log("🔴 問題発生: RS-002 (ダナPR連続差し戻し) ✅解消（ペアプロで対処）")
    log("")
    log("💡 PMの学び:")
    log("   1. 怠惰メンバーへの週次1on1が遅延発見に有効")
    log("   2. 新人の品質問題はペアプロで解決できる")
    log("   3. ブロック放置を防ぐデイリー更新義務化が必要")
    log("="*60)


# ─────────────────────────────────────────────────────────────
# メイン実行
# ─────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Sprint 1 シミュレーション実行")
    parser.add_argument("--from-day", type=int, default=1, help="実行開始日（デフォルト: 1）")
    parser.add_argument("--to-day", type=int, default=14, help="実行終了日（デフォルト: 14）")
    args = parser.parse_args()

    days = {
        1: day1,
        3: day3,
        5: day5,
        7: day7,
        9: day9,
        10: day10,
        12: day12,
        13: day13,
        14: day14,
    }

    print(f"\n🚀 Sprint 1 シミュレーション開始 (Day {args.from_day} 〜 Day {args.to_day})\n")

    for day_num in sorted(days.keys()):
        if args.from_day <= day_num <= args.to_day:
            days[day_num]()
            time.sleep(0.5)

    print("\n✅ Sprint 1 シミュレーション完了")
    print(f"仮想日時: {clock.today} / Day {clock.day_in_sprint}")
    print("Jiraで確認: https://koshifuruzono.atlassian.net/jira/software/projects/JZZG/boards")


if __name__ == "__main__":
    main()
