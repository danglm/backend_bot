from enum import Enum, IntFlag

class UserType(IntFlag):
    OWNER = 1
    ADMIN = 2
    MEMBER = 4
    STAFF = 8
    DRIVER = 16
    CUSTOMER = 32
    JANITOR = 64


class CustomTitle(str, Enum):
    # Tiến Nga Projects
    SUPER_MAIN = "super_main"
    MAIN_SUPPLIER = "main_supplier"           #Nhà cung cấp
    MEMBER_SUPPLIER = "member_supplier"       #Nhà cung cấp
    MAIN_SALES = "main_sales"               #Kinh doanh
    MEMBER_SALES = "member_sales"           #Kinh doanh
    MAIN_HR = "main_hr"                  #Nhân sự
    MEMBER_HR = "member_hr"              #Nhân sự
    MAIN_FINANCE = "main_finance"        #Tài chính
    MEMBER_FINANCE = "member_finance"    #Tài chính
    MAIN_PRODUCT = "main_product"             #Thành phẩm
    MEMBER_PRODUCT = "member_product"         #Thành phẩm
    MAIN_PARTNER = "main_partner"             #Đối tác
    MEMBER_PARTNER = "member_partner"         #Đối tác
    
    # Other Projects
    MAIN_DEVICE = "main_device"       #Thiết bị
    MEMBER_DEVICE = "member_device"   #Thiết bị
    MAIN_VEHICLE = "main_vehicle"     #Phương tiện
    MEMBER_VEHICLE = "member_vehicle" #Phương tiện
    MAIN_IMAGE = "main_image"         #Hình ảnh, giấy tờ
    MEMBER_IMAGE = "member_image"     #Hình ảnh, giấy tờ


def has_flag(user_mask, flag):
    """
    Check if a specific flag is set in the user_mask.
    """
    if user_mask is None:
        return False
    # If user_mask is a list or string from DB, we might need conversion
    # But assuming it's stored as an integer/IntFlag
    try:
        mask_val = int(user_mask)
        flag_val = int(flag)
        return (mask_val & flag_val) == flag_val
    except (ValueError, TypeError):
        return False

class Role(str, Enum):
    STAFF = "Nhân viên"
    DRIVER = "Tài xế"
    JANITOR = "Tạp vụ"

class LeaveType(str, Enum):
    NGHI_PHEP_NAM = "Nghỉ phép năm"
    NGHI_KHONG_PHEP = "Nghỉ không phép"
    NGHI_CON_KET_HON = "Nghỉ con kết hôn"
    NGHI_BU = "Nghỉ bù"
    NGHI_KET_HON = "Nghỉ kết hôn"
    NGHI_THAI_SAN = "Nghỉ thai sản"
    NGHI_KHONG_LUONG = "Nghỉ không lương"
    NGHI_HUONG_BHXH = "Nghỉ hưởng chế độ BHXH"
    KHAC = "Khác"
