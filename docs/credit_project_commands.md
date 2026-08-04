# Tài Liệu Hướng Dẫn Các Lệnh Nhóm "CREDIT" (Telegram Bot)

<style>
body {
  font-size: 14px !important;
}
</style>

Tài liệu này cung cấp hướng dẫn chi tiết về mục đích, cú pháp và cách thức hoạt động của các lệnh thuộc nhóm chức năng **CREDIT** trong Telegram Bot, được chia thành hai phân quyền chính: **Quản trị viên (Credit Main)** và **Khách hàng thành viên (Credit Member)**.

---

## 1. DÀNH CHO QUẢN TRỊ VIÊN (Credit Main) - `role == "main"`

Các lệnh dưới đây được áp dụng khi người dùng ở trong nhóm quản trị dự án có role là `main`.

### `/credit_tao_khach_hang` (hoặc `/credit_create_customer`)
*   **Mục đích:** Khởi tạo biểu mẫu (form) nhập thông tin để tạo mới một hồ sơ khách hàng tín dụng trong hệ thống.
*   **Cú pháp:** `/credit_tao_khach_hang` hoặc `/credit_create_customer`
*   **Cách thức hoạt động:**
    - Khi gọi lệnh không có tham số: Bot hiển thị **Form mẫu tạo khách hàng tín dụng** gồm các trường: Mã Khách Hàng (duy nhất), Tên Nhóm, Tên Khách Hàng, Liên Hệ Khách Hàng, **Chat ID (Telegram)**, Tổng Hạn Mức Tín Dụng, Hạn Mức Còn Lại, Tổng Nợ Gốc Hiện Tại (mặc định: 0), Phân Loại (mặc định: KCredit).
    - Người dùng sao chép Form, điền thông tin và gửi lại.
    - Bot kiểm tra xem nhóm chat hiện tại đã được đồng bộ vào dự án nào chưa (yêu cầu đã cấu hình qua lệnh `/syncchat`).
    - Kiểm tra xem Tên Nhóm và Liên Hệ Khách Hàng có hợp lệ trong danh sách thành viên dự án không, và kiểm tra tính duy nhất của Mã Khách Hàng.
    - Trường **Chat ID (Telegram)** được lưu vào cột `credit_customers.chat_id` (dùng cho các lệnh xem thông tin ở nhóm member):
        - Nếu điền: bot kiểm tra Chat ID đó có thuộc một nhóm member của dự án hay không, sai thì báo lỗi.
        - Nếu để trống: bot tự suy ra Chat ID theo Tên Nhóm đã đồng bộ. Nếu nhóm chưa có Chat ID (chưa chạy `/syncchat`), bot báo lỗi và không tạo khách hàng.
    - Nếu hợp lệ, lưu thông tin khách hàng mới vào cơ sở dữ liệu.

---

### `/credit_cap_nhat_khach_hang` (hoặc `/credit_update_customer`)
*   **Mục đích:** Chỉnh sửa thông tin chi tiết của một khách hàng tín dụng sẵn có.
*   **Cú pháp:** `/credit_cap_nhat_khach_hang` (chọn khách hàng bằng nút) hoặc `/credit_cap_nhat_khach_hang [Mã Khách Hàng]` / `/credit_update_customer [Mã Khách Hàng]`
*   **Cách thức hoạt động:**
    - Nếu gọi lệnh **không kèm tham số**: Bot hiển thị **danh sách khách hàng** dạng nút với nhãn `Mã Khách Hàng - Tên Khách Hàng`, phân trang tối đa 10 khách hàng mỗi trang kèm nút **<< Trước**, **Sau >>** và **Hủy**. Nhấn vào một khách hàng, bot trả về Form cập nhật của khách hàng đó.
    - Nếu gọi lệnh **kèm Mã Khách Hàng**: Bot tìm khách hàng và phản hồi ngay Form mẫu chứa dữ liệu hiện tại của khách hàng.
    - Người dùng chỉnh sửa các giá trị mong muốn trực tiếp trên Form và gửi lại.
    - Bot xác thực trùng lặp Mã Khách Hàng mới (nếu thay đổi) và độ chính xác của Tên Nhóm, sau đó lưu thay đổi vào DB.
    - Form cập nhật có sẵn trường **Chat ID (Telegram)** với giá trị hiện tại. Nếu sửa trực tiếp thì bot dùng giá trị đó (có kiểm tra thuộc nhóm member của dự án); nếu để trống thì bot tự đồng bộ lại `credit_customers.chat_id` theo Chat ID của nhóm member ứng với Tên Nhóm.

