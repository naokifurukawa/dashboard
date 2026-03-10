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

    daily_json = json.dumps(daily_rows, ensure_ascii=False)
    plan_json = json.dumps(plan_rows, ensure_ascii=False)

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
  </style>
</head>
<body>
  <header style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
    <h1 style="margin: 0;">FFG Bizship 請求・支払 登録ユーザー数</h1>
    <img src="bizship_logo.png" alt="BIZSHIP 請求書管理・支払" style="height: 32px; width: auto;">
  </header>

  <section class="section">
    <h2>日次トラッキング（事業者数）</h2>
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
    <p>ヘッダーをクリックでソート</p>
    <div class="table-wrap">
      <table id="daily-table">
        <thead><tr><th data-col="0">日付</th><th data-col="1">事業者数</th><th data-col="2">ログイン合計</th><th data-col="3">日次差分</th><th data-col="4">備考</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>
  </section>

  <script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
  <script>
    const dailyData = {daily_json};
    const planData = {plan_json};

    // 日次グラフ（事業者数のみ）
    const labels = dailyData.map(r => r.date.replace('2026-', ''));
    new Chart(document.getElementById('daily-chart'), {{
      type: 'line',
      data: {{
        labels: labels,
        datasets: [{{
          label: '事業者数',
          data: dailyData.map(r => parseInt(r.business_count || '0', 10)),
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          tension: 0.2,
          fill: true
        }}]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        interaction: {{ intersect: false, mode: 'index' }},
        plugins: {{ legend: {{ position: 'top' }} }},
        scales: {{ y: {{ type: 'linear', min: 0, title: {{ display: true, text: '事業者数' }} }} }}
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
  </script>
</body>
</html>
"""
    out_path = ROOT / "interactive_dashboard.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"Generated: {out_path}")


if __name__ == "__main__":
    main()
