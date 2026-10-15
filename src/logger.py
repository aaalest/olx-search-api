import logging
from rich.console import Console
from rich.logging import RichHandler
import asyncio
import sys

from config import settings


def setup_logger(name: str = "olx_search") -> logging.Logger:
    # TODO: print logs as JSON if settings.is_prod() is True
    enable_color = not settings.is_prod

    # 1. Unified console & handler
    console = Console(
        force_terminal=enable_color,
        color_system="auto" if enable_color else None,
        width=120,
    )

    handler = RichHandler(
        console=console,
        rich_tracebacks=True,
        markup=True,
        show_path=True,
        enable_link_path=False,  # Keep off to prevent OSC 8 escape codes
    )
    handler.setFormatter(logging.Formatter("%(message)s"))

    # 2. Attach handler to ROOT so every library inherits Rich formatting
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)

    # 3. Industry standard: Silence noisy library internals to WARNING
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # 4. Return your application logger
    app_logger = logging.getLogger(name)
    app_logger.setLevel(logging.INFO)
    app_logger.propagate = True  # Allows logs to bubble up to the root RichHandler

    return app_logger


logger = setup_logger()


def unhandled_exception_hook(exc_type, exc_value, exc_tb):
    # Exit cleanly without errors on user cancellation (Ctrl+C or async cancellation)
    if issubclass(exc_type, (KeyboardInterrupt, asyncio.CancelledError)):
        sys.exit(0)

    # Log any other unexpected crashes with full trace info
    logger.critical(
        "Unhandled exception encountered",
        exc_info=(exc_type, exc_value, exc_tb),
    )


sys.excepthook = unhandled_exception_hook
