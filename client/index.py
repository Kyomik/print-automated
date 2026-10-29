"""Composition root: configuration and concrete adapters are wired here."""

from pathlib import Path
import os
import sys
from threading import Thread

from application.automated_print_planner import AutomatedPrintPlanner
from application.automated_printing import AutomatedPrintUseCase
from application.print_workflow import PrintWorkflow
from config import ConfigError, load_config
from handlers.printer_handler import printer_handler
from handlers.server_event_handler import register_server_event_handlers
from services import FileService, PrinterService, SocketIoService
from services.automated_printing import AutomatedPrintRuleRepository
from services.document_analyzer import DocumentAnalyzer
from services.document_page_inspector import DocumentPageInspector
from services.windows_printer_capabilities import WindowsPrinterCapabilities
from ui.print_inbox import PrintInbox
from services.file_log_sink import FileLogSink
from utils.logger import cetak_log, configure_logger


def _application_directory():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _log_path():
    local_app_data = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    return local_app_data / "IloPrintClient" / "logs" / "client.log"


def main():
    app_dir = _application_directory()
    configure_logger(FileLogSink(_log_path()))
    try:
        config = load_config(app_dir / ".env")
    except ConfigError as error:
        cetak_log("error", str(error))
        return

    printer_service = PrinterService(
        capabilities_provider=WindowsPrinterCapabilities(),
    )
    file_service = FileService(folder_simpan=config["DOWNLOAD_DIR"])
    socket_service = SocketIoService(
        server_url=config["SERVER_URL"],
        api_token=config["API_TOKEN"],
    )
    automated_print = AutomatedPrintUseCase(
        printer_service,
        AutomatedPrintRuleRepository(app_dir / "automated-print.toml"),
        DocumentPageInspector(),
        AutomatedPrintPlanner(printer_service),
    )
    workflow = PrintWorkflow(file_service, printer_service, socket_service, automated_print)
    print_inbox = PrintInbox(workflow, document_analyzer=DocumentAnalyzer())
    socket_service.on_connection_status = print_inbox.connection_changed

    register_server_event_handlers(socket_service, print_inbox)
    printer_handler(socket_service, print_inbox)
    Thread(target=socket_service.jalankan, name="socketio-client", daemon=True).start()
    print_inbox.run()


if __name__ == "__main__":
    main()