---

### `/credit_xem_khach_hang` (hoặc `/credit_check_customer`)
*   **Mục đích:** Xem thông tin chi tiết về hạn mức tín dụng và danh sách toàn bộ các hợp đồng của một khách hàng.
*   **Cú pháp:** `/credit_xem_khach_hang [Mã Khách Hàng hoặc Tên Nhóm]` hoặc `/credit_check_customer [Mã Khách Hàng hoặc Tên Nhóm]`
*   **Cách thức hoạt động:**
    - Bot tìm kiếm khách hàng theo Mã Khách Hàng hoặc Tên Nhóm được chỉ định.
    - Định dạng hiển thị chi tiết: thông tin liên hệ, phân loại, tổng hạn mức, hạn mức còn lại, tổng nợ gốc hiện tại.
    - Liệt kê danh sách toàn bộ hợp đồng của khách hàng đó kèm trạng thái cụ thể của từng hợp đồng (Đang vay, Đã tất toán, Nợ xấu, Đã hủy) và hình thức vay (Thế chấp/Tín chấp).

---

### `/credit_tao_hop_dong` (hoặc `/credit_create_contract`)
*   **Mục đích:** Khởi tạo một hợp đồng tín dụng mới cho một khách hàng đã tồn tại.
*   **Cú pháp:** `/credit_tao_hop_dong` (chọn khách hàng bằng nút) hoặc `/credit_tao_hop_dong [Mã Khách Hàng]` / `/credit_create_contract [Mã Khách Hàng]`
*   **Cách thức hoạt động:**
    - Nếu gọi lệnh **không kèm tham số**: Bot hiển thị **danh sách khách hàng** dạng nút với nhãn `Mã Khách Hàng - Tên Khách Hàng`, phân trang tối đa 10 khách hàng mỗi trang kèm nút **<< Trước**, **Sau >>** và **Hủy**. Nhấn vào một khách hàng, bot trả về Form tạo hợp đồng đã điền sẵn thông tin của khách hàng đó.
    - Nếu gọi lệnh **kèm mã khách hàng**: Bot trả về ngay **Form mẫu tạo hợp đồng tín dụng** chứa sẵn thông tin cơ bản của khách hàng đó, yêu cầu người dùng điền thêm: Mã Hợp Đồng, Loại Hợp Đồng (thế chấp/tín chấp), Tiền Nợ Gốc, Ngày Bắt Đầu Vay, Ngày Đáo Hạn, Ngày Bắt Đầu Thu Lãi, Lãi Suất/Tháng (%), Số Tiền Lãi/Tháng, Tổng Số Tiền Trả Gốc, Tiền Nợ Gốc Còn Lại, Ghi Chú, Gửi Tin Nhắn Phát Sinh (Có/Không), Nội Dung Tin Nhắn, Phân Loại.
    - Người dùng điền Form và gửi lại. Bot kiểm tra trùng lặp Mã Hợp Đồng trong hệ thống.
    - **Ràng buộc hạn mức:** Đối với hợp đồng Thế chấp (`secured`), bot kiểm tra xem số tiền gốc của hợp đồng có vượt quá hạn mức tín dụng còn lại của khách hàng hay không. Nếu vượt quá, bot từ chối tạo hợp đồng.
    - Nếu hợp lệ, lưu hợp đồng mới, tự động trừ vào hạn mức còn lại và cộng dồn dư nợ gốc hiện tại của khách hàng.

---

