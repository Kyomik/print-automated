"""Rotating file adapter for application logs."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


class FileLogSink:
    def __init__(self, path: str | Path, max_bytes=2_000_000, backup_count=5):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._logger = logging.getLogger(f"ilo_client.file.{self.path.resolve()}")
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False
        if not self._logger.handlers:
            handler = RotatingFileHandler(
                self.path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            handler.setFormatter(logging.Formatter(
                "%(asctime)s [%(levelname)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            ))
            self._logger.addHandler(handler)

    def write(self, level: str, message: str) -> None:
        if level == "SUKSES":
            self._logger.log(25, "[SUKSES] %s", message)
        else:
            getattr(self._logger, level.lower())("%s", message)
