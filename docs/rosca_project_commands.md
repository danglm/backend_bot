# Tài Liệu Hướng Dẫn Các Lệnh Nhóm "HỤI" (ROSCA - Telegram Bot)

<style>
body {
  font-size: 14px !important;
}
</style>

Tài liệu này cung cấp hướng dẫn chi tiết về mục đích, cú pháp và cách thức hoạt động của các lệnh thuộc nhóm chức năng **HỤI (ROSCA)** trong Telegram Bot, được chia thành hai phân quyền chính: **Chủ hụi / Quản lý (Hụi Main)** và **Người chơi (Hụi Member)**.

---

## 1. DÀNH CHO QUẢN LÝ (Hụi Main / Chủ Hụi)

Các lệnh dưới đây được áp dụng khi người dùng ở trong nhóm quản trị dự án có role là `main` (Chủ hụi hoặc Admin).

### QUẢN LÝ NGƯỜI CHƠI (UserRosca)

#### `/hui_tao_nguoi_choi` (hoặc `/rosca_create_user`)
*   **Mục đích:** Đăng ký hồ sơ người chơi hụi mới vào hệ thống.
*   **Cú pháp:** `/hui_tao_nguoi_choi`
*   **Cách thức hoạt động:**
    - Gõ lệnh không kèm tham số để bot trả về Form: Mã ID (bắt buộc, ví dụ: `NC01`), Họ và Tên (bắt buộc), Username Telegram (không chứa chữ @), Số Điện Thoại, Số CCCD, Vai Trò (Owner/Player), Trạng Thái.
    - Người dùng điền Form gửi lại. Bot bóc tách dữ liệu và kiểm tra trùng lặp Mã ID, Số điện thoại và CCCD trong database.
    - Nếu hợp lệ, lưu vào bảng `user_roscas` với trạng thái `Active`.

#### `/hui_cap_nhat_nguoi_choi` (hoặc `/rosca_update_user`)
*   **Mục đích:** Sửa đổi thông tin cá nhân của người chơi đã có trên hệ thống.
*   **Cú pháp:** `/hui_cap_nhat_nguoi_choi [Mã ID]`
*   **Cách thức hoạt động:**
    - Bot tra cứu thông tin người chơi theo Mã ID và gửi Form điền sẵn dữ liệu hiện tại.
    - Người dùng sửa đổi thông tin cần cập nhật trên Form và gửi lại.
    - Bot kiểm tra trùng lặp SĐT/CCCD với người chơi khác trước khi lưu đè thông tin mới.

#### `/hui_xoa_nguoi_choi` (hoặc `/rosca_delete_user`)
*   **Mục đích:** Xóa hồ sơ người chơi ra khỏi hệ thống.
*   **Cú pháp:** `/hui_xoa_nguoi_choi [Mã ID]`
*   **Cách thức hoạt động:**
    - Bot hiển thị thông tin hồ sơ kèm 2 nút bấm inline: "Xác nhận" hoặc "Hủy".
    - Khi bấm xác nhận, thực hiện lệnh DELETE xóa vật lý bản ghi người chơi khỏi bảng `user_roscas`.

---

### QUẢN LÝ DÂY HỤI (Rosca)

#### `/hui_tao_day_hui` (hoặc `/roscas_create_roscas`)
*   **Mục đích:** Khởi tạo cấu hình và luật chơi cho một dây hụi (bát hụi) mới.
*   **Cú pháp:** `/hui_tao_day_hui`
*   **Cách thức hoạt động:**
    - Trả về Form cấu hình dây hụi: Mã Dây Hụi (bắt buộc, ví dụ: `DH01`), ID Chủ Hụi (trỏ sang bảng người chơi, vai trò phải là Owner), Số Tiền Gốc 1 Chân, Mức Bỏ Hụi Tối Thiểu/Tối Đa, Tổng Số Chân (total_parts), Tiền Thảo (Phí dịch vụ thu của người hốt), Ngày Bắt Đầu/Kết Thúc, Ngày Đóng Hàng Kỳ, Giờ Khui, Loại Hụi (ngày/tuần/tháng), Ghi Chú.
    - Gửi lại Form: Bot xác thực ID Chủ hụi tồn tại và có vai trò Owner, kiểm tra trùng lặp Mã Dây Hụi và lưu vào bảng `roscas`.

