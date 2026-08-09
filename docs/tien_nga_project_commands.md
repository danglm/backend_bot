# Tài Liệu Hướng Dẫn Các Lệnh Nhóm "TIẾN NGA" (Telegram Bot)

<style>
body {
  font-size: 12px !important;
}
</style>

Tài liệu này cung cấp hướng dẫn chi tiết về mục đích, cú pháp và cách thức hoạt động của các lệnh thuộc nhóm chức năng **TIẾN NGA** (Dự án Tiến Nga) trong Telegram Bot, được chia thành hai phân quyền chính: **Quản trị viên (Tiến Nga Main / Super Main)** và **Thành viên bộ phận (Tiến Nga Member)**.

---

## 1. DÀNH CHO QUẢN TRỊ VIÊN (Tiến Nga Main / Super Main)

Các lệnh dưới đây được áp dụng khi người dùng ở trong nhóm quản trị dự án có role là `main` và sở hữu custom title tương ứng với từng bộ phận hoặc `super_main` (quản trị chung).

### QUẢN LÝ CHUNG & HỆ THỐNG

#### `/tien_nga_ds_nhom_member` (hoặc `/tien_nga_list_member_group`)
*   **Mục đích:** Hiển thị danh sách các nhóm chat thành viên (member) trực thuộc nhóm quản trị (main) hiện tại.
*   **Cú pháp:** `/tien_nga_ds_nhom_member` hoặc `/tien_nga_list_member_group`
*   **Cách thức hoạt động:**
    - Bot thực hiện quét trong cơ sở dữ liệu để tìm tất cả các nhóm chat thành viên (`role == "member"`) có ID nhóm cha (`parent_id`) trùng khớp với ID của nhóm quản trị (`main`) đang gửi lệnh.
    - Hiển thị danh sách các nhóm thành viên kèm số lượng thành viên trong từng nhóm theo từng trang (phân trang tối đa 10 nhóm/trang).
    - Cung cấp bàn phím nút bấm inline để chuyển trang qua lại thuận tiện.

#### `/send_message`
*   **Mục đích:** Gửi thông báo hàng loạt (văn bản, hình ảnh, video, hoặc tin chuyển tiếp) từ nhóm quản trị đến các nhóm thành viên được chọn.
*   **Cú pháp:** `/send_message [Nội dung]` (hoặc reply tin nhắn cần gửi/chuyển tiếp kèm lệnh `/send_message`).
*   **Cách thức hoạt động:**
    - Bot ghi nhận nội dung tin nhắn soạn thảo hoặc tin nhắn reply từ quản trị viên.
    - Hiển thị menu chọn dự án (Tiến Nga, Credit, Rental, Ggomoosin, Other) dưới dạng nút bấm inline.
    - Sau khi chọn dự án, bot tiếp tục liệt kê danh sách các nhóm thành viên trực thuộc dự án đó kèm theo ô checkbox để quản trị viên tick chọn gửi đến một hoặc nhiều nhóm cùng lúc.
    - Nhấn "Xác nhận gửi" để thực thi phát thông báo đồng loạt.

---

### PHÂN HỆ QUẢN LÝ NHÂN SỰ (HR) - `custom_title == "main_hr"` hoặc `"super_main"`

> **Cập nhật 08/08/2026 — toàn bộ 11 lệnh HR đã chuyển sang menu nút bấm.**
> Gõ lệnh **không kèm tham số** để mở menu. Danh sách nhân viên hiển thị 10 người
> mỗi trang, có `<< Trước` / `Sau >>` / `Hủy`.
>
> **Phạm vi dữ liệu:** mỗi dự án chỉ thấy nhân viên của mình. Một nhân viên thuộc
> dự án khi thỏa **cả hai** điều kiện: `telegram_group` khớp một nhóm member của
> dự án **và** mã NV bắt đầu bằng tiền tố của dự án (Tiến Nga = `TN`,
> Ggomoosin = `G`). Nhân viên chỉ thỏa một điều kiện sẽ không hiển thị, và số
> lượng bị loại được cảnh báo ngay trên đầu danh sách.
>
> **Cú pháp gõ tay cũ vẫn dùng được** cho mọi lệnh — hữu ích khi biết sẵn mã NV.

#### `/tien_nga_tao_nhan_vien` (hoặc `/tien_nga_create_employee`)
*   **Mục đích:** Khởi tạo hồ sơ nhân viên mới và liên kết với tài khoản Telegram.
*   **Menu:** danh sách nhân viên hiện có (để tra mã đã dùng, tránh trùng) + nút **Thêm mới nhân viên** + **Hủy**.
*   **Cách thức hoạt động:**
    - Bấm **Thêm mới nhân viên** để bot hiển thị Form nhập thông tin: Mã NV (bắt buộc), Họ, Tên, Username Telegram (không chứa `@`), SĐT, Email, CCCD, Ngân hàng, Số tài khoản, Lương, Giờ vào ca/tan ca.
    - Copy Form, điền thông tin và gửi lại. Bot kiểm tra trùng Mã NV / Username / Email / SĐT rồi lưu vào bảng `Employee`.

#### `/tien_nga_cap_nhat_nhan_vien` (hoặc `/tien_nga_update_employee`)
*   **Mục đích:** Chỉnh sửa hồ sơ nhân viên đã tồn tại.
*   **Menu:** chọn nhân viên từ danh sách → bot trả về Form đã điền sẵn dữ liệu hiện tại.
*   **Cú pháp gõ tay:** `/tien_nga_cap_nhat_nhan_vien [Mã NV hoặc Username]`
*   **Cách thức hoạt động:** sửa các trường cần thay đổi trên Form (không sửa dòng Mã NV/Username) rồi gửi lại; bot đối chiếu và cập nhật vào bảng `Employee`.

#### `/tien_nga_xoa_nhan_vien` (hoặc `/tien_nga_delete_employee`)
*   **Mục đích:** Ghi nhận nhân viên nghỉ việc.
*   **Menu:** chọn nhân viên → màn xác nhận với 2 nút **Xác nhận** / **Huỷ**.
*   **Cú pháp gõ tay:** `/tien_nga_xoa_nhan_vien [Mã NV]`
*   **Cách thức hoạt động:** xóa mềm bằng cách chuyển `status` thành `inactive`, giữ nguyên lịch sử chấm công và giao dịch phục vụ đối soát lương. Nhân viên đã `inactive` sẽ không cho xóa lại.

#### `/tien_nga_giao_viec` (hoặc `/tien_nga_create_task`)
*   **Mục đích:** Phân công công việc cho nhân viên từ nhóm Quản lý.
*   **Menu:** chọn nhân viên → bot trả về Form giao việc **đã điền sẵn ô Người nhận**.
*   **Cách thức hoạt động:** điền Nội dung, Khung giờ (hh:mm - hh:mm), Ngày bắt đầu/kết thúc, Chu kỳ rồi gửi lại. Task lưu ở trạng thái `PENDING` và bot gửi thông báo "CÓ CÔNG VIỆC MỚI" xuống nhóm của nhân viên.

#### `/tien_nga_xuat_luong` (hoặc `/tien_nga_export_payroll`)
*   **Mục đích:** Chốt số công và bảng lương cho một nhân viên, xuất phiếu lương dạng ảnh và ghi nhận công nợ lương.
*   **Menu:** chọn nhân viên → chọn kỳ lương:
    - **Tháng này** / **Tháng trước** — một chạm.
    - **Chọn tháng** — lưới chọn năm + 12 tháng.
    - **Kỳ tùy chọn** — bot hiện lệnh mẫu để copy, dùng cho kỳ chéo tháng.
*   **Cú pháp gõ tay:**
    - `/tien_nga_xuat_luong TN001 05/2026` — trọn tháng.
    - `/tien_nga_xuat_luong TN001 05/07/2026 - 04/08/2026` — **kỳ chéo tháng**.
