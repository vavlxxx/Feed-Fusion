from fastapi import FastAPI
from gunicorn.app.base import BaseApplication
from src.utils.logging import get_logging_config


class GunicornApp(BaseApplication):
    def __init__(
        self,
        app: FastAPI,
        options: dict,
    ):
        self.options = options
        self.application = app
        super().__init__()

    @property
    def config_options(self) -> dict:
        return {
            k: v
            for k, v in self.options.items()
            if k in self.cfg.settings and v is not None
        }

    def load(self):
        return self.application

    def load_config(self):
        for k, v in self.config_options.items():
            self.cfg.set(k.lower(), v)


def get_app_options(
    host: str,
    port: int,
    access_log: str,
    error_log: str,
    workers: int,
    timeout: int,
    workers_class: str,
    reload: bool,
):
    return {
        "bind": f"{host}:{port}",
        "access_log": access_log,
        "error_log": error_log,
        "workers": workers,
        "worker_class": workers_class,
        "timeout": timeout,
        "reload": reload,
        "logconfig_dict": get_logging_config(),
    }
