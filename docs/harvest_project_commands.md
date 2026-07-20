# Tài Liệu Hướng Dẫn Các Lệnh Nhóm "THU HOẠCH" (Telegram Bot)

Tài liệu này cung cấp hướng dẫn chi tiết về mục đích, cú pháp và cách thức hoạt động của các lệnh thuộc nhóm chức năng **THU HOẠCH** (Dự án Thu Hoạch / Đất trồng trọt / Canh tác) trong Telegram Bot, được chia thành hai phân quyền chính: **Quản trị viên (Thu Hoạch Main / Super Main)** và **Thành viên hộ dân (Thu Hoạch Member)**.

---

## 1. DÀNH CHO QUẢN TRỊ VIÊN (Thu Hoạch Main / Super Main)

Các lệnh dưới đây được áp dụng khi người dùng ở trong nhóm quản trị dự án có role là `main` và sở hữu custom title là `main_harvest` hoặc `super_main` (quản trị chung).

### ĐẤT TRỒNG TRỘT & HỘ DÂN

#### `/tien_nga_tao_dat_trong_trot`
*   **Mục đích:** Khởi tạo hồ sơ quản lý một lô đất trồng trọt mới trên hệ thống.
*   **Cú pháp:** `/tien_nga_tao_dat_trong_trot`
*   **Cách thức hoạt động:**
    - Gõ lệnh không kèm tham số để nhận Form: Mã Đất, Tên Đất, Địa Chỉ, Trực Thuộc, Diện Tích, Diện tích Cao su, Diện tích trống, Số lượng cây thu hoạch/đang trồng.
    - Điền Form và gửi lại. Hệ thống tự động nhận diện Trực thuộc nếu Mã Đất bắt đầu bằng `VH` (Vĩnh Hà) hoặc `TN` (Tiến Nga).
    - Kiểm tra tính duy nhất của Mã Đất và lưu vào bảng `AgriculturalLand` ở trạng thái `ACTIVE`.

#### `/tien_nga_cap_nhat_dat_trong_trot`
*   **Mục đích:** Sửa đổi thông tin diện tích, cây trồng của một lô đất trồng trọt đã tồn tại.
*   **Cú pháp:** `/tien_nga_cap_nhat_dat_trong_trot [Mã Đất]`
*   **Cách thức hoạt động:**
    - Gõ lệnh kèm Mã Đất, bot tra cứu thông tin và phản hồi Form điền sẵn dữ liệu hiện tại.
    - Người dùng chỉnh sửa các số liệu (diện tích cạo mủ, số lượng cây...) và gửi lại.
    - Bot đối chiếu các thay đổi và cập nhật ghi đè lên bảng `AgriculturalLand`.

#### `/tien_nga_xoa_dat_trong_trot`
*   **Mục đích:** Vô hiệu hóa một lô đất trồng trọt khỏi danh sách hoạt động.
*   **Cú pháp:** `/tien_nga_xoa_dat_trong_trot [Mã Đất]`
*   **Cách thức hoạt động:**
    - Bot tra cứu thông tin lô đất và hiển thị tin nhắn xác nhận kèm nút bấm inline "Xác nhận" hoặc "Hủy".
    - Khi bấm xác nhận, bot thực hiện xóa mềm (Soft Delete) chuyển đổi trạng thái của lô đất thành `INACTIVE` để bảo toàn dữ liệu lịch sử.

#### `/tien_nga_ds_dat_trong_trot`
*   **Mục đích:** Xem danh sách tổng quan các lô đất trồng trọt đang quản lý.
*   **Cú pháp:** `/tien_nga_ds_dat_trong_trot`
*   **Cách thức hoạt động:**
    - Quét toàn bộ đất có trạng thái `ACTIVE`.
    - Nếu danh sách `<= 10` lô, hiển thị trực tiếp dưới dạng tin nhắn văn bản.
    - Nếu `> 10` lô, bot tự động xuất file Excel `dat_trong_trot.xlsx` định dạng bảng biểu đẹp mắt và gửi đính kèm.

#### `/tien_nga_kt_dat_trong_trot`
*   **Mục đích:** Xem chi tiết thông tin lô đất và lịch sử biến động số lượng cây.
*   **Cú pháp:** `/tien_nga_kt_dat_trong_trot [Mã Đất]`
*   **Cách thức hoạt động:**
    - Truy xuất thông tin diện tích, số cây cao su/sầu riêng đang thu hoạch hoặc đang trồng của lô đất.
    - Quét bảng nhật ký cây trồng để liệt kê 5 hoạt động trồng mới hoặc chặt cây gần đây nhất trên lô đất đó.

