# Tài Liệu Hướng Dẫn Các Lệnh Nhóm "OTHER" (Telegram Bot)

<style>
body {
  font-size: 14px !important;
}
</style>

Tài liệu này cung cấp hướng dẫn chi tiết về mục đích, cú pháp và cách thức hoạt động của các lệnh thuộc nhóm chức năng **OTHER** trong Telegram Bot, được chia thành ba khu vực quản lý chính: **Quản lý thiết bị (Other Device)**, **Quản lý hồ sơ/giấy tờ & lịch hẹn (Other Image)**, và **Quản lý phương tiện (Other Vehicle)**.

---

## 1. QUẢN LÝ THIẾT BỊ (Other Device) - `main_device`

Các lệnh dưới đây được áp dụng khi người dùng ở trong nhóm và có custom title cấu hình là `main_device`.

### `/other_tao_thiet_bi` (hoặc `/other_create_device`)
*   **Mục đích:** Khởi tạo biểu mẫu (form) nhập thông tin để tạo mới một thiết bị trong hệ thống.
*   **Cú pháp:** `/other_tao_thiet_bi` hoặc `/other_create_device`
*   **Cách thức hoạt động:**
    - Khi người dùng gửi lệnh, bot hiển thị một menu nút nhấn (Inline Buttons) cho phép chọn loại thiết bị muốn tạo (bao gồm: Điện thoại, Laptop, Máy tính bảng, Màn hình, Camera, Thiết bị khác).
    - Khi chọn một loại thiết bị cụ thể, bot tự động thay đổi nội dung tin nhắn hiện tại thành một **Biểu mẫu mẫu (Template Form)** tương ứng với các trường dữ liệu thích hợp và đính kèm lệnh khởi tạo phụ (ví dụ: `/other_create_laptop`, `/other_create_smartphone`...).
    - Người dùng sao chép form này, điền đầy đủ các thông tin chi tiết và gửi lại để hoàn tất tạo thiết bị.

---

### `/other_cap_nhat_thiet_bi` (hoặc `/other_update_device`)
*   **Mục đích:** Cập nhật thông tin chi tiết cho một thiết bị hiện có trong cơ sở dữ liệu.
*   **Cú pháp:** `/other_cap_nhat_thiet_bi [Mã Thiết Bị hoặc IMEI]` hoặc `/other_update_device [Mã Thiết Bị hoặc IMEI]`
*   **Cách thức hoạt động:**
    - Nếu gọi lệnh không có tham số: Bot hiển thị menu nút nhấn để người dùng chọn loại thiết bị cần cập nhật kèm hướng dẫn.
    - Nếu có tham số (Mã Thiết Bị hoặc IMEI của điện thoại): Bot tìm kiếm thiết bị tương ứng trong cơ sở dữ liệu.
    - Nếu tìm thấy, bot phản hồi bằng một **Form chứa thông tin hiện tại** của thiết bị đó.
    - Người dùng chỉ cần sao chép Form, chỉnh sửa các giá trị mong muốn và gửi lại tin nhắn dạng Form đó để bot cập nhật dữ liệu mới vào DB.

---

### `/other_xoa_thiet_bi` (hoặc `/other_delete_device`)
*   **Mục đích:** Vô hiệu hóa thiết bị khỏi danh sách hoạt động chính (thực hiện xóa mềm - soft delete).
*   **Cú pháp:** `/other_xoa_thiet_bi [Mã Thiết Bị hoặc IMEI]` hoặc `/other_delete_device [Mã Thiết Bị hoặc IMEI]`
*   **Cách thức hoạt động:**
    - Nếu gọi lệnh không có tham số: Bot hiển thị menu chọn loại thiết bị muốn xóa để xem hướng dẫn cú pháp chi tiết.
    - Nếu có tham số: Bot thực hiện tra cứu thiết bị trong cơ sở dữ liệu.
    - Thay vì xóa hẳn bản ghi khỏi DB để bảo toàn lịch sử hoạt động, bot cập nhật trạng thái hoạt động (status) của thiết bị sang trạng thái bảo trì/hỏng hóc (Điện thoại/Màn hình/Camera/TB Khác chuyển thành `broken`, Laptop chuyển thành `maintenance`).
    - Bot gửi tin nhắn thông báo xác nhận chuyển trạng thái thành công.

