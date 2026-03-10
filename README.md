# FFG IBM Emerada Portal - 日次トラッキング

## 概要

Slack チャンネル `#ext_ffg-ibm-emerada_portal` に投稿される日次レポートCSVから、**事業者数**と**ログイン数**をトラッキングするためのドキュメントです。

- **チャンネルID**: C097UJ00K4N
- **Slack URL**: https://ffgrh.slack.com/archives/C097UJ00K4N
- **対象期間**: 2026/3/2 以降

---

## CSVファイル一覧（2026/3/2〜）

| 日付 | ファイル名 | 投稿日時 | 備考 |
|------|------------|----------|------|
| 2026-03-02 | daily_diff_report_20260302.csv | 3/3 09:13, 18:31 | 初回。FFG ID列追加版あり |
| 2026-03-03 | daily_diff_report_20260303.csv | 3/4 09:14, 17:13 | |
| 2026-03-04 | daily_diff_report_20260304.csv | 3/5 08:58 | current_plan_title列追加 |
| 2026-03-05 | daily_diff_report_20260305.csv | 3/6 12:07 | 報告遅れ |
| 2026-03-06 | daily_diff_report_20260306.csv | 3/9 09:01 | 週末分まとめて |
| 2026-03-07 | daily_diff_report_20260307.csv | 3/9 09:01 | |
| 2026-03-08 | daily_diff_report_20260308.csv | 3/9 09:01 | |

※ その他: `Mont_Blanc_顧客利用状況データ_2026_03_08.csv`（週末請求書保存利用データ）、`20260304_福岡矢口株式会社.csv`（個別確認用）など

---

## daily_diff_report CSV の構造

メッセージから判明しているカラム:

| カラム名 | 説明 |
|----------|------|
| company_id | 企業ID |
| registration_status | 登録ステータス（registering=登録中 含む） |
| total_sign_in_count | 初回ログインからの累計回数（企業単位） |
| diff_from_previous_day | 前日との差分 |
| current_plan_title | 適用プラン名（有料/無料）（3/5以降） |
| FFG ID | 個人単位のFFG ID（最後の列、3/3以降） |

**集計の目安**:
- **事業者数**: 行数（または registration_status が有効な企業数）
- **ログイン数**: total_sign_in_count の合計、または diff_from_previous_day の合計（日次増分）

---

## トラッキングの進め方

### 1. SlackからCSVをダウンロード

1. [チャンネル #ext_ffg-ibm-emerada_portal](https://ffgrh.slack.com/archives/C097UJ00K4N) を開く
2. 該当日付の `daily_diff_report_YYYYMMDD.csv` をクリックしてダウンロード
3. `FFG_Portal/00_source/` に保存（例: `daily_diff_report_20260308.csv`）

### 2. 集計スクリプトで集計

```bash
cd FFG_Portal
python scripts/aggregate_daily.py
```

→ `FFG_Portal/daily_tracking.csv` に日次サマリーが出力・追記されます。

### 3. 手動で集計する場合

`daily_tracking.csv` を編集し、以下の形式で追記:

```csv
date,business_count,login_count_total,login_count_diff,note
2026-03-02,70,xxx,xxx,
2026-03-03,xx,xxx,xxx,
...
```

---

## ファイル構成

```
FFG_Portal/
├── README.md                 # 本ドキュメント
├── daily_tracking.csv        # 日次集計結果（事業者数・ログイン数）
├── interactive_dashboard.html # インタラクティブな表（ソート・検索可能）
├── 00_source/                # SlackからDLした daily_diff_report_*.csv を配置
└── scripts/
    ├── aggregate_daily.py    # 集計スクリプト
    └── generate_interactive_html.py  # インタラクティブHTML生成
```

### インタラクティブ表の更新

CSVを更新したら以下でHTMLを再生成:

```bash
python3 scripts/generate_interactive_html.py
```

---

## Vercel デプロイ

### 手順

1. [Vercel](https://vercel.com) にログイン
2. **Add New Project** で GitHub リポジトリをインポート
3. **Root Directory** を `FFG_Portal` に設定
4. **Deploy** を実行

ビルド時に `generate_interactive_html.py` が実行され、`daily_tracking.csv` と `monthly_plan.csv` から最新の HTML が生成されます。

### CLI からデプロイ

```bash
cd FFG_Portal
vercel
```

初回は `vercel login` が必要です。
