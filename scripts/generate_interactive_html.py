#!/usr/bin/env python3
"""Generate interactive HTML from CSV data."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    # Daily tracking
    daily_rows = []
    with open(ROOT / "daily_tracking.csv", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r.get("date"):
                daily_rows.append(r)

    # Monthly plan
    plan_rows = []
    plan_path = ROOT / "monthly_plan.csv"
    if plan_path.exists():
        with open(plan_path, encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                if r.get("year_month"):
                    plan_rows.append(r)

    # 3/8時点 利用状況
    usage_registration = []
    usage_feature = []
    usage_path = ROOT / "usage_summary_20260308.csv"
    if usage_path.exists():
        with open(usage_path, encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                if r.get("type") == "registration":
                    usage_registration.append(r)
                elif r.get("type") == "feature":
                    usage_feature.append(r)

    usage_customers = []
    usage_report_path = ROOT / "00_source" / "daily_diff_report_20260308.csv"
    if usage_report_path.exists():
        with open(usage_report_path, encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                if r.get("company_name"):
                    plan = r.get("current_plan_title") or "未設定"
                    if plan == "NULL":
                        plan = "未設定"
                    usage_customers.append({
                        "company_name": r["company_name"],
                        "plan": plan,
                        "login_count": r.get("total_sign_in_count", "0"),
                    })

    daily_json = json.dumps(daily_rows, ensure_ascii=False)
    plan_json = json.dumps(plan_rows, ensure_ascii=False)
    usage_reg_json = json.dumps(usage_registration, ensure_ascii=False)
    usage_feat_json = json.dumps(usage_feature, ensure_ascii=False)
    usage_cust_json = json.dumps(usage_customers, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>FFG Bizship 請求・支払 登録ユーザー数</title>
  <style>
    :root {{ font-family: "Hiragino Sans", "Hiragino Kaku Gothic ProN", sans-serif; }}
    body {{ max-width: 1200px; margin: 2rem auto; padding: 0 1rem; }}
    h1 {{ font-size: 1.5rem; margin-bottom: 0.5rem; }}
    h2 {{ font-size: 1.2rem; margin: 2rem 0 1rem; color: #333; }}
    .section {{ margin-bottom: 2rem; }}
    .table-wrap {{ overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 0.5rem 0.75rem; text-align: left; border-bottom: 1px solid #eee; }}
    th {{ background: #f5f5f5; font-weight: 600; cursor: pointer; user-select: none; white-space: nowrap; }}
    th:hover {{ background: #eee; }}
    th.sorted-asc::after {{ content: " ▲"; font-size: 0.7em; opacity: 0.7; }}
    th.sorted-desc::after {{ content: " ▼"; font-size: 0.7em; opacity: 0.7; }}
    .btn-csv {{ padding: 0.4rem 0.8rem; background: #2563eb; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.875rem; }}
    .btn-csv:hover {{ background: #1d4ed8; }}
  </style>
</head>
<body>
  <header style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
    <h1 style="margin: 0;">FFG Bizship 請求・支払 登録ユーザー数</h1>
    <img src="bizship_logo.png" alt="BIZSHIP 請求書管理・支払" style="height: 32px; width: auto;">
  </header>

  <section class="section">
    <h2>日次トラッキング（事業者数・ログイン数）</h2>
    <div class="chart-wrap" style="height: 280px; margin-bottom: 1.5rem;">
      <canvas id="daily-chart"></canvas>
    </div>
  </section>

  <section class="section">
    <h2>計画 vs 実績</h2>
    <div class="chart-wrap" style="height: 280px; margin-bottom: 1.5rem;">
      <canvas id="plan-vs-actual-chart"></canvas>
    </div>
  </section>

  <section class="section">
    <p style="display: flex; align-items: center; gap: 1rem; flex-wrap: wrap;">
      <span>ヘッダーをクリックでソート</span>
      <button type="button" class="btn-csv" id="btn-daily-csv">日次トラッキング CSV ダウンロード</button>
      <button type="button" class="btn-csv" id="btn-plan-csv">月次計画 CSV ダウンロード</button>
    </p>
    <div class="table-wrap">
      <table id="daily-table">
        <thead><tr><th data-col="0">日付</th><th data-col="1">事業者数</th><th data-col="2">ログイン合計</th><th data-col="3">ログイン数（日次）</th><th data-col="4">備考</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>
  </section>

  <section class="section" style="margin-top: 3rem; padding-top: 2rem; border-top: 1px solid #e5e7eb;">
    <h2>3/8時点 利用状況（顧客別）</h2>
    <p style="color: #6b7280; font-size: 0.875rem; margin-bottom: 1.5rem;">データソース: Mont_Blanc 顧客利用状況データ (2026/3/8)</p>

    <h3 style="font-size: 1rem; margin: 1.5rem 0 0.5rem; color: #374151;">登録状況</h3>
    <div class="table-wrap" style="margin-bottom: 2rem;">
      <table id="usage-reg-table">
        <thead><tr><th>区分</th><th>件数</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>

    <h3 style="font-size: 1rem; margin: 1.5rem 0 0.5rem; color: #374151;">機能別 利用状況</h3>
    <div class="table-wrap" style="margin-bottom: 2rem;">
      <table id="usage-feat-table">
        <thead><tr><th>機能</th><th>利用企業数</th><th>総件数</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>

    <h3 style="font-size: 1rem; margin: 1.5rem 0 0.5rem; color: #374151;">顧客別一覧</h3>
    <p style="display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; margin-bottom: 0.5rem;">
      <span style="font-size: 0.875rem;">ヘッダーをクリックでソート</span>
      <button type="button" class="btn-csv" id="btn-usage-csv">3/8利用状況 CSV ダウンロード</button>
    </p>
    <div class="table-wrap">
      <table id="usage-cust-table">
        <thead><tr><th data-col="0">企業名</th><th data-col="1">プラン</th><th data-col="2">ログイン数</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>
  </section>

  <script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
  <script>
    const dailyData = {daily_json};
    const planData = {plan_json};
    const usageRegData = {usage_reg_json};
    const usageFeatData = {usage_feat_json};
    const usageCustData = {usage_cust_json};

    // 日次グラフ（事業者数・ログイン数）
    const labels = dailyData.map(r => r.date.replace('2026-', ''));
    new Chart(document.getElementById('daily-chart'), {{
      type: 'line',
      data: {{
        labels: labels,
        datasets: [
          {{
            label: '事業者数',
            data: dailyData.map(r => parseInt(r.business_count || '0', 10)),
            borderColor: 'rgb(59, 130, 246)',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            tension: 0.2,
            fill: true,
            yAxisID: 'y'
          }},
          {{
            label: 'ログイン数',
            data: dailyData.map(r => parseInt(r.login_count_diff || '0', 10)),
            borderColor: 'rgb(34, 197, 94)',
            backgroundColor: 'rgba(34, 197, 94, 0.1)',
            tension: 0.2,
            fill: true,
            yAxisID: 'y1'
          }}
        ]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        interaction: {{ intersect: false, mode: 'index' }},
        plugins: {{ legend: {{ position: 'top' }} }},
        scales: {{
          y: {{ type: 'linear', min: 0, position: 'left', title: {{ display: true, text: '事業者数' }} }},
          y1: {{ type: 'linear', min: 0, position: 'right', title: {{ display: true, text: 'ログイン数（日次）' }} }}
        }}
      }}
    }});

    // 計画 vs 実績（月次）
    const planLabels = planData.map(p => p.year_month.replace('-', '/'));
    const planValues = planData.map(p => parseInt(p.free_users || '0', 10));
    const actualByMonth = {{}};
    dailyData.forEach(r => {{
      const ym = r.date.substring(0, 7);
      const v = parseInt(r.business_count || '0', 10);
      if (!(ym in actualByMonth) || v > actualByMonth[ym]) actualByMonth[ym] = v;
    }});
    const actualValues = planData.map(p => actualByMonth[p.year_month] ?? null);
    new Chart(document.getElementById('plan-vs-actual-chart'), {{
      type: 'bar',
      data: {{
        labels: planLabels,
        datasets: [
          {{ label: '計画', data: planValues, backgroundColor: 'rgba(156, 163, 175, 0.6)', borderColor: 'rgb(107, 114, 128)', borderWidth: 1 }},
          {{ label: '実績', data: actualValues, backgroundColor: 'rgba(59, 130, 246, 0.6)', borderColor: 'rgb(59, 130, 246)', borderWidth: 1 }}
        ]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        interaction: {{ intersect: false, mode: 'index' }},
        plugins: {{ legend: {{ position: 'top' }} }},
        scales: {{ y: {{ type: 'linear', min: 0, title: {{ display: true, text: '事業者数' }} }} }}
      }}
    }});

    function makeSortable(tableId) {{
      const table = document.getElementById(tableId);
      const ths = table.querySelectorAll('thead th');
      ths.forEach((th, i) => {{
        th.addEventListener('click', () => {{
          const tbody = table.querySelector('tbody');
          const rows = Array.from(tbody.querySelectorAll('tr'));
          const dir = th.classList.contains('sorted-asc') ? -1 : 1;
          ths.forEach(t => t.classList.remove('sorted-asc', 'sorted-desc'));
          th.classList.add(dir === 1 ? 'sorted-asc' : 'sorted-desc');
          rows.sort((a, b) => {{
            const va = a.cells[i]?.textContent?.trim() ?? '';
            const vb = b.cells[i]?.textContent?.trim() ?? '';
            const na = Number(va), nb = Number(vb);
            if (!isNaN(na) && !isNaN(nb)) return dir * (na - nb);
            return dir * String(va).localeCompare(vb);
          }});
          rows.forEach(r => tbody.appendChild(r));
        }});
      }});
    }}

    // Daily table
    const dailyTbody = document.querySelector('#daily-table tbody');
    dailyData.forEach(r => {{
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${{r.date}}</td><td>${{r.business_count}}</td><td>${{r.login_count_total}}</td><td>${{r.login_count_diff}}</td><td>${{r.note || ''}}</td>`;
      dailyTbody.appendChild(tr);
    }});
    makeSortable('daily-table');

    // CSV ダウンロード
    function escapeCsvCell(v) {{
      const s = String(v ?? '');
      if (/[",\\n\\r]/.test(s)) return '"' + s.replace(/"/g, '""') + '"';
      return s;
    }}
    function toCsv(rows, headers) {{
      const lines = [headers.map(escapeCsvCell).join(',')];
      rows.forEach(r => {{
        lines.push(headers.map(h => escapeCsvCell(r[h])).join(','));
      }});
      return lines.join('\\r\\n');
    }}
    function downloadCsv(csv, filename) {{
      const blob = new Blob(['\\ufeff' + csv], {{ type: 'text/csv;charset=utf-8' }});
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = filename;
      a.click();
      URL.revokeObjectURL(a.href);
    }}
    document.getElementById('btn-daily-csv').addEventListener('click', () => {{
      const headers = ['date', 'business_count', 'login_count_total', 'login_count_diff', 'note'];
      downloadCsv(toCsv(dailyData, headers), 'daily_tracking.csv');
    }});
    document.getElementById('btn-plan-csv').addEventListener('click', () => {{
      const headers = ['year_month', 'elapsed_months', 'free_users', 'paid_users', 'bpsp_users', 'total'];
      downloadCsv(toCsv(planData, headers), 'monthly_plan.csv');
    }});

    // 3/8時点 利用状況
    usageRegData.forEach(r => {{
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${{r.label}}</td><td>${{r.company_count}}社</td>`;
      document.querySelector('#usage-reg-table tbody').appendChild(tr);
    }});
    usageFeatData.forEach(r => {{
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${{r.label}}</td><td>${{r.company_count}}社</td><td>${{r.total_count || '-'}}</td>`;
      document.querySelector('#usage-feat-table tbody').appendChild(tr);
    }});
    usageCustData.sort((a, b) => parseInt(b.login_count || '0', 10) - parseInt(a.login_count || '0', 10));
    usageCustData.forEach(r => {{
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${{r.company_name}}</td><td>${{r.plan}}</td><td>${{r.login_count}}</td>`;
      document.querySelector('#usage-cust-table tbody').appendChild(tr);
    }});
    makeSortable('usage-cust-table');
    document.getElementById('btn-usage-csv').addEventListener('click', () => {{
      const headers = ['company_name', 'plan', 'login_count'];
      downloadCsv(toCsv(usageCustData, headers), 'usage_by_customer_20260308.csv');
    }});
  </script>
</body>
</html>
"""
    out_path = ROOT / "interactive_dashboard.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"Generated: {out_path}")


if __name__ == "__main__":
    main()
