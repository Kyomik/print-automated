"""Application reactions to informational WhatsApp events from the server."""

from protocol import ServerEvents
from utils.logger import cetak_log


def register_server_event_handlers(socket_service, print_inbox):
    displayed_qr = None

    def on_qr(payload):
        nonlocal displayed_qr
        qr = payload.get("qr") if isinstance(payload, dict) else None
        if not qr:
            # A missing QR is normal when the saved WhatsApp session is already connected.
            return
        if qr == displayed_qr:
            return

        displayed_qr = qr
        cetak_log("info", "[WhatsApp] QR siap ditampilkan di aplikasi.")
        print_inbox.show_whatsapp_qr(qr)

    def on_status(payload):
        status = payload.get("status") if isinstance(payload, dict) else payload
        cetak_log("info", f"[WhatsApp] Status koneksi: {status}")

    socket_service.on(ServerEvents.WHATSAPP_QR, on_qr)
    socket_service.on(ServerEvents.WHATSAPP_STATUS, on_status)
    socket_service.on_qr_received = on_qr
    socket_service.on_status_received = on_status