#### `/tien_nga_tao_ho_dan`
*   **Mục đích:** Tạo hồ sơ quản lý hộ nông dân liên kết với đất canh tác (cạo mủ khoán hoặc thu hoạch nông sản).
*   **Cú pháp:** `/tien_nga_tao_ho_dan`
*   **Cách thức hoạt động:**
    - Nhận Form yêu cầu điền: Mã Hộ Dân, Mã Thu Mua, Mã Đất, SĐT, Công Nợ, Đơn Giá Cạo Mủ, Thông tin Ngân hàng.
    - Điền Form gửi lại để bot lưu vào bảng `Households`.

#### `/tien_nga_cap_nhat_ho_dan`
*   **Mục đích:** Sửa thông tin định danh, tài khoản ngân hàng hoặc đơn giá cạo khoán của hộ dân.
*   **Cú pháp:** `/tien_nga_cap_nhat_ho_dan [Mã Hộ Dân]`

#### `/tien_nga_xoa_ho_dan`
*   **Mục đích:** Vô hiệu hóa hồ sơ hộ dân (Soft Delete).
*   **Cú pháp:** `/tien_nga_xoa_ho_dan [Mã Hộ Dân]`

#### `/tien_nga_ds_ho_dan`
*   **Mục đích:** Xem danh sách toàn bộ các hộ dân đang hợp tác.
*   **Cú pháp:** `/tien_nga_ds_ho_dan`
*   **Cách thức hoạt động:**
    - Quét danh sách hộ dân `ACTIVE`. Nếu số lượng lớn hơn 10 hộ, bot tự động xuất file Excel `ho_dan.xlsx` và gửi đính kèm.

---

### PHÂN HỆ CAO SU

#### `/tien_nga_kiem_tra_thu_hoach`
*   **Mục đích:** Truy xuất báo cáo chi tiết sản lượng mủ cao su thu hoạch của các hộ dân trong khoảng thời gian.
*   **Cú pháp:** `/tien_nga_kiem_tra_thu_hoach` hoặc `/tien_nga_kiem_tra_thu_hoach [Từ ngày] - [Đến ngày]`
*   **Cách thức hoạt động:**
    - Nếu không kèm tham số: Bot hiển thị các nút chọn Mã Đất/Nhóm Đất và chu kỳ thời gian (Hôm nay, Tuần này, Tháng này).
    - Tra cứu dữ liệu bảng `DailyPurchases` và kết xuất ra file Excel `thu_hoach_...xlsx`. Mỗi hộ dân được tách thành một sheet riêng biệt kê khai chi tiết khối lượng mủ nước, DRC, mủ khô, đơn giá, thành tiền, tạm ứng và nợ lưu sổ từng ngày.

#### `/tien_nga_so_sanh_thu_hoach`
*   **Mục đích:** Đánh giá hiệu suất và năng suất canh tác thực tế giữa các lô đất/hộ dân.
*   **Cú pháp:** `/tien_nga_so_sanh_thu_hoach [Từ ngày] - [Đến ngày]`
*   **Cách thức hoạt động:**
    - Tính tổng khối lượng mủ cạo được của mỗi hộ dân trong khoảng thời gian chỉ định.
    - Lấy diện tích cao su cạo (`rubber_area`) của lô đất hộ phụ trách để tính: Năng suất (Kg/Ha) = Tổng Khối Lượng / Diện Tích Cao Su.
    - Trả về file Excel có sheet "Tổng Hợp" so sánh trực quan hiệu quả năng suất của tất cả các hộ.

#### `/tien_nga_kt_thu_hoach_hang_ngay`
*   **Mục đích:** Kiểm tra sổ ghi chép sản lượng cạo mủ hàng ngày tại vườn của hộ dân/công nhân trước khi bán hoặc nhập kho.
*   **Cú pháp:** `/tien_nga_kt_thu_hoach_hang_ngay`
*   **Cách thức hoạt động:**
    - Sử dụng các nút bấm lọc theo Lô đất/Nhóm Đất và thời gian.
    - Trích xuất dữ liệu từ bảng `DailyHarvest` hiển thị số cây đã cạo, sản lượng mủ cạo thô để quản lý đối soát với lượng mủ thu mua thực tế.

#### `/tien_nga_cay_cao_su`
*   **Mục đích:** Ghi nhận biến động số lượng cây cao su (trồng mới hoặc chặt bỏ) trên các lô đất.
*   **Cú pháp:** `/tien_nga_cay_cao_su`
*   **Cách thức hoạt động:**
    - Gõ lệnh: Chọn hành động (Trồng mới/Chặt cây) và chọn lô đất.
    - Điền Form: Số lượng cây, Người thực hiện, Lý do.
    - Bot tự động cộng/trừ số lượng cây vào tổng số cây của lô đất đó trong bảng `AgriculturalLand` và ghi nhật ký vào `RubberTreeLog`.

