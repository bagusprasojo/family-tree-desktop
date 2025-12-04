from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from ..services import users


class LoginFrame(ttk.Frame):
    def __init__(self, master: tk.Misc, on_success):
        super().__init__(master, padding=30)
        self.on_success = on_success
        self.columnconfigure(0, weight=1)
        ttk.Label(self, text="Family Tree Login", font=("Segoe UI", 16, "bold")).grid(
            row=0, column=0, sticky="ew", pady=(0, 20)
        )
        self.username_var = tk.StringVar(value="admin")
        self.password_var = tk.StringVar()
        self._build_form()

    def _build_form(self):
        form = ttk.Frame(self)
        form.grid(row=1, column=0, sticky="nsew")
        ttk.Label(form, text="Username").grid(row=0, column=0, sticky="w")
        username_entry = ttk.Entry(form, textvariable=self.username_var)
        username_entry.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        username_entry.focus()

        ttk.Label(form, text="Password").grid(row=2, column=0, sticky="w")
        password_entry = ttk.Entry(form, textvariable=self.password_var, show="*")
        password_entry.grid(row=3, column=0, sticky="ew")
        password_entry.bind("<Return>", lambda _: self._attempt_login())

        ttk.Button(self, text="Login", command=self._attempt_login).grid(
            row=2, column=0, pady=20, sticky="ew"
        )

    def _attempt_login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        if not username or not password:
            messagebox.showwarning("Login", "Username dan password wajib diisi")
            return
        user = users.authenticate(username, password)
        if not user:
            messagebox.showerror("Login", "Kredensial salah")
            return
        self.on_success(user)

