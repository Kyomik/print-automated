"""Socket.IO transport adapter. Application code depends on this small API."""

from typing import Any, Callable
from threading import Event

import socketio

from utils.logger import cetak_log
from protocol import ClientEvents


class SocketIoService:
    def __init__(self, server_url: str, api_token: str, event_handlers=None):
        self.server_url = server_url
        self.api_token = api_token
        self.on_qr_received = None
        self.on_status_received = None
        self.on_connection_status = None
        self._running = False
        self._retry_now = Event()
        self.sio = socketio.Client(reconnection=True)
        self._register_connection_events()

        for event, handler in (event_handlers or {}).items():
            self.on(event, handler)

    def _register_connection_events(self):
        self.sio.on("connect", self._on_connect)
        self.sio.on("disconnect", self._on_disconnect)
        self.sio.on("connect_error", self._on_connect_error)

    def _on_connect(self):
        cetak_log("sukses", f"[SocketIO] Terhubung ke server: {self.server_url}")
        self._notify_connection(True, "Terhubung ke server")
        if self.on_status_received:
            self.get_whatsapp_status(self.on_status_received)
        self.get_whatsapp_qr()

    def _on_disconnect(self):
        cetak_log("warning", "[SocketIO] Terputus dari server.")
        self._notify_connection(False, "Koneksi ke server terputus")

    def _on_connect_error(self, error):
        cetak_log("error", f"[SocketIO] Koneksi ditolak/gagal: {error}")
        self._notify_connection(False, "Server tidak dapat dijangkau")

    def _notify_connection(self, connected, message):
        if self.on_connection_status:
            self.on_connection_status(connected, message)

    def on(self, event: str, handler: Callable):
        """Register one inbound event without exposing the socket to consumers."""
        self.sio.on(event, handler)

    def emit(self, event: str, payload: Any = None, callback=None):
        self.sio.emit(event, payload, callback=callback)

    def send_text(self, recipient: str, text: str, callback=None):
        self.emit(ClientEvents.SEND_TEXT, {"nomorTujuan": recipient, "isiPesan": text}, callback)

    def get_whatsapp_status(self, callback):
        self.emit(ClientEvents.GET_STATUS, callback=callback)

    def get_whatsapp_qr(self, callback=None):
        if callback is None and self.on_qr_received:
            callback = self.on_qr_received
        self.emit(ClientEvents.GET_QR, callback=callback)

    def report_print_result(self, result: dict):
        self.emit(ClientEvents.PRINT_RESULT, result)

    def run(self):
        cetak_log("info", f"[SocketIO] Menghubungkan ke {self.server_url} ...")
        self._running = True
        while self._running:
            try:
                if not self.sio.connected:
                    self.sio.connect(self.server_url, auth={"token": self.api_token}, wait_timeout=5)
                self.sio.wait()
            except Exception as error:
                cetak_log("error", f"[SocketIO] Gagal berjalan: {error}")
                self._notify_connection(False, "Server tidak dapat dijangkau")
            if self._running and not self.sio.connected:
                self._retry_now.wait(5)
                self._retry_now.clear()

    def reconnect(self):
        """Wake the connection loop so the user can retry immediately."""
        self._retry_now.set()

    def close(self):
        self._running = False
        self._retry_now.set()
        if self.sio.connected:
            self.sio.disconnect()

    # Compatibility with the previous entry point.
    def jalankan(self):
        try:
            self.run()
        except KeyboardInterrupt:
            self.close()
            cetak_log("info", "[SocketIO] Client dihentikan.")
        except Exception as error:
            cetak_log("error", f"[SocketIO] Gagal berjalan: {error}")
