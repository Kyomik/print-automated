"""Own attachment preparation and preview work outside the Tk event loop."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path

from PIL import Image

from services.document_analyzer import DocumentAnalyzer
from services.preview_renderer import PreviewRenderer
from utils.logger import cetak_log


class AttachmentController:
    def __init__(self, workflow, result_queue, worker_count=2, analyzer=None):
        self.workflow = workflow
        self.result_queue = result_queue
        self.analyzer = analyzer if analyzer is not None else DocumentAnalyzer()
        self._workers = ThreadPoolExecutor(
            max_workers=worker_count, thread_name_prefix="attachment"
        )

    def accept(self, payload):
        """Create a visible loading row immediately and prepare it in a worker."""
        if not isinstance(payload, dict) or not payload.get("file"):
            self._workers.submit(self._receive_invalid, payload)
            return None

        file_data = payload.get("file") or {}
        name = file_data.get("originalName") or file_data.get("name") or "File masuk"
        item = {
            "nama_file": Path(name).name,
            "message": payload.get("message", {}),
            "printing": False,
            "loading": True,
            "renderer": None,
            "frame_cache": {},
            "rendering_pages": set(),
            "display_pending": set(),
            "is_new": True,
        }
        self._workers.submit(self._prepare, payload, item)
        return item

    def render_page(self, item, page_index):
        self._workers.submit(self._render_page, item, page_index)

    def resize_preview(self, image, size, item, key):
        self._workers.submit(self._resize_preview, image, size, item, key)

    def close_renderer(self, renderer):
        self._workers.submit(renderer.close)

    def close(self, items):
        for item in items:
            renderer = item.get("renderer")
            if renderer is not None:
                self.close_renderer(renderer)
        self._workers.shutdown(wait=False, cancel_futures=True)

    def _receive_invalid(self, payload):
        try:
            self.workflow.receive_attachment(payload)
        except Exception as error:
            self.result_queue.put({"kind": "incoming_error", "error": str(error)})

    def _prepare(self, payload, item):
        renderer = PreviewRenderer()
        info = None
        try:
            info = self.workflow.receive_attachment(payload)
            file_info = payload.get("file") or {}
            info["ukuran_bytes"] = len(file_info.get("data") or b"")
            preview_info = renderer.open(Path(info["jalur"]))
            frame = self._render_and_analyze(renderer, 0)
            cetak_log("info", f"[Queue] File siap direview: {item['nama_file']}")
            self.result_queue.put({
                "kind": "preview_ready", "item": item, "info": info,
                "renderer": renderer, "preview_info": preview_info, "frame": frame,
            })
        except Exception as error:
            renderer.close()
            cetak_log("error", f"[Print Inbox] Gagal menyiapkan file/preview: {error}")
            self.result_queue.put({
                "kind": "preview_error", "item": item, "info": info, "error": error,
            })

    def _render_page(self, item, page_index):
        try:
            frame = self._render_and_analyze(item["renderer"], page_index)
            result = {"kind": "preview_page_ready", "item": item,
                      "page_index": page_index, "frame": frame}
        except Exception as error:
            cetak_log("error", f"[Print Inbox] Gagal merender halaman: {error}")
            result = {"kind": "preview_page_error", "item": item,
                      "page_index": page_index, "error": error}
        self.result_queue.put(result)

    def _render_and_analyze(self, renderer, page_index):
        frame = renderer.render(page_index)
        if frame.image is None:
            return frame
        analysis = self.analyzer.analyze(frame.image, frame.geometry)
        return replace(frame, analysis=analysis)

    def _resize_preview(self, image, size, item, key):
        try:
            display_image = image.copy()
            display_image.thumbnail(size, Image.Resampling.BILINEAR)
            result = {"kind": "preview_display_ready", "item": item,
                      "page_index": key[0], "key": key, "image": display_image}
        except Exception as error:
            result = {"kind": "preview_display_ready", "item": item,
                      "page_index": key[0], "key": key, "error": error}
        self.result_queue.put(result)
