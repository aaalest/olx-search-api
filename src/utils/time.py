from datetime import datetime, timezone


def get_current_utc_datetime() -> datetime:
    return datetime.now(timezone.utc)

def parse_iso_to_utc_datetime(iso_string: str) -> datetime:
    return datetime.fromisoformat(iso_string).astimezone(timezone.utc)