#### `/hui_cap_nhat_day_hui` (hoặc `/roscas_update_roscas`)
*   **Mục đích:** Chỉnh sửa cấu hình luật chơi của dây hụi đã tồn tại.
*   **Cú pháp:** `/hui_cap_nhat_day_hui [Mã Dây Hụi]`
*   **Cách thức hoạt động:**
    - Bot tra cứu thông tin dây hụi và phản hồi Form điền sẵn dữ liệu cũ (ngày tháng được định dạng chuẩn Việt Nam `DD/MM/YYYY`).
    - Người dùng chỉnh sửa thông tin cần thay đổi và gửi lại để cập nhật DB.

#### `/hui_xoa_day_hui` (hoặc `/roscas_delete_roscas`)
*   **Mục đích:** Xóa dây hụi khỏi hệ thống.
*   **Cú pháp:** `/hui_xoa_day_hui [Mã Dây Hụi]`
*   **Cách thức hoạt động:**
    - Hiển thị thông tin dây hụi và nút bấm xác nhận.
    - Khi bấm xác nhận, bot thực hiện xóa mềm (Soft Delete) bằng cách chuyển cột `status` thành `Deleted`.

---

### QUẢN LÝ CHÂN HỤI (RoscaMember)

#### `/hui_tao_chan_hui` (hoặc `/roscas_create_member`)
*   **Mục đích:** Đăng ký chân tham gia chơi cho thành viên trong một dây hụi cụ thể.
*   **Cú pháp:** `/hui_tao_chan_hui`
*   **Cách thức hoạt động:**
    - Nếu gõ lệnh trống: Bot quét các dây hụi đang ở trạng thái `Draft` hoặc `Active` và hiển thị dưới dạng menu nút bấm inline để chọn nhanh.
    - Sau khi chọn dây hụi, bot trả về Form: Mã Chân Hụi (ví dụ: `AT001`), Mã Dây Hụi, ID Người Chơi, Số Lượng Chân, Tổng Tiền Đã Đóng, Tổng Tiền Đã Nhận, Tổng Lợi Nhuận, Tỷ Suất LN, Trạng Thái, Ghi Chú.
    - Khi nộp Form, bot kiểm tra:
        - Mã Chân Hụi không được trùng lặp.
        - ID Người Chơi tồn tại trong hệ thống.
        - Người chơi chưa tham gia dây hụi này dưới một chân hụi khác (ngăn trùng lặp).
        - Tổng số chân đã đăng ký của dây hụi không vượt quá số chân tối đa (`total_parts`) quy định của dây hụi đó.

#### `/hui_cap_nhat_chan_hui` (hoặc `/roscas_update_member`)
*   **Mục đích:** Điều chỉnh thủ công các chỉ số tài chính của chân hụi (Tổng tiền đã đóng/nhận/lãi...).
*   **Cú pháp:** `/hui_cap_nhat_chan_hui [Mã Chân Hụi]`

#### `/hui_xoa_chan_hui` (hoặc `/roscas_delete_member`)
*   **Mục đích:** Xóa chân hụi khỏi danh sách tham gia dây hụi.
*   **Cú pháp:** `/hui_xoa_chan_hui [Mã Chân Hụi]`
*   **Cách thức hoạt động:**
    - Hiển thị thông tin chân hụi để xác nhận. Khi bấm xác nhận, thực hiện xóa mềm chuyển `status` thành `Deleted`.

---

### NGHIỆP VỤ ĐÓNG HỤI & HỐT HỤI

#### `/hui_dong_tien_chan_hui` (hoặc `/roscas_pay_contribution`)
*   **Mục đích:** Ghi nhận số tiền đóng hụi của người chơi theo từng kỳ khui.
*   **Cú pháp:** `/hui_dong_tien_chan_hui`
*   **Cách thức hoạt động:**
    - Bot hiển thị menu nút bấm chọn dây hụi đang hoạt động (`Active`).
    - Trả về Form đóng tiền: Mã Dây Hụi, Kỳ Khui, Kỳ Thu, Mã Chân Hụi, Số Tiền Đóng (mặc định mang dấu âm biểu thị tiền chi đóng hụi), Ngày Giờ, Trạng Thái (Paid/Late), Ghi Chú.
    - Kiểm tra số tiền đóng phải nằm trong hạn mức (lớn hơn `min_bid_amount` và nhỏ hơn `base_amount`).
    - Nhằm tránh lỗi double-click, bot lưu tạm giao dịch vào bộ nhớ đệm và hiển thị 2 nút bấm inline: "Xác nhận" hoặc "Hủy".
    - Khi bấm xác nhận:
        - Kiểm tra trong DB xem chân hụi này đã đóng tiền kỳ này chưa (ngăn trùng lặp).
        - Cập nhật cộng dồn số tiền đóng vào trường `total_contributed` của chân hụi.
        - Tạo bản ghi giao dịch mới trong bảng `rosca_contributions` với trạng thái `Paid`.

