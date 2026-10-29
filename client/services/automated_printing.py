"""Load developer-owned print rules from TOML."""

from pathlib import Path

from domain.automated_printing import AutomatedPrintRules


class AutomatedPrintRuleRepository:
    def __init__(self, path):
        self.path = Path(path)

    def load(self):
        try:
            import tomllib
        except ModuleNotFoundError:
            import tomli as tomllib
        with self.path.open("rb") as source:
            return AutomatedPrintRules.from_mapping(tomllib.load(source))
