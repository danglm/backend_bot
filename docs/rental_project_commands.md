# Tài Liệu Hướng Dẫn Các Lệnh Nhóm "RENTAL" (Telegram Bot)

<style>
body {
  font-size: 14px !important;
}
</style>

Tài liệu này cung cấp hướng dẫn chi tiết về mục đích, cú pháp và cách thức hoạt động của các lệnh thuộc nhóm chức năng **RENTAL** (Cho thuê bất động sản/nhà đất) trong Telegram Bot, được chia thành hai phân quyền chính: **Quản trị viên (Rental Main)** và **Khách hàng thành viên (Rental Member)**.

---

## 1. DÀNH CHO QUẢN TRỊ VIÊN (Rental Main) - `role == "main"`

Các lệnh dưới đây được áp dụng khi người dùng ở trong nhóm quản trị dự án có role là `main`.

### `/rental_tao_khach_hang` (hoặc `/rental_create_customer`)
*   **Mục đích:** Khởi tạo biểu mẫu (form) nhập thông tin để tạo mới một khách hàng cho thuê trong hệ thống.
*   **Cú pháp:** `/rental_tao_khach_hang` hoặc `/rental_create_customer`
*   **Cách thức hoạt động:**
    - Khi gọi lệnh không có tham số: Bot hiển thị **Form mẫu tạo khách hàng cho thuê** gồm các trường: Mã Khách Hàng (duy nhất), Tên Nhóm, Tên Khách Hàng, Liên Hệ Khách Hàng, Số Điện Thoại.
    - Người dùng sao chép Form, điền thông tin và gửi lại.
    - Bot kiểm tra xem nhóm chat hiện tại đã được đồng bộ vào dự án cho thuê nào chưa (qua lệnh `/syncchat`).
    - Kiểm tra xem Tên Nhóm có khớp với nhóm thành viên hợp lệ nào trong dự án không và kiểm tra tính duy nhất của Mã Khách Hàng.
    - Nếu hợp lệ, lưu thông tin khách hàng mới vào cơ sở dữ liệu.

---

### `/rental_kiem_tra_khach_hang` (hoặc `/rental_check_customer`)
*   **Mục đích:** Tra cứu thông tin chi tiết và danh sách toàn bộ hợp đồng cho thuê của một khách hàng.
*   **Cú pháp:** `/rental_kiem_tra_khach_hang [Mã Khách Hàng hoặc Tên Nhóm]` hoặc `/rental_check_customer [Mã Khách Hàng hoặc Tên Nhóm]`
*   **Cách thức hoạt động:**
    - Bot tìm kiếm khách hàng cho thuê theo Mã Khách Hàng hoặc Tên Nhóm trong cơ sở dữ liệu.
    - Định dạng hiển thị chi tiết: thông tin liên hệ, số điện thoại, tên nhóm.
    - Liệt kê danh sách tất cả các hợp đồng cho thuê của khách hàng đó kèm theo trạng thái cụ thể của từng hợp đồng (Đang thuê, Hết hạn, Đã hủy, Nợ xấu), mã bất động sản, thời gian thuê, tiền thuê/tháng và tiền cọc đang giữ.

---

### `/rental_tao_hop_dong` (hoặc `/rental_create_contract`)
*   **Mục đích:** Khởi tạo một hợp đồng cho thuê mới cho một khách hàng đã tồn tại.
*   **Cú pháp:** `/rental_tao_hop_dong [Mã Khách Hàng]` hoặc `/rental_create_contract [Mã Khách Hàng]`
*   **Cách thức hoạt động:**
    - Nếu gọi lệnh kèm mã khách hàng: Bot trả về **Form mẫu tạo hợp đồng cho thuê** chứa sẵn thông tin cơ bản của khách hàng đó, yêu cầu người dùng điền thêm các thông tin: Mã Hợp Đồng, Mã Bất Động Sản, Loại Hợp Đồng, Ngày Bắt Đầu Thuê (dd/mm/yyyy), Ngày Kết Thúc Thuê (dd/mm/yyyy), Tiền Cọc, Tiền Thuê / Tháng, Số tiền nợ của khách.
    - Người dùng điền Form và gửi lại. Bot kiểm tra trùng lặp Mã Hợp Đồng trong hệ thống.
    - Thực hiện chuyển đổi định dạng ngày thuê, tiền thuê và lưu hợp đồng mới vào cơ sở dữ liệu.

