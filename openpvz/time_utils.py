from datetime import datetime, date
import pytz


DEFAULT_TIMEZONE = pytz.timezone("Europe/Moscow")


def tz_now(timezone: pytz.BaseTzInfo = None) -> datetime:
    if timezone is None:
        timezone = DEFAULT_TIMEZONE
    now = pytz.utc.fromutc(datetime.utcnow())
    return now.astimezone(timezone)


def tz_today(timezone: pytz.BaseTzInfo = None) -> date:
    if timezone is None:
        timezone = DEFAULT_TIMEZONE
    return tz_now(timezone).date()


def date_to_tz_datetime(date: date, timezone=None) -> datetime:
    if timezone is None:
        timezone = DEFAULT_TIMEZONE
    return timezone.localize(datetime(year=date.year, month=date.month, day=date.day), is_dst=False)
