"""
Purchase Chart Image Generator
Render HTML/CSS Line Chart using Chart.js thành ảnh PNG bằng Playwright.
Hỗ trợ vẽ nhiều biểu đồ xếp dọc theo từng tháng.
"""
import io
import datetime
import json
from typing import List, Dict, Any

def build_purchase_chart_html(data: dict) -> str:
    """
    Tạo HTML cho Biểu Đồ Thu Mua.
    
    data dict cần có các key:
        title: Tiêu đề biểu đồ
        subtitle: Chi tiết thời gian/địa điểm
        charts: danh sách các dictionary theo tháng:
            [
                {
                    "month_label": "Tháng 10/2026",
                    "labels": ["01/10", "02/10", ...],
                    "weight": [...],
                    "actual_weight": [...],
                    "dry_rubber": [...]
                },
                ...
            ]
    """
    title = data.get("title", "Biểu Đồ Thu Mua Mủ")
    subtitle = data.get("subtitle", "")
    charts_json = json.dumps(data.get("charts", []))
    
    # HTML Template
    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Inter', sans-serif;
    background: transparent;
    display: flex;
    justify-content: center;
    padding: 24px;
    width: 1000px;
    min-height: 800px; /* Bắt buộc tối thiểu để load */
  }}
  .main-wrapper {{
    width: 100%;
    background: transparent;
    display: flex;
    flex-direction: column;
    gap: 32px; /* Khoảng cách giữa các tháng */
  }}
  .main-header {{
    text-align: center;
    background: #ffffff;
    border-radius: 16px;
    padding: 24px 32px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.06);
    border: 1px solid #f1f5f9;
  }}
  .main-header h1 {{
    font-size: 26px;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: 0.5px;
    text-transform: uppercase;
  }}
  .main-header p {{
    font-size: 15px;
    color: #64748b;
    font-weight: 500;
    margin-top: 6px;
  }}
  .chart-container {{
    background: #ffffff;
    border-radius: 16px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.06);
    padding: 24px 32px 32px 32px;
    border: 1px solid #f1f5f9;
    min-height: 480px;
    display: flex;
    flex-direction: column;
  }}
  .month-title {{
    font-size: 18px;
    font-weight: 700;
    color: #334155;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 12px;
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
    min-height: 380px;
  }}
</style>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
  <div class="main-wrapper" id="main-wrapper">
    <!-- Header -->
    <div class="main-header">
      <h1>{title}</h1>
      <p>{subtitle}</p>
    </div>
    
    <!-- Custom charts will be injected here -->
    <div id="charts-list"></div>
  </div>

  <script>
    const chartsData = {charts_json};
    
    window.onload = function() {{
      const listContainer = document.getElementById('charts-list');
      
      chartsData.forEach((cData, index) => {{
        // Cấu trúc DOM
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
        
        // Vẽ Chart.js
        const dataConfig = {{
          labels: cData.labels,
          datasets: [
            {{
              label: 'Khối Lượng',
              data: cData.weight,
              borderColor: '#3b82f6',
              backgroundColor: 'rgba(59, 130, 246, 0.1)',
              borderWidth: 2,
              pointRadius: 3,
              pointHoverRadius: 5,
              tension: 0.3,
              fill: true
            }},
            {{
              label: 'KL Thực Tế',
              data: cData.actual_weight,
              borderColor: '#10b981',
              backgroundColor: 'transparent',
              borderWidth: 2,
              pointRadius: 3,
              pointBackgroundColor: '#10b981',
              tension: 0.3
            }},
            {{
              label: 'Mủ Khô',
              data: cData.dry_rubber,
              borderColor: '#f59e0b',
              backgroundColor: 'transparent',
              borderWidth: 2,
              pointStyle: 'rectRot',
              pointRadius: 4,
              pointBackgroundColor: '#f59e0b',
              tension: 0.3
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
                  font: {{ family: 'Inter', size: 10 }},
                  color: '#64748b',
                  maxRotation: 45,
                  minRotation: 0,
                  autoSkip: true,
                  maxTicksLimit: 30
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
                      return value.toLocaleString('vi-VN') + " Kg";
                  }}
                }},
                title: {{
                  display: true,
                  text: 'Số lượng (Kg)',
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
    """Render HTML sang PNG bằng Playwright SYNC."""
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Viewport cao để tải trang rộng, chụp full_page hoặc theo element
        page = browser.new_page(
            viewport={"width": 1000, "height": 1000},
            device_scale_factor=2
        )
        
        page.set_content(html_content, wait_until="networkidle")
        page.wait_for_timeout(1000)
        
        # Lấy toàn bộ khối Div tổng để screenshot tự giãn theo chiều dọc
        container = page.locator(".main-wrapper")
        screenshot = container.screenshot(type="png", omit_background=True)
        
        browser.close()
    
    return screenshot

async def render_chart_html_to_png(html_content: str) -> bytes:
    """Async wrapper cho chart html."""
    import asyncio
    return await asyncio.to_thread(_render_chart_html_to_png_sync, html_content)

async def generate_chart_image(data: dict) -> io.BytesIO:
    """
    Tạo ảnh chart và đóng gói vào BytesIO để gửi qua pyrogram.
    """
    html = build_purchase_chart_html(data)
    png_bytes = await render_chart_html_to_png(html)
    
    buf = io.BytesIO(png_bytes)
    now_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    buf.name = f"chart_{now_str}.png"
    return buf
