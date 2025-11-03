"""时区工具 - 统一使用中国时区（Asia/Shanghai, UTC+8）"""

from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

# 中国时区
CHINA_TZ = ZoneInfo("Asia/Shanghai")


def now() -> datetime:
    """
    获取当前中国时间（无时区信息，但值为中国时间）

    Returns:
        datetime: 当前中国时间，无时区信息（naive），但时间值为 Asia/Shanghai 时区的时间

    Note:
        返回 naive datetime 以兼容 PostgreSQL TIMESTAMP WITHOUT TIME ZONE 字段
    """
    return datetime.now(CHINA_TZ).replace(tzinfo=None)


def today_start() -> datetime:
    """
    获取今天的开始时间（00:00:00，中国时区，无时区信息）

    Returns:
        datetime: 今天 00:00:00 的时间（naive，但值为中国时间）
    """
    china_now = datetime.now(CHINA_TZ)
    return china_now.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)


def to_china_tz(dt: datetime) -> datetime:
    """
    将任意时区的时间转换为中国时区

    Args:
        dt: 输入的 datetime 对象

    Returns:
        datetime: 转换为中国时区的时间
    """
    if dt.tzinfo is None:
        # 如果没有时区信息，假定为中国时区
        return dt.replace(tzinfo=CHINA_TZ)
    return dt.astimezone(CHINA_TZ)


def naive_to_china(dt: datetime) -> datetime:
    """
    将无时区信息的 datetime 视为中国时区的时间（保持 naive）

    Args:
        dt: 无时区信息的 datetime（假定为中国时间）

    Returns:
        datetime: 无时区信息的 datetime（原样返回）

    Note:
        由于系统统一使用 naive datetime 表示中国时间，此函数现在只是原样返回输入
        如果输入有时区信息，会先转换为中国时区，然后移除时区信息
    """
    if dt.tzinfo is not None:
        # 如果有时区信息，先转换为中国时区，然后移除时区
        return dt.astimezone(CHINA_TZ).replace(tzinfo=None)
    # 如果已经是 naive，直接返回（假定它已经是中国时间）
    return dt