#### `/tien_nga_kt_cay_cao_su`
*   **Mục đích:** Xem nhật ký lịch sử trồng mới/chặt bỏ cây cao su của một lô đất.
*   **Cú pháp:** `/tien_nga_kt_cay_cao_su`

---

### PHÂN HỆ SẦU RIÊNG

#### `/tien_nga_cay_sau_rieng`
*   **Mục đích:** Ghi nhận biến động số lượng cây sầu riêng (trồng mới hoặc chặt bỏ) trên các lô đất.
*   **Cú pháp:** `/tien_nga_cay_sau_rieng`
*   **Cách thức hoạt động:**
    - Chọn hành động (Trồng mới/Chặt cây) và chọn lô đất.
    - Nhập Form: Loại (Trồng mới/Chặt cây), Mã Đất, Ngày, Số lượng, Người thực hiện, Ghi chú.
    - Bot tự động cộng/trừ số lượng cây sầu riêng vào tổng số cây của lô đất đó trong bảng `AgriculturalLand` và ghi nhật ký vào bảng `CropTreeLog` ở loại cây trồng `sau_rieng`.

#### `/tien_nga_kt_cay_sau_rieng`
*   **Mục đích:** Xem chi tiết số lượng và nhật ký biến động trồng/chặt cây sầu riêng của lô đất.
*   **Cú pháp:** `/tien_nga_kt_cay_sau_rieng`
*   **Cách thức hoạt động:**
    - Chọn lô đất: Bot kết xuất báo cáo thống kê số cây thu hoạch, cây đang trồng, tổng cây hiện có cùng chi tiết lịch sử các lần trồng mới và chặt cây sầu riêng.

#### `/tien_nga_thu_hoach_sau_rieng`
*   **Mục đích:** Ghi nhận trực tiếp sản lượng thu hoạch sầu riêng của hộ dân (dành cho nhóm quản trị nhập thẳng, tự động ghi nhận không cần duyệt).
*   **Cú pháp:** `/tien_nga_thu_hoach_sau_rieng` hoặc `/tien_nga_thu_hoach_sau_rieng [Mã Hộ Dân]`
*   **Cách thức hoạt động:**
    - Nhập lệnh kèm Mã Hộ: Bot cấp Form: Mã Hộ Dân, Mã Đất, Ngày, Khối Lượng (Kg), Đơn Giá.
    - Gửi lại Form: Bot tính `Thành Tiền = Khối Lượng * Đơn Giá`. Lưu giao dịch vào bảng `DailyHarvest` ở loại cây `sau_rieng` và tự động cộng dồn số tiền thành tiền vào tổng công nợ của hộ dân.

#### `/tien_nga_kt_thu_hoach_sr`
*   **Mục đích:** Kiểm tra và xuất báo cáo chi tiết sản lượng thu hoạch sầu riêng ra file Excel.
*   **Cú pháp:** `/tien_nga_kt_thu_hoach_sr` hoặc `/tien_nga_kt_thu_hoach_sr [Mã Đất] [Từ ngày] - [Đến ngày]`
*   **Cách thức hoạt động:**
    - Quét bảng `DailyHarvest` lấy tất cả giao dịch thu hoạch sầu riêng (`crop_type == "sau_rieng"`) theo hộ dân/đất phụ trách và khoảng thời gian chỉ định.
    - Sử dụng `openpyxl` tạo file Excel gồm nhiều tab riêng biệt cho từng hộ dân kê khai chi tiết ngày, khối lượng trái, đơn giá, thành tiền và sheet tổng hợp.

---

### TÀI CHÍNH THU HOẠCH & CHI PHÍ VẬT TƯ

#### `/tien_nga_yeu_cau_thu_chi`
*   **Mục đích:** Tạo yêu cầu thu/chi tiền mặt hoặc chuyển khoản liên quan đến chi phí thu hoạch, vật tư nông nghiệp.
*   **Cú pháp:** `/tien_nga_yeu_cau_thu_chi`
*   **Cách thức hoạt động:**
    - Ghi nhận yêu cầu giải ngân vào bảng `DailyPayment` với trạng thái `PENDING` và chuyển tiếp thông báo sang nhóm tài chính để Kế toán trưởng/Owner duyệt.

#### `/tien_nga_thanh_toan_cong_no`
*   **Mục đích:** Ghi nhận việc công ty thanh toán tiền công/nợ cho hộ dân.
*   **Cú pháp:** `/tien_nga_thanh_toan_cong_no`
*   **Cách thức hoạt động:**
    - Trừ tự động số tiền thanh toán vào trường `total_debt` của hộ dân trong bảng `Households` và sinh ra một phiếu chi tương ứng.

