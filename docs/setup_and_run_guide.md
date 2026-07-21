# Hướng Dẫn Cài Đặt & Chạy Dự Án (Backend FastAPI & Telegram Bot)

<style>
body {
  font-size: 14px !important;
}
</style>

Tài liệu này hướng dẫn chi tiết các bước từ chuẩn bị môi trường, cài đặt thư viện, cấu hình cơ sở dữ liệu cho đến khi khởi chạy thành công dự án trên hệ điều hành Windows.

---

## Cấu Trúc Thư Mục Dự Án

Dưới đây là sơ đồ cấu trúc thư mục của dự án và chức năng của từng thư mục/tệp tin chính:

```text
backend/
├── alembic/                # Chứa các file kịch bản migration cơ sở dữ liệu của Alembic.
│   └── versions/           # Chi tiết các tệp migration qua các phiên bản.
├── app/                    # Thư mục chính chứa mã nguồn ứng dụng FastAPI.
│   ├── api/                # Các routers định nghĩa endpoints cho API.
│   │   └── v1/             # Endpoints phiên bản 1 (ví dụ: rosca.py, employee.py, auth.py,...).
│   ├── core/               # Chứa cấu hình cốt lõi (settings, bảo mật security, logger,...).
│   ├── crud/               # Chứa logic tương tác cơ sở dữ liệu (Create, Read, Update, Delete).
│   ├── db/                 # Quản lý kết nối DB và khai báo Base model của SQLAlchemy.
│   ├── models/             # Định nghĩa các Class ORM Models (ánh xạ sang bảng PostgreSQL).
│   ├── schemas/            # Định nghĩa Pydantic Schemas (kiểm tra kiểu dữ liệu đầu vào/đầu ra).
│   ├── services/           # Lớp chứa các logic nghiệp vụ phức tạp hoặc kết nối dịch vụ bên thứ ba.
│   └── main.py             # File khởi chạy ứng dụng FastAPI (đăng ký middlewares, routers, cron tasks).
├── bot/                    # Thư mục chứa mã nguồn của Telegram Bot (chạy song song với API).
│   ├── core/               # Cấu hình cốt lõi của Bot, kết nối, đăng ký bộ lọc (filters).
│   ├── handlers/           # Xử lý các câu lệnh/sự kiện (ví dụ: rosca.py, credit.py, tien_nga.py,...).
│   ├── keyboards/          # Định nghĩa giao diện nút nhấn tương tác (Inline/Reply Keyboards).
│   ├── middlewares/        # Bộ lọc trung gian xử lý tin nhắn trước khi gửi đến handlers.
│   ├── states/             # Quản lý các trạng thái nhập dữ liệu của người dùng (Finite State Machine).
│   └── utils/              # Các hàm tiện ích hỗ trợ định dạng tin nhắn, kiểm tra quyền, v.v.
├── docs/                   # Thư mục chứa tài liệu hướng dẫn và tài liệu API của dự án.
├── markdown/               # Thư mục chứa các hướng dẫn quy trình nghiệp vụ dạng markdown.
├── appsettings.json        # File cấu hình toàn cục (DB, Telegram, IP, Port, CORS, Scheduler,...).
├── ngrok_token.yml         # Cấu hình authtoken cho ngrok để tạo đường hầm public webhook.
├── requirements.txt        # Danh sách các thư viện Python cần cài đặt.
├── run.py                  # File khởi động tổng hợp (chạy ngrok, webhook bot, workers, và uvicorn).
├── sync_db_prod.py         # Công cụ đồng bộ nhanh cấu trúc DB từ Class Models sang Database thực tế.
├── apply_migration.bat     # Script Windows chạy nhanh lệnh cập nhật database của Alembic.
└── generate_migration.bat  # Script Windows chạy nhanh lệnh tự động sinh file migration của Alembic.
```

---



## 1. Chuẩn Bị Môi Trường