### `/credit_cap_nhat_hop_dong` (hoặc `/credit_update_contract`)
*   **Mục đích:** Chỉnh sửa thông tin chi tiết của một hợp đồng tín dụng đang hoạt động.
*   **Cú pháp:** `/credit_cap_nhat_hop_dong` (chọn bằng nút) hoặc `/credit_cap_nhat_hop_dong [Mã Hợp Đồng]` / `/credit_update_contract [Mã Hợp Đồng]`
*   **Cách thức hoạt động:**
    - Nếu gọi lệnh **không kèm tham số**: Bot hiển thị **danh sách khách hàng** dạng nút (`Mã Khách Hàng - Tên Khách Hàng`, tối đa 10/trang, kèm **<< Trước**, **Sau >>**, **Hủy**). Chọn một khách hàng, bot hiển thị **danh sách hợp đồng** của khách hàng đó (bỏ qua hợp đồng đã hủy, tối đa 10/trang, kèm **<< Trước**, **Sau >>**, **Quay lại**, **Hủy**). Chọn một hợp đồng, bot trả về Form cập nhật của hợp đồng đó.
    - Nếu gọi lệnh **kèm Mã Hợp Đồng**: Bot tìm hợp đồng và trả về ngay Form mẫu chứa đầy đủ thông tin hiện tại của hợp đồng đó.
    - Người dùng chỉnh sửa các trường dữ liệu cần thiết trên Form và gửi lại.
    - Bot kiểm tra trùng lặp Mã Hợp Đồng mới (nếu thay đổi).
    - **Cân đối lại hạn mức:** Nếu dư nợ gốc ban đầu thay đổi, bot sẽ tự động tính toán hoàn trả/trừ lại vào Hạn mức còn lại và dư nợ gốc tích lũy của khách hàng, sau đó cập nhật dữ liệu mới vào DB.

---

### `/credit_xem_hop_dong` (hoặc `/credit_check_contract`)
*   **Mục đích:** Tra cứu thông tin chi tiết của một hợp đồng tín dụng cụ thể.
*   **Cú pháp:** `/credit_xem_hop_dong [Mã Hợp Đồng]` hoặc `/credit_check_contract [Mã Hợp Đồng]`
*   **Cách thức hoạt động:**
    - Bot tìm kiếm hợp đồng trong cơ sở dữ liệu và xác thực hợp đồng đó có thuộc về nhóm hợp lệ trong dự án hiện tại không.
    - Tổng hợp và trả về tin nhắn chi tiết: trạng thái, loại hợp đồng (thế chấp/tín chấp), phân loại, thông tin khách hàng, số gốc ban đầu, gốc đã trả, gốc còn nợ, lãi suất, lãi tạm tính hàng tháng, nợ lãi tích lũy hiện tại, ngày vay, ngày đáo hạn và ngày tính lãi.

---

### `/credit_huy_hop_dong` (hoặc `/credit_cancel_contract`)
*   **Mục đích:** Thực hiện hủy bỏ một hợp đồng tín dụng.
*   **Cú pháp:** `/credit_huy_hop_dong` (chọn bằng nút) hoặc `/credit_huy_hop_dong [Mã Hợp Đồng]` / `/credit_cancel_contract [Mã Hợp Đồng]`
*   **Cách thức hoạt động:**
    - Nếu gọi lệnh **không kèm tham số**: Bot hiển thị **danh sách khách hàng** dạng nút (`Mã Khách Hàng - Tên Khách Hàng`, tối đa 10/trang, kèm **<< Trước**, **Sau >>**, **Hủy**). Chọn một khách hàng, bot hiển thị **danh sách hợp đồng** có thể hủy của khách hàng đó (bỏ qua hợp đồng đã hủy, kèm **Quay lại**, **Hủy**).
    - Chọn một hợp đồng, bot hiển thị **thông báo xác nhận hủy** (tên khách hàng, mã hợp đồng, trạng thái, lãi suất, dư nợ gốc) kèm 2 nút: **Xác nhận** và **Hủy**.
    - Nếu gọi lệnh **kèm Mã Hợp Đồng**: Bot đi thẳng tới màn hình xác nhận nói trên.
    - Khi người dùng click nút "Xác nhận", bot cập nhật trạng thái hợp đồng thành `CANCELLED` trong cơ sở dữ liệu và khóa không cho phép cập nhật hay tính lãi thêm.

---