---

### `/other_tao_sim` (hoặc `/other_create_sim`)
*   **Mục đích:** Tạo mới thông tin SIM điện thoại trong hệ thống.
*   **Cú pháp:** `/other_tao_sim` hoặc `/other_create_sim`
*   **Cách thức hoạt động:**
    - Khi gọi lệnh, bot phản hồi bằng một Form mẫu gồm các thông tin: Mã Định Danh, Số Điện Thoại (bắt buộc), Nhà Mạng, ICCID, Mã PUK, Gói Cước, Trạng Thái (mặc định: `active`), Loại SIM, Đang Ở Thiết Bị.
    - Người dùng sao chép, điền thông tin và gửi lại.
    - Bot xác thực các thông tin đầu vào (ví dụ: trạng thái phải thuộc `active`, `blocked`, `expired`) và lưu vào cơ sở dữ liệu.

---

### `/other_cap_nhat_sim` (hoặc `/other_update_sim`)
*   **Mục đích:** Chỉnh sửa thông tin của một SIM đang có trên hệ thống.
*   **Cú pháp:** `/other_cap_nhat_sim [Mã Định Danh hoặc Số Điện Thoại]` hoặc `/other_update_sim [Mã Định Danh hoặc Số Điện Thoại]`
*   **Cách thức hoạt động:**
    - Bot tìm kiếm SIM trong hệ thống theo Mã Định Danh hoặc Số Điện Thoại đã cung cấp.
    - Nếu tồn tại SIM tương ứng, bot phản hồi Form chứa dữ liệu hiện tại của SIM đó.
    - Người dùng chỉnh sửa các thông tin cần thay đổi trên Form và gửi lại tin nhắn để cập nhật vào cơ sở dữ liệu.

---

### `/other_xoa_sim` (hoặc `/other_delete_sim`)
*   **Mục đích:** Vô hiệu hóa SIM trong hệ thống (xóa mềm).
*   **Cú pháp:** `/other_xoa_sim [Mã Định Danh hoặc Số Điện Thoại]` hoặc `/other_delete_sim [Mã Định Danh hoặc Số Điện Thoại]`
*   **Cách thức hoạt động:**
    - Bot thực hiện tìm kiếm SIM theo Mã Định Danh hoặc Số Điện Thoại được chỉ định.
    - Nếu tìm thấy SIM hợp lệ, bot cập nhật trường trạng thái của SIM thành `expired` (đã hết hạn/vô hiệu hóa) để ẩn SIM khỏi danh sách hoạt động mà không làm mất log cũ.
    - Phản hồi thông báo xác nhận thao tác thành công.

---

### `/other_nhan_thiet_bi` (hoặc `/other_receive_device`)
*   **Mục đích:** Ghi nhận bàn giao thiết bị cho một thành viên cụ thể sử dụng.
*   **Cú pháp:** `/other_nhan_thiet_bi [Mã Thiết Bị hoặc IMEI]` hoặc `/other_receive_device [Mã Thiết Bị hoặc IMEI]`
*   **Cách thức hoạt động:**
    - Bot tìm kiếm thiết bị thông qua Mã Thiết Bị hoặc IMEI trong cơ sở dữ liệu.
    - Kiểm tra trạng thái hiện tại của thiết bị: Thao tác nhận thiết bị chỉ được chấp nhận nếu thiết bị đang ở trạng thái `available` (sẵn sàng bàn giao).
    - Nếu thỏa mãn điều kiện, bot tự động tạo bản ghi bàn giao (`DeviceAssignment`) ghi nhận tài khoản Telegram người nhận, thời gian nhận và tình trạng ban đầu của thiết bị.
    - Cập nhật trạng thái của thiết bị từ `available` thành `assigned` (đã bàn giao).

---