*   **Cách thức hoạt động:**
    - Ngày công chuẩn tính theo `work_type` của từng nhân viên, đếm trên **đúng khoảng ngày của kỳ**. Kỳ 05/07 → 04/08 = số ngày công còn lại của tháng 7 cộng số ngày đầu tháng 8.
    - Truy quét chấm công thực tế trong kỳ: ngày đi làm (nửa ngày tính 0.5), giờ tăng ca, ngày nghỉ phép.
    - Lương thực tế = (Lương tháng / Ngày công chuẩn) × Ngày làm thực tế, cộng tăng ca, thưởng, ăn trưa, năng suất, phụ cấp; trừ BHXH và phạt.
    - **Kỳ được ghi sổ vào tháng BẮT ĐẦU** của khoảng ngày (05/07 → 04/08 là lương tháng 7), khớp quy ước của API `/get-salaries`.
    - Cập nhật phần chênh lệch vào `total_debt` của nhân viên. Xuất lại cùng một kỳ chỉ cập nhật tại chỗ, không cộng dồn hai lần.
    - Vẽ bảng lương thành ảnh `.png`, gửi xuống nhóm chat riêng của nhân viên. Ảnh ghi rõ kỳ lương.

#### `/tien_nga_tao_lai_bang_cham_cong` (hoặc `/tien_nga_recreate_attendance_report`)
*   **Mục đích:** Vẽ lại bảng chấm công của nhân viên trong tháng dưới dạng ảnh.
*   **Menu:** chọn nhân viên → chọn tháng (Tháng này / Tháng trước / Chọn tháng).
*   **Cú pháp gõ tay:** `/tien_nga_tao_lai_bang_cham_cong [Mã NV] [MM/YYYY]`
*   **Cách thức hoạt động:** truy vấn `Attendance` lấy giờ vào/ra, tăng ca, lỗi chấm công từ mùng 1 đến cuối tháng rồi render thành ảnh gửi lên nhóm Quản lý.

#### `/tien_nga_danh_sach_cong_viec` (hoặc `/tien_nga_list_tasks`)
*   **Mục đích:** Xem công việc đã giao cho một nhân viên.
*   **Menu:** chọn nhân viên → chọn khoảng thời gian **3 / 6 / 12 / 24 tháng** gần nhất.
*   **Cú pháp gõ tay:** `/tien_nga_danh_sach_cong_viec [Mã NV] [Số tháng]`
*   **Cách thức hoạt động:** nhóm công việc theo 4 trạng thái PENDING, IN_PROGRESS, COMPLETED, CANCELLED và hiển thị kèm hạn hoàn thành.

#### `/tien_nga_xuat_danh_sach_luong` (hoặc `/tien_nga_list_payroll`)
*   **Mục đích:** Xuất bảng tổng hợp chi trả lương toàn dự án trong tháng ra Excel.
*   **Menu:** chọn tháng ngay (không cần chọn nhân viên).
*   **Cú pháp gõ tay:** `/tien_nga_xuat_danh_sach_luong [MM/YYYY]`
*   **Cách thức hoạt động:** quét bảng `Payroll` của tháng, **chỉ lấy nhân viên thuộc dự án hiện tại**, dựng Excel gồm lương cơ bản, tăng ca, phạt, thưởng, thực nhận, kèm dòng TỔNG CỘNG.

#### `/tien_nga_danh_sach_nhan_vien` (hoặc `/tien_nga_list_employee`)
*   **Mục đích:** Xem và thao tác nhanh trên danh sách nhân sự của dự án.
*   **Menu:** danh sách nhân viên có phân trang. Chọn một người sẽ hiện thêm **Cập nhật nhân viên** và **Xóa nhân viên**. Nút **Xuất Excel danh sách** luôn có sẵn.
*   **Cách thức hoạt động:** file Excel gồm thông tin cá nhân, CCCD, SĐT, STK ngân hàng, mức lương, giờ ca và công nợ. Danh sách bao gồm cả nhân viên đã nghỉ việc.

#### `/tien_nga_danh_sach_cham_cong` (hoặc `/tien_nga_list_attendance`)
*   **Mục đích:** Tải Excel lịch sử chấm công của một nhân viên trong tháng.
*   **Menu:** chọn nhân viên → chọn tháng.
*   **Cú pháp gõ tay:** `/tien_nga_danh_sach_cham_cong [Mã NV] [MM/YYYY]`
*   **Cách thức hoạt động:** xuất Excel gồm Ngày, Check-in, Check-out, Tăng ca, Số giờ làm, Ghi chú/Lỗi chấm công.

#### `/tien_nga_nghi_ngay_le`
*   **Mục đích:** Chấm công nghỉ lễ hưởng nguyên lương hàng loạt cho toàn bộ nhân viên của dự án.
*   **Menu:** chọn ngày **Ngày mai / Hôm nay / Hôm qua**, hoặc **Ngày khác** (bot hiện lệnh mẫu để copy).
*   **Cách thức hoạt động:**
    - Sau khi chọn ngày, bot hiển thị **danh sách nhân viên sẽ bị ảnh hưởng, có phân trang**, để kiểm tra trước.
    - Bấm **Xác nhận chấm nghỉ lễ** thì bot mới tạo bản ghi `Attendance` cho ngày đó với đủ công tiêu chuẩn. Nhân viên đã có dữ liệu chấm công ngày đó sẽ được bỏ qua.
*   **Cú pháp gõ tay:** `/tien_nga_nghi_ngay_le dd/mm/yyyy [Ghi chú]`

---

### PHÂN HỆ THU MUA & NHÀ CUNG CẤP - `custom_title == "main_supplier"` hoặc `"super_main"`

#### `/tien_nga_tao_khach_hang` (hoặc `/tien_nga_create_customer`)
*   **Mục đích:** Đăng ký một hộ nông dân/người bán mủ mới vào hệ thống.
*   **Cú pháp:** `/tien_nga_tao_khach_hang`
*   **Cách thức hoạt động:**
    - Gõ lệnh không kèm tham số: Bot hiển thị danh sách các Điểm Thu Mua để chọn.
    - Sau khi chọn điểm thu mua, bot trả về Form tạo khách hàng: Mã Điểm Thu, Tên Khách Hàng, Mã Hộ (bắt buộc, duy nhất), SĐT, Địa chỉ, Nguyên Liệu, Username TG, Nhóm Telegram, Ngân Hàng, STK, Số tiền nợ cũ, Ứng tiền cuối mùa, Ứng tiền trong tháng, Tổng công nợ, Trợ giá.
    - Người dùng điền Form gửi lại, bot kiểm tra trùng lặp Mã Hộ, lưu hồ sơ mới vào bảng `Customers`.

#### `/tien_nga_kiem_tra_khach_hang` (hoặc `/tien_nga_check_customer`)
*   **Mục đích:** Tra cứu thông tin hồ sơ và số dư công nợ của một hộ nông dân.
*   **Cú pháp:** `/tien_nga_kiem_tra_khach_hang [Mã Hộ]`
*   **Cách thức hoạt động:**
    - Tìm kiếm hộ dân trong bảng `Customers` và hiển thị chi tiết tên, số điện thoại, điểm thu mua liên kết và **Tổng công nợ hiện tại** (nợ cũ + phát sinh).

#### `/tien_nga_cap_nhat_khach_hang` (hoặc `/tien_nga_update_customer`)
*   **Mục đích:** Chỉnh sửa thông tin hồ sơ hoặc thông số tài chính của khách hàng.
*   **Cú pháp:** `/tien_nga_cap_nhat_khach_hang [Mã Hộ]`
*   **Cách thức hoạt động:**
    - Trích xuất dữ liệu cũ của khách hàng ra Form điền sẵn. Người dùng sửa đổi thông tin và gửi lại để bot lưu đè dữ liệu mới.

#### `/tien_nga_xoa_khach_hang` (hoặc `/tien_nga_delete_customer`)
*   **Mục đích:** Ngừng hợp tác hoặc ẩn khách hàng khỏi hệ thống hoạt động.
*   **Cú pháp:** `/tien_nga_xoa_khach_hang [Mã Hộ]`
*   **Cách thức hoạt động:**
    - Tra cứu khách hàng, hiển thị tin nhắn xác nhận kèm nút bấm inline.
    - Khi bấm xác nhận, thực hiện xóa mềm (chuyển `status` thành `INACTIVE`) để bảo toàn log giao dịch cũ.

#### `/tien_nga_ds_khach_hang` (hoặc `/tien_nga_list_customers`)
*   **Mục đích:** Xuất toàn bộ danh sách khách hàng và công nợ ra file Excel.
*   **Cú pháp:** `/tien_nga_ds_khach_hang`
*   **Cách thức hoạt động:**
    - Quét bảng `Customers`, kết xuất toàn bộ dữ liệu danh bạ, địa chỉ, ngân hàng, công nợ ra file Excel và gửi vào nhóm chat.