---

### `/rental_cap_nhat_hop_dong` (hoặc `/rental_update_contract`)
*   **Mục đích:** Chỉnh sửa thông tin chi tiết của một hợp đồng cho thuê đang có.
*   **Cú pháp:** `/rental_cap_nhat_hop_dong [Mã Hợp Đồng]` hoặc `/rental_update_contract [Mã Hợp Đồng]`
*   **Cách thức hoạt động:**
    - Bot tìm kiếm hợp đồng trong hệ thống và trả về Form mẫu chứa thông tin hiện tại của hợp đồng đó để chỉnh sửa.
    - Người dùng thay đổi các thông tin cần thiết trực tiếp trên Form và gửi lại (bao gồm cả trường Trạng Thái: `active`, `expired`, `cancelled`).
    - Bot kiểm tra trùng lặp Mã Hợp Đồng mới (nếu thay đổi), kiểm tra nhóm hợp lệ của dự án và cập nhật thông tin mới vào DB.

---

### `/rental_kiem_tra_hop_dong` (hoặc `/rental_check_contract`)
*   **Mục đích:** Tra cứu thông tin chi tiết và lịch sử đóng tiền thuê nhà hàng tháng của một hợp đồng.
*   **Cú pháp:** `/rental_kiem_tra_hop_dong [Mã Hợp Đồng]` hoặc `/rental_check_contract [Mã Hợp Đồng]`
*   **Cách thức hoạt động:**
    - Bot tìm kiếm hợp đồng cho thuê và khách hàng liên quan trong DB.
    - Truy xuất toàn bộ lịch sử các khoản thanh toán của hợp đồng này từ bảng `RentalPayment`.
    - Phân tích và liệt kê chi tiết đóng tiền của từng tháng (từ ngày bắt đầu thuê đến ngày kết thúc hoặc tháng hiện tại) để hiển thị trạng thái của tháng đó là: *Đã đóng đủ*, *Đóng thiếu*, hoặc *Chưa đóng*.
    - **Hỗ trợ xuất file Excel:** Nếu thời gian của hợp đồng kéo dài **trên 12 tháng**, bot sẽ tự động tạo một bảng Excel (`.xlsx`) được thiết kế chuyên nghiệp, ghi chi tiết thông tin thanh toán từng tháng, sau đó gửi đính kèm cho người dùng. Nếu thời gian hợp đồng **từ 12 tháng trở xuống**, chi tiết đóng tiền sẽ được hiển thị trực tiếp bằng tin nhắn HTML.

---

### `/rental_gia_han_hop_dong` (hoặc `/rental_extend_contract`)
*   **Mục đích:** Gia hạn thêm thời hạn thuê cho hợp đồng cho thuê nhà.
*   **Cú pháp:** `/rental_gia_han_hop_dong [Mã HĐ] [Số tháng]` hoặc `/rental_extend_contract [Mã HĐ] [Số tháng]`
*   **Cách thức hoạt động:**
    - Cộng số tháng gia hạn (mặc định là 1 nếu để trống, tối đa 60) vào ngày kết thúc thuê hiện tại.
    - Bot gửi tin nhắn xác nhận ghi rõ ngày kết thúc cũ và ngày kết thúc mới kèm 2 nút nhấn: "Xác nhận gia hạn" và "Hủy".
    - Khi click xác nhận, bot cập nhật ngày kết thúc thuê mới trong DB. Nếu hợp đồng đang ở trạng thái hết hạn (`EXPIRED`), bot tự động chuyển về trạng thái đang thuê hoạt động (`ACTIVE`).
    - Bot tự động gửi tin nhắn thông báo cập nhật ngày kết thúc mới sang nhóm chat của khách hàng thành viên.

