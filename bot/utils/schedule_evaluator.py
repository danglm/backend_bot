"""
Schedule Evaluator — kiểm tra config có nên trigger tại thời điểm hiện tại.
"""
import calendar
import datetime
from app.models.scheduled_notification import ScheduledNotifyConfig, ScheduleType


def should_trigger(config: ScheduledNotifyConfig, now: datetime.datetime) -> bool:
    """
    Kiểm tra config có nên trigger tại thời điểm hiện tại.
    
    Returns:
        True nếu config nên trigger, False nếu không.
    """
    # Check giờ/phút
    if now.hour != config.schedule_hour or now.minute != config.schedule_minute:
        return False

    schedule_type = config.schedule_type
    # Xử lý cả string lẫn enum
    if isinstance(schedule_type, str):
        schedule_type = schedule_type.lower()
    else:
        schedule_type = schedule_type.value.lower()

    if schedule_type == "daily":
        return True

    elif schedule_type == "weekly":
        if config.schedule_day_of_week is None:
            return False
        return now.weekday() == config.schedule_day_of_week

    elif schedule_type == "monthly":
        if config.schedule_day_of_month is None:
            return False
        target_day = config.schedule_day_of_month
        last_day = calendar.monthrange(now.year, now.month)[1]
        actual_day = min(target_day, last_day)
        return now.day == actual_day

    elif schedule_type == "yearly":
        if config.schedule_month is None:
            return False
        if now.month != config.schedule_month:
            return False
        target_day = config.schedule_day_of_month or 1
        last_day = calendar.monthrange(now.year, now.month)[1]
        actual_day = min(target_day, last_day)
        return now.day == actual_day

    elif schedule_type == "specific_date":
        if config.schedule_specific_date is None:
            return False
        return now.date() == config.schedule_specific_date

    return False
