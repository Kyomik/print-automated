"""Socket event names shared by client adapters and event handlers."""


class ServerEvents:
    WHATSAPP_QR = "whatsapp-qr"
    WHATSAPP_STATUS = "whatsapp-status"
    WHATSAPP_INCOMING = "whatsapp-incoming"


class ClientEvents:
    SEND_TEXT = "kirim_pesan_wa"
    GET_STATUS = "minta_status_wa"
    GET_QR = "minta_qr_wa"
    PRINT_RESULT = "respons_cetak"