### `/other_tra_thiet_bi` (hoặc `/other_return_device`)
*   **Mục đích:** Ghi nhận việc hoàn trả lại thiết bị và chuyển thiết bị về trạng thái sẵn sàng để người khác sử dụng.
*   **Cú pháp:** `/other_tra_thiet_bi [Mã Thiết Bị hoặc IMEI]` hoặc `/other_return_device [Mã Thiết Bị hoặc IMEI]`
*   **Cách thức hoạt động:**
    - Bot tìm kiếm thiết bị trong cơ sở dữ liệu. Chỉ cho phép thực hiện nếu trạng thái của thiết bị là `assigned` (đang được giữ sử dụng).
    - Truy vấn tìm bản ghi bàn giao (`DeviceAssignment`) hoạt động gần nhất của thiết bị đó (chưa có ngày trả).
    - Xác thực người thực hiện lệnh trả: Người gửi lệnh trên Telegram bắt buộc phải là người đang giữ thiết bị (trừ khi có quyền đặc biệt). Nếu không phải, bot từ chối và báo tên người đang giữ.
    - Nếu khớp thông tin, bot cập nhật thời gian trả, tình trạng khi trả, và chuyển trạng thái thiết bị từ `assigned` quay trở lại `available`.

---

### `/other_tra_cuu_thiet_bi` (hoặc `/other_check_device`)
*   **Mục đích:** Tra cứu thông tin chi tiết, trạng thái, người đang sử dụng hiện tại, danh sách ứng dụng đã cài đặt và các SIM đang lắp trên thiết bị.
*   **Cú pháp:** `/other_tra_cuu_thiet_bi [Mã Thiết Bị hoặc IMEI]` hoặc `/other_check_device [Mã Thiết Bị hoặc IMEI]`
*   **Cách thức hoạt động:**
    - Bot tìm kiếm thiết bị trong cơ sở dữ liệu (hỗ trợ cả tìm theo Mã Thiết Bị hoặc IMEI điện thoại).
    - Lấy thông tin người sử dụng hiện tại từ bản ghi bàn giao chưa trả.
    - Truy vấn danh sách ứng dụng được cài đặt thông qua bảng liên kết `InstalledApp`.
    - Lấy danh sách các SIM đang gắn trên thiết bị đó (chỉ áp dụng đối với smartphone).
    - Tổng hợp toàn bộ dữ liệu trên thành một tin nhắn có định dạng rõ ràng để gửi cho người dùng.

---

### `/other_lich_su_thiet_bi` (hoặc `/other_check_log_device`)
*   **Mục đích:** Xem lịch sử toàn bộ các lượt nhận/trả của một thiết bị cụ thể.
*   **Cú pháp:** `/other_lich_su_thiet_bi [Mã Thiết Bị hoặc IMEI]` hoặc `/other_check_log_device [Mã Thiết Bị hoặc IMEI]`
*   **Cách thức hoạt động:**
    - Bot tìm kiếm thiết bị và đếm tổng số bản ghi bàn giao (`DeviceAssignment`) của thiết bị đó.
    - Nếu thiết bị chưa từng được bàn giao, bot phản hồi thông tin chưa có lịch sử.
    - Nếu số lượng lượt bàn giao **lớn hơn 20**: Để tránh bị giới hạn ký tự và spam tin nhắn trên Telegram, bot xuất toàn bộ lịch sử thành file văn bản dạng `.txt` và gửi đính kèm cho người dùng.
    - Nếu số lượt bàn giao **từ 20 trở xuống**: Bot định dạng văn bản HTML và gửi trực tiếp danh sách lịch sử bàn giao chi tiết (bao gồm người nhận, ngày nhận, ngày trả, tình trạng ban đầu/khi trả) ngay trong tin nhắn chat.

---

### `/other_danh_sach_thiet_bi` (hoặc `/other_list_device`)
*   **Mục đích:** Xem danh sách tổng hợp toàn bộ các thiết bị đang có trên hệ thống.
*   **Cú pháp:** `/other_danh_sach_thiet_bi` hoặc `/other_list_device`
*   **Cách thức hoạt động:**
    - Truy vấn toàn bộ thiết bị đang quản lý (Smartphone, Laptop, Màn hình, Camera, TB Khác) cùng thông tin người giữ hiện tại, ứng dụng đã cài và SIM liên kết.
    - Nếu tổng số lượng thiết bị **lớn hơn 20**: Bot tự động kết xuất danh sách thành một file văn bản đính kèm `.txt` chứa đầy đủ chi tiết và gửi cho người dùng.
    - Nếu tổng số thiết bị **từ 20 trở xuống**: Bot gửi trực tiếp danh sách các thiết bị được định dạng đẹp mắt kèm thông tin về mã, trạng thái, người giữ và phụ kiện ngay trong phòng chat.