---

### `/rental_huy_hop_dong` (hoặc `/rental_cancel_contract`)
*   **Mục đích:** Hủy bỏ hợp đồng cho thuê.
*   **Cú pháp:** `/rental_huy_hop_dong [Mã Hợp Đồng]` hoặc `/rental_cancel_contract [Mã Hợp Đồng]`
*   **Cách thức hoạt động:**
    - Bot tra cứu hợp đồng và gửi tin nhắn tóm tắt (bao gồm khách hàng, biển số/mã BĐS, tiền cọc, tiền thuê, nợ) kèm 2 nút nhấn inline xác nhận: "Xác nhận hủy" và "Thoát".
    - Khi người dùng click nút "Xác nhận hủy", bot cập nhật trạng thái hợp đồng thành `CANCELLED` (đã hủy) trong cơ sở dữ liệu.

---

### `/rental_danh_sach_hop_dong` (hoặc `/rental_list_contract`)
*   **Mục đích:** Xem danh sách toàn bộ các hợp đồng cho thuê trong dự án hiện tại.
*   **Cú pháp:** `/rental_danh_sach_hop_dong` hoặc `/rental_list_contract`
*   **Cách thức hoạt động:**
    - Truy vấn toàn bộ hợp đồng cho thuê của các khách hàng thuộc dự án quản trị hiện tại.
    - Nhóm các hợp đồng theo từng trạng thái (Đang thuê, Hết hạn, Nợ xấu, Đã hủy).
    - Nếu tổng số hợp đồng **lớn hơn 20**: Bot tự động kết xuất danh sách thành file văn bản `.txt` đính kèm và gửi cho người dùng.
    - Nếu tổng số hợp đồng **từ 20 trở xuống**: Định dạng và hiển thị trực tiếp danh sách hợp đồng kèm tên khách hàng ngay trong tin nhắn chat.

---

### `/rental_xac_nhan_thanh_toan` (hoặc `/rental_payment_confirmed`)
*   **Mục đích:** Quản trị viên xác nhận thu tiền thuê nhà từ khách hàng bằng cách reply trực tiếp tin nhắn thông báo đóng tiền thuê.
*   **Cú pháp:** `/rental_xac_nhan_thanh_toan [Số tiền]` hoặc `/rental_payment_confirmed [Số tiền]` (Sử dụng bằng cách **Reply** vào tin nhắn THÔNG BÁO ĐÓNG TIỀN THUÊ của Bot).
*   **Cách thức hoạt động:**
    - Yêu cầu người dùng phải reply tin nhắn thông báo đóng tiền thuê hợp lệ của Bot và cung cấp số tiền đóng làm đối số.
    - Bot trích xuất Mã Hợp Đồng từ tin nhắn được reply.
    - Trừ trực tiếp số tiền đã đóng vào trường tổng tiền nợ (`rental_debt`) của hợp đồng trên DB.
    - Đồng thời lưu một bản ghi thanh toán mới vào bảng `RentalPayment` để lưu vết lịch sử đóng tiền hàng tháng của khách.
    - Gửi tin nhắn thông báo cập nhật tổng số tiền nợ còn lại của hợp đồng cho thuê đó.

---