#### `/tien_nga_tao_diem_thu_mua` (hoặc `/tien_nga_create_collection_point`)
*   **Mục đích:** Tạo một điểm thu mua mủ (xưởng/đại lý trung chuyển) mới.
*   **Cú pháp:** `/tien_nga_tao_diem_thu_mua`
*   **Cách thức hoạt động:**
    - Gõ lệnh để nhận Form: Tên Điểm Thu Mua, Địa Chỉ, Mã Viết Tắt (VD: LT - Lạc Tánh), Người Quản Lý, SĐT, Ghi Chú.
    - Mã viết tắt sẽ được sử dụng để tự động sinh mã hàng hàng ngày (Ví dụ: `LT20260505`).
    - Lưu điểm thu mua mới vào bảng `CollectionPoint`.

#### `/tien_nga_danh_sach_diem_thu_mua` (hoặc `/tien_nga_list_collection_point`)
*   **Mục đích:** Xem danh sách các điểm thu mua mủ trong hệ thống.
*   **Cú pháp:** `/tien_nga_danh_sach_diem_thu_mua`
*   **Cách thức hoạt động:**
    - Liệt kê toàn bộ các xưởng/điểm thu mua đang hoạt động kèm theo Mã ID, mã viết tắt, thông tin liên hệ và người quản lý.

#### `/tien_nga_cap_nhat_diem_thu_mua` (hoặc `/tien_nga_update_collection_point`)
*   **Mục đích:** Cập nhật thông tin chi tiết của một điểm thu mua mủ.
*   **Cú pháp:** `/tien_nga_cap_nhat_diem_thu_mua` (hoặc `/tien_nga_cap_nhat_diem_thu_mua [Mã Xưởng]`)
*   **Cách thức hoạt động:**
    - Nếu không kèm mã: Bot hiển thị menu nút bấm chọn xưởng cần cập nhật.
    - Cấp Form chứa thông tin cũ, người dùng chỉnh sửa thông tin cần thay đổi và gửi lại để lưu vào DB.

#### `/tien_nga_thu_mua_hang_ngay` (hoặc `/tien_nga_daily_purchase`)
*   **Mục đích:** Ghi nhận một giao dịch cân mua mủ hàng ngày từ hộ nông dân.
*   **Cú pháp:** `/tien_nga_thu_mua_hang_ngay [Mã Hộ]`
*   **Cách thức hoạt động:**
    - Bot trả về Form nhập số liệu: Khối lượng mủ nước, Trừ bì, Số độ (DRC), Đơn giá, Tạm ứng, Ghi chú và Lưu Sổ (Có/Không).
    - Gửi lại Form: Bot tự động tính:
        - Mủ khô = (Khối lượng - Trừ bì) * Số độ / 100.
        - Thành tiền = Mủ khô * (Đơn giá + Trợ giá).
    - Lô hàng tự động được gắn mã hàng theo tiền tố xưởng và ngày (Ví dụ: `LT20260505`).
    - Lưu giao dịch vào bảng `DailyPurchases`. Nếu Lưu Sổ = `Có`, số tiền thành tiền (sau khi trừ tạm ứng) tự động được cộng dồn vào tổng công nợ của khách hàng.

#### `/tien_nga_kiem_soat_hao_hut` (hoặc `/tien_nga_control_losses`)
*   **Mục đích:** Tổng kết khối lượng mua vào trong ngày của một mã hàng để chốt số liệu làm cơ sở tính hao hụt.
*   **Cú pháp:** `/tien_nga_kiem_soat_hao_hut` — hoặc nhập nhanh `/tien_nga_kiem_soat_hao_hut [Ngày thu mua] [Ngày dự kiến hoàn thành]` (`dd/mm/yyyy`, cả hai đều tùy chọn).
*   **Cách thức hoạt động:**
    - Bot hiển thị 4 nút chọn ngày: **Hôm nay**, **Hôm qua**, **Ngày bất kỳ**, **Hủy**.
    - Sau khi chọn ngày, bot liệt kê các Điểm Thu Mua có phát sinh giao dịch trong ngày đó (kèm mã hàng của từng điểm) và nút **Tất cả** (gộp mọi điểm thành mã hàng ảo `TN{yyyymmdd}`).
    - Chọn xong, bot hiện form kiểm soát: tự động cộng dồn tất cả các phiếu cân mủ để tính tổng mủ nước, tổng mủ khô, số độ trung bình và đơn giá trung bình đầu vào.
    - **Ngày dự kiến hoàn thành:** luôn hiển thị trên mọi màn hình (để `—` nếu chưa đặt). Nút **⏳ Dự kiến hoàn thành** ở màn chọn điểm thu mua và ở form cho phép chọn nhanh +1/+2/+3/+5/+7/+10 ngày kể từ ngày thu mua, hoặc "Ngày khác" / "Xóa ngày dự kiến". Ngày này được dùng để đối chiếu với `ProductTransaction` khi xuất báo cáo hao hụt.
    - Bấm "Lưu — Sản Xuất Mủ Khô" hoặc "Lưu — Bán Mủ Nước" để chốt số liệu vào bảng `LossControls` (có hỏi ghi đè nếu đã tồn tại).

#### `/tien_nga_kiem_tra_hao_hut` (hoặc `/tien_nga_check_losses`)
*   **Mục đích:** Đối soát và tính toán lượng hao hụt mủ giữa điểm mua (đầu vào) và nhập kho thực tế (đầu ra).
*   **Cú pháp:**
    - `/tien_nga_kiem_tra_hao_hut` — hao hụt **mủ khô** theo chu kỳ (luồng nút bấm)
    - `/tien_nga_kiem_tra_hao_hut 01/05/2026 - 31/05/2026` — chỉ định giai đoạn
    - `/tien_nga_kiem_tra_hao_hut [Mã hàng]` — hao hụt **bán mủ nước** của một lô (đối chiếu `PartnerBusinesses`)
*   **Cách thức hoạt động (mủ khô, theo chu kỳ):**
    1. Chọn loại kiểm tra: **Theo ngày (Hôm nay)** / **Theo tuần (Tuần này)** / **Theo tháng (Tháng này)** / **Theo giai đoạn** / **Hủy**. Các chu kỳ đều tính đến hôm nay.
    2. Chọn **Điểm Thu Mua** có lô đến hạn trong chu kỳ, hoặc **Tất cả (TN…)**.
    3. Bot lấy các lô trong `LossControls` có `estimated_completion` nằm trong chu kỳ (bỏ lô `wet_sale`), rồi cộng lượng `Nhập` từ `ProductTransaction` trong khoảng `[ngày thu mua, ngày dự kiến hoàn thành]`.
        - Lô của một xưởng khớp đúng mã hàng.
        - Lô `TN` là tổng của các xưởng nên gộp mọi mã hàng cùng ngày thu mua, **cộng thêm** các giao dịch nhập không có mã hàng (mặc định coi là mã `TN`, gán cho lô `TN` có ngày thu mua gần nhất về trước).
    4. Hiển thị tổng hợp: Mủ khô tạm tính / Nhập kho thực tế / Tổng thành tiền / Giá TB kỳ / Chênh lệch / % hao hụt / Tiền hao hụt. Nút **Chi tiết từng lô** phân trang 8 lô, sắp theo % hao hụt giảm dần.
        - Tỷ lệ hao hụt = `100 − (Tổng nhập kho / Tổng mủ khô tạm tính) × 100` (gộp theo khối lượng, không phải trung bình cộng % của các lô)
        - Giá mua TB kỳ = `Tổng thành tiền / Tổng mủ khô tạm tính` — bình quân theo **mủ khô**, trả lời "mua bình quân bao nhiêu một Kg"
        - Giá TB phần hao hụt = `Σ(đơn giá lô × hao hụt lô) / Σ hao hụt` — bình quân theo **khối lượng hao hụt**
        - **Tiền hao hụt = `Giá TB phần hao hụt × Chênh lệch`**
    *   **Vì sao hai loại giá TB:** phần mủ mất không phân bố đều theo mủ khô, nên `Giá mua TB kỳ × Chênh lệch` chỉ là xấp xỉ — lệch đúng bằng hiệp phương sai có trọng số giữa đơn giá và tỷ lệ hao hụt của các lô, lệch có hệ thống nên cộng nhiều kỳ không tự triệt tiêu. Đổi trọng số sang khối lượng hao hụt thì đẳng thức `giá × chênh lệch = tiền` đúng tuyệt đối.
        - Ví dụ: lô 60k/Kg hao 100 Kg + lô 40k/Kg hao 200 Kg → Giá mua TB kỳ `50.000` (× 300 ra `15.000.000`, sai); Giá TB phần hao hụt `46.667` (× 300 ra `14.000.000`, đúng bằng `60k×100 + 40k×200`).
        - Khi mọi lô cùng đơn giá, hai loại giá TB trùng nhau. Kỳ không hao hụt (`ΣL = 0`) thì lấy Giá mua TB kỳ để không chia cho 0.
    5. Lô chưa đặt ngày dự kiến hoàn thành không được tính; Bot hiện cảnh báo số lượng lô bị bỏ qua.
    6. **Xác nhận hao hụt:** nút ở màn tổng hợp chốt số liệu vào bảng `loss_checks` kèm loại kỳ (`day` / `week` / `month` / `custom`), chi tiết từng lô lưu vào `loss_check_items`. Chốt lại cùng kỳ + cùng phạm vi thì Bot hỏi ghi đè. Số đã chốt **không đổi** theo dữ liệu phát sinh sau, xem lại qua `/tien_nga_thong_ke_hao_hut`.

