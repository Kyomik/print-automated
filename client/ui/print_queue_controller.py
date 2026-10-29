"""Own the inbox file list, selection, and socket intake queue."""

from pathlib import Path
from queue import Empty, Queue

from utils.logger import cetak_log


class PrintQueueController:
    def __init__(self, attachment_controller):
        self._attachments = attachment_controller
        self.incoming = Queue()
        self.items = []
        self.selected_index = None

    @property
    def selected_item(self):
        if self.selected_index is None or self.selected_index >= len(self.items):
            return None
        return self.items[self.selected_index]

    def enqueue(self, payload):
        """Accept a Socket.IO callback without touching Tk from its thread."""
        file_info = payload.get("file") if isinstance(payload, dict) else None
        if isinstance(file_info, dict):
            name = file_info.get("originalName") or file_info.get("name") or "File masuk"
            cetak_log("info", f"[Socket] Event file diterima: {Path(name).name}")
        self.incoming.put(payload)

    def accept_pending(self, limit):
        selected_before_intake = self.selected_item
        received_items = []
        while len(received_items) < limit:
            try:
                payload = self.incoming.get_nowait()
            except Empty:
                break
            item = self._attachments.accept(payload)
            if item is not None:
                self.items.append(item)
                received_items.append(item)

        if not received_items:
            return [], False
        if selected_before_intake is not None:
            self.selected_index = self.item_index(selected_before_intake)
        else:
            self.selected_index = 0
        return received_items, selected_before_intake is None

    def select(self, index, mark_as_read=True):
        if not 0 <= index < len(self.items):
            return None
        self.selected_index = index
        item = self.items[index]
        if mark_as_read:
            item["is_new"] = False
        return item

    def item_index(self, item):
        return next((index for index, candidate in enumerate(self.items) if candidate is item), None)

    def remove(self, item):
        index = self.item_index(item)
        if index is None:
            return None
        removed = self.items.pop(index)
        self.selected_index = None
        return index, removed

    def clear(self):
        removed_items, self.items = self.items, []
        self.selected_index = None
        return removed_items