### `/credit_gia_han_hop_dong` (hoặc `/credit_extend_contract`)
*   **Mục đích:** Gia hạn thêm thời hạn đáo hạn cho một hợp đồng tín dụng.
*   **Cú pháp:** `/credit_gia_han_hop_dong` (chọn bằng nút) hoặc `/credit_gia_han_hop_dong [Mã HĐ] [Số tháng]` / `/credit_extend_contract [Mã HĐ] [Số tháng]`
*   **Cách thức hoạt động:**
    - Nếu gọi lệnh **không kèm tham số**: Bot hiển thị **danh sách khách hàng** dạng nút (`Mã Khách Hàng - Tên Khách Hàng`, tối đa 10/trang, kèm **<< Trước**, **Sau >>**, **Hủy**). Chọn một khách hàng, bot hiển thị **danh sách toàn bộ hợp đồng** của khách hàng đó — bao gồm cả hợp đồng Nợ xấu, Tất toán và Đã hủy — kèm **Quay lại**, **Hủy**.
    - Chọn một hợp đồng, bot trả về **Form gia hạn** (Mã Hợp Đồng, Tên Khách Hàng, Trạng Thái, Ngày Đáo Hạn Hiện Tại, **Số Tháng Gia Hạn**). Người dùng điền Số Tháng Gia Hạn rồi gửi lại Form.
    - Hợp đồng đang ở trạng thái `PAID` (Tất toán) hoặc `CANCELLED` (Đã hủy) vẫn được liệt kê nhưng không thể gia hạn — bot báo lỗi khi chọn.
    - Số tháng gia hạn (chấp nhận từ 1 đến 60) sẽ được cộng vào ngày đáo hạn hiện tại. Nếu không truyền, mặc định gia hạn là 1 tháng.
    - Bot hiển thị chi tiết thông tin ngày đáo hạn cũ và ngày đáo hạn mới đề xuất kèm theo 2 nút nhấn: "Xác nhận gia hạn" và "Hủy".
    - Khi xác nhận, bot cập nhật ngày đáo hạn mới trong DB. Nếu hợp đồng đang ở trạng thái nợ xấu (`BAD_DEBT`), bot tự động chuyển về trạng thái hoạt động bình thường (`ACTIVE`) và gỡ cảnh báo Blacklist.
    - Bot tự động gửi tin nhắn thông báo cập nhật ngày đáo hạn mới sang nhóm chat của khách hàng thành viên.

---

### `/credit_danh_sach_hop_dong` (hoặc `/credit_list_contract`)
*   **Mục đích:** Xem danh sách toàn bộ các hợp đồng tín dụng trong dự án hiện tại.
*   **Cú pháp:** `/credit_danh_sach_hop_dong` hoặc `/credit_list_contract`
*   **Cách thức hoạt động:**
    - Truy vấn toàn bộ hợp đồng của các nhóm thành viên trực thuộc nhóm quản trị hiện tại.
    - Nhóm các hợp đồng tìm được theo từng trạng thái: Đang vay, Nợ xấu, Đã tất toán, Đã hủy.
    - Nếu tổng số hợp đồng **lớn hơn 20**: Bot tự động kết xuất danh sách thành file văn bản `.txt` đính kèm và gửi cho người dùng.
    - Nếu tổng số hợp đồng **từ 20 trở xuống**: Định dạng và hiển thị danh sách chi tiết các hợp đồng kèm tên khách hàng ngay trong tin nhắn Telegram.

---

### `/credit_xac_nhan_thanh_toan` (hoặc `/credit_payment_confirmed`)
*   **Mục đích:** Cho phép Quản trị viên ghi nhận khoản tiền đóng nợ lãi từ khách hàng bằng cách reply trực tiếp tin nhắn thông báo đóng lãi.
*   **Cú pháp:** `/credit_xac_nhan_thanh_toan [Số tiền]` hoặc `/credit_payment_confirmed [Số tiền]` (Sử dụng bằng cách **Reply** vào tin nhắn THÔNG BÁO ĐÓNG TIỀN LÃI của Bot).
*   **Cách thức hoạt động:**
    - Yêu cầu người dùng phải reply tin nhắn thông báo đóng lãi hợp lệ của Bot và cung cấp số tiền đóng làm đối số.
    - Bot trích xuất Mã Hợp Đồng từ tin nhắn được reply.
    - Tạo bản ghi thanh toán tiền lãi mới (`CreditInterest`) và tự động trừ trực tiếp số tiền đã đóng vào trường tổng nợ lãi (`interest_debt`) của hợp đồng trên DB.
    - Nếu hợp đồng đang ở trạng thái nợ xấu, bot chuyển về `ACTIVE` và gỡ nhãn Blacklist.
    - Gửi tin nhắn thông báo cập nhật tổng nợ lãi còn lại của hợp đồng đó.