#### `/tien_nga_thong_ke_hao_hut` (hoặc `/tien_nga_loss_statistics`)
*   **Mục đích:** Xem lại các kỳ đã xác nhận hao hụt.
*   **Cú pháp:** `/tien_nga_thong_ke_hao_hut`
*   **Cách thức hoạt động:**
    - Bot hiện 5 nút: **Ngày**, **Tuần**, **Tháng**, **Giai đoạn**, **Hủy**.
    - Chọn loại kỳ → danh sách bản chốt thuộc loại đó (mới nhất trước, phân trang 8 bản/trang), mỗi dòng hiện chu kỳ, phạm vi và % hao hụt kèm cờ 🔴/🟡/🟢.
    - Chọn một bản chốt → toàn bộ số liệu tại thời điểm chốt, kèm người chốt và thời điểm chốt; nút **Chi tiết từng lô** mở danh sách lô đã lưu trong `loss_check_items`.

#### `/tien_nga_xuat_excel_hao_hut` (hoặc `/tien_nga_export_loss_excel`)
*   **Mục đích:** Xuất file Excel 4 tab thống kê hao hụt (mủ nước / mủ khô) theo khoảng thời gian. Trước đây lệnh này mang tên `/tien_nga_thong_ke_hao_hut`.
*   **Cú pháp:** `/tien_nga_xuat_excel_hao_hut`, hoặc kèm `27/05/2026` / `01/05/2026 - 31/05/2026`.
*   **Cách thức hoạt động:** hiển thị nút chọn khoảng thời gian (Hôm nay / 7 / 14 ngày / 1 / 3 / 6 tháng / 1 năm) rồi sinh file Excel. Lọc lô theo **ngày thu mua** (`day`), khác với lệnh kiểm tra hao hụt lọc theo ngày dự kiến hoàn thành.

#### `/tien_nga_xuat_bao_cao_thu_mua` (hoặc `/tien_nga_export_daily_purchase`)
*   **Mục đích:** Trích xuất phiếu cân mủ chi tiết của một giao dịch cụ thể để gửi cho nông dân.
*   **Cú pháp:** Sử dụng bằng cách **Reply** vào tin nhắn nhập mua mủ thành công của Bot và gõ lệnh `/tien_nga_xuat_bao_cao_thu_mua`.
*   **Cách thức hoạt động:**
    - Bot bóc tách mã giao dịch từ tin nhắn được reply.
    - Tra cứu dữ liệu và định dạng thành một phiếu báo cáo chi tiết (khối lượng, độ, đơn giá, trợ giá, tạm ứng, thành tiền) dưới dạng tin nhắn hoặc hình ảnh hóa đơn đẹp mắt để gửi cho khách.

#### `/tien_nga_xuat_hoa_don_luu_so` (hoặc `/tien_nga_export_saved_bill`)
*   **Mục đích:** Xuất hóa đơn/phiếu đối soát cho các giao dịch có ghi nhận nợ/lưu sổ.
*   **Cú pháp:** Sử dụng tương tự bằng cách **Reply** vào tin nhắn giao dịch mua mủ thành công có lưu sổ.

#### `/tien_nga_xuat_hoa_don_da_tt` (hoặc `/tien_nga_export_paid_bill`)
*   **Mục đích:** Xuất hóa đơn/phiếu đối soát cho các giao dịch đã thanh toán tiền mặt ngay trong ngày.
*   **Cú pháp:** Sử dụng tương tự bằng cách **Reply** vào tin nhắn giao dịch đã thanh toán tiền mặt thành công.

#### `/tien_nga_truy_xuat_tt_thu_mua` (hoặc `/tien_nga_export_info`)
*   **Mục đích:** Xuất bảng kê chi tiết toàn bộ lịch sử bán mủ của một hộ nông dân trong một khoảng thời gian ra file Excel.
*   **Cú pháp:** `/tien_nga_truy_xuat_tt_thu_mua [Mã Hộ] [Từ ngày] - [Đến ngày]`
*   **Cách thức hoạt động:**
    - Quét bảng `DailyPurchases` lọc theo Mã Hộ và khoảng thời gian.
    - Đổ dữ liệu ra file Excel có dòng tổng cộng khối lượng mủ nước, mủ khô, số tiền và gửi đính kèm.

#### `/tien_nga_bieu_do_thu_mua`
*   **Mục đích:** Vẽ biểu đồ trực quan hóa sản lượng thu mua mủ.
*   **Cú pháp:** `/tien_nga_bieu_do_thu_mua`
*   **Cách thức hoạt động:**
    - Bot truy vấn sản lượng mủ thu được hàng ngày trong tháng.
    - Sử dụng thư viện đồ họa vẽ biểu đồ cột/đường trực quan và gửi dưới dạng file ảnh `.png` lên nhóm.

#### `/tien_nga_bao_cao_da_thanh_toan` (hoặc `/tien_nga_paid_amount_report`)
*   **Mục đích:** Thống kê các giao dịch mua mủ thanh toán ngay (tiền mặt) trong khoảng thời gian để kế toán xuất quỹ.
*   **Cú pháp:** `/tien_nga_bao_cao_da_thanh_toan`
*   **Cách thức hoạt động:**
    - Truy vấn các giao dịch thu mua có trường nợ lưu sổ bằng 0 (`saved_amount == 0`) trong khoảng thời gian đã chọn và lập bảng tổng hợp báo cáo.

#### `/tien_nga_xuat_bao_cao_tong_hop` (hoặc `/tien_nga_export_summary`)
*   **Mục đích:** Báo cáo quản trị tổng hợp hoạt động thu mua mủ của toàn bộ các xưởng trực thuộc dự án.
*   **Cú pháp:** `/tien_nga_xuat_bao_cao_tong_hop` hoặc `/tien_nga_xuat_bao_cao_tong_hop [Từ ngày] - [Đến ngày]`
*   **Cách thức hoạt động:**
    - Tổng hợp toàn bộ dữ liệu thu mua trong khoảng thời gian, phân chia chi tiết ra các sheet Excel riêng biệt cho từng xưởng/điểm thu mua và một sheet tổng hợp, gửi file đính kèm.

#### `/tien_nga_bao_cao_luu_so` (hoặc `/tien_nga_save_amount_report`)
*   **Mục đích:** Thống kê danh sách các giao dịch mua mủ được ghi nhận nợ/lưu sổ (`saved_amount > 0`).

#### `/tien_nga_thong_ke_cong_no`
*   **Mục đích:** Xuất báo cáo tổng quan tình hình công nợ của toàn bộ hộ nông dân.

#### `/tien_nga_thu_mua_nguyen_lieu` (hoặc `/tien_nga_material_purchase`)
*   **Mục đích:** Ghi nhận mua sắm vật tư, nguyên liệu phục vụ sản xuất (như Acid, Củi trấu...).
*   **Cú pháp:** `/tien_nga_thu_mua_nguyen_lieu`
*   **Cách thức hoạt động:**
    - Hiển thị menu chọn kho nhập nguyên liệu.
    - Trả về Form điền thông tin: Mã khách hàng, khối lượng, đơn giá, tạm ứng, công nợ.
    - Tự động cộng số lượng nhập vào thẻ kho tồn kho tương ứng và ghi nhận công nợ với nhà cung cấp.

