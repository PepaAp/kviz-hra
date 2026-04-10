import tkinter as tk
from tkinter import simpledialog, ttk
from PIL import Image, ImageTk, ImageDraw
import urllib.request
import io
import random
from pathlib import Path

from src.crypto import encode_answer, decode_answer, decode_value
from src.data_store import QuizDataStore
from src.game import GameState
from src.models import GridCell
from src.results_store import ResultsStore


THEMES = {
    "light": {
        "bg": "#ecf0f1",
        "panel": "#1a252f",
        "panel_text": "#bdc3c7",
        "text": "#2c3e50",
        "muted": "#7f8c8d",
        "card": "#ffffff",
        "accent": "#27ae60",
        "info": "#3498db",
        "danger": "#e74c3c",
        "warning": "#f39c12",
        "hint": "#3498db",
        "skip": "#8e44ad",
        "tile": "#34495e",
        "tile_border": "#2c3e50",
        "tile_text": "#ecf0f1",
        "tile_num": "#95a5a6",
        "answer_box": "#e74c3c",
    },
    "dark": {
        "bg": "#0f1419",
        "panel": "#111821",
        "panel_text": "#9aa6b2",
        "text": "#e6edf3",
        "muted": "#9aa6b2",
        "card": "#1a2330",
        "accent": "#2ecc71",
        "info": "#4aa3ff",
        "danger": "#e0565b",
        "warning": "#f0b429",
        "hint": "#4aa3ff",
        "skip": "#9b59b6",
        "tile": "#273442",
        "tile_border": "#1f2a36",
        "tile_text": "#e6edf3",
        "tile_num": "#9aa6b2",
        "answer_box": "#b23a3a",
    },
}


def get_theme_name() -> str:
    return "light"


def get_theme() -> dict:
    name = get_theme_name()
    return THEMES.get(name, THEMES["dark"])


class ImageCache:
    cache = {}

    @classmethod
    def get_image(cls, url, question_id=None):
        if url in cls.cache:
            return cls.cache[url]
        if url and not url.startswith("http"):
            path = Path(url)
            if path.exists():
                img = Image.open(path).convert("RGB")
                cls.cache[url] = img
                return img
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                img_data = response.read()
            img = Image.open(io.BytesIO(img_data)).convert("RGB")
            cls.cache[url] = img
            return img
        except Exception as e:
            if question_id is None:
                print(f"Image load failed: {e}")
            else:
                print(f"Image load failed (id={question_id}): {e}")
            colors = ["#3498db", "#2ecc71", "#e74c3c", "#f39c12", "#9b59b6"]
            img = Image.new("RGB", (450, 450), color=colors[random.randint(0, 4)])
            draw = ImageDraw.Draw(img)
            draw.text((50, 200), "Image load failed", fill="white")
            return img


