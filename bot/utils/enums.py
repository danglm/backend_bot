from enum import Enum, IntFlag

class UserType(IntFlag):
    OWNER = 1
    ADMIN = 2
    MEMBER = 4
    STAFF = 8
    DRIVER = 16
    CUSTOMER = 32
    JANITOR = 64



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
