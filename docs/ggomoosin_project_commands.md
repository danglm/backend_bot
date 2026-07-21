# Tài Liệu Hướng Dẫn Các Lệnh Nhóm "GGOMOOSIN" (Telegram Bot)

<style>
body {
  font-size: 14px !important;
}
</style>

Tài liệu này cung cấp hướng dẫn chi tiết về mục đích, cú pháp và cách thức hoạt động của các lệnh thuộc nhóm chức năng **GGoMooSin** (Dự án Quản lý Nhân sự GGoMooSin) trong Telegram Bot, được chia thành hai phân quyền chính: **Quản trị viên (GGoMooSin Main / Super Main)** và **Nhân viên (GGoMooSin Member)**.

---

## 1. DÀNH CHO QUẢN TRỊ VIÊN (GGoMooSin Main / Super Main)

Các lệnh dưới đây được áp dụng khi người dùng ở trong nhóm quản trị dự án có role là `main` và sở hữu custom title là `main_hr` hoặc `super_main` (quản trị chung).

### QUẢN LÝ NHÂN SỰ (HR)

#### `/ggomoosin_tao_nhan_vien` (hoặc `/ggomoosin_create_employee`)
*   **Mục đích:** Khởi tạo hồ sơ nhân viên mới trên hệ thống GGoMooSin và liên kết tài khoản Telegram của họ.
*   **Cú pháp:** `/ggomoosin_tao_nhan_vien`
*   **Cách thức hoạt động:**
    - Gõ lệnh không kèm tham số để bot trả về Form nhập thông tin nhân viên: Mã NV (bắt buộc), Họ (bắt buộc), Tên (bắt buộc), Username Telegram (bắt buộc, không chứa chữ @), Số điện thoại, Email, Số CCCD, Ngân hàng, Số tài khoản, Lương thiết lập, Giờ vào ca/tan ca.
    - Người dùng điền Form gửi lại. Bot bóc tách dữ liệu và kiểm tra trùng lặp Mã NV, Username, Email, Số điện thoại trong bảng `Employee`.
    - Nếu thông tin hợp lệ, lưu vào cơ sở dữ liệu và gửi thông báo tạo thành công.

#### `/ggomoosin_cap_nhat_nhan_vien` (hoặc `/ggomoosin_update_employee`)
*   **Mục đích:** Chỉnh sửa thông tin hồ sơ của một nhân viên GGoMooSin đang hoạt động.
*   **Cú pháp:** `/ggomoosin_cap_nhat_nhan_vien [Mã NV hoặc Username]`
*   **Cách thức hoạt động:**
    - Bot tra cứu thông tin nhân viên và phản hồi Form điền sẵn dữ liệu hiện có.
    - Người dùng chỉnh sửa các trường thông tin trên Form và gửi lại để bot ghi đè cập nhật vào bảng `Employee`.

#### `/ggomoosin_xoa_nhan_vien` (hoặc `/ggomoosin_delete_employee`)
*   **Mục đích:** Cho nhân viên nghỉ việc hoặc vô hiệu hóa tài khoản nhân viên.
*   **Cú pháp:** `/ggomoosin_xoa_nhan_vien [Mã NV]`
*   **Cách thức hoạt động:**
    - Tra cứu nhân viên theo mã. Gửi tin nhắn xác nhận kèm nút bấm inline.
    - Khi bấm xác nhận, thực hiện xóa mềm (chuyển `status` thành `inactive`) để lưu giữ lịch sử chấm công và công nợ phục vụ chốt lương cuối cùng.

#### `/ggomoosin_xuat_luong` (hoặc `/ggomoosin_export_payroll`)
*   **Mục đích:** Chốt công và xuất bảng lương cuối tháng cho nhân viên dưới dạng hình ảnh, đồng thời ghi nhận công nợ lương.
*   **Cú pháp:** `/ggomoosin_xuat_luong [Mã NV] [Tháng/Năm]` (Ví dụ: `/ggomoosin_xuat_luong GG01 05/2026`)
*   **Cách thức hoạt động:**
    - Tính toán số ngày công tiêu chuẩn (trừ Chủ nhật) trong tháng.
    - Quét dữ liệu chấm công từ bảng `Attendance` để lấy: Số ngày đi làm thực tế, giờ tăng ca, số ngày nghỉ phép, đi trễ, về sớm.
    - Tính toán lương: Lương thực nhận = (Lương cơ bản / Ngày công chuẩn) x Số ngày làm thực tế + Lương tăng ca + Thưởng - Phạt/Bảo hiểm.
    - Cập nhật số tiền chênh lệch vào tổng công nợ lương (`total_debt`) của nhân viên trong database.
    - Tạo bảng lương chi tiết xuất ra file ảnh `.png` gửi trực tiếp xuống nhóm chat để đối soát.

