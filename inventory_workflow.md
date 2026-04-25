# 📦 Sơ Đồ Tư Duy — Hệ Thống Quản Lý Kho Tiến Nga

## Tổng quan hệ thống

```mermaid
mindmap
  root((📦 Quản Lý Kho))
    🏗️ Tạo Kho
      Tên nguyên liệu
      Tên kho
      Địa chỉ
      Sức chứa
    📋 Danh Sách Kho
      Xem tất cả kho
      Chọn kho để cập nhật
    🔍 Kiểm Tra Kho
      Xem tồn kho
      Xem sức chứa
      Thanh tiến trình sử dụng
    ✏️ Cập Nhật Kho
      Sửa tên kho
      Sửa số lượng
      Sửa sức chứa
    📥 Thu Mua Nguyên Liệu
      Nhập hàng vào kho
      Ghi nhận công nợ
      Tự động cộng tồn kho
    📤 Xuất Kho
      Xuất hàng ra khỏi kho
      Tự động trừ tồn kho
      Cảnh báo kho thấp
```

---

## Quy trình hoạt động chi tiết

### 1. 🏗️ Tạo Kho Mới (`/tien_nga_tao_kho`)

```mermaid
flowchart TD
    A["👤 Người dùng nhập lệnh\n/tien_nga_tao_kho"] --> B["📝 Bot hiển thị FORM\nđiền thông tin kho"]
    B --> C["✍️ Người dùng điền:\n• Tên Nguyên Liệu\n• Tên Kho\n• Địa Chỉ\n• Sức Chứa"]
    C --> D{"✅ Thông tin\nhợp lệ?"}
    D -- Có --> E["💾 Lưu kho mới\nvào hệ thống"]
    E --> F["✅ Thông báo\ntạo kho thành công"]
    D -- Không --> G["⚠️ Báo lỗi\nyêu cầu sửa lại"]

    style A fill:#4CAF50,color:#fff
    style F fill:#2196F3,color:#fff
    style G fill:#FF9800,color:#fff
```

> **Mục đích:** Tạo một kho mới để chứa nguyên liệu (Acid, Củi, Cao su, v.v.)

---

### 2. 📋 Danh Sách Kho (`/tien_nga_danh_sach_kho`)

```mermaid
flowchart TD
    A["👤 Nhập lệnh\n/tien_nga_danh_sach_kho"] --> B["📋 Bot hiển thị\ndanh sách tất cả kho"]
    B --> C["👆 Chọn 1 kho\ntừ danh sách"]
    C --> D["📝 Bot hiển thị FORM\ncập nhật kho đã chọn"]
    D --> E["✍️ Sửa thông tin\nvà gửi lại"]

    style A fill:#4CAF50,color:#fff
    style D fill:#2196F3,color:#fff
```

> **Mục đích:** Xem tất cả kho và chọn kho để cập nhật thông tin

---

### 3. 🔍 Kiểm Tra Kho (`/tien_nga_kiem_tra_kho`)

```mermaid
flowchart TD
    A["👤 Nhập lệnh\n/tien_nga_kiem_tra_kho"] --> B["📋 Bot hiển thị\ndanh sách kho"]
    B --> C["👆 Chọn 1 kho"]
    C --> D["📊 Bot hiển thị chi tiết:\n• Tên Kho & Nguyên Liệu\n• Tồn Kho: xxx kg\n• Sức Chứa: xxx kg\n• % Sử Dụng + Thanh Tiến Trình\n• Mã kho"]
    D --> E{"Tiếp tục?"}
    E -- "⬅️ Quay lại" --> B
    E -- "Đóng" --> F["❌ Kết thúc"]

    style A fill:#4CAF50,color:#fff
    style D fill:#9C27B0,color:#fff
```

> **Mục đích:** Xem nhanh tình trạng tồn kho của từng kho — bao nhiêu kg, còn bao nhiêu phần trăm sức chứa

---

### 4. ✏️ Cập Nhật Tồn Kho (`/tien_nga_cap_nhat_ton_kho`)

```mermaid
flowchart TD
    A["👤 Nhập lệnh\n/tien_nga_cap_nhat_ton_kho"] --> B["📝 Bot hiển thị FORM\nvới thông tin hiện tại"]
    B --> C["✍️ Sửa thông tin:\n• Tên Nguyên Liệu\n• Tên Kho\n• Số Lượng\n• Địa Chỉ\n• Sức Chứa"]
    C --> D["💾 Cập nhật kho\ntrong hệ thống"]
    D --> E["✅ Thông báo\ncập nhật thành công"]

    style A fill:#4CAF50,color:#fff
    style E fill:#2196F3,color:#fff
```

> **Mục đích:** Điều chỉnh trực tiếp số lượng tồn kho hoặc thông tin kho (dùng khi kiểm kê thực tế)

---

### 5. 📥 Thu Mua Nguyên Liệu (`/tien_nga_thu_mua_nguyen_lieu`)

