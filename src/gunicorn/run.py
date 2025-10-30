import sys
from pathlib import Path


sys.path.append(str(Path(__file__).parent.parent.parent))

from src.main import app
from src.config import settings
from src.gunicorn.app import GunicornApp, get_app_options


def main():
    GunicornApp(
        app=app,
        options=get_app_options(
            host=settings.GUNICORN_HOST,
            port=settings.GUNICORN_PORT,
            workers=settings.GUNICORN_WORKERS,
            timeout=settings.GUNICORN_TIMEOUT,
            workers_class=settings.GUNICORN_WORKERS_CLASS,
            access_log=settings.GUNICORN_ACCESS_LOG,
            error_log=settings.GUNICORN_ERROR_LOG,
            reload=settings.GUNICORN_RELOAD,
        ),
    ).run()


if __name__ == "__main__":
    main()