---

### `/credit_xac_nhan_no_xau` (hoặc `/credit_bad_debt`)
*   **Mục đích:** Chuyển đổi trạng thái hợp đồng sang nợ xấu (Blacklist) bằng cách reply tin nhắn cảnh báo.
*   **Cú pháp:** `/credit_xac_nhan_no_xau` hoặc `/credit_bad_debt` (Sử dụng bằng cách **Reply** vào tin nhắn CẢNH BÁO NỢ XẤU của Bot).
*   **Cách thức hoạt động:**
    - Yêu cầu người dùng reply tin nhắn cảnh báo nợ xấu hợp lệ của Bot.
    - Bot trích xuất Mã Hợp Đồng từ tin nhắn được reply, thay đổi trạng thái hợp đồng thành `BAD_DEBT` và tự động gắn thêm tiền tố `[BLACKLIST]` vào ghi chú của hợp đồng để đưa khách hàng vào danh sách hạn chế/truy thu đặc biệt.

---

### `/credit_bao_cao_dong_tien` (hoặc `/credit_cashflow_report`)
*   **Mục đích:** Xem báo cáo dòng tiền chi tiết của dự án tín dụng.
*   **Cú pháp:** `/credit_bao_cao_dong_tien` hoặc `/credit_cashflow_report`
*   **Cách thức hoạt động:**
    - Truy vấn toàn bộ khách hàng và hợp đồng đang hoạt động trong dự án trực thuộc. Khách hàng được đối chiếu theo `credit_customers.chat_id` (Chat ID nhóm member), không theo tên nhóm.
    - Tính toán các chỉ số: Tổng số hợp đồng đang vay, Tổng nợ gốc hiện tại, Tổng nợ lãi chưa thu, và Tổng tiền lãi đã thu được (tích lũy từ tất cả các giao dịch `CreditInterest`).
    - Phản hồi báo cáo tổng kết toàn dự án kèm 2 nút: **Chi tiết** và **Hủy**.
        - **Chi tiết:** liệt kê từng khách hàng với Số hợp đồng, Nợ gốc, Nợ lãi và Tổng thanh toán, sắp xếp theo Nợ gốc giảm dần. Phân trang tối đa 10 khách hàng mỗi trang kèm nút **<< Trước**, **Sau >>**, **Ẩn chi tiết** và **Hủy**.
        - **Ẩn chi tiết:** quay về báo cáo tổng.
        - **Hủy:** xóa tin nhắn báo cáo.

---

### `/credit_doanh_thu` (hoặc `/credit_revenue`)
*   **Mục đích:** Xem báo cáo doanh thu tiền lãi thực tế đã thu được trong một khoảng thời gian lọc tùy chọn.
*   **Cú pháp:** `/credit_doanh_thu` hoặc `/credit_revenue`
*   **Cách thức hoạt động:**
    - Người dùng có thể gõ trực tiếp khoảng thời gian lọc (ví dụ: `/credit_revenue 01/01/2026 - 31/01/2026`).
    - If gõ không kèm tham số: Bot hiển thị menu nút nhấn chọn nhanh khoảng thời gian lọc (7 ngày qua, 14 ngày qua, 21 ngày qua, 1 tháng qua, 1 quý qua, năm nay, năm trước).
    - Bot truy vấn các bản ghi thu lãi (`CreditInterest`) phát sinh trong khoảng thời gian đã chọn và hiển thị: Tổng Lãi Đã Thu thực tế, Tổng Nợ Gốc Đang Vay Hiện Tại, Tổng Nợ Lãi Chưa Trả của dự án.
    - Báo cáo kèm 2 nút: **Chi tiết** và **Hủy**.
        - **Chi tiết:** liệt kê từng hợp đồng với Lãi đã thu (trong kỳ), Nợ gốc và Nợ lãi chưa trả, sắp xếp theo Lãi đã thu giảm dần. Phân trang tối đa 10 hợp đồng mỗi trang kèm nút **<< Trước**, **Sau >>**, **Ẩn chi tiết** và **Hủy**.
        - **Ẩn chi tiết:** quay về báo cáo tổng.
        - **Hủy:** xóa tin nhắn báo cáo.
    - Khách hàng của dự án được đối chiếu theo `credit_customers.chat_id` (Chat ID nhóm member), không theo tên nhóm.