class WelcomeUI:
    def __init__(self, root):
        self.root = root
        self.theme = get_theme()
        for widget in self.root.winfo_children():
            widget.destroy()

        frame = tk.Frame(self.root, bg=self.theme["bg"])
        frame.pack(expand=True, fill=tk.BOTH)

        tk.Label(
            frame,
            text="VITEJTE VE HRE",
            font=("Segoe UI", 36, "bold"),
            bg=self.theme["bg"],
            fg=self.theme["text"],
        ).pack(pady=(150, 20))
        tk.Label(
            frame,
            text="Zahrajte si kviz, odhalte obrazek a uhodnete tajenku!",
            font=("Segoe UI", 16),
            bg=self.theme["bg"],
            fg=self.theme["muted"],
        ).pack(pady=(0, 60))

        tk.Button(
            frame,
            text="HRAT",
            font=("Segoe UI", 24, "bold"),
            bg=self.theme["accent"],
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.start_game,
            padx=40,
            pady=15,
        ).pack(pady=20)

        tk.Button(
            frame,
            text="Administrace",
            font=("Segoe UI", 12),
            bg=self.theme["panel"],
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.open_admin,
            padx=10,
            pady=5,
        ).pack(pady=50)

    def start_game(self):
        username = simpledialog.askstring("Prihlaseni", "Zadejte vase jmeno:", parent=self.root)
        if not username or not username.strip():
            return

        gs = GameState()
        if not gs.questions:
            self.show_popup("Chyba", "Zadne otazky v databazi! Pridejte otazky pres administraci.")
            return

        gs.username = username.strip()
        if gs.username.lower() == "demo":
            gs.points = 1000
        QuizUI(self.root, gs)

    def open_admin(self):
        pwd = simpledialog.askstring("Admin", "Zadejte heslo administratora (admin):", show="*", parent=self.root)
        if pwd == "admin":
            AdminUI(self.root)
        elif pwd is not None:
            self.show_popup("Chyba", "Spatne heslo!")

    def show_popup(self, title, message):
        popup = tk.Toplevel(self.root)
        popup.title(title)
        popup.geometry("400x150")
        popup.configure(bg=self.theme["bg"])
        tk.Label(
            popup,
            text=message,
            font=("Segoe UI", 12),
            bg=self.theme["bg"],
            fg=self.theme["danger"],
            wraplength=380,
        ).pack(expand=True, pady=20)
        btn = tk.Button(
            popup,
            text="OK",
            command=popup.destroy,
            bg=self.theme["danger"],
            fg="white",
            font=("Segoe UI", 12, "bold"),
            width=10,
        ).pack(pady=10)
        popup.bind("<Return>", lambda _e: popup.destroy())
        btn.bind("<Return>", lambda _e: popup.destroy())
        btn.focus_set()