### `/rental_xac_nhan_no_xau` (hoặc `/rental_bad_debt`)
*   **Mục đích:** Đưa một hợp đồng cho thuê và khách hàng vào danh sách đen nợ xấu (Blacklist).
*   **Cú pháp:** `/rental_xac_nhan_no_xau [Mã Hợp Đồng]` hoặc `/rental_bad_debt [Mã Hợp Đồng]`
*   **Cách thức hoạt động:**
    - Bot tra cứu thông tin hợp đồng và khách hàng theo mã.
    - Phản hồi thông tin hợp đồng và dư nợ kèm theo 2 nút nhấn inline xác nhận: "Xác nhận nợ xấu" và "Hủy".
    - Khi click nút "Xác nhận nợ xấu", bot sẽ chuyển trạng thái của hợp đồng cho thuê thành `BAD_DEBT` trong cơ sở dữ liệu để tiện theo dõi và xử lý.

---

### `/rental_xem_cong_no` (hoặc `/rental_xem_cong_no`)
*   **Mục đích:** Tra cứu tổng hợp công nợ và chi phí thuê nhà của một khách hàng cụ thể.
*   **Cú pháp:** `/rental_xem_cong_no [Mã Khách Hàng]` hoặc `/rental_xem_cong_no [Mã Khách Hàng]`
*   **Cách thức hoạt động:**
    - Bot tìm kiếm khách hàng theo Mã Khách Hàng.
    - Truy vấn toàn bộ hợp đồng cho thuê đang hoạt động (`ACTIVE` hoặc `EXPIRED`) của khách hàng đó.
    - Tính toán và hiển thị: Tổng số hợp đồng đang thuê, Tổng tiền thuê nhà/tháng, Tổng tiền nợ cần thanh toán tích lũy, và danh sách chi tiết nợ của từng hợp đồng cụ thể.

---

### `/rental_doanh_thu` (hoặc `/rental_doanh_thu`)
*   **Mục đích:** Xem báo cáo doanh thu tiền thuê nhà thực tế đã thu trong một khoảng thời gian lọc tùy chọn.
*   **Cú pháp:** `/rental_doanh_thu` hoặc `/rental_revenue`
*   **Cách thức hoạt động:**
    - Người dùng có thể gõ trực tiếp khoảng thời gian lọc (ví dụ: `/rental_revenue 01/01/2026 - 31/01/2026`).
    - Nếu gõ không kèm tham số: Bot hiển thị menu nút nhấn chọn nhanh khoảng thời gian lọc (7 ngày qua, 14 ngày qua, 21 ngày qua, 1 tháng qua, 1 quý qua, năm nay, năm trước).
    - Bot truy vấn các bản ghi đóng tiền thuê (`RentalPayment`) và hợp đồng trong khoảng thời gian đã chọn để hiển thị chi tiết: Doanh thu (Tổng tiền phải thu, Tổng tiền đã thu, Còn phải thu, Tỷ lệ thu tiền) và Thống kê thanh toán hợp đồng (Đã thanh toán, Chưa thanh toán, Quá hạn).

---

### `/rental_bao_cao_dong_tien` (hoặc `/rental_bao_cao_dong_tien`)
*   **Mục đích:** Xem báo cáo dòng tiền chi tiết của dự án cho thuê.
*   **Cú pháp:** `/rental_bao_cao_dong_tien` hoặc `/rental_cashflow_report`
*   **Cách thức hoạt động:**
    - Truy vấn toàn bộ khách hàng và hợp đồng đang hoạt động trong dự án.
    - Tính toán các chỉ số: Tổng số hợp đồng đang thuê, Tổng tiền cọc đang giữ, và Tổng tiền thuê thực tế đã thu được (tích lũy từ tất cả các giao dịch `RentalPayment`) và số nợ còn lại của từng khách hàng.
    - Phản hồi báo cáo dòng tiền chi tiết cho từng khách hàng và tổng kết toàn dự án (chia nhỏ tin nhắn gửi đi nếu nội dung vượt quá giới hạn ký tự).

---