---

### `/other_dong_bo_ung_dung` (hoặc `/other_sync_app`)
*   **Mục đích:** Cho phép cài đặt/đồng bộ hàng loạt một ứng dụng lên nhiều thiết bị (Điện thoại hoặc Laptop) cùng lúc.
*   **Cú pháp:** `/other_dong_bo_ung_dung [Mã Ứng Dụng (ID)]` hoặc `/other_sync_app [Mã Ứng Dụng (ID)]`
*   **Cách thức hoạt động:**
    - Bot kiểm tra ứng dụng tồn tại trong hệ thống theo Mã ID.
    - Lấy toàn bộ các thiết bị chưa được cài đặt ứng dụng này.
    - Gửi tin nhắn chứa danh sách thiết bị dưới dạng menu nút bấm (Inline Buttons) cho phép chọn nhiều thiết bị cùng lúc (click để tick/untick chọn).
    - Lưu phiên đồng bộ tạm thời vào bộ nhớ RAM. Khi người dùng bấm nút "Xác Nhận Đồng Bộ", bot sẽ tiến hành lưu hàng loạt bản ghi liên kết cài đặt ứng dụng (`InstalledApp`) cho các thiết bị đã chọn và thông báo kết quả.

---
---

## 2. QUẢN LÝ GIẤY TỜ & LỊCH HẸN (Other Image) - `main_image`

Các lệnh dưới đây được áp dụng khi người dùng ở trong nhóm và có custom title cấu hình là `main_image`.

### `/other_tao_giay_to` (hoặc `/other_create_document`)
*   **Mục đích:** Tạo mới hồ sơ, tài liệu hoặc giấy tờ cần giám sát thời hạn trong dự án.
*   **Cú pháp:** `/other_tao_giay_to` hoặc `/other_create_document`
*   **Cách thức hoạt động:**
    - Nếu gọi lệnh không kèm nội dung: Bot gửi Form mẫu tạo giấy tờ gồm các trường thông tin: Mã Giấy Tờ (tự sinh nếu để trống), Tên Giấy Tờ (bắt buộc), Số Hiệu, Phân Loại, Chủ Sở Hữu, Ngày Cấp, Ngày Hết Hạn, Ghi Chú.
    - Người dùng điền thông tin và gửi lại Form.
    - Bot thực hiện kiểm tra định dạng ngày cấp/ngày hết hạn (định dạng `dd/mm/yyyy`), kiểm tra trùng lặp mã và lưu trữ giấy tờ vào DB với trạng thái mặc định là `ACTIVE`.
    - Sau khi tạo thành công, bot phản hồi tin nhắn chúc mừng kèm một nút lệnh nhanh gợi ý thêm lịch hẹn nhắc nhở cho giấy tờ đó.

---

### `/other_them_lich_hen` (hoặc `/other_add_reminder`)
*   **Mục đích:** Tạo một lịch hẹn thông báo tự động (định kỳ hoặc một lần) liên quan đến hạn dùng của một giấy tờ cụ thể.
*   **Cú pháp:** `/other_them_lich_hen [Mã Giấy Tờ]` hoặc `/other_add_reminder [Mã Giấy Tờ]`
*   **Cách thức hoạt động:**
    - Nếu gọi lệnh không kèm form: Bot gửi Form mẫu cấu hình lịch hẹn: Nhóm Telegram (nhận thông báo, mặc định là nhóm hiện tại), Nhắc Trước (ngày hết hạn), Ngày Nhắc Nhở cố định, Giờ Nhắc Nhở, Chu Kỳ, Nội dung tin nhắn tùy biến.
    - Người dùng sao chép và điền Form gửi lại.
    - Bot kiểm tra tính hợp lệ của Mã Giấy Tờ, kiểm tra xem chu kỳ có hợp lệ không (`ONCE`, `DAILY`, `WEEKLY`, `MONTHLY`, `YEARLY`).
    - Lưu lịch hẹn nhắc nhở (`DocumentReminder`) ở trạng thái hoạt động (`ACTIVE`). Hệ thống ngầm quét thời gian và tự động gửi tin nhắn đến chat nhóm Telegram khi đến lịch hẹn.