---
---

## 2. DÀNH CHO KHÁCH HÀNG THÀNH VIÊN (Credit Member) - `role == "member"`

Các lệnh dưới đây được áp dụng khi người dùng ở trong nhóm thành viên dự án có role là `member`.

### `/credit_xem_tt_khach_hang` (hoặc `/credit_member_check_customer`)
*   **Mục đích:** Thành viên tự xem thông tin khách hàng tín dụng gắn với nhóm của mình.
*   **Cú pháp:** `/credit_xem_tt_khach_hang` hoặc `/credit_member_check_customer` (không cần tham số)
*   **Cách thức hoạt động:**
    - Bot xác định khách hàng theo `chat_id` của chính nhóm gửi lệnh (cột `credit_customers.chat_id`).
    - Hiển thị thông tin khách hàng: mã, tên, tên nhóm, liên hệ, phân loại, tổng hạn mức, hạn mức còn lại, tổng nợ gốc hiện tại, tổng số hợp đồng, tổng nợ gốc còn lại và tổng nợ lãi.
    - Kèm 2 nút: **Xem hợp đồng**, **Hủy**.
        - **Xem hợp đồng:** hiển thị danh sách hợp đồng của khách hàng đó dạng nút (có phân trang) kèm nút **Hủy**. Chọn một hợp đồng sẽ hiển thị thông tin hợp đồng kèm nút **Hủy**.
        - **Hủy:** xóa tin nhắn thao tác.
    - Nếu một nhóm gắn với nhiều khách hàng, Bot hiển thị danh sách khách hàng để chọn trước.

---

### `/credit_xem_tt_hop_dong` (hoặc `/credit_member_check_contract`)
*   **Mục đích:** Thành viên tự tra cứu chi tiết các hợp đồng của nhóm mình.
*   **Cú pháp:** `/credit_xem_tt_hop_dong` hoặc `/credit_member_check_contract` (không cần tham số)
*   **Cách thức hoạt động:**
    - Bot xác định khách hàng theo `chat_id` của chính nhóm gửi lệnh, sau đó hiển thị danh sách hợp đồng của khách hàng đó dạng nút (có phân trang) kèm nút **Hủy**.
    - Chọn một hợp đồng sẽ hiển thị thông tin hợp đồng: mã hợp đồng, khách hàng, loại hợp đồng, trạng thái, nợ gốc ban đầu, đã trả gốc, nợ gốc còn lại, nợ lãi hiện tại, ngày bắt đầu vay, ngày đáo hạn, ngày bắt đầu thu lãi, lãi suất/tháng, tiền lãi/tháng và ghi chú.
    - Màn hình thông tin hợp đồng có 2 nút: **Quay lại** (trở về danh sách hợp đồng), **Hủy**.

---

### `/credit_xem_cong_no` (hoặc `/credit_check_debt`)
*   **Mục đích:** Thành viên tự kiểm tra tổng hợp toàn bộ công nợ gốc và nợ lãi hiện tại của mình.
*   **Cú pháp:** `/credit_xem_cong_no` hoặc `/credit_check_debt` (không cần tham số)
*   **Cách thức hoạt động:**
    - Bot xác định khách hàng theo `chat_id` của chính nhóm gửi lệnh (cột `credit_customers.chat_id`), không cần nhập Mã Khách Hàng.
    - Nếu một nhóm gắn với nhiều khách hàng, Bot hiển thị danh sách khách hàng dạng nút để chọn (kèm nút **Hủy**).
    - Truy vấn toàn bộ hợp đồng đang ở trạng thái vay hoạt động (`ACTIVE` hoặc `BAD_DEBT`).
    - Tổng hợp và hiển thị chi tiết: Tổng số hợp đồng đang vay, Tổng nợ gốc còn lại, Tổng nợ lãi, Tổng công nợ hiện tại (Gốc + Lãi) và chi tiết công nợ gốc/lãi của từng hợp đồng cụ thể.
    - Màn hình công nợ có 2 nút: **Quay lại** (về danh sách khách hàng của nhóm), **Hủy** (xóa tin nhắn).