#### `/hui_huy_dong_tien`
*   **Mục đích:** Hủy bỏ một giao dịch đóng hụi đã ghi nhận sai sót.
*   **Cú pháp:** Sử dụng bằng cách **Reply** trực tiếp vào tin nhắn báo đóng tiền thành công của Bot và gõ lệnh `/hui_huy_dong_tien`.
*   **Cách thức hoạt động:**
    - Bot trích xuất ID giao dịch ẩn trong tin nhắn được reply.
    - Tìm giao dịch đóng hụi trong DB. Thực hiện trừ lại số tiền tương ứng khỏi tổng số tiền đã đóng (`total_contributed`) của chân hụi, sau đó xóa bản ghi khỏi bảng `rosca_contributions`.
    - Tự động chỉnh sửa nội dung tin nhắn báo thành công cũ trên Telegram thành `❌ [ĐÃ HỦY] Giao dịch đóng hụi...` để minh bạch lịch sử.

#### `/hui_rut_day_hui` (hoặc `/roscas_withdraw`)
*   **Mục đích:** Thực hiện ghi nhận việc người chơi đấu thầu thắng (hốt hụi), tính toán lợi nhuận và chuyển trạng thái chân hụi sang hụi chết.
*   **Cú pháp:** `/hui_rut_day_hui [Mã Chân Hụi] [Số Tiền Hốt]` (Ví dụ: `/hui_rut_day_hui AT001 5000000`)
*   **Cách thức hoạt động:**
    - Kiểm tra chân hụi đang ở trạng thái `Playing` (chưa hốt hụi).
    - **Logic tính toán Lời/Lỗ**:
        - Đếm số kỳ chân hụi đã đóng thực tế từ bảng giao dịch (`rosca_contributions`).
        - Tính số kỳ còn lại trong tương lai cần đóng hụi chết: `remaining_rounds = total_parts - paid_rounds - 1`.
        - Tính tổng chi phí dự kiến cả dây hụi: `min_receive = tiền_đã_đóng_ở_quá_khứ + (kỳ_còn_lại * số_tiền_hụi_chết_tối_đa)`.
        - Tiền thực nhận khi hốt kỳ này = Số tiền hốt nhập vào - Tiền thảo.
        - Hiệu số lợi nhuận: `profit = Tiền thực nhận - min_receive`.
    - Bot hiển thị bảng phân tích Lời/Lỗ chi tiết, kèm thông tin gợi ý "Mức hốt tối thiểu để có lời" và 2 nút bấm inline: "Xác nhận" và "Hủy".
    - Khi bấm xác nhận:
        - Cộng tiền thực nhận vào trường `total_received` của chân hụi.
        - Cộng lợi nhuận vào trường `total_profit` của chân hụi.
        - Chuyển trạng thái chân hụi sang `Dead` (Chân hụi chết).
        - Ghi nhận giao dịch hốt hụi với số tiền dương vào bảng `rosca_contributions` để theo dõi dòng tiền.

---
---

## 2. DÀNH CHO THÀNH VIÊN (Hụi Member / Người Chơi)

Các lệnh dưới đây được áp dụng khi người chơi thực hiện tra cứu thông tin hoặc tự thao tác đóng hụi trong nhóm thành viên.

#### `/hui_kiem_tra_chan_hui` (hoặc `/roscas_check_member`)
*   **Mục đích:** Người chơi tự tra cứu thông tin chi tiết và tình hình tài chính chân hụi của mình.
*   **Cú pháp:** `/hui_kiem_tra_chan_hui [Mã Chân Hụi]`
*   **Cách thức hoạt động:**
    - Truy xuất thông tin chân hụi: số lượng chân sở hữu, số kỳ đã đóng thực tế, tổng tiền đã đóng, tổng tiền đã nhận, tổng lợi nhuận và tỷ suất lợi nhuận hiện tại.
    - Hiển thị gợi ý động mức hốt tối thiểu để đạt điểm hòa vốn/có lời dựa trên số kỳ đóng thực tế.

