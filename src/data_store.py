import json
from pathlib import Path
from typing import List, Tuple

from src.models import Question


class QuizDataStore:
    def __init__(self, data_file: Path):
        self.data_file = data_file

    def load_raw(self) -> dict:
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return {"config": {}, "questions": []}
            return data
        except Exception:
            return {"config": {}, "questions": []}

    def save_raw(self, data: dict) -> None:
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self) -> Tuple[dict, List[Question]]:
        data = self.load_raw()
        config = data.get("config", {})
        questions = [Question(**q) for q in data.get("questions", [])]
        return config, questions
