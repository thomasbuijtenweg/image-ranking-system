"""Central logging setup for the Image Ranking System.

This module exists so that, over the course of the refactor, the hundreds
of `print()` calls scattered across the codebase can be migrated to proper
logging with levels, filtering, and a consistent format.

Usage:

    from core.logging_setup import get_logger
    log = get_logger(__name__)
    log.debug("fine-grained algorithm trace")
    log.info("user-visible status")
    log.warning("something odd but recoverable")
    log.error("failed operation")

Design notes:
- Named after `logging_setup` (not `logging`) to avoid shadowing the stdlib
  `logging` module, which would break any `import logging` elsewhere.
- Default level is INFO, matching the tone of the existing `print()` calls.
  Switch to DEBUG by setting the environment variable IRS_LOG_LEVEL=DEBUG
  before starting the app, or by calling `set_level('DEBUG')` at runtime.
- A single StreamHandler writes to stderr with a compact format. This keeps
  log output visible in terminals and captured by IDEs during development.
- `configure()` is idempotent: calling it more than once (e.g. from tests)
  is safe and won't duplicate handlers.
"""

import logging
import os
import sys
from typing import Optional


_ROOT_LOGGER_NAME = "irs"
_DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DEFAULT_DATEFMT = "%H:%M:%S"
_configured = False


def _resolve_level(level: Optional[str]) -> int:
    """Resolve a level name (or env var override) to a logging level int."""
    if level is None:
        level = os.environ.get("IRS_LOG_LEVEL", "INFO")
    level = level.upper()
    return getattr(logging, level, logging.INFO)


def configure(level: Optional[str] = None) -> None:
    """Attach a single StreamHandler to the IRS root logger. Idempotent."""
    global _configured
    root = logging.getLogger(_ROOT_LOGGER_NAME)
    root.setLevel(_resolve_level(level))

    if _configured:
        # Already set up — just update the level and move on.
        return

    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setFormatter(logging.Formatter(_DEFAULT_FORMAT, _DEFAULT_DATEFMT))
    root.addHandler(handler)
    # Don't propagate to the Python root logger; we own our output.
    root.propagate = False
    _configured = True


def set_level(level: str) -> None:
    """Change the IRS log level at runtime. Safe to call from anywhere."""
    logging.getLogger(_ROOT_LOGGER_NAME).setLevel(_resolve_level(level))


def get_logger(name: str) -> logging.Logger:
    """Return a logger under the `irs` namespace.

    Callers typically pass `__name__`. A module at `core.ranking_algorithm`
    becomes `irs.core.ranking_algorithm` in log output.
    """
    if not _configured:
        configure()
    # If the caller passes the literal 'irs' or a child of it, use as-is.
    # Otherwise, nest it under our root so filtering by `irs.*` catches it.
    if name == _ROOT_LOGGER_NAME or name.startswith(_ROOT_LOGGER_NAME + "."):
        return logging.getLogger(name)
    return logging.getLogger(f"{_ROOT_LOGGER_NAME}.{name}")