Dự án yêu cầu cài đặt sẵn các công cụ sau trên máy tính:
* **Python**: Khuyến nghị phiên bản **3.10** hoặc **3.11** (Tải từ [python.org](https://www.python.org/downloads/)).
* **PostgreSQL**: Công cụ quản trị cơ sở dữ liệu (Khuyến nghị bản 14 trở lên, tải từ [postgresql.org](https://www.postgresql.org/download/)).
* **Git**: Dùng để quản lý mã nguồn (Tải từ [git-scm.com](https://git-scm.com/)).

---

## 2. Các Bước Cài Đặt Chi Tiết

### Bước 2.1. Clone Code
Mở terminal (CMD, PowerShell hoặc Git Bash) và chạy lệnh clone dự án về máy:
```bash
git clone <URL_KHO_MA_NGUON>
cd backend
```

---

### Bước 2.2. Tạo Môi Trường Ảo (.venv)
Tạo một môi trường ảo Python độc lập cho dự án để tránh xung đột thư viện hệ thống:
```bash
# Tạo môi trường ảo với tên thư mục là .venv
python -m venv .venv
```

Kích hoạt môi trường ảo:
* **Trên Windows PowerShell:**
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
  *(Lưu ý: Nếu gặp lỗi quyền thực thi tập lệnh trên PowerShell, hãy chạy lệnh `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process` trước).*
* **Trên Windows CMD:**
  ```cmd
  .venv\Scripts\activate.bat
  ```
* **Trên Git Bash / Linux:**
  ```bash
  source .venv/Scripts/activate
  ```

Sau khi kích hoạt thành công, bạn sẽ thấy ký hiệu `(.venv)` xuất hiện ở đầu dòng lệnh của terminal.

---

### Bước 2.3. Cài Đặt Các Thư Viện (Dependencies)
Nâng cấp công cụ quản lý gói `pip` và cài đặt toàn bộ thư viện từ file `requirements.txt`:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> [!IMPORTANT]
> Dự án có sử dụng thư viện **Playwright** để chụp ảnh/tạo báo cáo hóa đơn. Sau khi cài đặt requirements, bạn bắt buộc phải tải về các trình duyệt không đầu (headless browsers) của Playwright bằng lệnh sau:
> ```bash
> playwright install
> ```

---

## 3. Cấu Hình Hệ Thống

Hệ thống sử dụng hai tệp cấu hình chính nằm ở thư mục gốc của dự án:

### 3.1. Cấu Hình Cơ Sở Dữ Liệu & Dịch Vụ (`appsettings.json`)
Mở tệp [appsettings.json](file:///d:/ExtraJob/backend/appsettings.json) và điều chỉnh các thông tin kết nối cho phù hợp với máy cá nhân của bạn:

```json
{
  "DB_Config": {
    "Project_Name": "Backend Project",
    "Postgres_Server": "localhost",
    "Postgres_User": "postgres",        // Tài khoản postgres của bạn
    "Postgres_Password": "16032002",    // Mật khẩu postgres của bạn
    "Postgres_DB": "hdg_group"          // Tên database cần tạo
  },
  "Service": {
    "IP_Address": "localhost",
    "Port": 8000
  },
  "Telegram": {
    "Bot_Token": "8602600233:AAHLi9VLcNjUPVu-_tywHPceas9zsHEhJqc",
    "Webhook_URL": "https://unaffecting-christel-semijocularly.ngrok-free.dev",
    "API_ID": "30082443",
    "API_HASH": "29fcf377da2ca440413a39f26b58d514"
  }
  // Các cấu hình scheduler và CORS khác...
}
```

#### Các bước thiết lập trên PostgreSQL:
1. Mở công cụ quản trị (pgAdmin hoặc kết nối qua terminal/DBeaver).
2. Tạo mới một cơ sở dữ liệu có tên trùng khớp cấu hình trên (ví dụ: `hdg_group`):
   ```sql
   CREATE DATABASE hdg_group;
   ```

---

### 3.2. Cấu Hình Ngrok Đường Truyền Ngoài (`ngrok_token.yml`)
Dự án sử dụng ngrok để tạo đường truyền công khai (public tunnel) giúp Webhook của Telegram có thể gửi sự kiện trực tiếp tới localhost của bạn.
Tạo hoặc chỉnh sửa tệp `ngrok_token.yml` ở thư mục gốc:
```yaml
authtoken: <TOKEN_NGROK_CUA_BAN>
region: ap
```
*(Token có thể lấy miễn phí khi đăng ký tài khoản tại [ngrok.com](https://ngrok.com/)).*

---

## 4. Khởi Tạo & Đồng Bộ Bảng Dữ Liệu

Dự án hỗ trợ hai phương pháp để khởi tạo và đồng bộ hóa cấu trúc bảng dữ liệu (schema) vào PostgreSQL:

### Phương pháp 1: Sử dụng Alembic (Quản lý theo phiên bản)
Alembic giúp quản lý lịch sử thay đổi cấu trúc bảng theo từng phiên bản (version control).

* **Cách 1: Chạy nhanh qua file Script (Windows)**
  Double-click vào tệp [apply_migration.bat](file:///d:/ExtraJob/backend/apply_migration.bat) ở thư mục gốc.
* **Cách 2: Chạy thủ công bằng lệnh terminal**
  ```bash
  alembic upgrade head
  ```
* **Khi muốn cập nhật thay đổi từ SQLAlchemy Models vào database:**
  Chạy lệnh:
  ```bash
  alembic revision --autogenerate -m "tên_mô_tả_migration"
  ```
  *(Hoặc chạy file [generate_migration.bat](file:///d:/ExtraJob/backend/generate_migration.bat)).*

### Phương pháp 2: Sử dụng Script tự động `sync_db_prod.py` (Đồng bộ trực tiếp SQLAlchemy Models)
Tệp [sync_db_prod.py](file:///d:/ExtraJob/backend/sync_db_prod.py) cho phép tự động đối chiếu các class model SQLAlchemy với cơ sở dữ liệu hiện tại, tự động phát hiện bảng thiếu, cột thiếu và tạo mã lệnh SQL để bổ sung vào DB mà không làm mất dữ liệu cũ.

* **Bước 1: Xem trước các thay đổi sẽ áp dụng (Dry Run):**
  ```bash
  python sync_db_prod.py --dry-run
  ```
* **Bước 2: Thực thi áp dụng thay đổi vào Database:**
  ```bash
  python sync_db_prod.py --apply
  ```
* **Các tùy chọn bổ sung:**
  * Chỉ định cơ sở dữ liệu đích khác (mặc định đọc từ `appsettings.json`):
    ```bash
    python sync_db_prod.py --apply --db-url "postgresql://user:pass@host/dbname"
    ```
  * Xuất câu lệnh SQL thay đổi ra tệp tin (không thực thi):
    ```bash
    python sync_db_prod.py --export-sql sync_changes.sql
    ```

---


## 5. Khởi Chạy Dự Án

Để chạy dự án đầy đủ (Bao gồm mở cổng ngrok, kích hoạt bot Telegram kết nối webhook, chạy các tác vụ nền định kỳ và khởi động máy chủ FastAPI uvicorn):

Chạy lệnh sau tại thư mục gốc của dự án:
```bash
python run.py
```
*(Hoặc dùng lệnh ngắn gọn trên Windows: `py run.py`)*

### Luồng khởi chạy trong tệp `run.py`:
1. Kiểm tra cấu hình và mở đường hầm **ngrok** tại cổng dịch vụ (mặc định: `8000`).
2. Trả về địa chỉ `Webhook URL` công khai (dạng `https://...ngrok-free.dev`).
3. Khởi động máy chủ **Uvicorn** chạy ứng dụng FastAPI.
4. Kích hoạt kết nối **Pyrogram Bot** và đăng ký các sự kiện tương tác Telegram.
5. Kích hoạt các **Background Workers** để kiểm tra lịch chấm công, nhắc nợ, nhắc giấy tờ xe, v.v.

### Truy cập hệ thống:
* **Giao diện tài liệu Swagger UI (API Docs):** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Thông tin trạng thái server:** [http://localhost:8000/](http://localhost:8000/)