#### `/hui_kiem_tra_dong_hui` (hoặc `/roscas_check_contributions`)
*   **Mục đích:** Người chơi kiểm tra lịch sử và trạng thái đóng hụi của chân hụi qua các kỳ khui.
*   **Cú pháp:** `/hui_kiem_tra_dong_hui [Mã Chân Hụi]`
*   **Cách thức hoạt động:**
    - Trích xuất toàn bộ lịch sử các kỳ khui của chân hụi sắp xếp theo thứ tự kỳ tăng dần.
    - Hiển thị trạng thái cụ thể của từng kỳ (`Paid` - đã đóng kèm ngày giờ đóng, `Late` - đóng trễ, `Unpaid` - chưa đóng), số tiền đã đóng từng kỳ.
    - Tổng hợp báo cáo cuối tin nhắn: Số kỳ đã đóng/chưa đóng, tổng tiền đã đóng và tổng số tiền còn nợ.

#### `/hui_thong_ke_hui` (hoặc `/roscas_export_stats`)
*   **Mục đích:** Xuất file Excel báo cáo thống kê tình hình chơi hụi tổng hợp của tất cả các chân hụi.
*   **Cú pháp:** `/hui_thong_ke_hui` (hoặc `/hui_thong_ke_hui [Mã Người Chơi]` để lọc riêng 1 người).
*   **Cách thức hoạt động:**
    - Quét toàn bộ chân hụi liên quan của người chơi trong DB.
    - Sử dụng file mẫu `Template_Hui.xlsx` được cấu hình sẵn các công thức Excel và định dạng.
    - Điền tự động các thông số dây hụi (số tiền gốc, tiền thảo, ngày bắt đầu, loại hụi...) và lịch sử đóng hụi qua các kỳ của từng chân hụi vào các sheet Excel tương ứng mang tên của từng người chơi.
    - Gửi file Excel báo cáo đính kèm lên Telegram.

#### `/hui_dong_tien_chan_hui` (hoặc `/roscas_pay_contribution`)
*   **Mục đích:** Người chơi tự khai báo đóng tiền chân hụi hàng kỳ qua form.
*   **Cú pháp:** `/hui_dong_tien_chan_hui`
*   **Cách thức hoạt động:**
    - Người chơi điền Form đóng tiền gửi lên. Bot lưu tạm giao dịch vào bộ nhớ đệm và gửi yêu cầu phê duyệt sang nhóm quản trị chính. Chủ hụi/Admin bấm xác nhận để chính thức duyệt giao dịch và cập nhật số liệu.

#### `/hui_rut_day_hui` (hoặc `/roscas_withdraw`)
*   **Mục đích:** Người chơi gửi yêu cầu rút hụi / hốt hụi kỳ hiện tại.
*   **Cú pháp:** `/hui_rut_day_hui [Mã Chân Hụi] [Số Tiền Hốt]`

#### `/hui_tinh_lai_gia_lap`
*   **Mục đích:** Tính toán giả lập năng suất lãi/lỗ và chi phí (%) của dây hụi khi chuẩn bị bỏ giá thầu hốt hụi.
*   **Cú pháp:** `/hui_tinh_lai_gia_lap [Mã Dây Hụi] [Số tiền bỏ sắp tới]` (Ví dụ: `/hui_tinh_lai_gia_lap DH01 100000`)
*   **Cách thức hoạt động:**
    - Trích xuất cấu hình dây hụi (tiền gốc, tổng chân, tiền thảo).
    - Tính toán số hụi chết hiện tại (số kỳ đã khui qua) và số hụi sống còn lại.
    - Tính toán giả lập:
        - Tổng tiền hốt dự kiến = (Số hụi chết * Tiền gốc) + ((Tiền gốc - Mức bỏ thầu) * Số hụi sống) - Tiền thảo.
        - Tổng hụi chuẩn = Tiền gốc * (Tổng số chân - 1).
        - Chi phí (%) = `100 - (Tổng tiền hốt / Tổng hụi chuẩn) * 100`.
    - Trả về tin nhắn báo cáo giả lập chi tiết giúp người chơi đưa ra quyết định bỏ giá hợp lý.

#### `/hui_bao_cao_hui`
*   **Mục đích:** Tra cứu báo cáo kết quả chơi hụi tổng hợp theo từng năm của cá nhân người chơi.
*   **Cú pháp:** `/hui_bao_cao_hui [Mã Người Chơi] [Năm]` (Ví dụ: `/hui_bao_cao_hui NC01 2025`)
*   **Cách thức hoạt động:**
    - Tra cứu tất cả chân hụi hoạt động của người chơi trong năm chỉ định.
    - Tổng hợp: Số chân hụi tham gia, số chân hốt có lời, số chân hốt bị lỗ, số chân đang hoạt động.
    - Thống kê tổng số tiền lãi/lỗ tích lũy của cả năm và hiển thị bảng chọn mở rộng xem chi tiết theo từng tháng hoặc chi tiết theo từng mã dây hụi bằng nút bấm inline.
