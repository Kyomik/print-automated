"""Parse an optional one-based page or inclusive page range."""

import re


def selected_page_indices(selection: str | None, page_count: int) -> tuple[int, ...]:
    if page_count < 1:
        raise ValueError("Dokumen tidak memiliki halaman untuk dicetak.")
    if selection is None or not selection.strip():
        return tuple(range(page_count))

    match = re.fullmatch(r"\s*(\d+)\s*(?:-\s*(\d+)\s*)?", selection)
    if not match:
        raise ValueError("Masukkan nomor halaman (contoh: 2) atau rentang (contoh: 2-5).")
    first = int(match.group(1))
    last = int(match.group(2) or first)
    if first < 1 or last < first or last > page_count:
        raise ValueError(f"Halaman harus berada di antara 1 dan {page_count}.")
    return tuple(range(first - 1, last))
