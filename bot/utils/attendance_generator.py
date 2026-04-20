"""
Attendance Image Generator
Render bảng chấm công thành ảnh PNG bằng HTML/CSS + Playwright.
"""
import io
import datetime


def build_attendance_html(
    employee_name: str,
    employee_id: str,
    month: int,
    year: int,
    records: list,
) -> str:
    """Tạo HTML bảng chấm công."""
    now_time = datetime.datetime.now().strftime("%H:%M %d/%m/%Y")

    # Build table rows
    table_rows = ""
    for idx, rec in enumerate(records):
        row_class = "even" if idx % 2 == 0 else "odd"
        day_str = f"{rec['day']:02d}/{rec['month']:02d}"
        date_label = rec.get("date_str", "")
        check_in = rec.get("check_in", "—")
        check_out = rec.get("check_out", "—")
        overtime = rec.get("overtime", "—")
        work_h = rec.get("work_hours", "—")
        error = rec.get("error", "")

        ci_class = "success" if check_in not in ("—", "") else "muted"
        co_class = "success" if check_out not in ("—", "") else "muted"
        err_class = "error" if error else ""

        table_rows += f"""
        <tr class="{row_class}">
          <td class="center">{day_str}</td>
          <td class="center">{date_label}</td>
          <td class="center {ci_class}">{check_in}</td>
          <td class="center {co_class}">{check_out}</td>
          <td class="center">{overtime}</td>
          <td class="center">{work_h}</td>
          <td class="{err_class}">{error}</td>
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
  .attendance {{
    width: 680px;
    background: #ffffff;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 4px 24px rgba(0,0,0,0.08);
  }}
  .att-header {{
    background: linear-gradient(135deg, #0c4a6e 0%, #075985 40%, #0369a1 100%);
    padding: 24px 28px 20px 28px;
    position: relative;
    overflow: hidden;
  }}
  .att-header::before {{
    content: '';
    position: absolute;
    top: -60%; right: -20%;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(56,189,248,0.15) 0%, transparent 70%);
    border-radius: 50%;
  }}
  .att-header::after {{
    content: '';
    position: absolute;
    bottom: -50%; left: -15%;
    width: 180px; height: 180px;
    background: radial-gradient(circle, rgba(125,211,252,0.1) 0%, transparent 70%);
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
    color: #7dd3fc; letter-spacing: 1.5px;
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
    color: #ffffff; letter-spacing: 3px;
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
  .employee-info {{
    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
    border: 1px solid #bae6fd;
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .employee-name {{
    font-size: 16px; font-weight: 800;
    color: #0c4a6e;
  }}
  .employee-detail {{
    font-size: 11px; color: #0369a1;
    font-weight: 500; margin-top: 3px;
  }}
  .employee-code {{
    background: #0369a1; color: #ffffff;
    font-size: 13px; font-weight: 800;
    padding: 7px 14px; border-radius: 10px;
    letter-spacing: 1px;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
  }}
  thead th {{
    background: #1e293b;
    color: #ffffff;
    font-weight: 700;
    font-size: 11px;
    padding: 5px 8px;
    text-align: center;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  thead th:first-child {{ border-radius: 8px 0 0 0; }}
  thead th:last-child {{ border-radius: 0 8px 0 0; }}
  tbody td {{
    padding: 5px 8px;
    font-size: 11px;
    color: #334155;
    font-weight: 500;
    border-bottom: 1px solid #f1f5f9;
  }}
  .center {{ text-align: center; }}
  tr.even {{ background: #f8fafc; }}
  tr.odd {{ background: #ffffff; }}
  .success {{ color: #16a34a; font-weight: 700; }}
  .error {{ color: #dc2626; font-weight: 600; font-size: 11px; }}
  .muted {{ color: #cbd5e1; }}
  .att-footer {{
    padding: 14px 20px;
    background: #f8fafc;
    border-top: 1px solid #e2e8f0;
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
  <div class="attendance">
    <div class="att-header">
      <div class="header-top">
        <div>
          <div class="brand-name">Bảng Chấm Công</div>
          <div class="brand-sub">Attendance Report</div>
        </div>
        <div class="header-badge">Tháng {month:02d}/{year}</div>
      </div>
      <div class="att-title">
        <h1>Chi Tiết Chấm Công</h1>
      </div>
    </div>
    <div class="tear"></div>
    <div class="att-body">
      <div class="employee-info">
        <div>
          <div class="employee-name">{employee_name}</div>
          <div class="employee-detail">Nhân viên</div>
        </div>
        <span class="employee-code">{employee_id}</span>
      </div>
      <table>
        <thead>
          <tr>
            <th>Ngày</th>
            <th>Thứ</th>
            <th>Check-in</th>
            <th>Check-out</th>
            <th>Tăng ca</th>
            <th>Giờ làm</th>
            <th>Ghi chú</th>
          </tr>
        </thead>
        <tbody>
          {table_rows}
        </tbody>
      </table>
    </div>
    <div class="att-footer">
      <div class="footer-left">Tổng: {num_records} ngày</div>
      <div class="footer-right">Tạo lúc: {now_time}</div>
    </div>
  </div>
</body>
</html>"""
    return html


def _render_attendance_to_png_sync(html_content: str) -> bytes:
    """
    Render HTML attendance thành PNG bytes bằng Playwright SYNC API.
    Chạy trong thread riêng để tránh lỗi NotImplementedError
    trên Windows event loop (Pyrogram/ProactorEventLoop).
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 760, "height": 1200},
            device_scale_factor=2
        )

        page.set_content(html_content, wait_until="networkidle")
        page.wait_for_timeout(800)

        element = page.locator(".attendance")
        screenshot = element.screenshot(type="png", omit_background=True)

        browser.close()

    return screenshot


async def render_attendance_to_png(html_content: str) -> bytes:
    """Async wrapper: chạy Playwright sync trong thread pool."""
    import asyncio
    return await asyncio.to_thread(_render_attendance_to_png_sync, html_content)


async def generate_attendance_image(
    employee_name: str,
    employee_id: str,
    month: int,
    year: int,
    records: list,
) -> io.BytesIO:
    """
    Tạo ảnh bảng chấm công từ data.
    Returns io.BytesIO buffer chứa PNG, sẵn sàng gửi qua Telegram.
    """
    html = build_attendance_html(employee_name, employee_id, month, year, records)
    png_bytes = await render_attendance_to_png(html)

    buf = io.BytesIO(png_bytes)
    buf.name = f"chamcong_{employee_id}_{month:02d}_{year}.png"
    return buf
