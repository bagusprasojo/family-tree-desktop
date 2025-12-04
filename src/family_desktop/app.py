from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .database import init_db
from .services.people import ensure_people
from .services.users import ensure_default_admin
from .ui.login import LoginFrame
from .ui.main import MainFrame

SAMPLE_PEOPLE = [
    {"name": "Ahmad", "gender": "male", "birth_date": "1960-01-01"},
    {"name": "Siti", "gender": "female", "birth_date": "1965-03-12"},
    {"name": "Budi", "gender": "male", "birth_date": "1990-07-21"},
    {"name": "Ani", "gender": "female", "birth_date": "1995-11-05"},
]


class FamilyApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Family Tree Desktop")
        self.geometry("1200x720")
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.current_frame: tk.Frame | None = None
        init_db()
        ensure_default_admin()
        ensure_people(SAMPLE_PEOPLE)
        self.show_login()

    def show_login(self):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = LoginFrame(self, self._on_login_success)
        self.current_frame.pack(fill="both", expand=True)

    def _on_login_success(self, user: dict):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = MainFrame(self, user)
        self.current_frame.pack(fill="both", expand=True)


def main():
    app = FamilyApp()
    app.mainloop()


if __name__ == "__main__":
    main()

