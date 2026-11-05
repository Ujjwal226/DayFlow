import calendar
from datetime import date, timedelta
from typing import List, Optional

from app.models.recurring_task import RecurrenceFrequency


def get_last_day_of_month(year: int, month: int) -> int:
    """Return the last day (e.g. 28, 29, 30, 31) of a given month/year."""
    return calendar.monthrange(year, month)[1]


def add_months(source_date: date, months: int, preferred_day: Optional[int] = None) -> date:
    """
    Add `months` to `source_date`.
    If preferred_day is specified (e.g. 31 or -1 for last day), clamp to the month's maximum days.
    """
    total_months = source_date.month - 1 + months
    year = source_date.year + total_months // 12
    month = total_months % 12 + 1
    max_day = get_last_day_of_month(year, month)

    if preferred_day is not None:
        if preferred_day == -1 or preferred_day > max_day:
            day = max_day
        else:
            day = max(1, preferred_day)
    else:
        day = min(source_date.day, max_day)

    return date(year, month, day)


def add_years(source_date: date, years: int, preferred_month: Optional[int] = None, preferred_day: Optional[int] = None) -> date:
    """
    Add `years` to `source_date`.
    Handles leap-year edge cases (e.g. Feb 29 -> Feb 28 on non-leap years).
    """
    target_year = source_date.year + years
    target_month = preferred_month if preferred_month is not None else source_date.month
    max_day = get_last_day_of_month(target_year, target_month)

    if preferred_day is not None:
        if preferred_day == -1 or preferred_day > max_day:
            day = max_day
        else:
            day = max(1, preferred_day)
    else:
        day = min(source_date.day, max_day)

    return date(target_year, target_month, day)


def calculate_next_occurrence(
    current_date: date,
    frequency: RecurrenceFrequency,
    interval: int = 1,
    weekdays: Optional[List[int]] = None,
    day_of_month: Optional[int] = None,
    month_of_year: Optional[int] = None,
) -> date:
    """
    Calculate the next occurrence date strictly AFTER current_date.
    weekdays: list of weekday integers (0=Monday, 6=Sunday).
    day_of_month: 1-31, or -1 for last day of month.
    month_of_year: 1-12.
    """
    interval = max(1, interval)

    if frequency == RecurrenceFrequency.DAILY:
        return current_date + timedelta(days=interval)

    elif frequency == RecurrenceFrequency.CUSTOM:
        # Custom interval in days
        return current_date + timedelta(days=interval)

    elif frequency == RecurrenceFrequency.WEEKLY:
        valid_weekdays = sorted(set(weekdays)) if weekdays else [current_date.weekday()]

        # 1. Look for remaining matching weekdays in the current week
        curr_weekday = current_date.weekday()
        for w in valid_weekdays:
            if w > curr_weekday:
                return current_date + timedelta(days=w - curr_weekday)

        # 2. Advance by (interval - 1) full weeks + jump to the first weekday of the target week
        days_to_next_week_monday = 7 - curr_weekday
        target_week_monday = current_date + timedelta(days=days_to_next_week_monday + (interval - 1) * 7)
        first_weekday = valid_weekdays[0]
        return target_week_monday + timedelta(days=first_weekday)

    elif frequency == RecurrenceFrequency.MONTHLY:
        pref_day = day_of_month if day_of_month is not None else current_date.day
        return add_months(current_date, months=interval, preferred_day=pref_day)

    elif frequency == RecurrenceFrequency.YEARLY:
        pref_month = month_of_year if month_of_year is not None else current_date.month
        pref_day = day_of_month if day_of_month is not None else current_date.day
        return add_years(current_date, years=interval, preferred_month=pref_month, preferred_day=pref_day)

    raise ValueError(f"Unsupported recurrence frequency: {frequency}")


def is_valid_recurrence_date(
    candidate_date: date,
    start_date: date,
    frequency: RecurrenceFrequency,
    interval: int = 1,
    weekdays: Optional[List[int]] = None,
    day_of_month: Optional[int] = None,
    month_of_year: Optional[int] = None,
    end_date: Optional[date] = None,
) -> bool:
    """
    Verify whether candidate_date is a valid occurrence date according to the recurrence rule.
    """
    if candidate_date < start_date:
        return False
    if end_date and candidate_date > end_date:
        return False

    if frequency == RecurrenceFrequency.DAILY:
        delta_days = (candidate_date - start_date).days
        return delta_days % max(1, interval) == 0

    elif frequency == RecurrenceFrequency.CUSTOM:
        delta_days = (candidate_date - start_date).days
        return delta_days % max(1, interval) == 0

    elif frequency == RecurrenceFrequency.WEEKLY:
        valid_weekdays = sorted(set(weekdays)) if weekdays else [start_date.weekday()]
        if candidate_date.weekday() not in valid_weekdays:
            return False
        # Calculate week distance from start_date's week (using Monday of week)
        start_week_monday = start_date - timedelta(days=start_date.weekday())
        candidate_week_monday = candidate_date - timedelta(days=candidate_date.weekday())
        weeks_diff = (candidate_week_monday - start_week_monday).days // 7
        return weeks_diff % max(1, interval) == 0

    elif frequency == RecurrenceFrequency.MONTHLY:
        # Check month interval
        total_months_diff = (candidate_date.year - start_date.year) * 12 + (candidate_date.month - start_date.month)
        if total_months_diff < 0 or total_months_diff % max(1, interval) != 0:
            return False
        pref_day = day_of_month if day_of_month is not None else start_date.day
        max_day = get_last_day_of_month(candidate_date.year, candidate_date.month)
        expected_day = max_day if (pref_day == -1 or pref_day > max_day) else max(1, pref_day)
        return candidate_date.day == expected_day

    elif frequency == RecurrenceFrequency.YEARLY:
        years_diff = candidate_date.year - start_date.year
        if years_diff < 0 or years_diff % max(1, interval) != 0:
            return False
        pref_month = month_of_year if month_of_year is not None else start_date.month
        if candidate_date.month != pref_month:
            return False
        pref_day = day_of_month if day_of_month is not None else start_date.day
        max_day = get_last_day_of_month(candidate_date.year, candidate_date.month)
        expected_day = max_day if (pref_day == -1 or pref_day > max_day) else max(1, pref_day)
        return candidate_date.day == expected_day

    return False


