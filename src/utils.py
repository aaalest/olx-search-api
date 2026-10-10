from datetime import datetime, timezone
from collections.abc import Callable


def safe_get(input_dict: dict, path: str, default=None, log_error: bool = True):
    value = input_dict
    for key in path.split("."):
        try:
            value = value[key]
        except (KeyError, TypeError):
            if log_error:
                print(f"[Warning] Failed to resolve path '{path}' at key '{key}'")
            return default

    if value is None:
        return default

    return value


def get_current_utc_datetime() -> datetime:
    return datetime.now(timezone.utc)


def parse_iso_to_utc_datetime(iso_string: str) -> datetime:
    return datetime.fromisoformat(iso_string).astimezone(timezone.utc)