#### `/tien_nga_them_vat_tu`
*   **Mục đích:** Ghi nhận chi phí mua sắm vật tư nông nghiệp (phân bón, hóa chất, nông cụ...) phân bổ cho từng lô đất hoặc dùng chung.
*   **Cú pháp:** `/tien_nga_them_vat_tu`
*   **Cách thức hoạt động:**
    - Bot cung cấp Form điền: Mã Đất, Ngày, Tên Vật Tư, Số Lượng, Đơn Vị, Đơn Giá, Nhà Cung Cấp, Mục Đích, Loại Cây (chung/cao_su/sau_rieng), Người Mua, Ghi Chú.
    - Khi người dùng gửi Form, bot tính `Tổng Tiền = Số Lượng * Đơn Giá` và lưu bản ghi vào bảng `SuppliesExpense`.

#### `/tien_nga_kt_vat_tu`
*   **Mục đích:** Xuất bảng thống kê chi tiết toàn bộ chi phí vật tư nông nghiệp đã sử dụng ra file Excel.
*   **Cú pháp:** `/tien_nga_kt_vat_tu` hoặc `/tien_nga_kt_vat_tu [Mã Đất] [Từ ngày] - [Đến ngày]`
*   **Cách thức hoạt động:**
    - Truy vấn bảng `SuppliesExpense` lọc theo bộ lọc và khoảng thời gian.
    - Tạo file Excel `chi_phi_vat_tu_...xlsx` tổng hợp thông số chi tiết của từng lô đất và gửi đính kèm.

#### `/tien_nga_xoa_vat_tu`
*   **Mục đích:** Xóa bản ghi chi phí vật tư nông nghiệp (khi nhập sai thông tin).
*   **Cú pháp:** `/tien_nga_xoa_vat_tu [ID bản ghi]`
*   **Cách thức hoạt động:**
    - Hiển thị chi tiết bản ghi cần xóa kèm nút bấm inline "Xác Nhận Xóa" hoặc "Hủy".
    - Khi bấm xác nhận, tiến hành DELETE xóa hẳn bản ghi khỏi bảng `SuppliesExpense`.

---
---

## 2. DÀNH CHO THÀNH VIÊN (Thu Hoạch Member)

Các lệnh dưới đây được áp dụng khi người dùng ở trong các nhóm chat thành viên trực thuộc có role là `member` và sở hữu custom title là `member_harvest` (Hộ dân/công nhân thu hoạch).

#### `/tien_nga_thu_hoach_hang_ngay` (hoặc `/tien_nga_daily_harvest`)
*   **Mục đích:** Hộ dân/công nhân khai báo khối lượng cạo mủ cao su hàng ngày tại vườn.
*   **Cú pháp:** `/tien_nga_thu_hoach_hang_ngay [Mã Hộ Dân]`
*   **Cách thức hoạt động:**
    - Hộ dân điền Form: Mã Hộ Dân, Mã Đất, Ngày, Số Lượng Cây cạo, Khối Lượng Mủ (Kg).
    - Gửi Form: Bot tra cứu đơn giá cạo mủ (`tapping_price`) của hộ dân trong bảng `Households` và tính `Thành Tiền = Số Lượng Cây * Đơn Giá`.
    - Bot gửi tin nhắn yêu cầu xác nhận kèm nút bấm inline "Xác Nhận" và "Từ Chối" lên nhóm quản trị chính (`main_harvest`).
    - Khi Admin/Owner duyệt, giao dịch được lưu vào bảng `DailyHarvest`, cộng số tiền thành tiền vào công nợ hộ dân và gửi thông báo xác nhận về nhóm member.

#### `/tien_nga_thu_hoach_sr_hang_ngay`
*   **Mục đích:** Hộ dân/công nhân khai báo sản lượng sầu riêng thu hoạch hàng ngày tại vườn.
*   **Cú pháp:** `/tien_nga_thu_hoach_sr_hang_ngay [Mã Hộ Dân]`
*   **Cách thức hoạt động:**
    - Hộ dân điền Form: Mã Hộ Dân, Mã Đất, Ngày, Khối Lượng (Kg), Đơn Giá (VNĐ/Kg).
    - Gửi Form: Tính toán `Thành Tiền = Khối Lượng * Đơn Giá`. Đẩy yêu cầu xác nhận lên nhóm quản trị chính.
    - Khi Admin/Owner duyệt, lưu giao dịch vào bảng `DailyHarvest` ở loại cây `sau_rieng`, cộng dồn vào công nợ hộ dân và phản hồi về nhóm member.

#### `/tien_nga_kiem_tra_ho_dan`
*   **Mục đích:** Hộ dân tự xem hồ sơ và tình hình công nợ của mình.
*   **Cú pháp:** `/tien_nga_kiem_tra_ho_dan [Mã Hộ Dân]`
*   **Cách thức hoạt động:**
    - Truy cập bảng `Households` in ra thông tin đất phụ trách, SĐT, công nợ hiện tại, đơn giá cạo mủ và thông tin tài khoản ngân hàng liên kết.
