"""Application logging policy, independent from the chosen storage adapter."""

from domain.ports import LogSink


class ApplicationLogger:
    _LEVELS = {"INFO", "WARNING", "ERROR", "SUKSES"}

    def __init__(self, sink: LogSink):
        self._sink = sink

    def log(self, level: str, message: str) -> None:
        normalized = str(level).upper()
        if normalized not in self._LEVELS:
            normalized = "INFO"
        self._sink.write(normalized, str(message))