class AdminUI:
    def __init__(self, root):
        self.root = root
        self.theme = get_theme()
        self.data_file = Path(__file__).parent.parent / "data.json"
        self.results_file = Path(__file__).parent.parent / "data" / "results.json"
        self.data_store = QuizDataStore(self.data_file)
        self.results_store = ResultsStore(self.results_file)

        for widget in self.root.winfo_children():
            widget.destroy()

        frame = tk.Frame(self.root, bg=self.theme["bg"])
        frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        top_frame = tk.Frame(frame, bg=self.theme["bg"])
        top_frame.pack(fill=tk.X)
        tk.Label(
            top_frame,
            text="ADMINISTRACE OTAZEK",
            font=("Segoe UI", 24, "bold"),
            bg=self.theme["bg"],
            fg=self.theme["text"],
        ).pack(side=tk.LEFT)
        tk.Button(
            top_frame,
            text="Zpet do menu",
            bg=self.theme["danger"],
            fg="white",
            font=("Segoe UI", 12),
            relief=tk.FLAT,
            command=lambda: WelcomeUI(self.root),
        ).pack(side=tk.RIGHT)

        self.tree = ttk.Treeview(frame, columns=("ID", "Category", "Answer", "URL"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Category", text="Kategorie")
        self.tree.heading("Answer", text="Odpoved")
        self.tree.heading("URL", text="Obrazek URL")
        self.tree.column("ID", width=50)
        self.tree.column("Category", width=150)
        self.tree.column("Answer", width=150)
        self.tree.pack(fill=tk.BOTH, expand=True, pady=20)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        tk.Label(
            frame,
            text="Vysledky",
            font=("Segoe UI", 14, "bold"),
            bg=self.theme["bg"],
            fg=self.theme["text"],
        ).pack(anchor="w", pady=(10, 5))

        self.results_tree = ttk.Treeview(
            frame,
            columns=("Time", "Username", "Score", "Elapsed", "Won"),
            show="headings",
        )
        self.results_tree.heading("Time", text="Cas")
        self.results_tree.heading("Username", text="Uzivatel")
        self.results_tree.heading("Score", text="Body")
        self.results_tree.heading("Elapsed", text="Cas hry (s)")
        self.results_tree.heading("Won", text="Vyhra")
        self.results_tree.column("Time", width=140)
        self.results_tree.column("Username", width=140)
        self.results_tree.column("Score", width=80)
        self.results_tree.column("Elapsed", width=100)
        self.results_tree.column("Won", width=60)
        self.results_tree.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        form = tk.Frame(frame, bg=self.theme["bg"])
        form.pack(fill=tk.X)

        tk.Label(form, text="Odpoved:", bg=self.theme["bg"], fg=self.theme["text"]).grid(row=0, column=0, sticky="w")
        self.ent_ans = tk.Entry(form, width=30)
        self.ent_ans.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form, text="Kategorie:", bg=self.theme["bg"], fg=self.theme["text"]).grid(row=0, column=2, sticky="w")
        self.ent_cat = tk.Entry(form, width=20)
        self.ent_cat.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(form, text="URL obrazku:", bg=self.theme["bg"], fg=self.theme["text"]).grid(row=1, column=0, sticky="w")
        self.ent_url = tk.Entry(form, width=50)
        self.ent_url.grid(row=1, column=1, columnspan=3, sticky="w", padx=5, pady=5)

        btns = tk.Frame(frame, bg=self.theme["bg"])
        btns.pack(fill=tk.X, pady=10)

        tk.Button(btns, text="Pridat", bg="#2ecc71", fg="white", command=self.add_question).pack(
            side=tk.LEFT, padx=5
        )
        tk.Button(btns, text="Aktualizovat", bg="#f39c12", fg="white", command=self.update_question).pack(
            side=tk.LEFT, padx=5
        )
        tk.Button(btns, text="Smazat", bg="#e74c3c", fg="white", command=self.delete_question).pack(
            side=tk.LEFT, padx=5
        )
        tk.Button(btns, text="Vycistit formular", bg="#bdc3c7", fg="black", command=self.clear_form).pack(
            side=tk.LEFT, padx=5
        )

        self.selected_id = None
        self.load_data()

    def load_data(self):
        self.data = self.data_store.load_raw()
        self.refresh_list()
        self.load_results()

    def load_results(self):
        self.results = self.results_store.load()
        self.refresh_results()

    def refresh_results(self):
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        for r in self.results or []:
            username = r.get("username")
            score = r.get("score")
            elapsed = r.get("elapsed_seconds")

            if username is None and r.get("username_enc"):
                username = decode_value(r.get("username_enc", ""))
            if score is None and r.get("score_enc"):
                decoded_score = decode_value(r.get("score_enc", ""))
                score = int(decoded_score) if decoded_score and decoded_score.isdigit() else decoded_score
            if elapsed is None and r.get("elapsed_enc"):
                decoded_elapsed = decode_value(r.get("elapsed_enc", ""))
                elapsed = int(decoded_elapsed) if decoded_elapsed and decoded_elapsed.isdigit() else decoded_elapsed

            self.results_tree.insert(
                "",
                "end",
                values=(
                    r.get("timestamp", ""),
                    username or "",
                    score if score is not None else "",
                    "" if elapsed is None else elapsed,
                    "Ano" if r.get("won") else "Ne",
                ),
            )

    def save_data(self):
        self.data_store.save_raw(self.data)

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for q in self.data.get("questions", []):
            decoded = decode_answer(q.get("answer_enc", ""))
            answer_text = decoded if decoded else q.get("answer_mask", "Tajne")
            self.tree.insert(
                "",
                "end",
                values=(q["id"], q["category"], answer_text, q.get("image_url", "")),
            )

    def clear_form(self):
        self.selected_id = None
        self.ent_ans.delete(0, tk.END)
        self.ent_cat.delete(0, tk.END)
        self.ent_url.delete(0, tk.END)

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        item = self.tree.item(sel[0])["values"]
        self.selected_id = int(item[0])
        self.ent_cat.delete(0, tk.END)
        self.ent_cat.insert(0, item[1])
        self.ent_ans.delete(0, tk.END)
        self.ent_ans.insert(0, item[2])
        self.ent_url.delete(0, tk.END)
        self.ent_url.insert(0, item[3])

    def show_popup(self, title, message):
        popup = tk.Toplevel(self.root)
        popup.title(title)
        popup.geometry("400x150")
        popup.configure(bg=self.theme["bg"])
        tk.Label(
            popup,
            text=message,
            font=("Segoe UI", 12),
            bg=self.theme["bg"],
            fg=self.theme["text"] if title == "OK" else self.theme["danger"],
            wraplength=380,
        ).pack(expand=True, pady=20)
        btn = tk.Button(
            popup,
            text="OK",
            command=popup.destroy,
            bg=self.theme["accent"] if title == "OK" else self.theme["danger"],
            fg="white",
            font=("Segoe UI", 12, "bold"),
            width=10,
        ).pack(pady=10)
        popup.bind("<Return>", lambda _e: popup.destroy())
        btn.bind("<Return>", lambda _e: popup.destroy())
        btn.focus_set()

    def add_question(self):
        ans = self.ent_ans.get().strip()
        cat = self.ent_cat.get().strip()
        url = self.ent_url.get().strip()
        if not ans or not url:
            self.show_popup("Chyba", "Odpoved a URL jsou povinne!")
            return

        import hashlib
        import unicodedata
        import re

        def norm(t):
            return re.sub(
                r"[^a-z0-9]",
                "",
                unicodedata.normalize("NFKD", t).encode("ASCII", "ignore").decode("utf-8").lower(),
            )

        answer_hash = hashlib.sha256(norm(ans).encode("utf-8")).hexdigest()
        answer_mask = "".join(" " if c == " " else "*" for c in ans)
        answer_enc = encode_answer(ans)

        questions = self.data.setdefault("questions", [])
        new_id = max([q["id"] for q in questions], default=0) + 1
        questions.append(
            {
                "id": new_id,
                "category": cat,
                "answer_hash": answer_hash,
                "answer_length": len(ans),
                "answer_mask": answer_mask,
                "answer_enc": answer_enc,
                "image_url": url,
            }
        )
        self.save_data()
        self.refresh_list()
        self.clear_form()
        self.show_popup("OK", "Otazka pridana.")

    def update_question(self):
        if not self.selected_id:
            return
        ans = self.ent_ans.get().strip()
        for q in self.data["questions"]:
            if q["id"] == self.selected_id:
                new_url = self.ent_url.get().strip()
                old_url = q.get("image_url", "")
                if ans != q.get("answer_mask", "Tajne") and "*" not in ans:
                    import hashlib
                    import unicodedata
                    import re

                    def norm(t):
                        return re.sub(
                            r"[^a-z0-9]",
                            "",
                            unicodedata.normalize("NFKD", t)
                            .encode("ASCII", "ignore")
                            .decode("utf-8")
                            .lower(),
                        )

                    q["answer_hash"] = hashlib.sha256(norm(ans).encode("utf-8")).hexdigest()
                    q["answer_length"] = len(ans)
                    q["answer_mask"] = "".join(" " if c == " " else "*" for c in ans)
                    q["answer_enc"] = encode_answer(ans)

                q["category"] = self.ent_cat.get().strip()
                if new_url != old_url:
                    q["image_filename"] = ""
                    q.pop("image_query", None)
                q["image_url"] = new_url
                if not q.get("image_filename"):
                    q.pop("image_filename", None)
                if not q.get("image_query"):
                    q.pop("image_query", None)
                break
        self.save_data()
        self.refresh_list()
        ImageCache.cache.clear()
        self.show_popup("OK", "Otazka upravena.")

    def delete_question(self):
        if not self.selected_id:
            return
        self.data["questions"] = [q for q in self.data["questions"] if q["id"] != self.selected_id]
        self.save_data()
        self.refresh_list()
        self.clear_form()
        self.show_popup("OK", "Otazka smazana.")


class QuizUI:
    def __init__(self, root, game_state: GameState):
        self.root = root
        self.game_state = game_state
        self.theme = get_theme()

        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.configure(bg=self.theme["bg"])
        self.original_image = None
        self.current_image = None
        self.image_tk = None
        self.timer_job = None
        self.load_token = 0
        self.is_loading = False
        self.skip_in_progress = False

        self.setup_ui()
        self.start_round()

    def start_round(self):
        self.stop_timer()
        self.game_state.reset_game(keep_points=True)
        if not self.game_state.current_question:
            self.game_state.game_active = False
            self.game_state.save_result(won=True)
            self.show_overlay(
                "Konec",
                "Prosli jste vsechny otazky.\nSpustte novou hru pro opakovani.",
                self.theme["info"],
                is_end=True,
            )
            return
        self.game_state.game_active = True
        ImageCache.cache.clear()
        self.load_image_async()
        self.update_display()
        self.update_timer()

    def stop_timer(self):
        if self.timer_job is not None:
            self.root.after_cancel(self.timer_job)
            self.timer_job = None

    def update_timer(self):
        if self.game_state.game_active and self.game_state.time_remaining > 0:
            self.game_state.time_remaining -= 1
            self.update_display()
            self.timer_job = self.root.after(1000, self.update_timer)
        elif self.game_state.game_active and self.game_state.time_remaining <= 0:
            self.game_state.game_active = False
            self.stop_timer()
            self.game_state.save_result(won=False)
            self.show_overlay(
                "Konec",
                f"Cas vyprsel!\nZiskali jste {self.game_state.points} bodu.",
                "#e74c3c",
                is_end=True,
            )

    def show_overlay(self, title, message, color, is_end=False, is_correct=False):
        overlay = tk.Frame(self.root, highlightthickness=4, highlightbackground=color, bg=self.theme["card"])
        overlay.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=500, height=250)

        tk.Label(
            overlay,
            text=title,
            font=("Segoe UI", 24, "bold"),
            bg=self.theme["card"],
            fg=color,
        ).pack(pady=(30, 10))
        tk.Label(
            overlay,
            text=message,
            font=("Segoe UI", 16),
            bg=self.theme["card"],
            fg=self.theme["text"],
        ).pack(pady=10)

        btn = tk.Button(
            overlay,
            text="ZAVRIT TUTO ZPRAVU A POKRACOVAT" if not is_end else "ZPET DO MENU",
            command=lambda: self.close_overlay(overlay, is_end, is_correct),
            bg=color,
            activebackground=color,
            fg="white",
            font=("Segoe UI", 14, "bold"),
            padx=20,
            pady=10,
            relief=tk.FLAT,
            cursor="hand2",
        )
        btn.pack(pady=10)
        btn.focus_set()
        overlay.bind("<Return>", lambda _e: self.close_overlay(overlay, is_end, is_correct))
        btn.bind("<Return>", lambda _e: self.close_overlay(overlay, is_end, is_correct))

    def close_overlay(self, overlay, is_end, is_correct):
        overlay.destroy()
        if is_end:
            WelcomeUI(self.root)
        elif is_correct:
            self.start_round()

    def load_image_async(self):
        if not self.game_state.current_question:
            return
        question = self.game_state.current_question
        self.load_token += 1
        load_token = self.load_token
        url = question.image_url
        local_path = None
        if not url and getattr(question, "image_filename", ""):
            local_path = Path(__file__).parent.parent / "images" / question.image_filename
            if local_path.exists():
                url = str(local_path)

        self.is_loading = True
        self.set_controls_enabled(False)
        self.original_image = None
        self.image_label.config(image="")
        self.image_label.config(cursor="watch")

        load_id = question.id
        load_url = url

        def bg_load():
            img = ImageCache.get_image(url, load_id)
            if img.size != (450, 450):
                img = img.resize((450, 450), Image.Resampling.LANCZOS)
            if (
                not self.game_state.current_question
                or self.game_state.current_question.id != load_id
                or self.game_state.current_question.image_url != load_url
                or self.load_token != load_token
            ):
                return
            self.original_image = img
            self.root.after(0, self.finish_load_image)

        import threading

        threading.Thread(target=bg_load, daemon=True).start()

    def finish_load_image(self):
        self.image_label.config(cursor="")
        self.update_grid_display()
        self.is_loading = False
        self.skip_in_progress = False
        self.set_controls_enabled(True)

    def set_controls_enabled(self, enabled: bool):
        state = tk.NORMAL if enabled else tk.DISABLED
        self.answer_input.config(state=state)
        self.submit_button.config(state=state)
        self.hint_button.config(state=state)
        self.skip_button.config(state=state)

    def setup_ui(self):
        top_panel = tk.Frame(self.root, bg=self.theme["panel"], relief=tk.FLAT, height=90)
        top_panel.pack(fill=tk.X, padx=0, pady=0)
        top_panel.pack_propagate(False)

        score_frame = tk.Frame(top_panel, bg=self.theme["panel"])
        score_frame.pack(side=tk.LEFT, padx=30, pady=15)
        tk.Label(score_frame, text="SKORE", font=("Segoe UI", 10, "bold"), bg=self.theme["panel"], fg=self.theme["panel_text"]).pack()
        self.score_label = tk.Label(score_frame, text="0", font=("Segoe UI", 22, "bold"), bg=self.theme["panel"], fg=self.theme["accent"])
        self.score_label.pack()

        time_frame = tk.Frame(top_panel, bg=self.theme["panel"])
        time_frame.pack(side=tk.RIGHT, padx=30, pady=15)
        tk.Label(time_frame, text="ZBYVA CAS", font=("Segoe UI", 10, "bold"), bg=self.theme["panel"], fg=self.theme["panel_text"]).pack()
        self.time_label = tk.Label(time_frame, text="00:00", font=("Segoe UI", 22, "bold"), bg=self.theme["panel"], fg=self.theme["info"])
        self.time_label.pack()

        cat_frame = tk.Frame(top_panel, bg=self.theme["panel"])
        cat_frame.pack(side=tk.TOP, padx=20, pady=15)
        self.category_label = tk.Label(cat_frame, text="KATEGORIE: -", font=("Segoe UI", 14, "bold"), bg=self.theme["panel"], fg=self.theme["warning"])
        self.category_label.pack()

        middle_panel = tk.Frame(self.root, bg=self.theme["bg"])
        middle_panel.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(middle_panel, text="ODHAL OBRAZEK A UHOD TAJENKU", font=("Segoe UI", 16, "bold"), bg=self.theme["bg"], fg=self.theme["text"]).pack(pady=(0, 10))

        image_frame = tk.Frame(middle_panel, bg="white", highlightthickness=0, bd=0)
        image_frame.pack(pady=5, fill=tk.BOTH, expand=True)
        outer_frame = tk.Frame(image_frame, bg="#bdc3c7", padx=3, pady=3)
        outer_frame.pack(expand=True)

        self.image_label = tk.Label(outer_frame, bg="white", bd=0)
        self.image_label.pack(fill=tk.BOTH, expand=True)
        self.image_label.bind("<Button-1>", self.on_image_click)

        bottom_panel = tk.Frame(self.root, bg=self.theme["card"], relief=tk.FLAT, bd=0)
        bottom_panel.pack(fill=tk.X, ipadx=20, ipady=15)

        tk.Label(bottom_panel, text="VASE TAJENKA", font=("Segoe UI", 12, "bold"), bg=self.theme["card"], fg=self.theme["muted"]).pack(anchor=tk.N)

        self.answer_canvas = tk.Canvas(bottom_panel, bg=self.theme["card"], height=80, relief=tk.FLAT, highlightthickness=0)
        self.answer_canvas.pack(fill=tk.X, pady=10)

        input_frame = tk.Frame(bottom_panel, bg=self.theme["card"])
        input_frame.pack(fill=tk.X, pady=10)

        self.answer_input = tk.Entry(input_frame, font=("Segoe UI", 18), width=35, relief=tk.SOLID, bd=1, justify="center")
        self.answer_input.pack(side=tk.TOP, pady=5)
        self.answer_input.bind("<Return>", lambda e: self.on_submit_answer())

        button_frame = tk.Frame(bottom_panel, bg=self.theme["card"])
        button_frame.pack(fill=tk.X, pady=(10, 20))

        self.submit_button = tk.Button(
            button_frame,
            text="Odeslat odpoved",
            command=self.on_submit_answer,
            bg=self.theme["accent"],
            activebackground=self.theme["accent"],
            fg="white",
            font=("Segoe UI", 14, "bold"),
            padx=30,
            pady=10,
            relief=tk.FLAT,
            cursor="hand2",
        )
        self.submit_button.pack(side=tk.LEFT, expand=True)

        self.hint_button = tk.Button(
            button_frame,
            text="Napoveda",
            command=self.on_hint_click,
            bg=self.theme["hint"],
            activebackground=self.theme["hint"],
            fg="white",
            font=("Segoe UI", 14, "bold"),
            padx=20,
            pady=10,
            relief=tk.FLAT,
            cursor="hand2",
        )
        self.hint_button.pack(side=tk.LEFT, expand=True)

        self.skip_button = tk.Button(
            button_frame,
            text="Preskocit",
            command=self.on_skip_click,
            bg=self.theme["skip"],
            activebackground=self.theme["skip"],
            fg="white",
            font=("Segoe UI", 12, "bold"),
            padx=20,
            pady=10,
            relief=tk.FLAT,
            cursor="hand2",
        )
        self.skip_button.pack(side=tk.LEFT, expand=True)

        tk.Button(
            button_frame,
            text="Zpet do menu",
            command=lambda: WelcomeUI(self.root),
            bg=self.theme["danger"],
            activebackground=self.theme["danger"],
            fg="white",
            font=("Segoe UI", 12),
            padx=20,
            pady=10,
            relief=tk.FLAT,
            cursor="hand2",
        ).pack(side=tk.RIGHT, padx=20)

    def update_display(self):
        color = self.theme["accent"] if self.game_state.points >= 50 else self.theme["warning"] if self.game_state.points >= 10 else self.theme["danger"]
        self.score_label.config(text=str(self.game_state.points), fg=color)
        mins = self.game_state.time_remaining // 60
        secs = self.game_state.time_remaining % 60
        self.time_label.config(text=f"{mins:01d}:{secs:02d}")
        if self.game_state.current_question:
            self.category_label.config(text=f"Kategorie: {self.game_state.current_question.category}")
        self.update_answer_display()

    def update_grid_display(self):
        if not self.original_image:
            return
        self.current_image = self.original_image.copy()
        draw = ImageDraw.Draw(self.current_image)
        cell_size = 450 // self.game_state.grid_size
        for cell_idx in range(self.game_state.grid_size ** 2):
            if cell_idx not in self.game_state.revealed_cells:
                cell = GridCell(cell_idx, self.game_state.grid_size)
                x1, y1, x2, y2 = cell.get_bounds(cell_size)
                draw.rectangle([x1, y1, x2, y2], fill=self.theme["tile"], outline=self.theme["tile_border"], width=2)
                draw.text((x1 + cell_size // 2 - 15, y1 + cell_size // 2 - 20), "?", fill=self.theme["tile_text"])
                draw.text((x1 + 5, y1 + 5), str(cell_idx + 1), fill=self.theme["tile_num"])
        self.image_tk = ImageTk.PhotoImage(self.current_image)
        self.image_label.config(image=self.image_tk)

    def update_answer_display(self):
        if not self.game_state.current_question:
            return
        q = self.game_state.current_question
        self.answer_canvas.delete("all")
        char_width = 50

        mask = getattr(q, "answer_mask", "*" * getattr(q, "answer_length", 10))
        total_width = len(mask) * char_width
        self.answer_canvas.update_idletasks()
        canvas_width = self.answer_canvas.winfo_width()
        if canvas_width < total_width + 60:
            canvas_width = total_width + 60
            self.answer_canvas.config(width=canvas_width)
        start_x = max(10, (canvas_width - total_width) // 2)

        y = 35

        answer_text = self.game_state.get_answer_text()

        for i, char in enumerate(mask):
            x = start_x + i * char_width
            if char.strip():
                self.answer_canvas.create_rectangle(x, y - 20, x + 40, y + 30, fill=self.theme["answer_box"], outline=self.theme["tile_border"], width=2)
                letter = ""
                if answer_text and i in self.game_state.revealed_letters:
                    letter = answer_text[i].upper()
                self.answer_canvas.create_text(x + 20, y + 5, text=letter, font=("Arial", 16, "bold"), fill=self.theme["tile_text"])
            else:
                self.answer_canvas.create_text(x + 20, y + 5, text="-", font=("Arial", 20, "bold"), fill=self.theme["muted"])

    def on_hint_click(self):
        if not self.game_state.game_active or self.is_loading or not self.game_state.current_question:
            return
        if not hasattr(self.game_state, "reveal_letter_hint"):
            return

        if self.game_state.reveal_letter_hint():
            self.update_display()
            if self.game_state.points < 0:
                self.game_state.game_active = False
                self.game_state.save_result(won=False)
                self.show_overlay("Konec hadani", "Skoncily vam body!", "#e74c3c", is_end=True)

    def on_skip_click(self):
        if not self.game_state.game_active or self.is_loading or self.skip_in_progress:
            return
        self.skip_in_progress = True
        if not self.game_state.skip_question():
            self.skip_in_progress = False
            self.game_state.game_active = False
            self.game_state.save_result(won=True)
            self.show_overlay(
                "Konec",
                "Prosli jste vsechny otazky.\nSpustte novou hru pro opakovani.",
                self.theme["info"],
                is_end=True,
            )
            return
        if self.game_state.points < 0:
            self.game_state.game_active = False
            self.game_state.save_result(won=False)
            self.show_overlay("Konec", "Skoncily vam body!", "#e74c3c", is_end=True)
            return
        if not self.game_state.current_question:
            self.game_state.game_active = False
            self.game_state.save_result(won=True)
            self.show_overlay(
                "Konec",
                "Prosli jste vsechny otazky.\nSpustte novou hru pro opakovani.",
                self.theme["info"],
                is_end=True,
            )
            return
        self.load_image_async()
        self.update_display()

    def on_image_click(self, event):
        if not self.game_state.game_active or not self.current_image or self.is_loading:
            return
        w, h = self.image_label.winfo_width(), self.image_label.winfo_height()
        if w <= 1 or h <= 1:
            return
        xo, yo = max(0, (w - 450) // 2), max(0, (h - 450) // 2)
        ix, iy = event.x - xo, event.y - yo
        if ix < 0 or iy < 0 or ix >= 450 or iy >= 450:
            return
        cell_idx = GridCell.get_cell_from_click(ix, iy, self.game_state.grid_size, 450, 450)

        if cell_idx in self.game_state.revealed_cells:
            return

        if cell_idx >= 0 and self.game_state.reveal_cell(cell_idx):
            self.update_display()
            self.update_grid_display()
            if self.game_state.points < 0:
                self.game_state.game_active = False
                self.game_state.save_result(won=False)
                self.show_overlay("Konec hadani", "Skoncily vam body!", "#e74c3c", is_end=True)

    def on_submit_answer(self, event=None):
        if not self.game_state.game_active or self.is_loading:
            return
        ans = self.answer_input.get().strip()
        if not ans:
            return

        is_correct = self.game_state.check_answer(ans)
        self.answer_input.delete(0, tk.END)
        self.update_display()

        if is_correct:
            self.show_overlay(
                "Spravne!",
                f"Spravne!\n+{self.game_state.config.get('correct_answer_bonus', 20)} bodu",
                "#27ae60",
                is_correct=True,
            )
        else:
            if self.game_state.points < 0:
                self.game_state.game_active = False
                self.game_state.save_result(won=False)
                self.show_overlay(
                    "Konec",
                    f"Spatna odpoved!\nZtracite {abs(self.game_state.config.get('wrong_answer_penalty', -5))} bodu\n\nSkoncily vam body!",
                    "#e74c3c",
                    is_end=True,
                )
            else:
                self.show_overlay(
                    "Spatne",
                    f"Spatna odpoved!\nZtracite {abs(self.game_state.config.get('wrong_answer_penalty', -5))} bodu",
                    "#e67e22",
                )
