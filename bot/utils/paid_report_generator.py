"""
Paid Report Image Generator
Render báo cáo thống kê đã thanh toán thành ảnh PNG bằng HTML/CSS + Playwright.
"""
import io
import datetime


def build_paid_report_html(
    target_name: str,
    timeframe: str,
    total_weight: str,
    total_paid: str,
    records: list,
) -> str:
    """Tạo HTML báo cáo đã thanh toán của Xưởng."""
    now_time = datetime.datetime.now().strftime("%H:%M %d/%m/%Y")

    # Build table rows
    table_rows = ""
    for idx, rec in enumerate(records):
        row_class = "even" if idx % 2 == 0 else "odd"
        hh_id = rec.get("id", "—")
        hh_name = rec.get("name", "—")
        weight = rec.get("weight", "0")
        amount = rec.get("amount", "0")

        table_rows += f"""
        <tr class="{row_class}">
          <td class="center"><b>{hh_id}</b></td>
          <td>{hh_name}</td>
          <td class="right text-blue">{weight}</td>
          <td class="right success">{amount}</td>
        </tr>"""

    num_records = len(records)

    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: transparent;
    display: flex;
    justify-content: center;
    padding: 0;
  }}
  .report-box {{
    width: 680px;
    background: #ffffff;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 4px 24px rgba(0,0,0,0.08);
  }}
  .att-header {{
    background: linear-gradient(135deg, #14532d 0%, #166534 40%, #15803d 100%);
    padding: 24px 28px 20px 28px;
    position: relative;
    overflow: hidden;
  }}
  .att-header::before {{
    content: '';
    position: absolute;
    top: -60%; right: -20%;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
    border-radius: 50%;
  }}
  .header-top {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    position: relative;
    z-index: 1;
  }}
  .brand-name {{
    font-size: 16px; font-weight: 800;
    color: #bbf7d0; letter-spacing: 1.5px;
    text-transform: uppercase;
  }}
  .brand-sub {{
    font-size: 11px; color: rgba(255,255,255,0.5);
    margin-top: 3px;
  }}
  .header-badge {{
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.2);
    color: #ffffff;
    font-size: 13px; font-weight: 700;
    padding: 6px 14px; border-radius: 10px;
    letter-spacing: 0.5px;
  }}
  .att-title {{
    text-align: center; margin-top: 14px;
    position: relative; z-index: 1;
  }}
  .att-title h1 {{
    font-size: 15px; font-weight: 700;
    color: #ffffff; letter-spacing: 2px;
    text-transform: uppercase;
  }}
  .tear {{
    height: 14px; background: #ffffff;
    position: relative; margin-top: -1px;
  }}
  .tear::before {{
    content: '';
    position: absolute;
    top: -7px; left: 0; right: 0;
    height: 14px;
    background: radial-gradient(circle at 7px 0, transparent 7px, #ffffff 7px) repeat-x;
    background-size: 14px 14px;
  }}
  .att-body {{
    padding: 6px 20px 20px 20px;
  }}
  .summary-info {{
    background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
    border: 1px solid #86efac;
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .info-block {{
    display: flex;
    flex-direction: column;
  }}
  .info-label {{
    font-size: 11px; color: #64748b;
    font-weight: 600; text-transform: uppercase;
  }}
  .info-val {{
    font-size: 15px; font-weight: 800;
    color: #0f172a; margin-top: 4px;
  }}
  .val-green {{
    color: #16a34a;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
  }}
  thead th {{
    background: #166534;
    color: #ffffff;
    font-weight: 700;
    font-size: 11px;
    padding: 10px 8px;
    text-align: center;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  thead th:first-child {{ border-radius: 8px 0 0 0; }}
  thead th:last-child {{ border-radius: 0 8px 0 0; }}
  tbody td {{
    padding: 9px 8px;
    font-size: 12px;
    color: #334155;
    font-weight: 500;
    border-bottom: 1px solid #f1f5f9;
  }}
  .center {{ text-align: center; }}
  .right {{ text-align: right; }}
  tr.even {{ background: #f0fdf4; }}
  tr.odd {{ background: #ffffff; }}
  .success {{ color: #16a34a; font-weight: 700; }}
  .text-blue {{ color: #0284c7; font-weight: 700; }}
  .att-footer {{
    padding: 14px 20px;
    background: #f0fdf4;
    border-top: 1px solid #bbf7d0;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .footer-left {{
    font-size: 11px; color: #64748b; font-weight: 600;
  }}
  .footer-right {{
    font-size: 10px; color: #94a3b8;
    text-align: right;
  }}
</style>
</head>
<body>
  <div class="report-box">
    <div class="att-header">
      <div class="header-top">
        <div>
          <div class="brand-name">THỐNG KÊ ĐÃ THANH TOÁN</div>
          <div class="brand-sub">{timeframe}</div>
        </div>
        <div class="header-badge">{target_name}</div>
      </div>
      <div class="att-title">
        <h1>CHI TIẾT THANH TOÁN THEO HỘ</h1>
      </div>
    </div>
    <div class="tear"></div>
    <div class="att-body">
      <div class="summary-info">
        <div class="info-block">
          <span class="info-label">Tổng khối lượng Mủ</span>
          <span class="info-val text-blue">{total_weight}</span>
        </div>
        <div class="info-block" style="text-align: right;">
          <span class="info-label">Tổng đã thanh toán</span>
          <span class="info-val val-green">{total_paid}</span>
        </div>
      </div>
      <table>
        <thead>
          <tr>
            <th>Mã Hộ</th>
            <th style="text-align: left;">Tên Khách Hàng</th>
            <th style="text-align: right;">Khối lượng</th>
            <th style="text-align: right;">Đã Thanh Toán</th>
          </tr>
        </thead>
        <tbody>
          {table_rows}
        </tbody>
      </table>
    </div>
    <div class="att-footer">
      <div class="footer-left">Số lượng hộ: {num_records}</div>
      <div class="footer-right">Tạo lúc: {now_time}</div>
    </div>
  </div>
</body>
</html>"""
    return html


def _render_paid_report_to_png_sync(html_content: str) -> bytes:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 760, "height": 1200},
            device_scale_factor=2
        )

        page.set_content(html_content, wait_until="networkidle")
        page.wait_for_timeout(800)

        element = page.locator(".report-box")
        screenshot = element.screenshot(type="png", omit_background=True)

        browser.close()

    return screenshot


async def render_paid_report_to_png(html_content: str) -> bytes:
    import asyncio
    return await asyncio.to_thread(_render_paid_report_to_png_sync, html_content)


async def generate_paid_report_image(
    target_name: str,
    timeframe: str,
    total_weight: str,
    total_paid: str,
    records: list,
) -> io.BytesIO:
    html = build_paid_report_html(target_name, timeframe, total_weight, total_paid, records)
    png_bytes = await render_paid_report_to_png(html)

    buf = io.BytesIO(png_bytes)
    buf.name = f"thanhtoan_{target_name}.png"
    return buf