#### `/tien_nga_xuat_kho`
*   **Mục đích:** Ghi nhận xuất nguyên liệu ra khỏi kho để phục vụ sản xuất.
*   **Cú pháp:** `/tien_nga_xuat_kho`
*   **Cách thức hoạt động:**
    - Chọn kho và điền Form khối lượng xuất.
    - Bot kiểm tra nếu khối lượng xuất vượt quá tồn kho hiện tại sẽ chặn giao dịch. Nếu hợp lệ, trừ trực tiếp tồn kho và ghi log xuất kho.

#### `/tien_nga_ung_tien` (hoặc `/tien_nga_cash_advance`)
*   **Mục đích:** Ghi nhận một khoản tạm ứng trước tiền bán mủ cho hộ dân/khách hàng.
*   **Cú pháp:** `/tien_nga_ung_tien [Mã Hộ] [Số tiền ứng]`
*   **Hai loại ứng tiền:** *Ứng tiền Cuối mùa* (cột `cash_advance`) và *Ứng tiền Trong tháng* (cột `cash_advance_monthly`). Hai loại dùng chung một hạn mức.
*   **Cách thức hoạt động:**
    - Sau khi nhập lệnh, bot hiện màn xác nhận kèm 3 nút: "Ứng tiền Cuối mùa", "Ứng tiền Trong tháng" và "Hủy". Chưa chọn loại thì chưa ghi nhận gì.
    - Kiểm tra hạn mức ứng tiền: Số tiền ứng tối đa được tính dựa trên tỷ lệ % (MaxCashAdvance trong config) tổng số tiền bán mủ của hộ dân ở mùa vụ trước. Số đã ứng dùng để so hạn mức là **tổng cả hai loại**.
    - Nếu vượt quá hạn mức, bot chặn giao dịch và yêu cầu Owner duyệt vượt ngưỡng (gõ `/confirmed` reply tin nhắn cảnh báo). Tin cảnh báo có dòng "Loại ứng" để `/confirmed` cộng đúng cột.
    - Nếu hợp lệ hoặc được Owner duyệt, bot cộng tiền ứng vào đúng loại đã chọn, ghi một dòng vào bảng `cash_advance_logs`, và gửi thông báo ghi nhận ứng tiền xuống nhóm thành viên của hộ dân.

#### `/tien_nga_khau_tru_tien_ung`
*   **Mục đích:** Thực hiện khấu trừ số tiền đã ứng trước đó vào tiền bán mủ/tiền giao dịch.
*   **Cú pháp:** `/tien_nga_khau_tru_tien_ung [Mã Hộ] [Số tiền khấu trừ]`
*   **Cách thức hoạt động:**
    - Bot kiểm tra số dư ứng của từng loại. Màn xác nhận chỉ hiện nút của loại còn đủ số dư: "Khấu trừ Ứng Cuối mùa" / "Khấu trừ Ứng Trong tháng", kèm nút "Hủy".
    - Nếu tổng đủ nhưng không loại nào một mình đủ, bot báo số dư từng loại và yêu cầu khấu trừ thành nhiều lần.
    - Khi bấm xác nhận, trừ vào đúng loại đã chọn, ghi một dòng `DEDUCT` vào bảng `cash_advance_logs` và gửi thông báo biến động số dư xuống nhóm member của hộ dân.

#### `/tien_nga_danh_sach_ung_tien` (hoặc `/tien_nga_ds_ung_tien`)
*   **Mục đích:** Xuất báo cáo danh sách toàn bộ các khoản ứng tiền của hộ dân/khách hàng ra file Excel.
*   **Cú pháp:** `/tien_nga_danh_sach_ung_tien`
*   **Cách thức hoạt động:**
    - Lấy các hộ còn tiền ứng ở bất kỳ loại nào, tổng hợp mã hộ, tên khách hàng, Ứng Tiền Cuối Mùa, Ứng Tiền Trong Tháng, Tổng Ứng và xuất ra file Excel đính kèm (mỗi tab là một điểm thu mua, có dòng tổng cộng).

#### `/tien_nga_lich_su_ung_tien` (hoặc `/tien_nga_ls_ung_tien`)
*   **Mục đích:** Xem nhật ký biến động tiền ứng (ứng thêm / khấu trừ) của một hộ dân.
*   **Cú pháp:** `/tien_nga_lich_su_ung_tien` hoặc `/tien_nga_lich_su_ung_tien [Mã Hộ]`
*   **Cách thức hoạt động:**
    - Không truyền tham số thì mở luồng nút bấm: Điểm Thu Mua → Hộ dân → Nhật ký.
    - Hiển thị số dư hiện tại của hai loại ứng và 20 giao dịch gần nhất: loại ứng, số tiền, số dư trước → sau, người thực hiện, và người duyệt nếu là khoản ứng vượt hạn mức.
    - Nhật ký chỉ có dữ liệu từ thời điểm hệ thống tách hai loại ứng tiền; các khoản ứng trước đó không có bản ghi.

---

### PHÂN HỆ QUẢN LÝ ĐỐI TÁC (Partner) - `custom_title == "main_partner"` hoặc `"super_main"`

> **Từ 09/08/2026:** tất cả lệnh dưới đây đều chọn được bằng **nút bấm**. Gõ lệnh không kèm tham số để bot hiện danh sách; vẫn hỗ trợ gõ thẳng mã như trước. Các lệnh này chỉ dùng trong **nhóm main** — nhóm member xem mục "PHÂN HỆ ĐỐI TÁC (Member Partner)".

#### `/tien_nga_tao_doi_tac` (hoặc `/tien_nga_create_partner`)
*   **Mục đích:** Tạo hồ sơ quản lý đối tác thương mại B2B mới (doanh nghiệp thu mua thành phẩm, xưởng đối tác...).
*   **Cú pháp:** `/tien_nga_tao_doi_tac`
*   **Cách thức hoạt động:**
    - Bot hiện danh sách các mã đối tác **đã dùng** để tránh đặt trùng, kèm nút **Thêm mới đối tác**.
    - Bấm nút để nhận Form điền: Mã đối tác (VD: DT001, bắt buộc, duy nhất), Tên công ty, Công nợ, Username TG, Nhóm Telegram, Ngân hàng, Số TK.
    - Bot kiểm tra trùng mã và tạo mới đối tác.

#### `/tien_nga_cap_nhat_doi_tac` (hoặc `/tien_nga_update_partner`)
*   **Mục đích:** Chỉnh sửa thông tin liên hệ của đối tác đã tồn tại.
*   **Cú pháp:** `/tien_nga_cap_nhat_doi_tac` (chọn bằng nút) hoặc `/tien_nga_cap_nhat_doi_tac [Mã Đối Tác]`
*   **Cách thức hoạt động:** Chọn đối tác từ danh sách → bot hiện form đã điền sẵn dữ liệu hiện tại, chỉ cần sửa rồi gửi lại. Danh sách gồm **cả đối tác đang khóa**, để còn đường mở lại.

#### `/tien_nga_xoa_doi_tac` (hoặc `/tien_nga_delete_partner`)
*   **Mục đích:** Ngừng hợp tác với đối tác (Soft Delete).
*   **Cú pháp:** `/tien_nga_xoa_doi_tac` (chọn bằng nút) hoặc `/tien_nga_xoa_doi_tac [Mã Đối Tác]`
*   **Cách thức hoạt động:** Chọn đối tác → bot hiện **màn xác nhận** kèm cảnh báo nếu công nợ khác 0 → bấm *Xác nhận xóa* mới thực sự chuyển trạng thái DELETED.

#### `/tien_nga_ds_doi_tac` (hoặc `/tien_nga_list_partner`)
*   **Mục đích:** Xem danh sách đối tác và mở nhanh mọi thao tác trên một đối tác.
*   **Cú pháp:** `/tien_nga_ds_doi_tac`
*   **Cách thức hoạt động:**
    - Danh sách 10 đối tác/trang. Bấm chọn một đối tác (hiện dấu ✅) sẽ mở thêm 4 nút: **Thông tin chi tiết**, **Cập nhật thông tin**, **Xóa đối tác**, **Thực hiện giao dịch**.
    - Nút **Xuất Excel danh sách** luôn hiện, xuất toàn bộ đối tác kèm công nợ.

