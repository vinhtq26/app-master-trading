import logging
import colorlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import uuid

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request.state.request_id = str(uuid.uuid4())
        response = await call_next(request)
        return response

class APILoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logging.info(f"API called: {request.method} {request.url.path}")
        response = await call_next(request)
        return response

def setup_logging(log_file="app_trading.log"):
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(levelname)s - [%(threadName)s] [RequestID: %(request_id)s] - %(message)s",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    )

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(levelname)s - [%(threadName)s] [RequestID: %(request_id)s] - %(message)s"
    ))

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler]
    )

class CustomLogRecord(logging.LogRecord):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Provide a default value for request_id if it is missing
        if not hasattr(self, 'request_id'):
            self.request_id = 'N/A'

# Override the default factory to use CustomLogRecord
logging.setLogRecordFactory(CustomLogRecord)

# Call this function in the main entry point of your application
setup_logging()