#### `/ggomoosin_tao_lai_bang_cham_cong` (hoặc `/ggomoosin_recreate_attendance_report`)
*   **Mục đích:** Vẽ lại bảng tổng quan lịch sử chấm công trong tháng của nhân viên dưới dạng hình ảnh.
*   **Cú pháp:** `/ggomoosin_tao_lai_bang_cham_cong [Mã NV] [Tháng/Năm]`
*   **Cách thức hoạt động:**
    - Truy vấn bảng `Attendance` lấy dữ liệu giờ vào, giờ ra, tăng ca, lỗi chấm công từng ngày của nhân viên.
    - Tạo file ảnh `tong_hop_cong.png` và gửi lên nhóm.

#### `/ggomoosin_xuat_danh_sach_luong` (hoặc `/ggomoosin_list_payroll`)
*   **Mục đích:** Xuất bảng tổng hợp chi trả lương của toàn bộ nhân viên GGoMooSin trong tháng ra file Excel.
*   **Cú pháp:** `/ggomoosin_xuat_danh_sach_luong [Tháng/Năm]`
*   **Cách thức hoạt động:**
    - Quét toàn bộ bảng `Payroll` trong tháng/năm, kết nối thông tin họ tên, phòng ban từ bảng `Employee`.
    - Dựng bảng Excel chứa: Lương cơ bản, lương tăng ca, thưởng, phạt, thực nhận, kèm dòng TỔNG CỘNG tự động tính quỹ lương phải chi trả. Xuất file Excel gửi đính kèm.

#### `/ggomoosin_danh_sach_nhan_vien` (hoặc `/ggomoosin_list_employee`)
*   **Mục đích:** Xuất file Excel danh sách toàn bộ hồ sơ nhân sự của GGoMooSin.
*   **Cú pháp:** `/ggomoosin_danh_sach_nhan_vien`
*   **Cách thức hoạt động:**
    - Truy vấn bảng `Employee` lấy thông tin cá nhân, chức vụ, mức lương cơ bản, SĐT, STK ngân hàng của toàn bộ nhân viên.
    - Đổ dữ liệu và định dạng bằng thư viện `openpyxl` tạo file Excel `ggomoosin_ds_nv_...xlsx` gửi lên nhóm.

#### `/ggomoosin_danh_sach_cham_cong` (hoặc `/ggomoosin_list_attendance`)
*   **Mục đích:** Tải file Excel chi tiết lịch sử chấm công hàng ngày của một nhân viên trong tháng.
*   **Cú pháp:** `/ggomoosin_danh_sach_cham_cong [Mã NV] [Tháng/Năm]`

#### `/ggomoosin_nghi_ngay_le`
*   **Mục đích:** Thiết lập ngày nghỉ lễ hưởng nguyên lương hàng loạt cho toàn bộ nhân viên.
*   **Cú pháp:** `/ggomoosin_nghi_ngay_le`
*   **Cách thức hoạt động:**
    - Trả về Form cấu hình: Ngày nghỉ lễ, Tên ngày lễ.
    - Gửi lại Form: Quét toàn bộ danh sách nhân viên đang hoạt động và tự động tạo các bản ghi chấm công `Attendance` cho ngày đó với ghi chú là tên ngày nghỉ lễ và tính đủ công làm việc tiêu chuẩn.

---

### CÁC LỆNH TẠM ẨN / KHÔNG HIỂN THỊ MENU GỢI Ý

Các lệnh dưới đây đã được lập trình đầy đủ chức năng nhưng tạm thời bị ẩn khỏi menu gợi ý của bot (phần comment trong `commands.py`) hoặc chạy qua cơ chế Reply:

#### `/ggomoosin_giao_viec` (hoặc `/ggomoosin_create_task`)
*   **Mục đích:** Giao việc (Task) trực tiếp cho nhân viên.
*   **Cú pháp:** `/ggomoosin_giao_viec`
*   **Cách thức hoạt động:**
    - Nhận Form điền: Mã nhân viên nhận việc, Nội dung công việc, Khung giờ (hh:mm - hh:mm), Ngày bắt đầu/kết thúc, Chu kỳ.
    - Lưu vào DB ở trạng thái `PENDING` và đẩy thông báo xuống nhóm chat của nhân viên.

#### `/ggomoosin_huy_task` (hoặc `/ggomoosin_cancel_task`)
*   **Mục đích:** Hủy một công việc đã giao.
*   **Cú pháp:** Sử dụng bằng cách **Reply** vào tin nhắn giao việc của Bot và gõ lệnh `/ggomoosin_huy_task`.
*   **Cách thức hoạt động:**
    - Bot nhận diện mã công việc từ tin nhắn được reply và cập nhật trạng thái công việc sang `CANCELLED` trong database.

#### `/ggomoosin_danh_sach_cong_viec` (hoặc `/ggomoosin_check_tasks`)
*   **Mục đích:** Xem danh sách và tiến độ toàn bộ các công việc đã giao cho nhân sự.
*   **Cú pháp:** `/ggomoosin_danh_sach_cong_viec`

---
---

## 2. DÀNH CHO THÀNH VIÊN (GGoMooSin Member / Nhân Viên)

Các lệnh dưới đây được áp dụng khi người dùng ở trong các nhóm chat nhân viên trực thuộc có role là `member` và sở hữu custom title là `member_hr`.

