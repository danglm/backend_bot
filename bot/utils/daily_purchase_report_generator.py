"""
Daily Purchase Report Image Generator
Render báo cáo mua mủ theo khách hàng thành ảnh PNG bằng HTML/CSS + Playwright.
"""
import io
import datetime


def fmt_money_vn(val) -> str:
    """Format số tiền kiểu Việt Nam: 1.000.000 hoặc 1.000.000,5"""
    if val is None:
        return "0"
    negative = val < 0
    abs_val = abs(float(val))

    if abs_val != int(abs_val):
        int_part = int(abs_val)
        dec_part = str(round(abs_val, 2)).split('.')[1]
        formatted = f"{int_part:,}".replace(",", ".") + f",{dec_part}"
    else:
        formatted = f"{int(abs_val):,}".replace(",", ".")

    return f"-{formatted}" if negative else formatted


def fmt_num_vn(val) -> str:
    """Format số thực kiểu VN: 1.234,5"""
    if val is None:
        return "0"
    abs_val = abs(float(val))
    negative = val < 0
    if abs_val != int(abs_val):
        int_part = int(abs_val)
        dec_part = str(round(abs_val, 2)).split('.')[1]
        formatted = f"{int_part:,}".replace(",", ".") + f",{dec_part}"
    else:
        formatted = f"{int(abs_val):,}".replace(",", ".")
    return f"-{formatted}" if negative else formatted