---

### `/other_cap_nhat_giay_to` (hoặc `/other_update_document`)
*   **Mục đích:** Thay đổi/chỉnh sửa thông tin chi tiết của một hồ sơ, giấy tờ đã tạo.
*   **Cú pháp:** `/other_cap_nhat_giay_to [Mã Giấy Tờ (UUID)]` hoặc `/other_update_document [Mã Giấy Tờ (UUID)]`
*   **Cách thức hoạt động:**
    - Bot kiểm tra xem giấy tờ có tồn tại theo Mã UUID được cung cấp hay không.
    - Nếu tồn tại, bot gửi lại Form mẫu điền sẵn dữ liệu hiện tại của giấy tờ đó.
    - Người dùng sửa đổi các thông tin cần thiết trực tiếp trên Form và gửi lại tin nhắn để bot cập nhật dữ liệu mới vào DB.

---

### `/other_cap_nhat_lich_hen` (hoặc `/other_update_reminder`)
*   **Mục đích:** Chỉnh sửa cấu hình hoặc trạng thái hoạt động của một lịch hẹn nhắc nhở.
*   **Cú pháp:** `/other_cap_nhat_lich_hen [Mã Lịch Hẹn (UUID)]` hoặc `/other_update_reminder [Mã Lịch Hẹn (UUID)]`
*   **Cách thức hoạt động:**
    - Nếu gọi lệnh không có tham số: Bot hiển thị danh sách các lịch hẹn đang hoạt động kèm bàn phím phân trang dưới dạng nút bấm để người dùng chọn trực tiếp.
    - Nếu có tham số: Bot tìm lịch hẹn theo Mã UUID tương ứng và trả về Form chứa thông tin chi tiết lịch hẹn hiện tại (bao gồm cả trường Trạng Thái: `ACTIVE` hoặc `INACTIVE`).
    - Người dùng sửa thông tin trên Form và gửi lại để cập nhật lịch nhắc nhở mới.

---

### `/other_xoa_giay_to` (hoặc `/other_xoa_giay_to`)
*   **Mục đích:** Xóa/lưu trữ một hồ sơ giấy tờ và tắt toàn bộ các lịch hẹn liên quan (xóa mềm).
*   **Cú pháp:** `/other_xoa_giay_to [Mã Giấy Tờ (UUID)]` hoặc `/other_delete_document [Mã Giấy Tờ (UUID)]`
*   **Cách thức hoạt động:**
    - Nếu gọi lệnh không có tham số: Bot hiển thị danh sách các giấy tờ hoạt động kèm menu phân trang để người dùng chọn xóa.
    - Nếu có tham số Mã UUID: Bot tìm giấy tờ và cập nhật trạng thái thành `ARCHIVED` (Lưu trữ) để ẩn khỏi các báo cáo thông thường.
    - Để tránh các thông báo nhắc nhở rác, bot tự động quét và chuyển trạng thái toàn bộ các lịch hẹn nhắc nhở (`DocumentReminder`) liên kết với giấy tờ này thành `INACTIVE` (Ngừng hoạt động).

---

### `/other_xoa_lich_hen` (hoặc `/other_delete_reminder`)
*   **Mục đích:** Tắt hoặc dừng một lịch hẹn nhắc nhở cụ thể.
*   **Cú pháp:** `/other_xoa_lich_hen [Mã Lịch Hẹn (UUID)]` hoặc `/other_delete_reminder [Mã Lịch Hẹn (UUID)]`
*   **Cách thức hoạt động:**
    - Nếu gọi lệnh không có tham số: Bot hiển thị danh sách các lịch nhắc nhở đang chạy kèm menu phân trang để người dùng chọn tắt nhanh.
    - Nếu cung cấp Mã UUID lịch hẹn: Bot thay đổi trường trạng thái của lịch nhắc nhở đó thành `INACTIVE`. Từ thời điểm này, hệ thống sẽ ngừng gửi thông báo tự động cho lịch hẹn này.

