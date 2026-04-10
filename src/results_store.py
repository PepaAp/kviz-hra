import json
from pathlib import Path
from typing import List


class ResultsStore:
    def __init__(self, results_file: Path):
        self.results_file = results_file

    def load(self) -> List[dict]:
        try:
            if self.results_file.exists():
                with open(self.results_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data if isinstance(data, list) else []
            return []
        except Exception:
            return []

    def append(self, result: dict) -> None:
        existing = self.load()
        existing.append(result)
        self.results_file.parent.mkdir(parents=True, exist_ok=True)
        self.results_file.write_text(
            json.dumps(existing, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
