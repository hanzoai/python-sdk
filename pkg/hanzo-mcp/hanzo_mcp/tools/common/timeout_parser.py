"""Human-readable timeout parsing utilities."""

import re
from typing import Union


def parse_timeout(timeout_str: Union[str, int, float]) -> float:
    """Parse timeout from human-readable string or numeric value.

    Supports formats like:
    - "2min", "5m", "120s", "30sec", "1.5h", "0.5hr"
    - 120 (seconds as number)
    - "120" (seconds as string)

    Args:
        timeout_str: Timeout value as string or number

    Returns:
        Timeout in seconds as float

    Raises:
        ValueError: If format is not recognized
    """
    if isinstance(timeout_str, (int, float)):
        return float(timeout_str)

    if isinstance(timeout_str, str):
        # Handle pure numeric strings
        try:
            return float(timeout_str)
        except ValueError:
            pass

        # Handle human-readable formats
        timeout_str = timeout_str.lower().strip()

        # Regex patterns for different time units
        patterns = [
            # Hours: 1h, 1.5hr, 2hour, 3hours
            (r"^(\d*\.?\d+)\s*h(?:r|our|ours)?$", 3600),
            # Minutes: 2m, 5min, 10mins, 1.5minute
            (r"^(\d*\.?\d+)\s*m(?:in|ins|inute|inutes)?$", 60),
            # Seconds: 30s, 120sec, 45secs, 60second, 90seconds
            (r"^(\d*\.?\d+)\s*s(?:ec|ecs|econd|econds)?$", 1),
        ]

        for pattern, multiplier in patterns:
            match = re.match(pattern, timeout_str)
            if match:
                value = float(match.group(1))
                return value * multiplier

        # If no pattern matches, raise error
        raise ValueError(
            f"Invalid timeout format: '{timeout_str}'. "
            f"Supported formats: 2min, 5m, 120s, 30sec, 1.5h, 0.5hr, or numeric seconds."
        )

    raise ValueError(f"Unsupported timeout type: {type(timeout_str)}")


def format_timeout(seconds: float) -> str:
    """Format timeout seconds into human-readable string.

    Args:
        seconds: Timeout in seconds

    Returns:
        Human-readable string like "2m", "90s", "1.5h"
    """
    if seconds >= 3600:  # >= 1 hour
        hours = seconds / 3600
        if hours.is_integer():
            return f"{int(hours)}h"
        else:
            return f"{hours:.1f}h"
    elif seconds >= 60:  # >= 1 minute
        minutes = seconds / 60
        if minutes.is_integer():
            return f"{int(minutes)}m"
        else:
            return f"{minutes:.1f}m"
    else:  # < 1 minute
        if seconds.is_integer():
            return f"{int(seconds)}s"
        else:
            return f"{seconds:.1f}s"


# Test the parser
if __name__ == "__main__":
    test_cases = ["2min", "5m", "120s", "30sec", "1.5h", "0.5hr", "90", 120, 3600.0, "1hour", "2hours", "30seconds"]

    for case in test_cases:
        try:
            result = parse_timeout(case)
            formatted = format_timeout(result)
            print(f"{case} -> {result}s ({formatted})")
        except ValueError as e:
            print(f"{case} -> ERROR: {e}")
