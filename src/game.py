import random
import time
from pathlib import Path
from typing import Optional
from src.crypto import decode_answer, encode_value, hash_answer, normalize_answer
from src.data_store import QuizDataStore
from src.models import Question
from src.results_store import ResultsStore

class GameState:
    def __init__(self):
        self.data_file = Path(__file__).parent.parent / "data.json"
        self.results_file = Path(__file__).parent.parent / "data" / "results.json"
        self.data_store = QuizDataStore(self.data_file)
        self.results_store = ResultsStore(self.results_file)
        self.played_questions = set()
        self.load_data()
        self.current_question = None
        self.points = self.config.get("initial_points", 50)
        self.time_remaining = self.config.get("time_limit", 600)
        self.game_active = False
        self.grid_size = self.config.get("grid_size", 3)
        self.revealed_cells = set()
        self.revealed_letters = set()
        self.wrong_attempts = 0
        self.username = ""
        self.game_started_at = None
        self.result_saved = False

    def load_data(self):
        try:
            self.config, self.questions = self.data_store.load()
        except Exception as e:
            print("Error loading data:", e)
            self.config = {
                "initial_points": 50,
                "time_limit": 600,
                "grid_size": 3,
                "cell_reveal_cost": -2,
                "wrong_answer_penalty": -5,
                "correct_answer_bonus": 20,
            }
            self.questions = []

    def reset_game(self, keep_points=False):
        self.load_data()
        if self.questions:
            current_ids = {q.id for q in self.questions}
            self.played_questions = {qid for qid in self.played_questions if qid in current_ids}
        self.result_saved = False
        if not keep_points:
            self.points = self.config.get("initial_points", 50)
            self.played_questions.clear()
        self.time_remaining = self.config.get("time_limit", 600)
        self.revealed_cells = set()
        self.revealed_letters = set()
        self.wrong_attempts = 0
        self.game_active = False
        self.game_started_at = time.time()
        if self.questions:
            self.current_question = self._pick_question()

    def _pick_question(self) -> Optional[Question]:
        if not self.questions:
            return None
        unplayed = [q for q in self.questions if q.id not in self.played_questions]
        if not unplayed:
            return None
        question = random.choice(unplayed)
        self.played_questions.add(question.id)
        return question

    def skip_question(self) -> bool:
        if not self.questions:
            return False
        self.points += self.config.get("skip_penalty", -10)
        self.revealed_cells = set()
        self.revealed_letters = set()
        self.wrong_attempts = 0
        self.current_question = self._pick_question()
        return self.current_question is not None

    def get_answer_text(self) -> Optional[str]:
        if not self.current_question:
            return None
        return decode_answer(getattr(self.current_question, "answer_enc", ""))

    def reveal_letter_hint(self) -> bool:
        if not self.current_question:
            return False
        answer = self.get_answer_text()
        if not answer:
            return False
        possible = [i for i, c in enumerate(answer) if c != " " and i not in self.revealed_letters]
        if not possible:
            return False
        idx = random.choice(possible)
        self.revealed_letters.add(idx)
        self.points += self.config.get("hint_cost", -5)
        return True

    def reveal_cell(self, cell_index: int) -> bool:
        if cell_index < 0 or cell_index >= self.grid_size ** 2 or cell_index in self.revealed_cells:
            return False
        self.revealed_cells.add(cell_index)
        self.points += self.config.get("cell_reveal_cost", -2)
        return True

    def check_answer(self, user_answer: str) -> bool:
        if not self.current_question: return False

        user_hash = hash_answer(user_answer)

        if user_hash == self.current_question.answer_hash:
            hidden_cells = (self.grid_size ** 2) - len(self.revealed_cells)
            base_bonus = self.config.get("correct_answer_bonus", 20)
            hidden_bonus = self.config.get("hidden_cell_bonus", 1) * max(hidden_cells, 0)
            self.points += base_bonus + hidden_bonus
            return True

        decoded = self.get_answer_text()
        if decoded and normalize_answer(decoded) == normalize_answer(user_answer):
            hidden_cells = (self.grid_size ** 2) - len(self.revealed_cells)
            base_bonus = self.config.get("correct_answer_bonus", 20)
            hidden_bonus = self.config.get("hidden_cell_bonus", 1) * max(hidden_cells, 0)
            self.points += base_bonus + hidden_bonus
            return True
        
        self.wrong_attempts += 1
        self.points += self.config.get("wrong_answer_penalty", -5)
        return False
        
    def save_result(self, won: bool):
        if self.result_saved:
            return
        if not self.username:
            return

        elapsed = None
        if self.game_started_at:
            elapsed = int(time.time() - self.game_started_at)

        result = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "won": bool(won),
            "username_enc": encode_value(self.username.strip()),
            "score_enc": encode_value(str(int(self.points))),
            "elapsed_enc": encode_value(str(int(elapsed) if elapsed is not None else "")),
        }
        self.results_store.append(result)
        self.result_saved = True

