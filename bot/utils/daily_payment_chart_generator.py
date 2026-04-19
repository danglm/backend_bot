"""
Daily Payment Chart Image Generator
Render HTML/CSS Line Chart using Chart.js thành ảnh PNG bằng Playwright.
Hỗ trợ vẽ nhiều biểu đồ xếp dọc theo từng tháng.
"""
import io
import datetime
import json
from typing import List, Dict, Any

def build_daily_payment_chart_html(data: dict) -> str:
    title = data.get("title", "BIỂU ĐỒ THU CHI HÀNG NGÀY")
    subtitle = data.get("subtitle", "")
    charts_json = json.dumps(data.get("charts", []))
    
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
    padding: 24px;
    width: 1200px;
    min-height: 800px;
  }}
  .report-box {{
    width: 100%;
    background: #ffffff;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 4px 24px rgba(0,0,0,0.08);
    display: flex;
    flex-direction: column;
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
    width: 300px; height: 300px;
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
    font-size: 18px; font-weight: 800;
    color: #bee3f8; letter-spacing: 1.5px;
    text-transform: uppercase;
  }}
  .brand-sub {{
    font-size: 13px; color: rgba(255,255,255,0.5);
    margin-top: 4px;
  }}
  .header-badge {{
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.2);
    color: #ffffff;
    font-size: 13px; font-weight: 700;
    padding: 6px 14px; border-radius: 10px;
    letter-spacing: 0.5px;
  }}
  .header-main-title {{
    font-size: 24px; font-weight: 800;
    color: #ffffff; letter-spacing: 0.5px;
    margin-top: 14px;
    position: relative;
    z-index: 1;
  }}
  .tear {{
    height: 14px; background: #f8fafc;
    position: relative; margin-top: -1px;
  }}
  .tear::before {{
    content: '';
    position: absolute;
    top: -7px; left: 0; right: 0;
    height: 14px;
    background: radial-gradient(circle at 7px 0, transparent 7px, #f8fafc 7px) repeat-x;
    background-size: 14px 14px;
  }}
  .att-body {{
    padding: 20px 28px 32px 28px;
    background: #f8fafc;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 32px;
  }}
  .chart-container {{
    background: #ffffff;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.04);
    padding: 20px;
    border: 1px solid #e2e8f0;
    min-height: 480px;
    display: flex;
    flex-direction: column;
  }}
  .month-title {{
    font-size: 16px;
    font-weight: 800;
    color: #1a365d;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 12px;
    text-transform: uppercase;
  }}
  .month-title::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: #e2e8f0;
  }}
  .chart-wrapper {{
    flex: 1;
    position: relative;
    width: 100%;
    height: 100%;
    min-height: 400px;
  }}
