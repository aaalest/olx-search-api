from collections.abc import Callable
from logger import logger


def safe_get(input_dict: dict, path: str, default=None, log_error: bool = True):
    value = input_dict
    for key in path.split("."):
        try:
            value = value[key]
        except (KeyError, TypeError):
            if log_error:
                logger.warning(f"Failed to resolve path '{path}' at key '{key}'")
            return default

    if value is None:
        return default

    return value


"""
Apply a function to a value if it is not None, otherwise return None
"""
def maybe[T, R](func: Callable[[T], R], value: T | None) -> R | None:
    return None if value is None else func(value)
