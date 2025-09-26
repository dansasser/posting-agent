import logging
import sys
import json

from app.configs import settings

class JsonFormatter(logging.Formatter):
    """
    Formats log records as JSON strings.
    """
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record['exc_info'] = self.formatException(record.exc_info)
        if hasattr(record, 'extra'):
            log_record['extra'] = record.extra
        return json.dumps(log_record)

def get_logger(name: str) -> logging.Logger:
    """
    Configures and returns a logger with specified name.

    The logger is configured to output structured JSON logs to stdout.
    The log level is determined by the LOG_LEVEL setting.
    """
    logger = logging.getLogger(name)

    # Prevents duplicate logs in case this function is called multiple times.
    if logger.hasHandlers():
        return logger

    logger.setLevel(settings.LOG_LEVEL)

    handler = logging.StreamHandler(sys.stdout)

    # Use JsonFormatter for structured logging
    formatter = JsonFormatter()
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False  # Prevent logs from propagating to the root logger

    return logger

# Example of a basic logger if JSON is not desired.
# def get_logger(name: str) -> logging.Logger:
#     logging.basicConfig(
#         level=settings.LOG_LEVEL,
#         format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
#         stream=sys.stdout
#     )
#     return logging.getLogger(name)