#### `/tien_nga_giao_dich_doi_tac` (hoặc `/tien_nga_partner_transaction`)
*   **Mục đích:** Ghi nhận đơn hàng mua bán mủ thành phẩm hoặc vật tư lớn với Đối tác.
*   **Cú pháp:** `/tien_nga_giao_dich_doi_tac` (chọn bằng nút) hoặc `/tien_nga_giao_dich_doi_tac [Mã Đối Tác]`
*   **Cách thức hoạt động:**
    - Chọn đối tác → chọn Nhập/Xuất → chọn loại sản phẩm → điền Form: khối lượng, đơn giá, trạng thái thanh toán (Lưu sổ/Thanh toán ngay).
    - Tính toán `Thành tiền = Khối lượng * Đơn giá`. Lưu vào bảng `PartnerTransactions`. Nếu là Lưu sổ, tự động cộng/trừ số tiền tương ứng vào công nợ `total_debt` của đối tác.

#### `/tien_nga_kiem_tra_giao_dich` (hoặc `/tien_nga_check_transaction`)
*   **Mục đích:** Tra cứu lịch sử các đơn hàng mua/bán với đối tác.
*   **Cú pháp:** `/tien_nga_kiem_tra_giao_dich` (chọn bằng nút) hoặc `/tien_nga_kiem_tra_giao_dich [Mã Đối Tác] [dd/mm/yyyy] [dd/mm/yyyy]`
*   **Ghi chú:** Lọc theo khoảng ngày chỉ làm được bằng cách gõ tay; chọn bằng nút luôn tra toàn bộ thời gian.

#### `/tien_nga_kiem_tra_cong_no` (hoặc `/tien_nga_check_debt`)
*   **Mục đích:** Xem nhanh số dư công nợ hiện tại của Đối tác, Khách hàng, Nhân sự hoặc Hộ dân.
*   **Cú pháp:** `/tien_nga_kiem_tra_cong_no` (chọn bằng nút) hoặc `/tien_nga_kiem_tra_cong_no [Mã]`
*   **Cách thức hoạt động:**
    - Màn 1: chọn loại đối tượng (Đối tác / Hộ dân / Khách hàng / Nhân sự).
    - Màn 2: chọn đối tượng. Riêng **Khách hàng** có thêm bước lọc theo Điểm Thu Mua trước, vì toàn hệ thống có hơn 500 khách hàng.
    - Nhân sự chỉ hiện người thuộc **đúng dự án** của nhóm đang gõ lệnh.

#### `/tien_nga_thanh_toan_cong_no` (hoặc `/tien_nga_payment_of_debt`)
*   **Mục đích:** Ghi nhận chuyển khoản hoặc chi tiền mặt để thanh toán cấn trừ công nợ.
*   **Cú pháp:** `/tien_nga_thanh_toan_cong_no` (chọn bằng nút) hoặc `/tien_nga_thanh_toan_cong_no [Mã] [Số Tiền]`
*   **Cách thức hoạt động:**
    - Chọn loại đối tượng → chọn đối tượng → bot hiện sẵn dòng lệnh đã điền mã, chỉ cần thay `[Số Tiền]` rồi gửi lại.
    - Sau đó chọn **Thu Công Nợ** / **Trả Công Nợ**. Bot cập nhật số dư công nợ mới và lưu lịch sử giao dịch.
*   **Hỗ trợ:** Đối tác, Khách hàng, Nhân sự, Hộ dân. Dùng được ở cả dự án Tiến Nga lẫn Thu Hoạch.

#### `/tien_nga_yeu_cau_thu_chi`
*   **Mục đích:** Tạo phiếu yêu cầu thu/chi tiền mặt hoặc chuyển khoản cho đối tác đưa sang bộ phận tài chính duyệt.

#### `/tien_nga_bao_cao_doi_tac`
*   **Mục đích:** Xuất Excel sao kê toàn bộ lịch sử biến động tài chính của đối tác trong khoảng thời gian phục vụ đối soát công nợ cuối tháng.
*   **Cú pháp:** `/tien_nga_bao_cao_doi_tac [Mã Đối Tác] [Từ ngày-Đến ngày]`

---

### PHÂN HỆ QUẢN LÝ CỔ ĐÔNG & QUỸ ĐẦU TƯ - `custom_title == "main_shareholder"` hoặc `"super_main"`

#### `/tien_nga_tao_dau_tu` (hoặc `/tien_nga_create_investment`)
*   **Mục đích:** Tạo quỹ đầu tư mới. Hỗ trợ quỹ phân cấp (Quỹ Main - Quỹ cha và Quỹ Member - Quỹ con).
*   **Cú pháp:** `/tien_nga_tao_dau_tu`
*   **Cách thức hoạt động:**
    - Quản lý chọn loại quỹ muốn tạo (Main hoặc Member). Đối với Quỹ Member, phải chọn một Quỹ Main đang hoạt động làm quỹ cha.
    - Điền Form: Mã Đầu Tư, Tên Đầu Tư, Ngày Bắt Đầu. Vốn ban đầu mặc định là 0 VNĐ.
    - Lưu vào DB ở trạng thái `ACTIVE`.

#### `/tien_nga_kiem_tra_quy_dau_tu`
*   **Mục đích:** Tra cứu tình hình tài chính (Vốn, tổng thu, tổng chi, lợi nhuận) và danh sách cổ đông của các Quỹ Đầu Tư.
*   **Cú pháp:** `/tien_nga_kiem_tra_quy_dau_tu`
*   **Cách thức hoạt động:**
    - Bot hiển thị danh sách các Quỹ Main. Chọn Quỹ Main sẽ hiện tiếp các Quỹ Member con trực thuộc.
    - Báo cáo hiển thị rõ: Vốn ban đầu, Tổng Thu, Tổng Chi, Lợi nhuận. Có nút bấm phụ để hiển thị danh sách cổ đông góp vốn và tỷ lệ % cổ phần.

#### `/tien_nga_tao_co_dong` (hoặc `/tien_nga_create_shareholder`)
*   **Mục đích:** Ghi nhận một khoản góp vốn mới của cổ đông (Tạo mới hoặc cộng dồn vốn).
*   **Cú pháp:** `/tien_nga_tao_co_dong`
*   **Cách thức hoạt động:**
    - Chọn Quỹ Main cần góp vốn, điền Form: Mã Cổ Đông, Tên, Số tiền đầu tư, Ngày bắt đầu.
    - Nếu Mã Cổ Đông đã có: Cộng dồn vốn mới vào vốn cũ. Nếu chưa có: Tạo cổ đông mới.
    - Khi bấm xác nhận, hệ thống tự động tạo một phiếu Thu (Daily Payment) ở trạng thái `APPROVED` để cộng vốn trực tiếp vào Quỹ Đầu Tư.

#### `/tien_nga_chia_co_tuc` (hoặc `/tien_nga_dividend_distribution`)
*   **Mục đích:** Tính toán và phân bổ lợi nhuận tự động cho các cổ đông theo tỷ lệ góp vốn.
*   **Cú pháp:** `/tien_nga_chia_co_tuc`
*   **Cách thức hoạt động:**
    - Chọn Quỹ Main cần chia cổ tức. Bot quét và gom toàn bộ dữ liệu tài chính của tất cả các Quỹ Member con trực thuộc.
    - Lợi nhuận chia = Tổng Thu - Tổng Chi - Tổng Vốn Góp.
    - Phân bổ số tiền cổ tức nhận được cho từng cổ đông dựa trên tỷ lệ % cổ phần nắm giữ và hiển thị bảng chi tiết để quản lý duyệt.

#### `/tien_nga_thanh_toan_co_dong`
*   **Mục đích:** Hoàn trả tiền góp vốn và phân chia lợi nhuận/lỗ cho cổ đông khi họ muốn rút vốn hoặc thanh lý quỹ.
*   **Cú pháp:** `/tien_nga_thanh_toan_co_dong`

