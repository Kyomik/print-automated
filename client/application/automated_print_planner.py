"""Resolve page analyses into contiguous batches with matching printer settings."""

from dataclasses import dataclass
import re

from domain.ports import PrinterGateway
from domain.printer import PrintOptions


@dataclass(frozen=True)
class PrintBatch:
    printer_name: str
    page_indices: tuple[int, ...]
    options: PrintOptions

    @property
    def page_selection(self):
        first = self.page_indices[0] + 1
        last = self.page_indices[-1] + 1
        return str(first) if first == last else f"{first}-{last}"


class AutomatedPrintPlanner:
    def __init__(self, printer_gateway: PrinterGateway):
        self._printers = printer_gateway

    def plan(self, pages, selected_indices, rules):
        batches = []
        capabilities_by_printer = {}
        for index in selected_indices:
            rule = rules.resolve(pages[index])
            printer_name = self._resolve_printer_name(rule.printer_name)
            printer_key = printer_name.casefold()
            capabilities = capabilities_by_printer.get(printer_key)
            if capabilities is None:
                capabilities = self._printers.ambil_kemampuan_printer(printer_name)
                capabilities_by_printer[printer_key] = capabilities
            source = None
            if rule.paper_source is not None:
                source = next((choice for choice in capabilities.sources
                               if choice.name.casefold() == rule.paper_source.casefold()), None)
            paper = next((choice for choice in capabilities.paper_sizes
                          if self._matches_paper_size(choice.name, rule.paper_size)), None)
            if rule.paper_source is not None and source is None:
                raise ValueError(
                    f"Sumber kertas '{rule.paper_source}' tidak ditemukan pada {rule.printer_name}."
                )
            if paper is None:
                raise ValueError(
                    f"Ukuran kertas '{rule.paper_size}' tidak ditemukan pada {rule.printer_name}."
                )
            options = PrintOptions(source.id if source else None, paper.id)
            if batches and self._same_route(batches[-1], index, printer_name, options):
                previous = batches[-1]
                batches[-1] = PrintBatch(
                    previous.printer_name, previous.page_indices + (index,), options
                )
            else:
                batches.append(PrintBatch(printer_name, (index,), options))
        return tuple(batches)

    def _resolve_printer_name(self, configured_name):
        """Resolve a configured model prefix to the exact Windows queue name."""
        installed = self._printers.ambil_semua_printer()
        configured = " ".join(configured_name.casefold().split())
        exact = next((name for name in installed
                      if " ".join(name.casefold().split()) == configured), None)
        if exact:
            return exact

        # Treat TOML names as literal model names, not user-supplied regex.
        prefix = re.compile(r"^" + re.escape(configured) + r"(?:\b|$)", re.IGNORECASE)
        matches = [name for name in installed if prefix.search(" ".join(name.split()))]
        if not matches:
            raise ValueError(
                f"Printer '{configured_name}' tidak ditemukan. Periksa nama di automated-print.toml."
            )

        # Prefer the shortest matching queue name, and avoid a '(Copy N)' queue
        # when Windows also exposes the primary queue for the same printer.
        return min(matches, key=lambda name: (
            len(name.split()) - len(configured_name.split()),
            bool(re.search(r"\(copy\s+\d+\)", name, re.IGNORECASE)),
            name.casefold(),
        ))

    @staticmethod
    def _same_route(batch, page_index, printer_name, options):
        return (
            batch.page_indices[-1] + 1 == page_index
            and batch.printer_name.casefold() == printer_name.casefold()
            and batch.options == options
        )

    @staticmethod
    def _matches_paper_size(driver_name, configured_name):
        driver_tokens = driver_name.casefold().split()
        configured_tokens = configured_name.casefold().split()
        return bool(driver_tokens and configured_tokens and (
            driver_name.casefold() == configured_name.casefold()
            or driver_tokens[0] == configured_tokens[0]
        ))
