from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Optional

TURKISH_MONTHS = {
    1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan',
    5: 'Mayıs', 6: 'Haziran', 7: 'Temmuz', 8: 'Ağustos',
    9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'
}

def get_turkey_timezone() -> ZoneInfo:
    return ZoneInfo('Europe/Istanbul')

def get_today_turkey_date() -> str:
    """Returns today's date in YYYY-MM-DD format based on Europe/Istanbul."""
    now_tr = datetime.now(get_turkey_timezone())
    return now_tr.strftime('%Y-%m-%d')

def format_report_date(date_str: str) -> str:
    """Converts YYYY-MM-DD to readable Turkish format (e.g. 15 Eylül 2026)."""
    dt = datetime.strptime(date_str, '%Y-%m-%d')
    day = dt.day
    month_name = TURKISH_MONTHS.get(dt.month, str(dt.month))
    year = dt.year
    return f"{day} {month_name} {year}"

def format_date_dots(date_str: str) -> str:
    """Converts YYYY-MM-DD to DD.MM.YYYY."""
    dt = datetime.strptime(date_str, '%Y-%m-%d')
    return dt.strftime('%d.%m.%Y')

def parse_utc_to_turkey_time(time_iso: Optional[str]) -> str:
    """Parses ISO UTC timestamp into Turkey local HH:MM."""
    if not time_iso:
        return ''
    try:
        dt_utc = datetime.fromisoformat(time_iso.replace('Z', '+00:00'))
        dt_tr = dt_utc.astimezone(get_turkey_timezone())
        return dt_tr.strftime('%H:%M')
    except Exception:
        return ''

def get_turkey_date_from_utc_time(time_iso: Optional[str]) -> str:
    """Gets the calendar date in Turkey (YYYY-MM-DD) for a given UTC timestamp."""
    if not time_iso:
        return get_today_turkey_date()
    try:
        dt_utc = datetime.fromisoformat(time_iso.replace('Z', '+00:00'))
        dt_tr = dt_utc.astimezone(get_turkey_timezone())
        return dt_tr.strftime('%Y-%m-%d')
    except Exception:
        return get_today_turkey_date()

def get_last_n_days_turkey(days: int = 7) -> list[str]:
    """Returns list of last N dates in YYYY-MM-DD format based on Europe/Istanbul, ending today."""
    from datetime import timedelta
    now_tr = datetime.now(get_turkey_timezone())
    return get_dates_ending_at(now_tr.strftime('%Y-%m-%d'), days)


def get_dates_ending_at(end_date: str, days: int = 7) -> list[str]:
    """Returns list of N dates in YYYY-MM-DD format ending at end_date (inclusive)."""
    from datetime import timedelta
    dt_end = datetime.strptime(end_date, '%Y-%m-%d')
    dates = []
    for i in range(days - 1, -1, -1):
        d = dt_end - timedelta(days=i)
        dates.append(d.strftime('%Y-%m-%d'))
    return dates

def format_date_range_readable(start_date: str, end_date: str) -> str:
    dt1 = datetime.strptime(start_date, '%Y-%m-%d')
    dt2 = datetime.strptime(end_date, '%Y-%m-%d')
    m1 = TURKISH_MONTHS.get(dt1.month, str(dt1.month))
    m2 = TURKISH_MONTHS.get(dt2.month, str(dt2.month))
    if dt1.year == dt2.year:
        if dt1.month == dt2.month:
            return f"{dt1.day} - {dt2.day} {m2} {dt2.year}"
        return f"{dt1.day} {m1} - {dt2.day} {m2} {dt2.year}"
    return f"{dt1.day} {m1} {dt1.year} - {dt2.day} {m2} {dt2.year}"
