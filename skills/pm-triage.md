# Skill: pm-triage
# チケット自動トリアージ

## 概要
新規チケットを読んでClaudeが担当チーム・優先度・タイプ・スプリントを自動判定する。
PMが毎朝チケットを確認してラベルを付ける作業を自動化する。

## 使い方（Claude Codeから）
```
/pm-triage --issue JZZG-5
/pm-triage --all-unassigned
/pm-triage --issue JZZG-5 --dry-run
```

## プロンプト

```
あなたはAI PMアシスタントです。以下のJiraチケットをトリアージしてください。

## チケット情報
キー: {ticket_key}
タイトル: {title}
本文:
{body}

## チーム一覧（開発チームのみ対象）
- dev-a: 開発チームA（フロントエンド・UI / React/TypeScript）
- dev-b: 開発チームB（バックエンド・API / Go/Python）
- dev-c: 開発チームC（インフラ・SRE / AWS/GCP）

## チームメンバー特性（重要: 割り当て時に考慮する）
dev-a:
  - アリス（リード・高パフォーマー）: 複雑なタスクを割り当て可
  - ボブ（普通）: 標準的なタスク
  - チャーリー（怠惰傾向）: 締め切りが重要なクリティカルパスタスクは避ける
  - ダナ（新人・品質不安）: 単純なタスクのみ。バグ修正は避ける

dev-b:
  - イブ（リード・高パフォーマー）: 設計・複雑なタスク
  - フランク（普通）: 標準的なタスク
  - グレース（怠惰・ベテラン）: 見積もりに余裕を持たせる
  - ヒロ（普通）: 標準的なタスク

dev-c:
  - イバン（リード・高パフォーマー）: 高リスクインフラ作業
  - ジュリア（普通）: 標準的な作業
  - ケン（無能傾向）: 複雑な設定変更・本番影響ある作業は避ける

## スプリント（2026年）
- Sprint 1: 3/2〜3/16（セットアップ・初期実装）
- Sprint 2: 3/17〜3/30（コア機能実装）
- Sprint 3: 3/31〜4/13（テスト・法務確認）
- Sprint 4: 4/14〜4/27（仕上げ・リリース準備）

## 判断基準
- priority/critical: サービス停止・セキュリティ脆弱性・ブロッカー
- priority/high: スプリント目標に関わる主要機能
- priority/medium: 通常の機能開発・改善
- priority/low: Nice-to-have・将来対応

## 出力形式（JSONのみ）
{
  "team": "dev-a|dev-b|dev-c",
  "assignee_suggestion": "alice|bob|charlie|dana|eve|frank|grace|hiro|ivan|julia|ken",
  "priority": "critical|high|medium|low",
  "type": "feature|bug|task|spike",
  "sprint": "Sprint 1|Sprint 2|Sprint 3|Sprint 4|null",
  "story_points": 1|2|3|5|8|13,
  "reason": "判断理由（日本語・50字以内）",
  "risk_flag": "none|delay_risk|quality_risk|blocker_risk",
  "risk_reason": "リスクフラグがある場合の理由（なければnull）"
}
```

## リスクフラグ判定ルール
| フラグ | 条件 |
|--------|------|
| `delay_risk` | チャーリーまたはグレースへの割り当て候補 + priority/high以上 |
| `quality_risk` | ダナまたはケンへの割り当て候補 + type/bug or type/feature |
| `blocker_risk` | 他チケットへの依存関係あり + critical path |
| `none` | 上記に該当しない |

## 活用場面
- デイリー: 新規チケット受信後すぐに実行
- スプリント計画前: バックログ全件を一括トリアージ
- オンボーディング: PMが新メンバーにトリアージの見本を示す際

## 実装スクリプト
`pm_agent/triage.py`
