from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from PIL import Image, ImageTk

from ..services import kinship, marriages, people, reports, tree_builder, users


class MainFrame(ttk.Frame):
    def __init__(self, master: tk.Misc, current_user: dict):
        super().__init__(master, padding=10)
        self.current_user = current_user
        self.people_cache: list[dict] = []
        self.marriage_cache: list[dict] = []
        self._tree_image = None
        self._diagram_base_image: Image.Image | None = None
        self._diagram_zoom: float = 1.0
        self._diagram_canvas_image: int | None = None
        self._build_header()
        self._build_tabs()
        self._refresh_all()

    # region Layout helpers
    def _build_header(self):
        header = ttk.Frame(self)
        header.pack(fill="x", pady=(0, 10))
        ttk.Label(
            header,
            text=f"Family Tree Desktop - Logged in as {self.current_user['username']} ({self.current_user['role']})",
            font=("Segoe UI", 12, "bold"),
        ).pack(side="left")
        ttk.Button(header, text="Refresh All", command=self._refresh_all).pack(side="right")

    def _build_tabs(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)
        self.people_tab = ttk.Frame(self.notebook, padding=10)
        self.marriage_tab = ttk.Frame(self.notebook, padding=10)
        self.children_tab = ttk.Frame(self.notebook, padding=10)
        self.diagram_tab = ttk.Frame(self.notebook, padding=10)
        self.report_tab = ttk.Frame(self.notebook, padding=10)
        self.mahram_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.people_tab, text="Data Orang")
        self.notebook.add(self.marriage_tab, text="Data Pernikahan")
        self.notebook.add(self.children_tab, text="Relasi Anak")
        self.notebook.add(self.diagram_tab, text="Diagram")
        self.notebook.add(self.report_tab, text="Laporan")
        self.notebook.add(self.mahram_tab, text="Pencarian Mahram")
        if self.current_user["role"] == "admin":
            self.user_tab = ttk.Frame(self.notebook, padding=10)
            self.notebook.add(self.user_tab, text="Pengguna")
            self._build_user_tab()
        self._build_people_tab()
        self._build_marriage_tab()
        self._build_children_tab()
        self._build_diagram_tab()
        self._build_reports_tab()
        self._build_mahram_tab()

    # endregion
    # region People Tab
    def _build_people_tab(self):
        frame = self.people_tab
        frame.columnconfigure(0, weight=4)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(1, weight=1)
        search_frame = ttk.Frame(frame)
        search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5), padx=(0, 20))
        search_frame.columnconfigure(1, weight=1)
        ttk.Label(search_frame, text="Cari Nama").grid(row=0, column=0, sticky="w")
        self.people_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.people_search_var)
        search_entry.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        self.people_search_var.trace_add("write", lambda *_: self._apply_people_filter())

        columns = ("name", "gender", "birth", "death")
        tree_container = ttk.Frame(frame)
        tree_container.grid(row=1, column=0, sticky="nsew", padx=(0, 20), pady=(0, 5))
        tree_container.columnconfigure(0, weight=1)
        tree_container.rowconfigure(0, weight=1)
        self.people_tree = ttk.Treeview(tree_container, columns=columns, show="headings", height=18)
        self.people_tree.grid(row=0, column=0, sticky="nsew")
        for col in columns:
            self.people_tree.heading(col, text=col.title())
        self.people_tree.bind("<<TreeviewSelect>>", lambda _: self._fill_person_form())
        y_scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.people_tree.yview)
        x_scrollbar = ttk.Scrollbar(tree_container, orient="horizontal", command=self.people_tree.xview)
        self.people_tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        y_scrollbar.grid(row=0, column=1, sticky="ns")
        x_scrollbar.grid(row=1, column=0, sticky="ew", columnspan=2)
        form = ttk.Frame(frame)
        form.grid(row=1, column=1, sticky="nsew")
        form.columnconfigure(0, weight=1)
        form.grid_columnconfigure(1, weight=1)
        self.person_form_vars = {
            "id": tk.IntVar(value=0),
            "name": tk.StringVar(),
            "gender": tk.StringVar(value="male"),
            "birth": tk.StringVar(),
            "death": tk.StringVar(),
        }
        ttk.Label(form, text="Nama").grid(row=0, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.person_form_vars["name"], width=40).grid(row=1, column=0, sticky="w")
        ttk.Label(form, text="Gender").grid(row=2, column=0, sticky="w")
        ttk.Combobox(
            form,
            textvariable=self.person_form_vars["gender"],
            values=("male", "female"),
            state="readonly",
            width=40,
        ).grid(row=3, column=0, sticky="w")
        ttk.Label(form, text="Tanggal Lahir (YYYY-MM-DD)").grid(row=4, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.person_form_vars["birth"], width=40).grid(row=5, column=0, sticky="w")
        ttk.Label(form, text="Tanggal Wafat").grid(row=6, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.person_form_vars["death"], width=40).grid(row=7, column=0, sticky="w")
        ttk.Label(form, text="Catatan").grid(row=8, column=0, sticky="w")
        self.person_notes = tk.Text(form, height=5, width=40)
        self.person_notes.grid(row=9, column=0, sticky="w", pady=(0, 10))
        btn_frame = ttk.Frame(form)
        btn_frame.grid(row=10, column=0, sticky="ew")
        ttk.Button(btn_frame, text="Baru", command=self._reset_person_form).pack(side="left")
        ttk.Button(btn_frame, text="Simpan", command=self._save_person).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Hapus", command=self._delete_person).pack(side="left")

    def refresh_people(self):
        self.people_cache = people.list_people()
        self._apply_people_filter()

    def _apply_people_filter(self):
        if not hasattr(self, "people_tree"):
            return
        term = getattr(self, "people_search_var", None)
        query = (term.get() if term else "").strip().lower()
        rows = self.people_cache
        if query:
            rows = [person for person in rows if query in (person["name"] or "").lower()]
        self.people_tree.delete(*self.people_tree.get_children())
        for person in rows:
            self.people_tree.insert(
                "",
                "end",
                iid=person["id"],
                values=(person["name"], person["gender"], person["birth_date"], person["death_date"]),
            )

    def _fill_person_form(self):
        selection = self.people_tree.selection()
        if not selection:
            return
        iid = int(selection[0])
        data = next((p for p in self.people_cache if p["id"] == iid), None)
        if not data:
            return
        self.person_form_vars["id"].set(iid)
        self.person_form_vars["name"].set(data["name"])
        self.person_form_vars["gender"].set(data["gender"])
        self.person_form_vars["birth"].set(data["birth_date"] or "")
        self.person_form_vars["death"].set(data["death_date"] or "")
        self.person_notes.delete("1.0", "end")
        self.person_notes.insert("1.0", data["notes"])

    def _reset_person_form(self):
        for var in self.person_form_vars.values():
            if isinstance(var, tk.StringVar):
                var.set("")
            elif isinstance(var, tk.IntVar):
                var.set(0)
        self.person_form_vars["gender"].set("male")
        self.person_notes.delete("1.0", "end")

    def _save_person(self):
        payload = {
            "name": self.person_form_vars["name"].get(),
            "gender": self.person_form_vars["gender"].get(),
            "birth_date": self.person_form_vars["birth"].get() or None,
            "death_date": self.person_form_vars["death"].get() or None,
            "notes": self.person_notes.get("1.0", "end").strip(),
        }
        try:
            if self.person_form_vars["id"].get():
                people.update_person(self.person_form_vars["id"].get(), payload)
            else:
                people.create_person(payload)
            messagebox.showinfo("Data Orang", "Data tersimpan")
            self._reset_person_form()
            self.refresh_people()
            self.refresh_marriages()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _delete_person(self):
        if not self.person_form_vars["id"].get():
            messagebox.showinfo("Hapus", "Pilih data yang akan dihapus")
            return
        if not messagebox.askyesno("Hapus", "Yakin hapus data orang?"):
            return
        try:
            people.delete_person(self.person_form_vars["id"].get())
            self._reset_person_form()
            self.refresh_people()
            self.refresh_marriages()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # endregion
    # region Marriage Tab
    def _build_marriage_tab(self):
        frame = self.marriage_tab
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(1, weight=1)
        search_frame = ttk.Frame(frame)
        search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5), padx=(0, 10))
        search_frame.columnconfigure(1, weight=1)
        ttk.Label(search_frame, text="Cari Nama").grid(row=0, column=0, sticky="w")
        self.marriage_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.marriage_search_var)
        search_entry.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        self.marriage_search_var.trace_add("write", lambda *_: self._apply_marriage_filter())
        columns = ("husband", "wife", "date")
        self.marriage_tree = ttk.Treeview(frame, columns=columns, show="headings", height=10)
        for col in columns:
            self.marriage_tree.heading(col, text=col.title())
        self.marriage_tree.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        self.marriage_tree.bind("<<TreeviewSelect>>", lambda _: self._fill_marriage_form())
        form = ttk.Frame(frame)
        form.grid(row=1, column=1, sticky="nsew")
        form.columnconfigure(0, weight=1)
        self.marriage_form = {
            "id": tk.IntVar(value=0),
            "husband": tk.StringVar(),
            "wife": tk.StringVar(),
            "date": tk.StringVar(),
            "notes": tk.StringVar(),
        }
        ttk.Label(form, text="Suami").grid(row=0, column=0, sticky="w")
        self.husband_combo = ttk.Combobox(form, textvariable=self.marriage_form["husband"], state="readonly")
        self.husband_combo.grid(row=1, column=0, sticky="ew")
        ttk.Label(form, text="Istri").grid(row=2, column=0, sticky="w")
        self.wife_combo = ttk.Combobox(form, textvariable=self.marriage_form["wife"], state="readonly")
        self.wife_combo.grid(row=3, column=0, sticky="ew")
        ttk.Label(form, text="Tanggal Nikah").grid(row=4, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.marriage_form["date"]).grid(row=5, column=0, sticky="ew")
        ttk.Label(form, text="Catatan").grid(row=6, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.marriage_form["notes"]).grid(row=7, column=0, sticky="ew")
        btn_frame = ttk.Frame(form)
        btn_frame.grid(row=8, column=0, sticky="ew", pady=10)
        ttk.Button(btn_frame, text="Baru", command=self._reset_marriage_form).pack(side="left")
        ttk.Button(btn_frame, text="Simpan", command=self._save_marriage).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Hapus", command=self._delete_marriage).pack(side="left")

    def refresh_marriages(self):
        self.marriage_cache = marriages.list_marriages()
        self._apply_marriage_filter()
        self.husband_combo["values"] = self._people_labels_by_gender("male")
        self.wife_combo["values"] = self._people_labels_by_gender("female")
        self._refresh_marriage_selector()

    def _apply_marriage_filter(self):
        if not hasattr(self, "marriage_tree"):
            return
        term = getattr(self, "marriage_search_var", None)
        query = (term.get() if term else "").strip().lower()
        rows = self.marriage_cache
        if query:
            rows = [
                marriage
                for marriage in rows
                if query in ((marriage.get("husband") or {}).get("name") or "").lower()
                or query in ((marriage.get("wife") or {}).get("name") or "").lower()
            ]
        self.marriage_tree.delete(*self.marriage_tree.get_children())
        for marriage in rows:
            self.marriage_tree.insert(
                "",
                "end",
                iid=marriage["id"],
                values=(
                    marriage["husband"]["name"] if marriage.get("husband") else "-",
                    marriage["wife"]["name"] if marriage.get("wife") else "-",
                    marriage.get("marriage_date"),
                ),
            )

    def _fill_marriage_form(self):
        selection = self.marriage_tree.selection()
        if not selection:
            return
        iid = int(selection[0])
        data = next((m for m in self.marriage_cache if m["id"] == iid), None)
        if not data:
            return
        self.marriage_form["id"].set(iid)
        if data.get("husband"):
            self.marriage_form["husband"].set(f"{data['husband']['name']} (#{data['husband']['id']})")
        if data.get("wife"):
            self.marriage_form["wife"].set(f"{data['wife']['name']} (#{data['wife']['id']})")
        self.marriage_form["date"].set(data.get("marriage_date") or "")
        self.marriage_form["notes"].set(data.get("notes") or "")

    def _reset_marriage_form(self):
        for var in self.marriage_form.values():
            if isinstance(var, tk.StringVar):
                var.set("")
            elif isinstance(var, tk.IntVar):
                var.set(0)

    def _save_marriage(self):
        husband_id = self._extract_person_id(self.marriage_form["husband"].get())
        wife_id = self._extract_person_id(self.marriage_form["wife"].get())
        payload = {
            "husband_id": husband_id,
            "wife_id": wife_id,
            "marriage_date": self.marriage_form["date"].get() or None,
            "notes": self.marriage_form["notes"].get(),
        }
        try:
            if self.marriage_form["id"].get():
                marriages.update_marriage(self.marriage_form["id"].get(), payload)
            else:
                marriages.create_marriage(payload)
            messagebox.showinfo("Pernikahan", "Data tersimpan")
            self.refresh_marriages()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _delete_marriage(self):
        if not self.marriage_form["id"].get():
            messagebox.showinfo("Hapus", "Pilih data pernikahan terlebih dahulu")
            return
        if not messagebox.askyesno("Hapus", "Hapus data pernikahan?"):
            return
        marriages.delete_marriage(self.marriage_form["id"].get())
        self._reset_marriage_form()
        self.refresh_marriages()

    # endregion
    # region Children Tab
    def _build_children_tab(self):
        frame = self.children_tab
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text="Pilih Pernikahan").pack(anchor="w")
        self.marriage_selector = ttk.Combobox(frame, state="readonly")
        self.marriage_selector.pack(fill="x")
        self.marriage_selector.bind("<<ComboboxSelected>>", lambda _: self._refresh_children_view())
        self.children_tree = ttk.Treeview(frame, columns=("child",), show="headings", height=10)
        self.children_tree.heading("child", text="Anak")
        self.children_tree.pack(fill="both", expand=True, pady=10)
        form = ttk.Frame(frame)
        form.pack(fill="x")
        ttk.Label(form, text="Tambah Anak").grid(row=0, column=0, sticky="w")
        self.child_combo = ttk.Combobox(form, state="readonly")
        self.child_combo.grid(row=1, column=0, sticky="ew")
        ttk.Button(form, text="Tambah", command=self._add_child).grid(row=1, column=1, padx=5)
        ttk.Button(form, text="Hapus Relasi", command=self._remove_child).grid(row=1, column=2)

    def _refresh_marriage_selector(self):
        values = []
        for marriage in self.marriage_cache:
            husband = marriage["husband"]["name"] if marriage.get("husband") else "?"
            wife = marriage["wife"]["name"] if marriage.get("wife") else "?"
            values.append(f"{marriage['id']} - {husband} & {wife}")
        self.marriage_selector["values"] = values
        self.child_combo["values"] = [f"{p['id']} - {p['name']}" for p in self.people_cache]
        if hasattr(self, "diagram_marriage_combo"):
            self.diagram_marriage_combo["values"] = values
            if values:
                self.diagram_marriage_combo.set(values[0])
            else:
                self.diagram_marriage_combo.set("")

    def _current_marriage_id(self) -> int | None:
        return self._extract_marriage_id(self.marriage_selector.get())

    def _refresh_children_view(self):
        self.children_tree.delete(*self.children_tree.get_children())
        marriage_id = self._current_marriage_id()
        if not marriage_id:
            return
        rows = marriages.list_children(marriage_id)
        for row in rows:
            child = row["child"]
            self.children_tree.insert("", "end", iid=row["id"], values=(f"{child['name']} (#{child['id']})",))

    def _add_child(self):
        marriage_id = self._current_marriage_id()
        child_text = self.child_combo.get()
        if not marriage_id or not child_text:
            messagebox.showwarning("Relasi", "Pilih pernikahan dan anak")
            return
        child_id = int(child_text.split(" - ")[0])
        try:
            marriages.add_child(marriage_id, child_id)
            self._refresh_children_view()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _remove_child(self):
        selection = self.children_tree.selection()
        if not selection:
            messagebox.showinfo("Hapus", "Pilih relasi anak")
            return
        marriages.remove_child(int(selection[0]))
        self._refresh_children_view()

    # endregion
    # region Diagram Tab
    def _build_diagram_tab(self):
        frame = self.diagram_tab
        control_frame = ttk.Frame(frame)
        control_frame.pack(pady=10)
        self.diagram_control_frame = control_frame
        ttk.Label(control_frame, text="Pilih Pernikahan").pack(side="left", padx=5)
        self.diagram_marriage_combo = ttk.Combobox(control_frame, state="readonly", width=35)
        self.diagram_marriage_combo.pack(side="left", padx=5)
        ttk.Button(control_frame, text="Bangun Diagram", command=self._render_diagram).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Zoom In", command=lambda: self._zoom_diagram(1.2)).pack(
            side="left", padx=(15, 5)
        )
        ttk.Button(control_frame, text="Zoom Out", command=lambda: self._zoom_diagram(1 / 1.2)).pack(
            side="left", padx=5
        )

        image_frame = ttk.Frame(frame)
        image_frame.pack(fill="both", expand=True)
        self.diagram_image_frame = image_frame
        self.diagram_canvas = tk.Canvas(image_frame, background="white", highlightthickness=0)
        self.diagram_canvas.pack(fill="both", expand=True)
        self.diagram_canvas.bind("<ButtonPress-1>", self._start_canvas_drag)
        self.diagram_canvas.bind("<B1-Motion>", self._drag_canvas)
        self.diagram_canvas.bind("<Configure>", lambda _: self._display_diagram_image())

    def _render_diagram(self):
        marriage_id = self._extract_marriage_id(self.diagram_marriage_combo.get())
        if not marriage_id:
            messagebox.showwarning("Diagram", "Pilih pernikahan terlebih dahulu")
            return
        try:
            image_path = tree_builder.build_tree_image(
                filename=f"family_tree_{marriage_id}", root_marriage_id=marriage_id
            )
            self._diagram_base_image = Image.open(image_path)
            self._set_diagram_zoom_to_fit()
            self._display_diagram_image()
            messagebox.showinfo("Diagram", f"Diagram tersimpan di {image_path}")
        except Exception as exc:
            messagebox.showerror("Diagram", f"Gagal membangun diagram: {exc}")

    def _set_diagram_zoom_to_fit(self):
        if not self._diagram_base_image:
            return
        self.update_idletasks()
        canvas_width = max(self.diagram_canvas.winfo_width(), 1)
        canvas_height = max(self.diagram_canvas.winfo_height(), 1)
        base_width = max(self._diagram_base_image.width, 1)
        base_height = max(self._diagram_base_image.height, 1)
        scale = min(canvas_width / base_width, canvas_height / base_height)
        self._diagram_zoom = max(scale, 0.1)

    def _display_diagram_image(self):
        if not self._diagram_base_image:
            return
        base = self._diagram_base_image
        target_width = max(1, int(base.width * self._diagram_zoom))
        target_height = max(1, int(base.height * self._diagram_zoom))
        if target_width == base.width and target_height == base.height:
            img = base
        else:
            img = base.resize((target_width, target_height), Image.LANCZOS)

        self._tree_image = ImageTk.PhotoImage(img)
        canvas_width = max(self.diagram_canvas.winfo_width(), 1)
        canvas_height = max(self.diagram_canvas.winfo_height(), 1)
        display_width = max(target_width, canvas_width)
        display_height = max(target_height, canvas_height)
        offset_x = (display_width - target_width) / 2
        offset_y = (display_height - target_height) / 2
        self.diagram_canvas.configure(scrollregion=(0, 0, display_width, display_height))
        if self._diagram_canvas_image is None:
            self._diagram_canvas_image = self.diagram_canvas.create_image(
                offset_x,
                offset_y,
                anchor="nw",
                image=self._tree_image,
            )
        else:
            self.diagram_canvas.coords(self._diagram_canvas_image, offset_x, offset_y)
            self.diagram_canvas.itemconfigure(self._diagram_canvas_image, image=self._tree_image)

    def _zoom_diagram(self, factor: float):
        if not self._diagram_base_image:
            return
        new_zoom = self._diagram_zoom * factor
        self._diagram_zoom = min(max(new_zoom, 0.1), 5.0)
        self._display_diagram_image()

    def _start_canvas_drag(self, event):
        if hasattr(self, "diagram_canvas"):
            self.diagram_canvas.scan_mark(event.x, event.y)

    def _drag_canvas(self, event):
        if hasattr(self, "diagram_canvas"):
            self.diagram_canvas.scan_dragto(event.x, event.y, gain=1)

    # endregion
    # region Reports Tab
    def _build_reports_tab(self):
        frame = self.report_tab
        ttk.Button(frame, text="Laporan Keluarga (PDF)", command=self._generate_family_pdf).pack(
            fill="x", pady=5
        )
        ttk.Button(frame, text="Ekspor Orang (CSV)", command=self._export_csv).pack(fill="x", pady=5)
        ttk.Label(frame, text="Profil Individu (pilih orang)").pack(anchor="w", pady=(20, 5))
        self.report_person_combo = ttk.Combobox(frame, state="readonly")
        self.report_person_combo.pack(fill="x")
        ttk.Button(frame, text="Cetak Profil", command=self._generate_person_pdf).pack(fill="x", pady=5)

    def _generate_family_pdf(self):
        path = reports.generate_family_pdf()
        messagebox.showinfo("Laporan", f"Laporan keluarga dibuat: {path}")

    def _generate_person_pdf(self):
        text = self.report_person_combo.get()
        if not text:
            messagebox.showwarning("Profil", "Pilih orang")
            return
        person_id = self._extract_person_id(text)
        path = reports.generate_person_pdf(person_id)
        messagebox.showinfo("Profil", f"Profil dibuat di {path}")

    def _export_csv(self):
        path = reports.export_people_csv()
        messagebox.showinfo("Ekspor", f"Data diekspor ke {path}")

    # endregion
    # region Mahram
    def _build_mahram_tab(self):
        frame = self.mahram_tab
        ttk.Label(frame, text="Orang 1").grid(row=0, column=0, sticky="w")
        self.mahram_a = ttk.Combobox(frame, state="readonly")
        self.mahram_a.grid(row=1, column=0, sticky="ew")
        ttk.Label(frame, text="Orang 2").grid(row=2, column=0, sticky="w")
        self.mahram_b = ttk.Combobox(frame, state="readonly")
        self.mahram_b.grid(row=3, column=0, sticky="ew")
        ttk.Button(frame, text="Cari Relasi", command=self._search_mahram).grid(row=4, column=0, pady=10)
        self.mahram_result = ttk.Label(frame, text="")
        self.mahram_result.grid(row=5, column=0, sticky="w")

    def _search_mahram(self):
        pid_a = self._extract_person_id(self.mahram_a.get())
        pid_b = self._extract_person_id(self.mahram_b.get())
        if not pid_a or not pid_b:
            messagebox.showwarning("Relasi", "Pilih dua orang")
            return
        result = kinship.find_relationship(pid_a, pid_b)
        if not result:
            self.mahram_result.configure(text="Tidak ditemukan hubungan")
            return
        text = f"Jarak {result.distance} - {'Mahram' if result.is_mahram else 'Bukan Mahram'}\n{' -> '.join(result.path)}"
        self.mahram_result.configure(text=text)

    # endregion
    # region User Tab
    def _build_user_tab(self):
        frame = self.user_tab
        columns = ("username", "role")
        self.user_tree = ttk.Treeview(frame, columns=columns, show="headings", height=8)
        for col in columns:
            self.user_tree.heading(col, text=col.title())
        self.user_tree.pack(fill="both", expand=True)
        form = ttk.Frame(frame)
        form.pack(fill="x", pady=10)
        ttk.Label(form, text="Username").grid(row=0, column=0, sticky="w")
        self.new_user_name = tk.StringVar()
        ttk.Entry(form, textvariable=self.new_user_name).grid(row=1, column=0, sticky="ew")
        ttk.Label(form, text="Password").grid(row=0, column=1, sticky="w")
        self.new_user_pass = tk.StringVar()
        ttk.Entry(form, textvariable=self.new_user_pass, show="*").grid(row=1, column=1, sticky="ew")
        ttk.Label(form, text="Role").grid(row=0, column=2, sticky="w")
        self.new_user_role = tk.StringVar(value="admin")
        ttk.Combobox(form, textvariable=self.new_user_role, values=("admin", "user"), state="readonly").grid(
            row=1, column=2, sticky="ew"
        )
        ttk.Button(form, text="Tambah User", command=self._add_user).grid(row=1, column=3, padx=5)
        self.refresh_users()

    def refresh_users(self):
        if self.current_user["role"] != "admin":
            return
        data = users.list_users()
        self.user_tree.delete(*self.user_tree.get_children())
        for row in data:
            self.user_tree.insert("", "end", iid=row["id"], values=(row["username"], row["role"]))

    def _add_user(self):
        if not self.new_user_name.get() or not self.new_user_pass.get():
            messagebox.showwarning("User", "Isi username dan password")
            return
        try:
            users.create_user(self.new_user_name.get(), self.new_user_pass.get(), self.new_user_role.get())
            self.refresh_users()
            self.new_user_name.set("")
            self.new_user_pass.set("")
        except Exception as exc:
            messagebox.showerror("User", str(exc))

    # endregion
    def _people_labels_by_gender(self, gender: str) -> list[str]:
        target = (gender or "").strip().lower()
        male_aliases = {"male", "m", "lakilaki", "laki", "pria"}
        female_aliases = {"female", "f", "perempuan", "wanita"}

        def normalize(value: str | None) -> str:
            if not value:
                return ""
            return value.strip().lower().replace("-", "").replace(" ", "")

        def matches(person_gender: str | None) -> bool:
            norm = normalize(person_gender)
            if target == "male":
                return norm in male_aliases
            if target == "female":
                return norm in female_aliases
            return True

        return [f"{p['name']} (#{p['id']})" for p in self.people_cache if matches(p.get("gender"))]

    def _extract_person_id(self, label: str) -> int | None:
        if not label or "#" not in label:
            return None
        try:
            return int(label.split("#")[-1].strip(")"))
        except ValueError:
            return None

    def _extract_marriage_id(self, label: str) -> int | None:
        if not label or " - " not in label:
            return None
        try:
            return int(label.split(" - ", 1)[0])
        except ValueError:
            return None

    def _refresh_all(self):
        self.refresh_people()
        self.refresh_marriages()
        self._refresh_children_view()
        self.refresh_users()
        combos = [self.report_person_combo, self.mahram_a, self.mahram_b]
        values = [f"{p['name']} (#{p['id']})" for p in self.people_cache]
        for combo in combos:
            combo["values"] = values
