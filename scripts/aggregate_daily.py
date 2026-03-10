#!/usr/bin/env python3
"""
FFG Portal 日次レポート集計スクリプト

00_source/ に配置した daily_diff_report_YYYYMMDD.csv を読み込み、
事業者数・ログイン数を集計して daily_tracking.csv に追記します。

使い方:
  python scripts/aggregate_daily.py

前提:
  - daily_diff_report_*.csv が 00_source/ にあること
  - CSVに company_id, total_sign_in_count, diff_from_previous_day 等の列があること
"""

import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# パス
ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = ROOT / "00_source"
OUTPUT_FILE = ROOT / "daily_tracking.csv"


def detect_columns(row: list) -> dict:
    """ヘッダー行からカラム名→インデックスのマッピングを取得"""
    mapping = {}
    for i, col in enumerate(row):
        col_lower = str(col).strip().lower()
        if "company" in col_lower or col_lower == "company_id":
            mapping["company_id"] = i
        elif "total_sign_in" in col_lower or "sign_in_count" in col_lower:
            mapping["total_sign_in_count"] = i
        elif "diff_from" in col_lower or "diff" in col_lower:
            mapping["diff_from_previous_day"] = i
        elif "registration" in col_lower:
            mapping["registration_status"] = i
    return mapping


def safe_int(val) -> int:
    """安全に整数に変換"""
    if val is None or val == "":
        return 0
    try:
        return int(float(str(val).replace(",", "")))
    except (ValueError, TypeError):
        return 0


def process_csv(path: Path) -> Optional[dict]:
    """
    daily_diff_report CSV を処理し、事業者数・ログイン数を返す。
    返却: { "date": "YYYY-MM-DD", "business_count": int, "login_total": int, "login_diff": int }
    """
    # ファイル名から日付を抽出 (daily_diff_report_20260308.csv)
    stem = path.stem
    if "daily_diff_report_" not in stem:
        return None
    date_str = stem.replace("daily_diff_report_", "")
    if len(date_str) != 8:
        return None
    try:
        dt = datetime.strptime(date_str, "%Y%m%d")
        date_out = dt.strftime("%Y-%m-%d")
    except ValueError:
        return None

    rows = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header:
            return None
        mapping = detect_columns(header)
        idx_company = mapping.get("company_id")
        idx_total = mapping.get("total_sign_in_count")
        idx_diff = mapping.get("diff_from_previous_day")

        max_idx = max(
            idx_company if idx_company is not None else 0,
            idx_total if idx_total is not None else 0,
            idx_diff if idx_diff is not None else 0,
        )
        for row in reader:
            if len(row) <= max_idx:
                continue
            rows.append(row)

    business_count = len(rows)
    login_total = 0
    login_diff = 0

    for row in rows:
        if idx_total is not None and idx_total < len(row):
            login_total += safe_int(row[idx_total])
        if idx_diff is not None and idx_diff < len(row):
            login_diff += safe_int(row[idx_diff])

    return {
        "date": date_out,
        "business_count": business_count,
        "login_total": login_total,
        "login_diff": login_diff,
    }


def load_existing_tracking() -> List[Dict]:
    """既存の daily_tracking.csv を読み込む"""
    if not OUTPUT_FILE.exists():
        return []
    rows = []
    with open(OUTPUT_FILE, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def merge_and_save(existing: List[Dict], new_rows: List[Dict]) -> None:
    """既存データと新規集計をマージして保存"""
    by_date = {r["date"]: r for r in existing}
    for r in new_rows:
        d = r["date"]
        if d not in by_date:
            by_date[d] = {
                "date": d,
                "business_count": "",
                "login_count_total": "",
                "login_count_diff": "",
                "note": "",
            }
        # 数値があれば上書き
        if r.get("business_count") is not None:
            by_date[d]["business_count"] = r["business_count"]
        if r.get("login_total") is not None:
            by_date[d]["login_count_total"] = r["login_total"]
        if r.get("login_diff") is not None:
            by_date[d]["login_count_diff"] = r["login_diff"]

    sorted_dates = sorted(by_date.keys())
    with open(OUTPUT_FILE, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["date", "business_count", "login_count_total", "login_count_diff", "note"],
        )
        w.writeheader()
        for d in sorted_dates:
            row = by_date[d]
            w.writerow({
                "date": row["date"],
                "business_count": row.get("business_count", ""),
                "login_count_total": row.get("login_count_total", ""),
                "login_count_diff": row.get("login_count_diff", ""),
                "note": row.get("note", ""),
            })


def main() -> None:
    if not SOURCE_DIR.exists():
        print(f"ソースディレクトリがありません: {SOURCE_DIR}")
        print("00_source/ を作成し、daily_diff_report_*.csv を配置してください。")
        return

    csv_files = list(SOURCE_DIR.glob("daily_diff_report_*.csv"))
    if not csv_files:
        print(f"daily_diff_report_*.csv が {SOURCE_DIR} に見つかりません。")
        print("Slack から CSV をダウンロードして 00_source/ に保存してください。")
        return

    results = []
    for p in sorted(csv_files):
        r = process_csv(p)
        if r:
            results.append(r)
            print(f"  {p.name} -> 事業者数={r['business_count']}, ログイン合計={r['login_total']}, 日次差分={r['login_diff']}")

    if not results:
        print("有効な集計結果がありません。CSVの形式を確認してください。")
        return

    existing = load_existing_tracking()
    # 既存のキーを維持しつつ、新規集計で上書き
    new_rows = [
        {
            "date": r["date"],
            "business_count": r["business_count"],
            "login_total": r["login_total"],
            "login_diff": r["login_diff"],
        }
        for r in results
    ]
    merge_and_save(existing, new_rows)
    print(f"\n{OUTPUT_FILE} を更新しました。")


if __name__ == "__main__":
    main()
