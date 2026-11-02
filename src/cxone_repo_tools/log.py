import logging, sys, time
from logging.handlers import RotatingFileHandler

LOG_FORMAT = "[%(asctime)s][%(name)s][%(levelname)s] %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

ROLLING_LOG_MAX_BYTES = 10 * 1024 * 1024
ROLLING_LOG_BACKUP_COUNT = 5


def configure_logging(debug: bool, log_file: str | None) -> None:
    """Configures the root logger before a command executes.

    Log lines are prefixed with the UTC timestamp, the logger name, and the
    level, each in brackets.  Output goes to stdout unless a log file is
    given, in which case a size-based rolling log file is used and nothing is
    written to stdout.
    """
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    formatter.converter = time.gmtime

    if log_file is not None and len(log_file) > 0:
        handler = RotatingFileHandler(
            log_file,
            maxBytes=ROLLING_LOG_MAX_BYTES,
            backupCount=ROLLING_LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
    else:
        handler = logging.StreamHandler(sys.stdout)

    handler.setFormatter(formatter)

    root = logging.getLogger()
    for existing in list(root.handlers):
        root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(logging.DEBUG if debug else logging.INFO)
