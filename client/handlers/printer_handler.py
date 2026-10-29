"""Connect incoming attachment events to the desktop print inbox."""

from protocol import ServerEvents


def printer_handler(socket_service, print_inbox):
    socket_service.on(ServerEvents.WHATSAPP_INCOMING, print_inbox.enqueue)