### `/rental_tao_phieu_thu` (hoặc `/rental_tao_phieu_thu`)
*   **Mục đích:** Tạo một phiếu thu thanh toán tiền thuê nhà độc lập cho hợp đồng để lưu lịch sử mà không làm thay đổi trực tiếp trường dư nợ trong bảng rentals.
*   **Cú pháp:** `/rental_tao_phieu_thu` hoặc `/rental_tao_phieu_thu [Mã Hợp Đồng]`
*   **Cách thức hoạt động:**
    - Nếu gọi không kèm form: Bot gửi Form mẫu tạo phiếu thu gồm: Mã hợp đồng, Ngày thanh toán (mặc định là hôm nay), Số tiền thanh toán.
    - Người dùng điền Form gửi lại. Bot phân tích và validate số tiền, ngày thanh toán (định dạng `dd/mm/yyyy`).
    - Thêm bản ghi thanh toán mới vào bảng `RentalPayment` để cập nhật vào lịch sử đóng tiền hàng tháng của hợp đồng cho thuê đó.

---
---

## 2. DÀNH CHO KHÁCH HÀNG THÀNH VIÊN (Rental Member) - `role == "member"`

Các lệnh dưới đây được áp dụng khi người dùng ở trong nhóm thành viên dự án có role là `member`.

### `/rental_kiem_tra_khach_hang` (hoặc `/rental_check_customer`)
*   **Mục đích:** Thành viên tự kiểm tra thông tin tài khoản và danh sách các hợp đồng cho thuê của mình.
*   **Cú pháp:** `/rental_kiem_tra_khach_hang [Mã Khách Hàng]` hoặc `/rental_check_customer [Mã Khách Hàng]`
*   **Cách thức hoạt động:**
    - Bot xác thực Mã Khách Hàng được nhập (chỉ cho phép xem nếu Mã Khách Hàng thuộc về nhóm chat của thành viên gửi lệnh).
    - Hiển thị thông tin liên hệ, SĐT và danh sách các hợp đồng cho thuê liên quan, bao gồm trạng thái hợp đồng, mã bất động sản, thời gian thuê, tiền thuê/tháng và tiền cọc đang giữ.

---

### `/rental_kiem_tra_hop_dong` (hoặc `/rental_check_contract`)
*   **Mục đích:** Thành viên tự tra cứu chi tiết và lịch sử đóng tiền thuê nhà từng tháng của hợp đồng cho thuê của mình.
*   **Cú pháp:** `/rental_kiem_tra_hop_dong [Mã Hợp Đồng]` hoặc `/rental_check_contract [Mã Hợp Đồng]`
*   **Cách thức hoạt động:**
    - Bot tìm kiếm hợp đồng trong DB và xác thực hợp đồng đó có đúng thuộc quyền sở hữu của khách hàng trong nhóm chat đó hay không.
    - Truy xuất toàn bộ lịch sử các khoản thanh toán từ bảng `RentalPayment`.
    - Nếu thời gian thuê trên 12 tháng, bot tự động tạo bảng Excel (`.xlsx`) chi tiết lịch sử đóng tiền từng tháng để gửi đính kèm. Ngược lại, bot hiển thị trực tiếp bằng tin nhắn chat.

---

### `/rental_xem_cong_no` (hoặc `/rental_check_debt`)
*   **Mục đích:** Thành viên tự tra cứu công nợ tích lũy và chi phí thuê nhà hàng tháng của bản thân.
*   **Cú pháp:** `/rental_xem_cong_no [Mã Khách Hàng]` hoặc `/rental_check_debt [Mã Khách Hàng]`
*   **Cách thức hoạt động:**
    - Bot tìm kiếm khách hàng theo Mã Khách Hàng và kiểm tra quyền truy cập của nhóm chat.
    - Truy vấn toàn bộ hợp đồng đang hoạt động (`ACTIVE` hoặc `EXPIRED`) của khách hàng đó.
    - Tổng hợp và hiển thị chi tiết: Tổng số hợp đồng đang thuê, Tổng tiền thuê nhà/tháng, Tổng tiền nợ cần thanh toán tích lũy, và danh sách chi tiết nợ của từng hợp đồng cụ thể.
