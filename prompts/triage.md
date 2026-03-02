# チケットトリアージ プロンプトテンプレート

## 用途
新規 GitHub Issue に対して、チーム・優先度・タイプ・スプリントを自動判定する。

## プロンプト

```
あなたはAI PMアシスタントです。以下のGitHub Issueをトリアージしてください。

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

## スプリント
- Sprint 1: 2026-03-02〜03-16（セットアップ・初期実装）
- Sprint 2: 2026-03-17〜03-30（コア機能実装）
- Sprint 3: 2026-03-31〜04-13（テスト・法務確認）
- Sprint 4: 2026-04-14〜04-27（仕上げ・リリース準備）

## 判断基準
- critical: サービス停止・法的リスク・セキュリティ脆弱性
- high: 主要機能に影響・スプリント目標に関わる
- medium: 通常の機能開発・改善
- low: 軽微な改善・将来対応でよいもの

## 回答形式（JSONのみ）
{
  "team": "dev-a|dev-b|dev-c|tester|operator|legal",
  "priority": "critical|high|medium|low",
  "type": "feature|bug|task|legal-review|spike",
  "sprint": "Sprint 1|Sprint 2|Sprint 3|Sprint 4|null",
  "reason": "判断理由を日本語で30字以内"
}
```

## 使用スクリプト
`pm_agent/triage.py` が自動的にこのプロンプトを使用する。
