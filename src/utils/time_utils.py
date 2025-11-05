"""Time and date utility functions."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from src.constants import MILLISECONDS_PER_SECOND, SECONDS_PER_MINUTE


def get_timestamp() -> datetime:
    """Get current UTC timestamp.

    Returns:
        Current UTC datetime

    Example:
        >>> now = get_timestamp()
        >>> print(f"Current time: {now}")
        Current time: 2025-11-05 12:00:00+00:00
    """
    return datetime.now(timezone.utc)


def format_duration(milliseconds: int) -> str:
    """Format duration in milliseconds to human-readable string.

    Args:
        milliseconds: Duration in milliseconds

    Returns:
        Formatted string (e.g., "1.5s", "230ms")

    Example:
        >>> format_duration(1500)
        '1.50s'
        >>> format_duration(230)
        '230ms'
    """
    if milliseconds < 1000:
        return f"{milliseconds}ms"

    seconds = milliseconds / 1000
    if seconds < 60:
        return f"{seconds:.2f}s"

    minutes = seconds / 60
    if minutes < 60:
        return f"{minutes:.2f}m"

    hours = minutes / 60
    return f"{hours:.2f}h"


def is_expired(
    timestamp: datetime,
    ttl: int,
    now: Optional[datetime] = None,
) -> bool:
    """Check if a timestamp has expired based on TTL.

    Args:
        timestamp: The original timestamp
        ttl: Time to live in seconds
        now: Current time (default: now in UTC)

    Returns:
        True if expired

    Example:
        >>> old_time = datetime(2025, 1, 1, tzinfo=timezone.utc)
        >>> is_expired(old_time, 3600)  # 1 hour TTL
        True
    """
    if now is None:
        now = get_timestamp()

    age = (now - timestamp).total_seconds()
    return age > ttl


def milliseconds_to_seconds(milliseconds: int) -> float:
    """Convert milliseconds to seconds.

    Args:
        milliseconds: Time in milliseconds

    Returns:
        Time in seconds

    Example:
        >>> milliseconds_to_seconds(1500)
        1.5
    """
    return milliseconds / MILLISECONDS_PER_SECOND


def seconds_to_milliseconds(seconds: float) -> int:
    """Convert seconds to milliseconds.

    Args:
        seconds: Time in seconds

    Returns:
        Time in milliseconds

    Example:
        >>> seconds_to_milliseconds(1.5)
        1500
    """
    return int(seconds * MILLISECONDS_PER_SECOND)


def format_timestamp(
    timestamp: datetime,
    format_str: str = "%Y-%m-%d %H:%M:%S",
) -> str:
    """Format timestamp to string.

    Args:
        timestamp: Datetime to format
        format_str: Format string (default: ISO-like format)

    Returns:
        Formatted timestamp string

    Example:
        >>> ts = datetime(2025, 11, 5, 12, 30, 45, tzinfo=timezone.utc)
        >>> format_timestamp(ts)
        '2025-11-05 12:30:45'
    """
    return timestamp.strftime(format_str)


def get_time_ago(timestamp: datetime, now: Optional[datetime] = None) -> str:
    """Get human-readable time ago string.

    Args:
        timestamp: Past timestamp
        now: Current time (default: now in UTC)

    Returns:
        Human-readable string (e.g., "2 hours ago")

    Example:
        >>> past = datetime.now(timezone.utc) - timedelta(hours=2)
        >>> get_time_ago(past)
        '2 hours ago'
    """
    if now is None:
        now = get_timestamp()

    delta = now - timestamp

    seconds = delta.total_seconds()

    if seconds < 60:
        return f"{int(seconds)} seconds ago"

    minutes = seconds / 60
    if minutes < 60:
        return f"{int(minutes)} minutes ago" if minutes != 1 else "1 minute ago"

    hours = minutes / 60
    if hours < 24:
        return f"{int(hours)} hours ago" if hours != 1 else "1 hour ago"

    days = hours / 24
    if days < 30:
        return f"{int(days)} days ago" if days != 1 else "1 day ago"

    months = days / 30
    if months < 12:
        return f"{int(months)} months ago" if months != 1 else "1 month ago"

    years = months / 12
    return f"{int(years)} years ago" if years != 1 else "1 year ago"


def add_seconds(timestamp: datetime, seconds: int) -> datetime:
    """Add seconds to a timestamp.

    Args:
        timestamp: Original timestamp
        seconds: Seconds to add

    Returns:
        New timestamp

    Example:
        >>> ts = datetime(2025, 11, 5, 12, 0, 0, tzinfo=timezone.utc)
        >>> new_ts = add_seconds(ts, 3600)  # Add 1 hour
        >>> print(new_ts.hour)
        13
    """
    return timestamp + timedelta(seconds=seconds)


def get_expiry_time(ttl: int, now: Optional[datetime] = None) -> datetime:
    """Calculate expiry time from TTL.

    Args:
        ttl: Time to live in seconds
        now: Current time (default: now in UTC)

    Returns:
        Expiry timestamp

    Example:
        >>> expiry = get_expiry_time(3600)  # 1 hour from now
        >>> print(f"Expires at: {expiry}")
        Expires at: 2025-11-05 13:00:00+00:00
    """
    if now is None:
        now = get_timestamp()

    return now + timedelta(seconds=ttl)