</style>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.0.0"></script>
</head>
<body>
  <div class="report-box" id="main-wrapper">
    <!-- Header -->
    <div class="att-header">
      <div class="header-top">
        <div>
          <div class="brand-name">CÔNG TY TIẾN NGA</div>
          <div class="brand-sub">HỆ THỐNG PHÂN TÍCH TÀI CHÍNH</div>
        </div>
        <div class="header-badge">HÀNG NGÀY</div>
      </div>
      <div class="header-main-title">{title}</div>
      <div class="brand-sub" style="color: #ffffff; margin-top: 4px; font-size: 14px;">{subtitle.replace(chr(10), ' • ')}</div>
    </div>
    
    <!-- Tear effect -->
    <div class="tear"></div>

    <!-- Body -->
    <div class="att-body" id="charts-list">
    </div>
  </div>

  <script>
    // Register the datalabels plugin
    Chart.register(ChartDataLabels);

    const chartsData = {charts_json};
    
    // Custom number formatter for VN format
    function formatVND(value) {{
      if (value === 0) return '';
      return value.toLocaleString('vi-VN');
    }}

    window.onload = function() {{
      const listContainer = document.getElementById('charts-list');
      
      chartsData.forEach((cData, index) => {{
        const container = document.createElement('div');
        container.className = 'chart-container';
        container.style.marginTop = index > 0 ? '32px' : '0';
        
        const titleLine = document.createElement('div');
        titleLine.className = 'month-title';
        titleLine.innerText = cData.month_label;
        container.appendChild(titleLine);
        
        const wrapper = document.createElement('div');
        wrapper.className = 'chart-wrapper';
        
        const canvas = document.createElement('canvas');
        canvas.id = 'chart_canvas_' + index;
        wrapper.appendChild(canvas);
        container.appendChild(wrapper);
        
        listContainer.appendChild(container);
        
        const dataConfig = {{
          labels: cData.labels,
          datasets: [
            {{
              label: 'Số Tiền Thu',
              data: cData.thu,
              borderColor: '#10b981', // green
              backgroundColor: 'rgba(16, 185, 129, 0.1)',
              borderWidth: 2,
              pointRadius: 4,
              pointBackgroundColor: '#10b981',
              tension: 0.3,
              fill: true,
              datalabels: {{
                color: '#047857',
                align: 'top',
                anchor: 'end',
                offset: 4,
                font: {{ family: 'Inter', weight: '600', size: 11 }},
                formatter: formatVND
              }}
            }},
            {{
              label: 'Số Tiền Chi',
              data: cData.chi,
              borderColor: '#ef4444', // red
              backgroundColor: 'rgba(239, 68, 68, 0.1)',
              borderWidth: 2,
              pointRadius: 4,
              pointBackgroundColor: '#ef4444',
              tension: 0.3,
              fill: true,
              datalabels: {{
                color: '#b91c1c',
                align: 'bottom',
                anchor: 'start',
                offset: 4,
                font: {{ family: 'Inter', weight: '600', size: 11 }},
                formatter: formatVND
              }}
            }}
          ]
        }};

        const config = {{
          type: 'line',
          data: dataConfig,
          options: {{
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            layout: {{
                padding: {{ top: 30, bottom: 30, left: 10, right: 10 }}
            }},
            interaction: {{
              mode: 'index',
              intersect: false,
            }},
            plugins: {{
              legend: {{
                position: 'top',
                labels: {{
                  font: {{ family: 'Inter', size: 13, weight: '600' }},
                  usePointStyle: true,
                  padding: 20
                }}
              }},
              tooltip: {{ enabled: false }}
            }},
            scales: {{
              x: {{
                grid: {{ color: '#f1f5f9' }},
                ticks: {{
                  font: {{ family: 'Inter', size: 11 }},
                  color: '#64748b',
                  maxRotation: 45,
                  minRotation: 0,
                  autoSkip: false
                }}
              }},
              y: {{
                beginAtZero: true,
                border: {{ display: false }},
                grid: {{ color: '#e2e8f0', drawBorder: false }},
                ticks: {{
                  font: {{ family: 'Inter', size: 11 }},
                  color: '#64748b',
                  callback: function(value) {{
                      return value.toLocaleString('vi-VN');
                  }}
                }},
                title: {{
                  display: true,
                  text: 'Số Tiền (VNĐ)',
                  color: '#94a3b8',
                  font: {{ family: 'Inter', size: 12, weight: '600' }}
                }}
              }}
            }}
          }}
        }};
        
        new Chart(document.getElementById('chart_canvas_' + index), config);
      }});
    }};
  </script>
</body>
</html>"""
    return html

def _render_chart_html_to_png_sync(html_content: str) -> bytes:
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Tăng viewport width để có chỗ hiển thị nhãn số tiền lớn
        page = browser.new_page(
            viewport={"width": 1200, "height": 1000},
            device_scale_factor=2
        )
        
        page.set_content(html_content, wait_until="networkidle")
        page.wait_for_timeout(1500) # Đợi render ChartJS và plugins
        
        container = page.locator("#main-wrapper")
        screenshot = container.screenshot(type="png", omit_background=True)
        
        browser.close()
    
    return screenshot

async def render_daily_payment_chart_html_to_png(html_content: str) -> bytes:
    import asyncio
    return await asyncio.to_thread(_render_chart_html_to_png_sync, html_content)

async def generate_daily_payment_chart_image(data: dict) -> io.BytesIO:
    html = build_daily_payment_chart_html(data)
    png_bytes = await render_daily_payment_chart_html_to_png(html)
    
    buf = io.BytesIO(png_bytes)
    now_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    buf.name = f"chart_{now_str}.png"
    return buf