---

### `/other_danh_sach_giay_to` (hoặc `/other_list_documents`)
*   **Mục đích:** Hiển thị danh sách phân trang toàn bộ các hồ sơ giấy tờ đang được theo dõi tích cực.
*   **Cú pháp:** `/other_danh_sach_giay_to [Trang]` hoặc `/other_list_documents [Trang]`
*   **Cách thức hoạt động:**
    - Truy vấn các giấy tờ có trạng thái hoạt động `ACTIVE` được liên kết với dự án.
    - Hiển thị danh sách được chia trang (tối đa 10 giấy tờ trên một trang).
    - Đính kèm bàn phím nút bấm chứa tên các giấy tờ để người dùng bấm vào xem thông tin chi tiết hoặc di chuyển sang các trang tiếp theo/trước đó.

---
---

## 3. QUẢN LÝ PHƯƠNG TIỆN (Other Vehicle) - `main_vehicle`

Các lệnh dưới đây được áp dụng khi người dùng ở trong nhóm và có custom title cấu hình là `main_vehicle`.

### `/other_tao_xe` (hoặc `/other_create_vehicle`)
*   **Mục đích:** Khai báo một phương tiện (xe) mới vào hệ thống quản lý.
*   **Cú pháp:** `/other_tao_xe` hoặc `/other_create_vehicle`
*   **Cách thức hoạt động:**
    - Nếu gọi lệnh không có form: Bot trả về Form mẫu đăng ký xe mới gồm: Biển Số (bắt buộc, duy nhất), Loại Xe, Thương Hiệu, Model, Màu Sắc, Chủ Xe, Trạng Thái (mặc định: `inactivity`).
    - Người dùng sao chép Form, điền thông tin chi tiết và gửi lại.
    - Bot kiểm tra xem biển số xe đã tồn tại trong DB chưa, kiểm tra tính hợp lệ của trạng thái xe (`activited`, `inactivity`, `is_removed`).
    - Thêm xe mới vào cơ sở dữ liệu nếu thông tin hợp lệ.

---

### `/other_cap_nhat_xe` (hoặc `/other_update_vehicle`)
*   **Mục đích:** Thay đổi/cập nhật thông tin chi tiết của một phương tiện.
*   **Cú pháp:** `/other_cap_nhat_xe [Biển Số hoặc ID]` hoặc `/other_update_vehicle [Biển Số hoặc ID]`
*   **Cách thức hoạt động:**
    - Tra cứu xe trong cơ sở dữ liệu dựa trên Biển Số hoặc ID được cung cấp.
    - Trả về Form mẫu chứa đầy đủ các thông tin hiện tại của xe đó.
    - Người dùng chỉnh sửa các trường dữ liệu cần thiết trực tiếp trên Form và gửi lại tin nhắn cho bot để cập nhật thông tin mới vào hệ thống.

---

### `/other_xoa_xe` (hoặc `/other_delete_vehicle`)
*   **Mục đích:** Vô hiệu hóa/Ngừng quản lý xe khỏi hệ thống (xóa mềm).
*   **Cú pháp:** `/other_xoa_xe [Biển Số hoặc ID]` hoặc `/other_delete_vehicle [Biển Số hoặc ID]`
*   **Cách thức hoạt động:**
    - Tra cứu thông tin xe trong cơ sở dữ liệu.
    - Để bảo toàn lịch sử di chuyển/nhận trả xe của tài xế trước đó, bot không xóa cứng bản ghi khỏi DB mà cập nhật trường trạng thái hoạt động của xe thành `is_removed` (đã xóa).
    - Gửi phản hồi xác nhận xóa thành công.

---

