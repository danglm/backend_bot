"""
Payroll Image Generator
Render bảng lương thành ảnh PNG bằng HTML/CSS + Playwright.
"""
import io
import datetime


def build_payroll_html(
    employee_name: str,
    employee_id: str,
    month: int,
    year: int,
    data: dict,
) -> str:
    """Tạo HTML bảng lương (payroll)."""
    now_time = datetime.datetime.now().strftime("%H:%M %d/%m/%Y")

    def fmt_money(val):
        if val is None:
            return "—"
        return f"{val:,.0f}".replace(",", ".")

    # Data fields
    standard_days = data.get("standard_working_days", 0)
    actual_days = data.get("actual_working_days", 0)
    leave_days = data.get("leave_days", 0)
    unpaid_leave = data.get("unpaid_leave", 0)
    total_overtime = data.get("total_overtime", 0)
    leave_balance = data.get("leave_balance", 0)

    base_salary = data.get("base_salary")
    salary_earned = data.get("salary_earned")
    overtime_salary = data.get("overtime_salary_earned")
    bonus = data.get("bonus", 0)
    penalty = data.get("penalty", 0)
    bhxh = data.get("bhxh", 0)
    total_net = data.get("total_net_salary")

    position = data.get("position", "")
    department = data.get("department", "")

    # Summary color
    net_color = "#16a34a" if (total_net or 0) > 0 else "#dc2626"

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
  .payroll {{
    width: 620px;
    background: #ffffff;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 4px 24px rgba(0,0,0,0.08);
  }}
  .pay-header {{
    background: linear-gradient(135deg, #0c4a6e 0%, #075985 40%, #0369a1 100%);
    padding: 24px 28px 20px 28px;
    position: relative;
    overflow: hidden;
  }}
  .pay-header::before {{
    content: '';
    position: absolute;
    top: -60%; right: -20%;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(56,189,248,0.15) 0%, transparent 70%);
    border-radius: 50%;
  }}
  .pay-header::after {{
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
  .pay-title {{
    text-align: center; margin-top: 14px;
    position: relative; z-index: 1;
  }}
  .pay-title h1 {{
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
  .pay-body {{
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
  .section-title {{
    font-size: 12px; font-weight: 700;
    color: #1e293b; text-transform: uppercase;
    letter-spacing: 1px;
    margin: 18px 0 10px 0;
    padding-bottom: 6px;
    border-bottom: 2px solid #e2e8f0;
  }}
  .info-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-bottom: 12px;
  }}
  .info-item {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    background: #f8fafc;
    border-radius: 8px;
    border: 1px solid #f1f5f9;
  }}
  .info-label {{
    font-size: 11px; color: #64748b;
    font-weight: 600;
  }}
  .info-value {{
    font-size: 13px; color: #1e293b;
    font-weight: 700;
  }}
  .salary-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 14px;
    border-bottom: 1px solid #f1f5f9;
  }}
  .salary-row:last-child {{
    border-bottom: none;
  }}
  .salary-label {{
    font-size: 12px; color: #475569;
    font-weight: 600;
  }}
  .salary-value {{
    font-size: 13px; color: #1e293b;
    font-weight: 700;
  }}
  .salary-add {{ color: #16a34a; }}
  .salary-sub {{ color: #dc2626; }}
  .total-box {{
    background: linear-gradient(135deg, #0c4a6e 0%, #0369a1 100%);
    border-radius: 12px;
    padding: 16px 18px;
    margin-top: 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .total-label {{
    font-size: 14px; color: #bae6fd;
    font-weight: 700; text-transform: uppercase;
    letter-spacing: 1px;
  }}
  .total-value {{
    font-size: 20px; color: #ffffff;
    font-weight: 900;
  }}
  .pay-footer {{
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
  <div class="payroll">
    <div class="pay-header">
      <div class="header-top">
        <div>
          <div class="brand-name">Bảng Lương</div>
          <div class="brand-sub">Payroll Statement</div>
        </div>
        <div class="header-badge">Tháng {month:02d}/{year}</div>
      </div>
      <div class="pay-title">
        <h1>Phiếu Lương Nhân Viên</h1>
      </div>
    </div>
    <div class="tear"></div>
    <div class="pay-body">
      <div class="employee-info">
        <div>
          <div class="employee-name">{employee_name}</div>
          <div class="employee-detail">{position} {('| ' + department) if department else ''}</div>
        </div>
        <span class="employee-code">{employee_id}</span>
      </div>

      <div class="section-title">Thông tin chấm công</div>
      <div class="info-grid">
        <div class="info-item">
          <span class="info-label">Công chuẩn</span>
          <span class="info-value">{standard_days} ngày</span>
        </div>
        <div class="info-item">
          <span class="info-label">Ngày công thực tế</span>
          <span class="info-value">{actual_days} ngày</span>
        </div>
        <div class="info-item">
          <span class="info-label">Nghỉ phép năm</span>
          <span class="info-value">{leave_days} ngày</span>
        </div>
        <div class="info-item">
          <span class="info-label">Nghỉ không phép</span>
          <span class="info-value">{unpaid_leave} ngày</span>
        </div>
        <div class="info-item">
          <span class="info-label">Tăng ca</span>
          <span class="info-value">{total_overtime:.1f}h</span>
        </div>
        <div class="info-item">
          <span class="info-label">Phép năm còn lại</span>
          <span class="info-value">{leave_balance or 0} ngày</span>
        </div>
      </div>

      <div class="section-title">Chi tiết lương</div>
      <div class="salary-row">
        <span class="salary-label">Lương cơ bản</span>
        <span class="salary-value">{fmt_money(base_salary)} đ</span>
      </div>
      <div class="salary-row">
        <span class="salary-label">Thành tiền lương ({actual_days} ngày)</span>
        <span class="salary-value salary-add">+{fmt_money(salary_earned)} đ</span>
      </div>
      <div class="salary-row">
        <span class="salary-label">Lương tăng ca ({total_overtime:.1f}h)</span>
        <span class="salary-value salary-add">+{fmt_money(overtime_salary)} đ</span>
      </div>
      <div class="salary-row">
        <span class="salary-label">Thưởng</span>
        <span class="salary-value salary-add">+{fmt_money(bonus)} đ</span>
      </div>
      <div class="salary-row">
        <span class="salary-label">BHXH</span>
        <span class="salary-value salary-sub">-{fmt_money(bhxh)} đ</span>
      </div>
      <div class="salary-row">
        <span class="salary-label">Phạt / Khấu trừ</span>
        <span class="salary-value salary-sub">-{fmt_money(penalty)} đ</span>
      </div>

      <div class="total-box">
        <span class="total-label">Tổng lương thực nhận</span>
        <span class="total-value">{fmt_money(total_net)} đ</span>
      </div>
    </div>
    <div class="pay-footer">
      <div class="footer-left">Kỳ lương: Tháng {month:02d}/{year}</div>
      <div class="footer-right">Tạo lúc: {now_time}</div>
    </div>
  </div>
</body>
</html>"""
    return html


def _render_payroll_to_png_sync(html_content: str) -> bytes:
    """Render HTML payroll thành PNG bytes bằng Playwright SYNC API."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 700, "height": 1200},
            device_scale_factor=2
        )

        page.set_content(html_content, wait_until="networkidle")
        page.wait_for_timeout(800)

        element = page.locator(".payroll")
        screenshot = element.screenshot(type="png", omit_background=True)

        browser.close()

    return screenshot


async def render_payroll_to_png(html_content: str) -> bytes:
    """Async wrapper: chạy Playwright sync trong thread pool."""
    import asyncio
    return await asyncio.to_thread(_render_payroll_to_png_sync, html_content)


async def generate_payroll_image(
    employee_name: str,
    employee_id: str,
    month: int,
    year: int,
    data: dict,
) -> io.BytesIO:
    """
    Tạo ảnh bảng lương từ data.
    Returns io.BytesIO buffer chứa PNG, sẵn sàng gửi qua Telegram.
    """
    html = build_payroll_html(employee_name, employee_id, month, year, data)
    png_bytes = await render_payroll_to_png(html)

    buf = io.BytesIO(png_bytes)
    buf.name = f"bangluong_{employee_id}_{month:02d}_{year}.png"
    return buf