def build_daily_purchase_report_html(data: dict) -> str:
    """
    Tạo HTML báo cáo mua mủ ngày cho 1 khách hàng.
    
    data dict cần có:
        ten_kh, ma_ho, diem_thu_mua, timeframe,
        records: list of dict {ngay, tuan, tro_gia, kl, bi, kl_tt, so_do, mu_kho, don_gia, gia_ht, thanh_tien, luu_so, thanh_toan}
        tong_kl, tong_thanh_tien, tong_luu_so, tong_thanh_toan
    """
    now_time = datetime.datetime.now().strftime("%H:%M %d/%m/%Y")
    records = data.get("records", [])
    num_records = len(records)

    # Build table rows
    table_rows = ""
    for idx, rec in enumerate(records):
        row_class = "even" if idx % 2 == 0 else "odd"
        luu_so_val = rec.get("luu_so", 0) or 0
        thanh_toan_val = rec.get("thanh_toan", 0) or 0

        if luu_so_val > 0:
            phanbo_label = "Lưu sổ"
            phanbo_class = "text-amber"
            phanbo_val = fmt_money_vn(luu_so_val)
        else:
            phanbo_label = "Thanh toán"
            phanbo_class = "success"
            phanbo_val = fmt_money_vn(thanh_toan_val)

        table_rows += f"""
        <tr class="{row_class}">
          <td class="center">{rec.get('ngay', '—')}</td>
          <td class="center">{rec.get('tuan', '—')}</td>
          <td class="right">{rec.get('tro_gia', 0)}</td>
          <td class="right text-blue">{fmt_num_vn(rec.get('kl', 0))}</td>
          <td class="right">{fmt_num_vn(rec.get('bi', 0))}</td>
          <td class="right">{fmt_num_vn(rec.get('kl_tt', 0))}</td>
          <td class="right">{fmt_num_vn(rec.get('so_do', 0))}</td>
          <td class="right">{fmt_num_vn(rec.get('mu_kho', 0))}</td>
          <td class="right">{fmt_money_vn(rec.get('don_gia', 0))}</td>
          <td class="right">{fmt_money_vn(rec.get('gia_ht', 0))}</td>
          <td class="right success">{fmt_money_vn(rec.get('thanh_tien', 0))}</td>
          <td class="right {phanbo_class}"><small>{phanbo_label}</small><br>{phanbo_val}</td>
        </tr>"""

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
    width: 1100px;
    background: #ffffff;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 4px 24px rgba(0,0,0,0.08);
  }}
  .att-header {{
    background: linear-gradient(135deg, #1a365d 0%, #2b4c7e 40%, #3b6fa0 100%);
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
    color: #bee3f8; letter-spacing: 1.5px;
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
  .customer-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 14px;
    position: relative;
    z-index: 1;
  }}
  .customer-name {{
    font-size: 20px; font-weight: 800;
    color: #ffffff; letter-spacing: 0.5px;
  }}
  .customer-code {{
    background: rgba(255,255,255,0.2);
    border: 1px solid rgba(255,255,255,0.3);
    color: #ffffff;
    font-size: 16px; font-weight: 800;
    padding: 6px 16px; border-radius: 10px;
    letter-spacing: 1.5px;
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
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
  }}
  .info-block {{
    display: flex;
    flex-direction: column;
  }}
  .info-label {{
    font-size: 10px; color: #64748b;
    font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  .info-val {{
    font-size: 15px; font-weight: 800;
    color: #0f172a; margin-top: 4px;
  }}
  .val-green {{ color: #16a34a; }}
  .val-blue {{ color: #0284c7; }}
  .val-amber {{ color: #d97706; }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 11px;
  }}
  thead th {{
    background: #1a365d;
    color: #ffffff;
    font-weight: 700;
    font-size: 10px;
    padding: 2px 8px;
    text-align: center;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    white-space: nowrap;
  }}
  thead th:first-child {{ border-radius: 8px 0 0 0; }}
  thead th:last-child {{ border-radius: 0 8px 0 0; }}
  tbody td {{
    padding: 2px 8px;
    font-size: 11px;
    color: #334155;
    font-weight: 500;
    border-bottom: 1px solid #f1f5f9;
    white-space: nowrap;
  }}
  .center {{ text-align: center; }}
  .right {{ text-align: right; }}
  tr.even {{ background: #f8fafc; }}
  tr.odd {{ background: #ffffff; }}
  .success {{ color: #16a34a; font-weight: 700; }}
  .text-blue {{ color: #0284c7; font-weight: 700; }}
  .text-amber {{ color: #d97706; font-weight: 700; }}
  tfoot td {{
    padding: 5px 8px;
    font-size: 12px;
    font-weight: 800;
    border-top: 2px solid #1a365d;
    background: #f1f5f9;
  }}
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
  <div class="report-box">
    <div class="att-header">
      <div class="header-top">
        <div>
          <div class="brand-name">BÁO CÁO MUA MỦ</div>
          <div class="brand-sub">Điểm thu mua: {data.get('diem_thu_mua', '—')}</div>
        </div>
        <div class="header-badge">{data.get('timeframe', '')}</div>
      </div>
      <div class="customer-row">
        <div class="customer-name">{data.get('ten_kh', '—')}</div>
        <div class="customer-code">{data.get('ma_ho', '—')}</div>
      </div>
    </div>
    <div class="tear"></div>
    <div class="att-body">
      <div class="summary-info">
        <div class="info-block">
          <span class="info-label">Số lần mua</span>
          <span class="info-val">{num_records}</span>
        </div>
        <div class="info-block">
          <span class="info-label">Tổng KL</span>
          <span class="info-val val-blue">{fmt_num_vn(data.get('tong_kl', 0))} kg</span>
        </div>
        <div class="info-block" style="text-align: right;">
          <span class="info-label">Tổng thành tiền</span>
          <span class="info-val val-green">{fmt_money_vn(data.get('tong_thanh_tien', 0))} đ</span>
        </div>
        <div class="info-block" style="text-align: right;">
          <span class="info-label">Lưu sổ</span>
          <span class="info-val val-amber">{fmt_money_vn(data.get('tong_luu_so', 0))} đ</span>
        </div>
        <div class="info-block" style="text-align: right;">
          <span class="info-label">Thanh toán</span>
          <span class="info-val val-green">{fmt_money_vn(data.get('tong_thanh_toan', 0))} đ</span>
        </div>
      </div>
      <table>
        <thead>
          <tr>
            <th>Ngày</th>
            <th>Tuần</th>
            <th>Trợ giá</th>
            <th>KL (kg)</th>
            <th>Bì (kg)</th>
            <th>KL TT</th>
            <th>Số độ</th>
            <th>Mủ khô</th>
            <th>Đơn giá</th>
            <th>Giá HT</th>
            <th>Thành tiền</th>
            <th>Phân bổ</th>
          </tr>
        </thead>
        <tbody>
          {table_rows}
        </tbody>
        <tfoot>
          <tr>
            <td colspan="3" class="center"><b>TỔNG CỘNG</b></td>
            <td class="right text-blue">{fmt_num_vn(data.get('tong_kl', 0))}</td>
            <td></td>
            <td class="right">{fmt_num_vn(data.get('tong_kl_tt', 0))}</td>
            <td></td>
            <td class="right">{fmt_num_vn(data.get('tong_mu_kho', 0))}</td>
            <td></td>
            <td></td>
            <td class="right success">{fmt_money_vn(data.get('tong_thanh_tien', 0))}</td>
            <td></td>
          </tr>
        </tfoot>
      </table>
    </div>
    <div class="att-footer">
      <div class="footer-left">Khách hàng: {data.get('ten_kh', '')} ({data.get('ma_ho', '')})</div>
      <div class="footer-right">Tạo lúc: {now_time}</div>
    </div>
  </div>
</body>
</html>"""
    return html


def _render_to_png_sync(html_content: str) -> bytes:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 1180, "height": 1200},
            device_scale_factor=2
        )

        page.set_content(html_content, wait_until="networkidle")
        page.wait_for_timeout(800)

        element = page.locator(".report-box")
        screenshot = element.screenshot(type="png", omit_background=True)

        browser.close()

    return screenshot


async def render_to_png(html_content: str) -> bytes:
    import asyncio
    return await asyncio.to_thread(_render_to_png_sync, html_content)


async def generate_daily_purchase_report_image(data: dict) -> io.BytesIO:
    """Tạo ảnh báo cáo mua mủ từ data dict. Returns io.BytesIO PNG buffer."""
    html = build_daily_purchase_report_html(data)
    png_bytes = await render_to_png(html)

    buf = io.BytesIO(png_bytes)
    buf.name = f"daily_purchase_{data.get('ma_ho', 'report')}.png"
    return buf