#### `/ggomoosin_cham_cong` (hoặc `/ggomoosin_check_in`)
*   **Mục đích:** Nhân viên tự chấm công bắt đầu ca làm việc hàng ngày.
*   **Cú pháp:** `/ggomoosin_cham_cong`
*   **Cách thức hoạt động:**
    - Xác thực tài khoản Telegram của nhân viên và kiểm tra giờ chấm công thực tế (phải nằm trong khoảng 30 phút trước hoặc sau giờ vào ca quy định).
    - So sánh thời gian thực tế để ghi nhận trạng thái: đúng giờ, đi trễ, đi sớm và lưu vào bảng `Attendance`.

#### `/ggomoosin_tan_ca` (hoặc `/ggomoosin_check_out`)
*   **Mục đích:** Chấm công kết thúc ca làm việc và tính toán giờ tăng ca.
*   **Cú pháp:** `/ggomoosin_tan_ca`
*   **Cách thức hoạt động:**
    - Kiểm tra nhân viên đã check-in ngày hôm đó chưa. Chỉ cho phép check-out sau giờ tan ca quy định đến 23:59 cùng ngày.
    - Nếu tan ca muộn hơn giờ quy định, số giờ thừa tự động được tính là giờ tăng ca (overtime). Cập nhật tổng số giờ làm việc thực tế và lưu vào DB.

#### `/ggomoosin_dang_ky_tang_ca` (hoặc `/ggomoosin_request_overtime`)
*   **Mục đích:** Nhân viên gửi đơn đề xuất làm thêm giờ (tăng ca).
*   **Cú pháp:** `/ggomoosin_dang_ky_tang_ca`
*   **Cách thức hoạt động:**
    - Điền Form: Ngày tăng ca, Khung giờ tăng ca (Ví dụ: 18:00 - 21:00), Người duyệt, Lý do.
    - Đẩy yêu cầu duyệt sang nhóm Quản lý. Nếu được duyệt (nhấn inline button), hệ thống tự động cập nhật giờ tăng ca vào bản ghi chấm công của ngày tương ứng.

#### `/ggomoosin_xem_cham_cong` (hoặc `/ggomoosin_list_check_in`)
*   **Mục đích:** Nhân viên tự kiểm tra lịch sử chấm công và số giờ làm việc của mình trong tháng.
*   **Cú pháp:** `/ggomoosin_xem_cham_cong` (hoặc `/ggomoosin_xem_cham_cong [Tháng/Năm]`)
*   **Cách thức hoạt động:**
    - Bot truy xuất toàn bộ lịch sử chấm công trong tháng được chỉ định và vẽ thành bảng biểu hình ảnh trực quan (.png) gồm: Ngày, giờ vào, giờ ra, tăng ca, tổng giờ làm, lỗi chấm công và gửi vào chat.

#### `/ggomoosin_cap_nhat_cong` (hoặc `/ggomoosin_request_attendance_update`)
*   **Mục đích:** Gửi yêu cầu giải trình xin cập nhật/bổ sung chấm công khi bị quên check-in/out hoặc sai lệch giờ giấc.
*   **Cú pháp:** `/ggomoosin_cap_nhat_cong`

---

### CÁC LỆNH TẠM ẨN / KHÔNG HIỂN THỊ MENU GỢI Ý

#### `/ggomoosin_xin_nghi_phep` (hoặc `/ggomoosin_request_leave`)
*   **Mục đích:** Nhân viên gửi đơn xin nghỉ phép trực tuyến.
*   **Cú pháp:** `/ggomoosin_xin_nghi_phep`
*   **Cách thức hoạt động:**
    - Nhận Form điền: Thời gian nghỉ, Loại nghỉ (phép năm, không lương, ốm...), Người duyệt, Người hỗ trợ, Lý do.
    - Gửi Form: Bot kiểm tra số ngày phép còn lại. Nếu hợp lệ, gửi đơn xin nghỉ phép vào nhóm của Quản lý Nhân sự (MAIN_HR) kèm nút bấm duyệt/từ chối. Nếu được duyệt, hệ thống tự động tạo bản ghi chấm công nghỉ phép cho các ngày đó.

#### `/ggomoosin_xem_nghi_phep` (hoặc `/ggomoosin_list_request_leave`)
*   **Mục đích:** Xem danh sách các ngày đã nghỉ phép trong tháng và quỹ phép năm còn lại.
*   **Cú pháp:** `/ggomoosin_xem_nghi_phep`

#### `/ggomoosin_xem_cong_viec` (hoặc `/ggomoosin_list_tasks`)
*   **Mục đích:** Nhân viên kiểm tra danh sách và cập nhật tiến độ các công việc được giao.
*   **Cú pháp:** `/ggomoosin_xem_cong_viec`
*   **Cách thức hoạt động:**
    - Hiển thị danh sách công việc dưới dạng nút bấm inline. Nhân viên bấm vào nút để xem chi tiết và cập nhật trạng thái sang `IN_PROGRESS` hoặc `COMPLETED`.
