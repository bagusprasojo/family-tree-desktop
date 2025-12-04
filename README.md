# Family Tree Desktop

A Tkinter-based desktop application for managing extended family data, visualising genealogy graphs, generating PDF/CSV reports, and running mahram lookup backed by a MySQL (or SQLite for development) database.

## Fitur Utama
- CRUD data orang lengkap dengan catatan dan tanggal kehidupan.
- CRUD data pernikahan dan relasi anak (child-parent) sesuai ERD.
- Autentikasi multi-user dengan role (`admin`, `user`).
- Diagram silsilah otomatis menggunakan Graphviz.
- Laporan PDF (keluarga & profil individu) serta ekspor CSV.
- Pencarian mahram (jarak hubungan) menggunakan algoritma BFS.

## Prasyarat
- Python 3.10+
- MySQL server aktif dan database kosong (mis. `family_tree`).
- Graphviz binary sudah terpasang di PATH.

## Instalasi
```bash
python -m venv env
source env/Scripts/activate            # cmd: env\Scripts\activate
pip install -e .
```

Salin `.env.example` menjadi `.env`, lalu sesuaikan kredensial database:
```ini
FAMILY_DB_URL=mysql+pymysql://user:pass@localhost/family_tree
```

## Menjalankan Aplikasi
```bash
python -m family_desktop.app
```

- Akun admin awal otomatis dibuat (`admin` / `admin123`). Ubah password melalui tab Pengguna.
- Data orang contoh otomatis dimuat agar UI tidak kosong.

## Struktur Direktori Penting
- `src/family_desktop/app.py` – entrypoint Tkinter.
- `src/family_desktop/database.py` & `models.py` – ORM SQLAlchemy.
- `src/family_desktop/services/` – logika bisnis (CRUD, laporan, diagram, mahram).
- `src/family_desktop/ui/` – komponen UI (login + main window).
- `generated/` – hasil diagram PNG.
- `reports/` – PDF laporan.
- `exports/` – file CSV.

## Catatan Penggunaan
1. Login memakai akun admin atau user biasa.
2. Gunakan tab *Data Orang* / *Data Pernikahan* / *Relasi Anak* untuk CRUD.
3. Tab *Diagram* menghasilkan PNG sekaligus menampilkan preview.
4. Tab *Laporan* menghasilkan PDF/CSV sesuai pilihan.
5. Tab *Pencarian Mahram* pilih dua orang untuk menghitung jarak hubungan.
6. Tab *Pengguna* muncul khusus admin untuk menambah akun baru.

## Pengembangan Lanjut
- Implementasi validasi lanjutan (mis. tanggal, duplikasi).
- Integrasi Graphviz interaktif atau export SVG.
- Menambahkan fitur import CSV massal.
"# family-tree-desktop" 
