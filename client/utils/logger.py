"""Compatibility facade for application logging calls."""

from application.logging_service import ApplicationLogger


_logger = None


def configure_logger(sink):
    global _logger
    _logger = ApplicationLogger(sink)


def cetak_log(tipe, pesan):
    if _logger is not None:
        _logger.log(tipe, pesan)
