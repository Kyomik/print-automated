"""Persist validated server attachments without transforming their bytes."""

import re
from pathlib import Path

from utils.logger import cetak_log


MIME_EXTENSIONS = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
WINDOWS_RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}


class FileService:
    def __init__(self, folder_simpan):
        self.folder_simpan = Path(folder_simpan)

    @staticmethod
    def _safe_name(value):
        # Drop any client supplied path and keep only a safe Windows filename.
        name = Path(str(value or "").replace("\\", "/")).name
        name = INVALID_FILENAME_CHARS.sub("_", name).rstrip(" .")[:180]
        if Path(name).stem.upper() in WINDOWS_RESERVED_NAMES:
            name = f"_{name}"
        return name if name not in ("", ".", "..") else ""

    def _available_path(self, name):
        path = self.folder_simpan / name
        if not path.exists():
            return path

        stem, suffix = path.stem, path.suffix
        index = 1
        while True:
            candidate = self.folder_simpan / f"{stem} ({index}){suffix}"
            if not candidate.exists():
                return candidate
            index += 1

    def simpan_file(self, incoming):
        """Save `{message, file}` as received; prefer WhatsApp's original name."""
        file_info = incoming.get("file") if isinstance(incoming, dict) else None
        if not isinstance(file_info, dict):
            raise ValueError("Payload tidak memiliki metadata file")

        data = file_info.get("data")
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise ValueError("Data file bukan binary yang valid")

        server_name = self._safe_name(file_info.get("name"))
        original_name = self._safe_name(file_info.get("originalName"))
        mime_type = str(file_info.get("mimeType") or "").lower()
        extension = Path(server_name).suffix if server_name else ""
        if not extension:
            extension = MIME_EXTENSIONS.get(mime_type, ".bin")

        # Keep the WhatsApp name when present. If it has no extension, derive
        # the extension from the server's validated filename or MIME type.
        file_name = original_name or server_name or "attachment"
        current_extension = Path(file_name).suffix
        if extension and current_extension.lower() != extension.lower():
            file_name = f"{Path(file_name).stem}{extension}"
        elif not current_extension:
            file_name += extension

        self.folder_simpan.mkdir(parents=True, exist_ok=True)
        # Multiple attachment workers can save at once. Reserve each name
        # atomically and retry if another worker claimed it first.
        while True:
            file_path = self._available_path(file_name)
            try:
                with file_path.open("xb") as output:
                    output.write(bytes(data))
                break
            except FileExistsError:
                continue

        cetak_log("sukses", f"[FileService] File disimpan: {file_path}")
        return {
            "nama_file": file_path.name,
            "jalur": str(file_path),
            "original_name": original_name or server_name or file_path.name,
            "mime_type": mime_type,
        }