#### `/tien_nga_lich_su_gd` (hoặc `/tien_nga_shareholder_history`)
*   **Mục đích:** Trích xuất báo cáo toàn bộ các giao dịch tài chính (góp vốn, nhận cổ tức) của một cổ đông trong khoảng thời gian.
*   **Cú pháp:** `/tien_nga_lich_su_gd [Mã Cổ Đông] [Từ ngày - Đến ngày]`

---

### PHÂN HỆ QUẢN LÝ TÀI CHÍNH - `custom_title == "main_finance"` hoặc `"super_main"`

#### `/tien_nga_xn_thanh_toan_cong_no`
*   **Mục đích:** Duyệt và cấn trừ công nợ đồng loạt cho một nhóm đối tượng (Nhân viên hoặc Nhà cung cấp).
*   **Cú pháp:** `/tien_nga_xn_thanh_toan_cong_no`
*   **Cách thức hoạt động:**
    - Quản lý chọn đối tượng cần xử lý (Nhân sự / Nhà cung cấp).
    - Bot hiển thị danh sách tất cả cá nhân/đơn vị kèm số dư công nợ hiện tại và ô checkbox ảo.
    - Tích chọn những người đã thanh toán xong và bấm "Xác nhận thanh toán" để cấn trừ hàng loạt trong DB.

#### `/confirm_payment`
*   **Mục đích:** Phê duyệt một phiếu yêu cầu chi tiêu được đề xuất (Lớp bảo mật cuối, chỉ Owner được dùng).
*   **Cú pháp:** Sử dụng bằng cách **Reply** vào tin nhắn yêu cầu duyệt phiếu của Bot và gõ lệnh `/confirm_payment`.
*   **Cách thức hoạt động:**
    - Trích xuất mã phiếu yêu cầu từ tin nhắn được reply.
    - Chuyển trạng thái phiếu từ `PENDING` sang `APPROVED`.
    - Cộng tiền chi vào `total_expense` của Quỹ Đầu Tư liên quan, trừ vào `profit` của Quỹ và đồng bộ lên Quỹ Main.

#### `/deny_payment`
*   **Mục đích:** Từ chối/bác bỏ phiếu yêu cầu chi tiêu không hợp lệ.
*   **Cú pháp:** Sử dụng tương tự bằng cách **Reply** vào tin nhắn yêu cầu duyệt phiếu và gõ lệnh `/deny_payment`.

#### `/tien_nga_xuat_bao_cao_thu_chi`
*   **Mục đích:** Tải xuống file Excel bảng kê chi tiết toàn bộ các phiếu thu/chi đã được duyệt trong một khoảng thời gian của một Quỹ.
*   **Cú pháp:** `/tien_nga_xuat_bao_cao_thu_chi` hoặc `/tien_nga_xuat_bao_cao_thu_chi [Từ ngày - Đến ngày]`

#### `/tien_nga_xuat_bc_tong_hop`
*   **Mục đích:** Xuất báo cáo tài chính vĩ mô dạng Excel thể hiện lãi/lỗ của toàn bộ hệ thống các Quỹ Member.
*   **Cú pháp:** `/tien_nga_xuat_bc_tong_hop [Tháng/Năm]` hoặc `[Năm]`

#### `/tien_nga_can_bang_ke_toan`
*   **Mục đích:** Xuất bảng cân đối kế toán tài chính của dự án.

---

### PHÂN HỆ QUẢN LÝ KHO - `custom_title == "main_inventory"` hoặc `"super_main"`

#### `/tien_nga_tao_kho` (hoặc `/tien_nga_create_inventory`)
*   **Mục đích:** Tạo một kho chứa nguyên liệu mới (Acid, củi, mủ...) trên hệ thống.
*   **Cú pháp:** `/tien_nga_tao_kho`
*   **Cách thức hoạt động:**
    - Nhận Form: Tên Nguyên Liệu, Tên Kho, Số Lượng Ban Đầu, Địa Chỉ, Sức Chứa.
    - Lưu thông tin kho vào bảng `Inventory`.

#### `/tien_nga_danh_sach_kho` (hoặc `/tien_nga_list_inventory`)
*   **Mục đích:** Liệt kê toàn bộ các kho hiện có kèm theo lượng tồn kho hiện tại và địa chỉ.
*   **Cú pháp:** `/tien_nga_danh_sach_kho`

#### `/tien_nga_kiem_tra_kho` (hoặc `/tien_nga_check_inventory`)
*   **Mục đích:** Xem chi tiết và tính toán tỷ lệ % diện tích sử dụng của một kho cụ thể.
*   **Cú pháp:** `/tien_nga_kiem_tra_kho`
*   **Cách thức hoạt động:**
    - Bot hiển thị danh sách các kho dưới dạng nút bấm inline.
    - Khi chọn kho, bot tính toán % sử dụng = (Tồn kho / Sức chứa) * 100 và gửi báo cáo chi tiết.

#### `/tien_nga_cap_nhat_ton_kho`
*   **Mục đích:** Chỉnh sửa thông số kho hoặc điều chỉnh trực tiếp số lượng tồn kho khi kiểm kê thực tế.
*   **Cú pháp:** `/tien_nga_cap_nhat_ton_kho`

---

### PHÂN HỆ QUẢN LÝ SẢN PHẨM - `custom_title == "main_product"` hoặc `"super_main"`

#### `/tien_nga_giao_dich_san_pham` (hoặc `/tien_nga_product_transaction`)
*   **Mục đích:** Ghi nhận nghiệp vụ Nhập/Xuất sản phẩm khỏi kho, tự động tính tiền, công nợ và cập nhật tồn kho.
*   **Cú pháp:** `/tien_nga_giao_dich_san_pham`
*   **Cách thức hoạt động:**
    - Bot hiển thị danh sách kho để chọn, sau đó yêu cầu chọn loại giao dịch (Nhập Kho / Xuất Kho).
    - Cấp Form điền: Mã Hàng, Mã Khách Hàng, Số Lượng (Kg), Đơn Giá và Ghi Chú.
    - Đối với giao dịch "Xuất", bot kiểm tra nếu vượt quá tồn kho thực tế sẽ chặn. Nếu hợp lệ, bot tự động cộng/trừ số lượng tồn kho và cập nhật số dư công nợ của khách hàng trong bảng `Customers`.

#### `/tien_nga_xuat_bao_cao_san_pham` (hoặc `/tien_nga_export_product_report`)
*   **Mục đích:** Tổng hợp và xuất báo cáo tình hình giao dịch sản phẩm trong khoảng thời gian ra Excel.
*   **Cú pháp:** `/tien_nga_xuat_bao_cao_san_pham` hoặc `/tien_nga_xuat_bao_cao_san_pham [Từ ngày - Đến ngày]`

---
---

## 2. DÀNH CHO THÀNH VIÊN (Tiến Nga Member)

Các lệnh dưới đây được áp dụng khi người dùng ở trong các nhóm chat thành viên trực thuộc có role là `member` và sở hữu các custom title tương ứng.

### PHÂN HỆ NHÂN VIÊN (Member HR) - `custom_title == "member_hr"`

#### `/tien_nga_cham_cong` (hoặc `/tien_nga_check_in`)
*   **Mục đích:** Nhân viên thực hiện chấm công bắt đầu ca làm việc hàng ngày.
*   **Cú pháp:** `/tien_nga_cham_cong`
*   **Cách thức hoạt động:**
    - Bot xác thực tài khoản Telegram có khớp với hồ sơ nhân viên trong DB.
    - Kiểm tra giờ chấm công thực tế: Chỉ cho phép chấm công trong vòng 30 phút trước hoặc sau giờ vào ca quy định.
    - So sánh thời gian thực tế để ghi nhận trạng thái: đúng giờ, đi trễ, hoặc đi sớm vào bảng `Attendance` và thông báo kết quả.

#### `/tien_nga_tan_ca` (hoặc `/tien_nga_check_out`)
*   **Mục đích:** Ghi nhận thời gian kết thúc ca làm việc và tính toán giờ tăng ca.
*   **Cú pháp:** `/tien_nga_tan_ca`
*   **Cách thức hoạt động:**
    - Kiểm tra nhân viên đã check-in ngày hôm đó chưa. Chỉ cho phép check-out sau giờ tan ca quy định đến 23:59 cùng ngày.
    - Nếu tan ca muộn hơn giờ quy định, số giờ thừa tự động được ghi nhận là giờ tăng ca (overtime). Tính toán tổng số giờ làm việc thực tế và cập nhật vào DB.