### `/other_nhan_xe` (hoặc `/other_receive_vehicle`)
*   **Mục đích:** Cho phép tài xế đăng ký nhận sử dụng xe.
*   **Cú pháp:** `/other_nhan_xe [Biển Số]` hoặc `/other_receive_vehicle [Biển Số]`
*   **Cách thức hoạt động:**
    - Nếu không cung cấp biển số: Bot tự động truy vấn và liệt kê danh sách các xe rảnh (đang ở trạng thái `inactivity` - Không hoạt động) để người dùng tiện lựa chọn, kèm hướng dẫn cú pháp nhận xe.
    - Nếu cung cấp biển số: Bot tìm xe trong DB, kiểm tra xem trạng thái của xe có phải là `inactivity` không. Nếu xe đang hoạt động (`activited`), bot từ chối và hiển thị tên tài khoản Telegram của người đang giữ xe đó. Nếu xe đã bị xóa (`is_removed`), bot báo không thể nhận.
    - Nếu hợp lệ, bot cập nhật trạng thái của xe thành `activited` và ghi nhận một bản ghi hoạt động mới (`RECEIVE`) liên kết tài xế Telegram đó với xe.

---

### `/other_tra_xe` (hoặc `/other_return_vehicle`)
*   **Mục đích:** Hoàn trả xe sau khi sử dụng để xe sẵn sàng cho lượt bàn giao tiếp theo.
*   **Cú pháp:** `/other_tra_xe [Biển Số]` hoặc `/other_return_vehicle [Biển Số]`
*   **Cách thức hoạt động:**
    - Bot tra cứu thông tin xe. Chỉ cho phép thực hiện nếu trạng thái của xe là `activited` (Đang hoạt động).
    - Xác minh thông tin tài xế trả xe: Bot kiểm tra xem người thực hiện lệnh trả xe có khớp với người gửi log nhận xe (`RECEIVE`) gần nhất của chiếc xe này hay không. Nếu không trùng khớp, bot từ chối thao tác trả xe để đảm bảo an toàn.
    - Nếu hợp lệ, bot cập nhật trạng thái xe về `inactivity` (Không hoạt động) và lưu một log hoạt động `RETURN` vào hệ thống.

---

### `/other_lich_su_xe` (hoặc `/other_check_log_vehicle`)
*   **Mục đích:** Xem lịch sử hoạt động nhận/trả xe và danh sách tài xế đã sử dụng xe.
*   **Cú pháp:** `/other_lich_su_xe [Biển Số]` hoặc `/other_check_log_vehicle [Biển Số]`
*   **Cách thức hoạt động:**
    - Bot đếm tổng số lượt log hoạt động `RECEIVE` (nhận xe) của phương tiện trong cơ sở dữ liệu.
    - Nếu chưa từng phát sinh hoạt động nào, bot báo xe chưa có lịch sử.
    - Nếu tổng số lượt nhận **lớn hơn 20**: Bot xuất toàn bộ lịch sử chi tiết (tên tài xế, thời gian nhận xe, thời gian trả xe tương ứng) thành file văn bản dạng `.txt` đính kèm để người dùng tải về.
    - Nếu tổng số lượt nhận **từ 20 trở xuống**: Bot định dạng và hiển thị trực tiếp danh sách lịch sử sử dụng chi tiết ngay trên cửa sổ chat.

---

### `/other_danh_sach_phuong_tien` (hoặc `/other_list_vehicle`)
*   **Mục đích:** Hiển thị danh sách toàn bộ các phương tiện đang hoạt động trong hệ thống quản lý (không hiển thị các xe đã xóa).
*   **Cú pháp:** `/other_danh_sach_phuong_tien` hoặc `/other_list_vehicle`
*   **Cách thức hoạt động:**
    - Truy vấn toàn bộ xe trong DB (ngoại trừ xe có trạng thái `is_removed`).
    - Nhóm danh sách các phương tiện tìm được thành 2 danh mục: **Đang hoạt động** (`activited`) và **Không hoạt động** (`inactivity`).
    - Đối với các xe "Đang hoạt động", bot tự động tìm và đính kèm tên tài khoản Telegram của tài xế đang giữ xe hiện tại.
    - Định dạng và gửi toàn bộ danh sách đã nhóm cho người dùng qua tin nhắn chat (chia nhỏ tin nhắn nếu nội dung quá dài).
