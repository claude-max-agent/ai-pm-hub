# Skill: pm-sprint-report
# スプリントレポート自動生成

## 概要
スプリント終了時に完了率・ブロッカー・チーム別分析・次スプリントへの引き継ぎを
日本語ナラティブレポートとして自動生成する。経営層・関係者への報告資料に使える。

## 使い方
```
/pm-sprint-report --sprint "Sprint 1"
/pm-sprint-report --sprint "Sprint 1" --format executive  # 経営層向け
/pm-sprint-report --sprint "Sprint 1" --discord
```

## プロンプト

```
あなたはAI PMアシスタントです。以下のスプリントデータをもとに完了レポートを作成してください。

## スプリント情報
スプリント名: {sprint_name}
期間: {start} 〜 {end}
目標: {goal}
チーム: 開発チームA/B/C

## 進捗データ
- 完了チケット: {closed_count}件
- 未完了（繰り越し）: {open_count}件
- ブロック発生数: {blocked_count}件（うち解消済み: {resolved_blocked_count}件）
- 完了率: {completion_rate:.1f}%

## チーム別詳細
{team_breakdown}
（チーム名 / 完了件数 / 繰り越し件数 / ブロック件数 / 主要完了タスク）

## インシデント・課題
{incidents_and_issues}

## 出力形式

**📊 スプリントレポート: {sprint_name}**
**期間:** {start} 〜 {end}
**目標達成度:** {completion_rate:.0f}% （{closed_count}/{total_count}件完了）

### サマリー
{全体評価を3〜4文で。良かった点・課題・数値を含める}

### チーム別ハイライト
**開発チームA（フロントエンド）**
{2〜3文。特記事項（問題あれば名指しOK）}

**開発チームB（バックエンド）**
{2〜3文}

**開発チームC（インフラ）**
{2〜3文}

### 発生した問題と対応
{発生した問題を時系列で記載。特に遅延・品質問題・メンバー起因の問題}

### 次スプリントへの申し送り
- 繰り越しチケット: {open_count}件（優先度・対応方針を記載）
- 要注意メンバー: {underperformer_names}（モニタリング継続）
- 改善アクション: {action_items}

### KPI
| 指標 | 今回 | 前回比 |
|------|------|--------|
| 完了率 | {completion_rate:.0f}% | ± |
| ブロック発生数 | {blocked_count}件 | ± |
| 平均リードタイム | X日 | ± |
```

## 使い分け
- `--format executive`: 経営層向け（問題の深掘りなし・数値とサマリーのみ）
- デフォルト: チームメンバー・PM向け（詳細あり）

## 実装スクリプト
`pm_agent/sprint_report.py`