#### `/tien_nga_xin_nghi_phep` (hoặc `/tien_nga_request_leave`)
*   **Mục đích:** Nhân viên gửi đơn xin nghỉ phép trực tuyến.
*   **Cú pháp:** `/tien_nga_xin_nghi_phep`
*   **Cách thức hoạt động:**
    - Gõ lệnh để nhận Form điền: Thời gian nghỉ, Loại nghỉ (phép năm, không lương, ốm...), Người duyệt, Người hỗ trợ, Lý do. Hiển thị số ngày phép năm còn lại.
    - Điền Form gửi lại: Bot kiểm tra số ngày phép còn lại. Nếu hợp lệ, bot gửi đơn xin nghỉ phép vào nhóm của Quản lý Nhân sự (MAIN_HR) kèm nút bấm duyệt/từ chối.
    - Nếu được duyệt, hệ thống tự động tạo bản ghi chấm công nghỉ phép cho các ngày đó và trừ vào quỹ phép năm của nhân viên.

#### `/tien_nga_dang_ky_tang_ca` (hoặc `/tien_nga_request_overtime`)
*   **Mục đích:** Nhân viên gửi đơn đề xuất làm thêm giờ (tăng ca).
*   **Cú pháp:** `/tien_nga_dang_ky_tang_ca`
*   **Cách thức hoạt động:**
    - Nhận Form điền: Ngày tăng ca, Khung giờ tăng ca (Ví dụ: 18:00 - 21:00), Người duyệt, Lý do.
    - Điền Form gửi lại: Đẩy yêu cầu duyệt sang nhóm Quản lý. Nếu được duyệt, hệ thống tự động cập nhật giờ tăng ca vào bản ghi chấm công của ngày tương ứng.

#### `/tien_nga_xem_cham_cong` (hoặc `/tien_nga_list_check_in`)
*   **Mục đích:** Nhân viên tự kiểm tra lịch sử chấm công và số giờ làm việc của mình trong tháng.
*   **Cú pháp:** `/tien_nga_xem_cham_cong` (hoặc `/tien_nga_xem_cham_cong [Tháng/Năm]`)
*   **Cách thức hoạt động:**
    - Bot truy xuất toàn bộ lịch sử chấm công của nhân viên trong tháng được chỉ định và vẽ thành bảng biểu hình ảnh trực quan (.png) gồm: Ngày, giờ vào, giờ ra, tăng ca, tổng giờ làm, ghi chú và gửi vào tin nhắn chat.

#### `/tien_nga_xem_nghi_phep` (hoặc `/tien_nga_list_request_leave`)
*   **Mục đích:** Xem danh sách các ngày đã nghỉ phép trong tháng và quỹ phép năm còn lại.
*   **Cú pháp:** `/tien_nga_xem_nghi_phep` (hoặc `/tien_nga_xem_nghi_phep [Tháng/Năm]`)

#### `/tien_nga_xem_cong_viec` (hoặc `/tien_nga_check_tasks`)
*   **Mục đích:** Nhân viên kiểm tra và cập nhật tiến độ các công việc được giao.
*   **Cú pháp:** `/tien_nga_xem_cong_viec`
*   **Cách thức hoạt động:**
    - Bot liệt kê các công việc (Task) được giao cho nhân viên dưới dạng nút bấm inline kèm nhãn trạng thái (PENDING, IN_PROGRESS, COMPLETED).
    - Nhân viên có thể bấm vào công việc để xem chi tiết và sử dụng nút bấm để tự cập nhật trạng thái tiến độ công việc sang `IN_PROGRESS` hoặc báo cáo hoàn thành `COMPLETED`.

#### `/tien_nga_cap_nhat_cong` (hoặc `/tien_nga_request_attendance_update`)
*   **Mục đích:** Gửi yêu cầu giải trình cập nhật/bổ sung chấm công khi bị quên check-in/out hoặc sai lệch giờ giấc.
*   **Cú pháp:** `/tien_nga_cap_nhat_cong`

---

### PHÂN HỆ CỔ ĐÔNG (Member Shareholder) - `custom_title == "member_shareholder"`

#### `/tien_nga_kiem_tra_quy_dau_tu`
*   **Mục đích:** Cổ đông tự kiểm tra tình hình tài chính của các quỹ đầu tư mà mình tham gia góp vốn.
*   **Cú pháp:** `/tien_nga_kiem_tra_quy_dau_tu`
*   **Cách thức hoạt động:**
    - Bot tự động lọc và chỉ hiển thị danh sách các quỹ mà cổ đông thuộc nhóm chat đó có góp vốn.
    - Cổ đông có thể bấm vào quỹ cụ thể để xem báo cáo nhanh về Vốn, thu, chi và lợi nhuận tích lũy.

#### `/tien_nga_lich_su_gd`
*   **Mục đích:** Xem lịch sử các giao dịch tài chính (góp vốn, chia cổ tức) của cá nhân/nhóm cổ đông.
*   **Cú pháp:** `/tien_nga_lich_su_gd [Mã Cổ Đông]`

---

### PHÂN HỆ ĐỐI TÁC (Member Partner) - `custom_title == "member_partner"`

> **Đổi tên lệnh từ 09/08/2026.** Hai lệnh cũ `/tien_nga_kiem_tra_giao_dich` và `/tien_nga_kiem_tra_cong_no` nay **chỉ dùng ở nhóm main**. Nhóm member dùng hai lệnh `tt` dưới đây. Gõ lệnh cũ trong nhóm member, bot sẽ báo lỗi kèm tên lệnh mới.
>
> Lệnh member **không có danh sách để chọn** — mỗi nhóm chỉ xem được đối tượng gắn với chính nhóm mình qua trường *Nhóm Telegram*.

#### `/tien_nga_kiem_tra_tt_giao_dich` (hoặc `/tien_nga_member_check_transaction`)
*   **Mục đích:** Đối tác tự xem lịch sử giao dịch mua bán hàng hóa của mình với Tiến Nga.
*   **Cú pháp:** `/tien_nga_kiem_tra_tt_giao_dich` hoặc `/tien_nga_kiem_tra_tt_giao_dich [dd/mm/yyyy] [dd/mm/yyyy]`
*   **Cách thức hoạt động:** Bot tự nhận ra đối tác của nhóm rồi hiện nút Nhập / Xuất. Nhóm chưa được gắn đối tác nào thì bot báo để liên hệ quản trị viên.

#### `/tien_nga_kiem_tra_tt_cong_no` (hoặc `/tien_nga_member_check_debt`)
*   **Mục đích:** Tự kiểm tra số dư công nợ hiện tại của nhóm mình với Tiến Nga.
*   **Cú pháp:** `/tien_nga_kiem_tra_tt_cong_no`
*   **Cách thức hoạt động:** Bot tra trường *Nhóm Telegram* trên cả 4 bảng Đối tác / Hộ dân / Khách hàng / Nhân sự nên **nhóm member khách hàng, nhân sự và hộ dân cũng dùng được lệnh này**. Nếu một nhóm gắn với nhiều đối tượng, bot hiện nút để chọn.

#### `/tien_nga_doi_tac_thanh_toan`
*   **Mục đích:** Gửi yêu cầu/đề xuất thanh toán công nợ hoặc thu chi tiền sang nhóm Quản lý.
*   **Cú pháp:** `/tien_nga_doi_tac_thanh_toan`

---

### PHÂN HỆ NHÀ CUNG CẤP / THU MUA - `custom_title == "member_supplier"`

#### `/tien_nga_kiem_tra_khach_hang`
*   **Mục đích:** Hộ nông dân tự kiểm tra thông tin tài khoản và tổng công nợ của mình.
*   **Cú pháp:** `/tien_nga_kiem_tra_khach_hang [Mã Hộ]`

#### `/tien_nga_xuat_bao_cao_thu_mua`
*   **Mục đích:** Hộ nông dân xuất phiếu cân mủ chi tiết của một giao dịch cụ thể để đối soát số liệu.

#### `/tien_nga_xuat_hoa_don_luu_so`
*   **Mục đích:** Hộ nông dân xuất hóa đơn của các giao dịch ghi nợ/lưu sổ.

#### `/tien_nga_xuat_hoa_don_da_tt`
*   **Mục đích:** Hộ nông dân xuất hóa đơn của các giao dịch đã thanh toán tiền mặt thành công.
