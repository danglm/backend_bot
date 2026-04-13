"""
Receipt Image Generator
Render HTML/CSS templates thành ảnh PNG bằng Playwright.
"""
import io
import datetime
from dataclasses import dataclass
from typing import Optional


def fmt_money_vn(val: float) -> str:
    """Format số tiền kiểu Việt Nam: 1.000.000 hoặc 1.000.000,5"""
    if val is None:
        return "0"
    negative = val < 0
    abs_val = abs(val)
    
    if abs_val != int(abs_val):
        int_part = int(abs_val)
        dec_part = str(round(abs_val, 2)).split('.')[1]
        formatted = f"{int_part:,}".replace(",", ".") + f",{dec_part}"
    else:
        formatted = f"{int(abs_val):,}".replace(",", ".")
    
    return f"-{formatted}" if negative else formatted


def build_chotso_ketoan_html(data: dict) -> str:
    """
    Tạo HTML biên lai Chốt Sổ Kế Toán.
    
    data dict cần có các key:
        ngay, diem_thu_mua, ten_kh, ma_ho,
        tien_mua_mu_ngay, cong_no_cuoi_ky,
        tong_tam_ung_thang, tong_mua_mu_thang,
        tong_da_thanh_toan_thang, cong_no_hien_tai
    """
    cong_no = data.get("cong_no_hien_tai", 0)
    if cong_no < 0:
        debt_color = "#dc2626"
        debt_status = "CÒN NỢ"
        debt_bg = "rgba(220, 38, 38, 0.08)"
        debt_border = "rgba(220, 38, 38, 0.2)"
    elif cong_no > 0:
        debt_color = "#16a34a"
        debt_status = "CÒN DƯ"
        debt_bg = "rgba(22, 163, 74, 0.08)"
        debt_border = "rgba(22, 163, 74, 0.2)"
    else:
        debt_color = "#64748b"
        debt_status = "ĐÃ QUYẾT TOÁN"
        debt_bg = "rgba(100, 116, 139, 0.08)"
        debt_border = "rgba(100, 116, 139, 0.2)"

    # Parse ngày
    ngay_parts = data["ngay"].replace("/", "-").split("-")
    if len(ngay_parts) == 3:
        day_str = ngay_parts[0]
        month_year_str = f"Tháng {ngay_parts[1]}/{ngay_parts[2]}"
    else:
        day_str = data["ngay"]
        month_year_str = ""

    now_time = datetime.datetime.now().strftime("%H:%M:%S")
    ref = f"{data.get('ma_ho','')}-{data['ngay'].replace('-','').replace('/','')}"

    # Build monthly rows
    monthly_rows = ""
    monthly_items = [
        ("Tổng Tạm Ứng Tháng", data.get("tong_tam_ung_thang", 0)),
        ("Tổng Mua Mủ Tháng", data.get("tong_mua_mu_thang", 0)),
        ("Tổng Đã Thanh Toán Tháng", data.get("tong_da_thanh_toan_thang", 0)),
    ]
    for label, val in monthly_items:
        css_class = "negative" if val < 0 else ("positive" if val > 0 else "")
        monthly_rows += f"""
        <div class="data-row">
          <span class="label">{label}</span>
          <span class="value {css_class}">{fmt_money_vn(val)}</span>
        </div>"""

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
  .receipt {{
    width: 440px;
    background: #ffffff;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 4px 24px rgba(0,0,0,0.08);
    position: relative;
  }}
  .receipt-header {{
    background: linear-gradient(135deg, #0c4a6e 0%, #075985 40%, #0369a1 100%);
    padding: 26px 28px 22px 28px;
    position: relative;
    overflow: hidden;
  }}
  .receipt-header::before {{
    content: '';
    position: absolute;
    top: -60%; right: -25%;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(56, 189, 248, 0.15) 0%, transparent 70%);
    border-radius: 50%;
  }}
  .receipt-header::after {{
    content: '';
    position: absolute;
    bottom: -50%; left: -15%;
    width: 180px; height: 180px;
    background: radial-gradient(circle, rgba(125, 211, 252, 0.1) 0%, transparent 70%);
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
    font-size: 18px; font-weight: 800;
    color: #7dd3fc; letter-spacing: 1.5px;
    text-transform: uppercase;
  }}
  .brand-sub {{
    font-size: 10px; color: rgba(255,255,255,0.45);
    margin-top: 2px; letter-spacing: 0.5px;
  }}
  .header-date {{ text-align: right; }}
  .header-date .day {{
    font-size: 28px; font-weight: 800;
    color: #ffffff; line-height: 1;
  }}
  .header-date .month-year {{
    font-size: 11px; color: rgba(255,255,255,0.6);
    font-weight: 500; margin-top: 2px;
  }}
  .receipt-title {{
    text-align: center; margin-top: 18px;
    position: relative; z-index: 1;
  }}
  .receipt-title h1 {{
    font-size: 17px; font-weight: 700;
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
  .receipt-body {{
    padding: 6px 28px 24px 28px;
  }}
  .customer-card {{
    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
    border: 1px solid #bae6fd;
    border-radius: 12px;
    padding: 16px 18px;
    margin-bottom: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .customer-name {{
    font-size: 18px; font-weight: 800;
    color: #0c4a6e; letter-spacing: 0.5px;
  }}
  .customer-detail {{
    font-size: 11px; color: #0369a1;
    font-weight: 500; margin-top: 4px;
  }}
  .customer-code {{
    background: #0369a1; color: #ffffff;
    font-size: 14px; font-weight: 800;
    padding: 8px 14px; border-radius: 10px;
    letter-spacing: 1px;
  }}
  .section-title {{
    font-size: 10px; font-weight: 700;
    color: #94a3b8; text-transform: uppercase;
    letter-spacing: 1.5px; margin-bottom: 10px;
    display: flex; align-items: center; gap: 8px;
  }}
  .section-title::after {{
    content: ''; flex: 1; height: 1px;
    background: #e2e8f0;
  }}
  .highlight-box {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 20px;
  }}
  .highlight-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 0;
  }}
  .highlight-row .label {{
    font-size: 12px; color: #64748b; font-weight: 500;
  }}
  .highlight-row .value {{
    font-size: 14px; color: #0f172a; font-weight: 700;
  }}
  .divider {{
    border: none;
    border-top: 1.5px dashed #e2e8f0;
    margin: 4px 0;
  }}
  .data-rows {{ margin-bottom: 20px; }}
  .data-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 9px 0;
    border-bottom: 1px solid #f1f5f9;
  }}
  .data-row:last-child {{ border-bottom: none; }}
  .data-row .label {{
    font-size: 12.5px; color: #475569; font-weight: 500;
  }}
  .data-row .value {{
    font-size: 13px; color: #1e293b; font-weight: 700;
    font-variant-numeric: tabular-nums;
  }}
  .data-row .value.negative {{ color: #dc2626; }}
  .data-row .value.positive {{ color: #16a34a; }}
  .total-box {{
    background: linear-gradient(135deg, {debt_bg} 0%, {debt_bg} 100%);
    border: 1.5px solid {debt_border};
    border-radius: 12px;
    padding: 18px;
    margin-bottom: 16px;
    position: relative; overflow: hidden;
  }}
  .total-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }}
  .total-label {{
    font-size: 12px; color: #64748b;
    font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  .total-badge {{
    font-size: 9px; font-weight: 800;
    color: {debt_color};
    background: {debt_bg};
    border: 1px solid {debt_border};
    padding: 3px 10px; border-radius: 20px;
    letter-spacing: 1px;
  }}
  .total-amount {{
    font-size: 26px; font-weight: 900;
    color: {debt_color}; text-align: right;
    letter-spacing: -0.5px;
  }}
  .total-currency {{
    font-size: 14px; font-weight: 600;
    color: {debt_color}; opacity: 0.7;
  }}
  .receipt-footer {{
    padding: 16px 28px 20px 28px;
    background: #f8fafc;
    border-top: 1px solid #e2e8f0;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .footer-left {{
    font-size: 10px; color: #94a3b8; line-height: 1.6;
  }}
  .footer-left strong {{ color: #64748b; }}
  .footer-right {{ text-align: right; }}
  .footer-time {{
    font-size: 10px; color: #94a3b8;
    font-family: 'Inter', monospace;
  }}
  .footer-verify {{
    font-size: 9px; color: #cbd5e1;
    font-family: 'Inter', monospace;
    letter-spacing: 0.8px; margin-top: 4px;
  }}
  .stamp {{
    position: absolute;
    bottom: 120px; right: 20px;
    border: 3px solid rgba(3, 105, 161, 0.18);
    color: rgba(3, 105, 161, 0.18);
    font-size: 22px; font-weight: 900;
    padding: 5px 14px; border-radius: 8px;
    letter-spacing: 3px;
    transform: rotate(-12deg);
    pointer-events: none; z-index: 2;
  }}
</style>
</head>
<body>
  <div class="receipt">
    <div class="stamp">ĐÃ CHỐT SỔ</div>
    <div class="receipt-header">
      <div class="header-top">
        <div>
          <div class="brand-name">Chốt Sổ Kế Toán</div>
          <div class="brand-sub">Điểm Thu Mua: {data['diem_thu_mua']}</div>
        </div>
        <div class="header-date">
          <div class="day">{day_str}</div>
          <div class="month-year">{month_year_str}</div>
        </div>
      </div>
      <div class="receipt-title">
        <h1>Bảng Quyết Toán Ngày</h1>
      </div>
    </div>
    <div class="tear"></div>
    <div class="receipt-body">
      <div class="customer-card">
        <div>
          <div class="customer-name">{data['ten_kh']}</div>
          <div class="customer-detail">Khách hàng thu mua</div>
        </div>
        <span class="customer-code">{data['ma_ho']}</span>
      </div>
      <div class="section-title">Chi tiết giao dịch trong ngày</div>
      <div class="highlight-box">
        <div class="highlight-row">
          <span class="label">Số lượng (kg)</span>
          <span class="value">{data.get('so_luong', '0')}</span>
        </div>
        <div class="highlight-row">
          <span class="label">Số độ (%)</span>
          <span class="value">{data.get('so_do', '0')}</span>
        </div>
        <div class="highlight-row">
          <span class="label">Mủ khô</span>
          <span class="value">{data.get('mu_kho', '0')}</span>
        </div>
        <div class="highlight-row">
          <span class="label">Trợ giá</span>
          <span class="value">{data.get('tro_gia', '0')}</span>
        </div>
        <div class="highlight-row">
          <span class="label">Đơn giá (vnđ/kg)</span>
          <span class="value">{", ".join(fmt_money_vn(x) for x in data.get('don_gia', []))}</span>
        </div>
        <div class="highlight-row">
          <span class="label">Giá hỗ trợ (vnđ/kg)</span>
          <span class="value">{", ".join(fmt_money_vn(x) for x in data.get('gia_ho_tro', []))}</span>
        </div>
        <hr class="divider">
        <div class="highlight-row">
          <span class="label">Tiền Mua Mủ Ngày</span>
          <span class="value">{fmt_money_vn(data.get('tien_mua_mu_ngay', 0))}</span>
        </div>
        <div class="highlight-row">
          <span class="label">Công Nợ Cuối Kỳ</span>
          <span class="value">{fmt_money_vn(data.get('cong_no_cuoi_ky', 0))}</span>
        </div>
      </div>
      <hr class="divider">
      <div class="section-title">Tổng hợp tháng</div>
      <div class="data-rows">{monthly_rows}
      </div>
      <div class="total-box">
        <div class="total-header">
          <span class="total-label">Công Nợ Hiện Tại</span>
          <span class="total-badge">{debt_status}</span>
        </div>
        <div class="total-amount">
          {fmt_money_vn(data['cong_no_hien_tai'])} <span class="total-currency">VNĐ</span>
        </div>
      </div>
    </div>
    <div class="receipt-footer">
      <div class="footer-left">
        Điểm thu mua: <strong>{data['diem_thu_mua']}</strong><br>
        Ngày chốt: <strong>{data['ngay']}</strong>
      </div>
      <div class="footer-right">
        <div class="footer-time">Xuất lúc: {now_time}</div>
        <div class="footer-verify">REF: {ref}</div>
      </div>
    </div>
  </div>
</body>
</html>"""
    return html


def _render_html_to_png_sync(html_content: str) -> bytes:
    """
    Render HTML string thành PNG bytes bằng Playwright SYNC API.
    Chạy trong thread riêng để tránh lỗi NotImplementedError 
    trên Windows event loop (Pyrogram/ProactorEventLoop).
    """
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 520, "height": 900},
            device_scale_factor=2
        )
        
        page.set_content(html_content, wait_until="networkidle")
        page.wait_for_timeout(800)
        
        receipt = page.locator(".receipt")
        screenshot = receipt.screenshot(type="png", omit_background=True)
        
        browser.close()
    
    return screenshot


async def render_html_to_png(html_content: str) -> bytes:
    """Async wrapper: chạy Playwright sync trong thread pool."""
    import asyncio
    return await asyncio.to_thread(_render_html_to_png_sync, html_content)


async def generate_chotso_ketoan_image(data: dict) -> io.BytesIO:
    """
    Tạo ảnh biên lai chốt sổ kế toán từ data dict.
    Returns io.BytesIO buffer chứa PNG, sẵn sàng gửi qua Telegram.
    """
    html = build_chotso_ketoan_html(data)
    png_bytes = await render_html_to_png(html)
    
    buf = io.BytesIO(png_bytes)
    buf.name = f"chotso_{data.get('ma_ho', 'receipt')}_{data['ngay'].replace('-','').replace('/','')}.png"
    return buf
