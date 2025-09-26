import asyncio
import logging
import os

import uvicorn
from asgiref.wsgi import WsgiToAsgi
from dotenv import load_dotenv
from rich.logging import RichHandler

from sqlite_logger import _SQLiteLoggingHandler
from src import app

if os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
else:
    try:
        import uvloop

        asyncio.set_event_loop(uvloop.new_event_loop())
    except ImportError:
        pass

load_dotenv()

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
DEVELOPMENT = os.getenv("DEVELOPMENT", "True").lower() == "true"

if DEVELOPMENT:
    app.logger.setLevel(logging.DEBUG)

sqlite_handler = _SQLiteLoggingHandler()
sqlite_handler.connect("db.sqlite3")

logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=[RichHandler(), sqlite_handler])

LOGGING_CONFIG: dict[str, object] = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"custom": {"()": RichHandler}},
}

if __name__ == "__main__":
    uvicorn.run(WsgiToAsgi(app), host="0.0.0.0", port=8000, log_config=LOGGING_CONFIG)