```mermaid
flowchart TD
    A["👤 Nhập lệnh\n/tien_nga_thu_mua_nguyen_lieu"] --> B["📋 Chọn kho\ntừ danh sách"]
    B --> C["📝 Bot hiển thị FORM\nđiền thông tin thu mua"]
    C --> D["✍️ Người dùng điền:\n• Loại Nguyên Liệu\n• Ngày Giao Dịch\n• Mã Khách Hàng\n• Khối Lượng\n• Đơn Giá"]
    D --> E["🤖 Bot TỰ ĐỘNG tính:\n• Thành Tiền = KL × Đơn Giá\n• Công Nợ = Thành Tiền - Tạm Ứng"]
    E --> F["💾 Lưu giao dịch"]
    F --> G["📦 TỰ ĐỘNG cộng\ntồn kho += Khối Lượng"]
    G --> H{"Có Mã KH?"}
    H -- Có --> I["💰 Cộng công nợ\nvào tài khoản KH"]
    H -- Không --> J["—"]
    I --> K["✅ Thông báo\nthu mua thành công\n+ Số dư kho mới"]
    J --> K

    style A fill:#4CAF50,color:#fff
    style E fill:#FF9800,color:#fff
    style G fill:#9C27B0,color:#fff
    style K fill:#2196F3,color:#fff
```

> **Mục đích:** Ghi nhận nhập hàng vào kho — tự động tính tiền, cộng tồn kho, và ghi công nợ cho khách hàng

---

### 6. 📤 Xuất Kho (`/tien_nga_xuat_kho`)

```mermaid
flowchart TD
    A["👤 Nhập lệnh\n/tien_nga_xuat_kho"] --> B["📋 Chọn kho\ntừ danh sách"]
    B --> C["📝 Bot hiển thị FORM\nđiền thông tin xuất kho"]
    C --> D["✍️ Người dùng điền:\n• Khối Lượng Xuất\n• Người Thực Hiện\n• Ghi Chú"]
    D --> E{"Tồn kho\n≥ KL xuất?"}
    E -- Có --> F["📦 TỰ ĐỘNG trừ\ntồn kho -= KL xuất"]
    E -- Không --> G["⚠️ Báo lỗi:\nXuất quá tồn kho"]
    F --> H{"Tồn kho\nthấp hơn\nngưỡng cảnh báo?"}
    H -- Có --> I["🚨 GỬI CẢNH BÁO\nđến nhóm chính:\nKho sắp hết hàng!"]
    H -- Không --> J["✅ Xuất kho\nthành công"]
    I --> J

    style A fill:#4CAF50,color:#fff
    style G fill:#f44336,color:#fff
    style I fill:#FF9800,color:#fff
    style J fill:#2196F3,color:#fff
```

> **Mục đích:** Ghi nhận xuất hàng ra khỏi kho — tự động trừ tồn kho và cảnh báo nếu kho sắp hết

---

## Luồng tổng thể

```mermaid
flowchart LR
    subgraph THIẾT_LẬP["🔧 Thiết Lập Ban Đầu"]
        A["🏗️ Tạo Kho"]
    end
    
    subgraph VẬN_HÀNH["⚙️ Vận Hành Hàng Ngày"]
        B["📥 Thu Mua\nNguyên Liệu"]
        C["📤 Xuất Kho"]
    end
    
    subgraph GIÁM_SÁT["👁️ Giám Sát"]
        D["🔍 Kiểm Tra Kho"]
        E["📋 Danh Sách Kho"]
        F["✏️ Cập Nhật Kho"]
    end

    A --> B
    A --> C
    B -->|"+ Tồn kho"| D
    C -->|"- Tồn kho"| D
    D --> F
    E --> F

    style THIẾT_LẬP fill:#E3F2FD,stroke:#1565C0
    style VẬN_HÀNH fill:#FFF3E0,stroke:#E65100
    style GIÁM_SÁT fill:#E8F5E9,stroke:#2E7D32
```

---

## Bảng tóm tắt

| Lệnh | Chức năng | Ai dùng? | Tác động |
|---|---|---|---|
| `/tien_nga_tao_kho` | Tạo kho mới | Owner, Admin | Thêm kho vào hệ thống |
| `/tien_nga_danh_sach_kho` | Xem & chọn kho | Owner, Admin | Hiển thị form cập nhật |
| `/tien_nga_kiem_tra_kho` | Kiểm tra tồn kho | Owner, Admin | Xem chi tiết, % sức chứa |
| `/tien_nga_cap_nhat_ton_kho` | Cập nhật số liệu kho | Owner, Admin | Sửa trực tiếp tồn kho |
| `/tien_nga_thu_mua_nguyen_lieu` | Nhập hàng vào kho | Owner, Admin | **+** Tồn kho, **+** Công nợ KH |
| `/tien_nga_xuat_kho` | Xuất hàng ra khỏi kho | Owner, Admin | **-** Tồn kho, cảnh báo nếu thấp |

> [!TIP]
> **Thu mua** = hàng vào kho (tồn kho **tăng**) · **Xuất kho** = hàng ra khỏi kho (tồn kho **giảm**)
