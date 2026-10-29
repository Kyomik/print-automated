"""Coordinate document preview state, rendering requests, and preview widgets."""

import tkinter as tk

from PIL import ImageTk

from domain.page_selection import selected_page_indices
from utils.logger import cetak_log


class PreviewController:
    def __init__(self, widgets, queue_controller, attachment_controller, set_status, refresh_queue):
        self._widgets = widgets
        self._queue = queue_controller
        self._attachments = attachment_controller
        self._set_status = set_status
        self._refresh_queue = refresh_queue
        self._image = None
        self._page_index = 0
        self._page_count = 0
        self._description = ""

    def select(self, index):
        item = self._queue.select(index)
        if item is None:
            return
        self._refresh_queue()
        self.show_item(item)

    def show_selected(self):
        item = self._queue.selected_item
        if item is not None:
            self.show_item(item)

    def show_item(self, item):
        self._widgets["name_label"].configure(text=item["nama_file"])
        if item.get("loading"):
            self._page_count = 0
            self._page_index = 0
            self._widgets["meta_label"].configure(text="Sedang menyimpan file dan menyiapkan preview…")
            self._widgets["page_var"].set("")
            self._show_message("Mohon tunggu, file sedang diproses.")
            self.update_action_states()
            return
        if item.get("preview_error"):
            self._page_count = 0
            self._page_index = 0
            self._widgets["meta_label"].configure(
                text="Preview tidak tersedia" if item.get("preview_unavailable") else "File gagal disiapkan"
            )
            self._show_message(
                "File tersimpan dan dapat dicetak, tetapi preview gagal dibuat."
                if item.get("preview_unavailable") else "File tidak dapat disiapkan."
            )
            self.update_action_states()
            return

        info = item["preview_info"]
        size_kb = item.get("ukuran_bytes", 0) / 1024
        self._widgets["meta_label"].configure(text=f"{info.description}  ·  {size_kb:.0f} KB")
        self._description = info.description
        self._page_count = info.page_count
        selection = item.get("page_selection")
        # An empty selection means print every page. Keep the page field empty
        # for newly received documents; the preview itself still opens on page 1.
        self._widgets["page_var"].set(selection or "")
        self._widgets["page_total"].configure(text=f"/{self._page_count}")
        try:
            self._page_index = selected_page_indices(selection, self._page_count)[0]
        except ValueError:
            self._page_index = 0
        self.update_action_states()
        self._render_current_page()

    def handle_item_result(self, result, refresh=True):
        item = result["item"]
        index = self._queue.item_index(item)
        if index is None:
            renderer = result.get("renderer")
            if renderer is not None:
                self._attachments.close_renderer(renderer)
            return

        item["loading"] = False
        if result["kind"] == "preview_error":
            item["preview_error"] = str(result["error"])
            if result.get("info"):
                item.update(result["info"])
                item["preview_unavailable"] = True
                message = "File tersimpan, tetapi preview tidak dapat dibuat. File tetap bisa dicetak."
                color = "#b54708"
            else:
                message = "File gagal diterima atau disimpan. Periksa log untuk detail."
                color = "#b42318"
            self._set_status(message, color)
            if refresh:
                self._refresh_queue()
            if self._queue.selected_index == index:
                self.show_item(item)
            return

        item.update(result["info"])
        item["renderer"] = result["renderer"]
        item["preview_info"] = result["preview_info"]
        item["frame_cache"][0] = result["frame"]
        if refresh:
            self._refresh_queue()
        if self._queue.selected_index == index:
            self.show_item(item)
        self._set_status("File siap. Tinjau preview sebelum mencetak.", "#067647")

    def handle_page_result(self, result):
        widgets = self._widgets
        widgets["prev_page_action"].finish()
        widgets["next_page_action"].finish()
        item = result["item"]
        item["rendering_pages"].discard(result["page_index"])
        self.update_action_states()
        item_index = self._queue.item_index(item)
        if item_index is None:
            return
        if result["kind"] == "preview_page_error":
            if self._queue.selected_index == item_index:
                self._show_message("Halaman ini gagal ditampilkan.")
            return
        item["frame_cache"][result["page_index"]] = result["frame"]
        if self._queue.selected_index == item_index and self._page_index == result["page_index"]:
            self._render_current_page()

    def handle_display_result(self, result):
        item = result["item"]
        item.setdefault("display_pending", set()).discard(result["key"])
        if self._queue.selected_index is None:
            return
        if self._queue.item_index(item) != self._queue.selected_index:
            return
        if self._page_index != result["page_index"]:
            return
        if result.get("error"):
            self._show_message("Preview gagal disesuaikan ke ukuran jendela.")
            cetak_log("error", f"[Preview] Gagal menyesuaikan ukuran gambar: {result['error']}")
            return
        self._image = ImageTk.PhotoImage(result["image"])
        self._widgets["preview_label"].configure(image=self._image, text="")

    def update_action_states(self):
        item = self._queue.selected_item
        index = self._page_index
        rendering = bool(item and index in item.get("rendering_pages", set()))
        has_pages = bool(
            item and not item.get("loading") and not item.get("preview_error")
            and self._page_count > 0
        )
        self._widgets["page_entry"].configure(state="normal" if has_pages else "disabled")
        self._widgets["page_total"].configure(text=f"/{self._page_count}" if has_pages else "")
        self._widgets["prev_page_action"].set_enabled(
            has_pages and index > 0 and not rendering
        )
        self._widgets["next_page_action"].set_enabled(
            has_pages and index < self._page_count - 1 and not rendering
        )

    def change_page(self, amount):
        target = self._page_index + amount
        if not 0 <= target < self._page_count:
            return True
        self._page_index = target
        item = self._queue.selected_item
        if item is not None:
            item["page_selection"] = str(target + 1)
        self._widgets["page_var"].set(str(target + 1))
        self._render_current_page()
        self.update_action_states()
        return item is None or target in item["frame_cache"]

    def commit_page_selection(self):
        item = self._queue.selected_item
        if item is None or item.get("loading") or item.get("preview_error"):
            return
        selection = self._widgets["page_var"].get().strip()
        try:
            indices = selected_page_indices(selection, self._page_count)
        except ValueError as error:
            self._set_status(str(error), "#b42318")
            self._widgets["page_var"].set(item.get("page_selection") or "")
            return
        item["page_selection"] = selection or None
        self._page_index = indices[0]
        self._widgets["page_var"].set(selection or "")
        self._render_current_page()
        self.update_action_states()

    def dispose_item(self, item):
        renderer = item.get("renderer")
        if renderer is not None:
            self._attachments.close_renderer(renderer)

    def show_empty(self):
        self._page_count = 0
        self._page_index = 0
        self._image = None
        self._widgets["preview_label"].configure(
            image="", text="Pilih file untuk melihat preview"
        )
        self._widgets["name_label"].configure(text="Belum ada file dipilih")
        self._widgets["meta_label"].configure(
            text="File yang masuk akan muncul di daftar sebelah kiri."
        )
        self._widgets["page_var"].set("")
        self._widgets["page_total"].configure(text="")
        self.update_action_states()

    def _render_current_page(self):
        item = self._queue.selected_item
        if item is None or item.get("loading") or item.get("preview_error"):
            return
        frame = item["frame_cache"].get(self._page_index)
        if frame is None:
            if self._page_index not in item["rendering_pages"]:
                item["rendering_pages"].add(self._page_index)
                self._attachments.render_page(item, self._page_index)
            self._show_message("Sedang memuat halaman…")
            return
        if frame.image is not None:
            details = self._page_details(frame)
            self._widgets["meta_label"].configure(text=details)
            self._show_image(frame.image, item, self._page_index)
        else:
            self._show_message(frame.text or "Preview tidak tersedia", text=True)

    def _show_image(self, image, item, page_index):
        area = self._widgets["preview_area"]
        size = (max(area.winfo_width() - 36, 300), max(area.winfo_height() - 36, 300))
        key = (page_index, size)
        pending = item.setdefault("display_pending", set())
        if key in pending:
            return
        pending.add(key)
        self._show_message("Menyiapkan tampilan preview…")
        self._attachments.resize_preview(image, size, item, key)

    def _page_details(self, frame):
        analysis = frame.analysis
        if analysis is None:
            return self._description
        details = [self._description, analysis.color_content.value]
        if analysis.dimensions is not None:
            details.append(analysis.dimensions.description)
        return "  ·  ".join(details)

    def _show_message(self, message, text=False):
        self._image = None
        self._widgets["preview_label"].configure(
            image="", text=message, anchor="nw" if text else "center",
            justify="left" if text else "center", font=("Segoe UI", 10), padx=24, pady=20,
        )
