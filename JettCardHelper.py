# --- existing imports (same as yours) ---
import os
import sys
import sqlite3
from datetime import datetime
from typing import Optional, List, Tuple
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_NAME = "CETI Visitor Card Tracker"

def app_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(app_dir(), "cards.db")

def resource_path(rel_path: str) -> str:
    base = getattr(sys, "_MEIPASS", app_dir())
    return os.path.join(base, rel_path)

def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def connect_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=10000;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


# ======================
#   DB INITIALIZATION
# ======================
def ensure_db():
    os.makedirs(app_dir(), exist_ok=True)
    with connect_db() as conn:
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS cards(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('Available','Out','Lost')) DEFAULT 'Available',
                holder TEXT,
                signed_out_at TEXT,
                notes TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS history(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_label TEXT NOT NULL,
                holder TEXT NOT NULL,
                signed_out_at TEXT NOT NULL,
                returned_at TEXT,
                notes TEXT
            )
        """)

        cols = {row[1] for row in c.execute("PRAGMA table_info(cards)").fetchall()}
        if "code" not in cols:
            c.execute("ALTER TABLE cards ADD COLUMN code TEXT")
        if "home_location" not in cols:
            c.execute("ALTER TABLE cards ADD COLUMN home_location TEXT")

        c.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_cards_code_unique
            ON cards(code) WHERE code IS NOT NULL
        """)

        conn.commit()


def populate_default_cards():
    """Populate the preset card set (your existing seeding logic)."""
    with connect_db() as conn:
        c = conn.cursor()
        for i in range(1, 11):
            loc = "119-1 Cabinet" if i <= 4 else "118-2 Cabinet"
            code = f"{1000 + i:04d}"
            c.execute(
                "INSERT INTO cards(label,status,code,home_location) VALUES(?, 'Available', ?, ?)",
                (f"Lab Visitor {i}", code, loc)
            )
        for i in range(1, 21):
            code = f"{2000 + i:04d}"
            loc = "Second Floor Admin" if i <= 10 else "Third Floor Admin"
            c.execute(
                "INSERT INTO cards(label,status,code,home_location) VALUES(?, 'Available', ?, ?)",
                (f"Visitor {i}", code, loc)
            )
        c.execute("INSERT INTO cards(label,status,code,home_location) VALUES(?, 'Available', ?, ?)",
                  ("JHSC", "3001", "118-1 Cabinet"))
        c.execute("INSERT INTO cards(label,status,code,home_location) VALUES(?, 'Available', ?, ?)",
                  ("PHE 2", "3002", "118-1 Cabinet"))
        c.execute("INSERT INTO cards(label,status,code,home_location) VALUES(?, 'Available', ?, ?)",
                  ("Lab Manager Card", "9000", "Lab Manager's Office"))
        conn.commit()


def is_first_run() -> bool:
    """Return True if cards table exists but has no entries."""
    try:
        with connect_db() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM cards")
            return c.fetchone()[0] == 0
    except sqlite3.Error:
        return True


def ask_first_time_popup(root):
    """Ask user if they want preset cards or blank DB."""
    popup = tk.Toplevel(root)
    popup.title("First-Time Setup")
    popup.geometry("360x200")
    popup.resizable(False, False)
    ttk.Label(popup, text="Welcome to CETI Visitor Card Tracker!", font=("Segoe UI", 11, "bold")).pack(pady=15)
    ttk.Label(popup, text="Would you like to start with preset cards or begin with a blank list?",
              wraplength=320, justify="center").pack(pady=10)

    def add_presets():
        populate_default_cards()
        messagebox.showinfo("Preset Added", "Preset cards have been added successfully.")
        popup.destroy()

    ttk.Button(popup, text="Add Preset Cards", command=add_presets).pack(pady=5)
    ttk.Button(popup, text="Start Blank", command=popup.destroy).pack(pady=5)


# ======================
#   EXISTING FUNCTIONS
# ======================
# (All your original fetch_cards, sign_out_card, return_card, etc. remain untouched)
# [Paste everything from your original file here after ensure_db — unchanged!]
# I’ll skip re-pasting them here for brevity; nothing is removed or altered.


def fetch_cards(search: str = "") -> List[Tuple]:
    with connect_db() as conn:
        c = conn.cursor()
        if search.strip():
            like = f"%{search.strip()}%"
            c.execute("""
                SELECT id, IFNULL(code,''), label, status, IFNULL(holder,''), IFNULL(signed_out_at,''),
                       CASE WHEN status='Available' THEN IFNULL(home_location,'') ELSE IFNULL(notes,'') END AS display_notes,
                       IFNULL(home_location,'')
                  FROM cards
                 WHERE label LIKE ? OR holder LIKE ? OR notes LIKE ? OR IFNULL(code,'') LIKE ? OR IFNULL(home_location,'') LIKE ?
            """, (like, like, like, like, like))
        else:
            c.execute("""
                SELECT id, IFNULL(code,''), label, status, IFNULL(holder,''), IFNULL(signed_out_at,''),
                       CASE WHEN status='Available' THEN IFNULL(home_location,'') ELSE IFNULL(notes,'') END AS display_notes,
                       IFNULL(home_location,'')
                  FROM cards
            """)
        rows = c.fetchall()

    # Natural sort by label
    def nat_key(label: str):
        m = re.search(r"(.*?)(\d+)$", label.strip())
        if m:
            return (m.group(1).strip().lower(), int(m.group(2)))
        return (label.strip().lower(), float("inf"))

    rows.sort(key=lambda r: nat_key(r[2]))
    return rows

def sign_out_card(card_id: int, holder: str, notes: str = ""):
    t = now_str()
    with connect_db() as conn:
        c = conn.cursor()
        c.execute("SELECT label, status FROM cards WHERE id=?", (card_id,))
        row = c.fetchone()
        if not row:
            raise RuntimeError("Card not found")
        label, status = row
        if status != "Available":
            raise RuntimeError("Card is not available")
        c.execute("""
            UPDATE cards
               SET status='Out', holder=?, signed_out_at=?, notes=?
             WHERE id=?
        """, (holder.strip(), t, (notes or "").strip(), card_id))
        c.execute("""
            INSERT INTO history(card_label, holder, signed_out_at, returned_at, notes)
            VALUES(?,?,?,?,?)
        """, (label, holder.strip(), t, None, (notes or "").strip()))
        conn.commit()

def return_card(card_id: int):
    t = now_str()
    with connect_db() as conn:
        c = conn.cursor()
        c.execute("SELECT label, status FROM cards WHERE id=?", (card_id,))
        row = c.fetchone()
        if not row:
            raise RuntimeError("Card not found")
        label, status = row
        if status != "Out":
            raise RuntimeError("Card is not currently out")
        c.execute("""
            UPDATE cards
               SET status='Available', holder=NULL, signed_out_at=NULL, notes=NULL
             WHERE id=?
        """, (card_id,))
        # close latest open history row
        c.execute("""
            UPDATE history
               SET returned_at=?
             WHERE id = (
                 SELECT id FROM history
                  WHERE card_label=? AND returned_at IS NULL
                  ORDER BY id DESC
                  LIMIT 1
             )
        """, (t, label))
        conn.commit()

def mark_lost(card_id: int):
    with connect_db() as conn:
        c = conn.cursor()
        c.execute("UPDATE cards SET status='Lost' WHERE id=?", (card_id,))
        conn.commit()

def mark_found(card_id: int):
    with connect_db() as conn:
        c = conn.cursor()
        c.execute("SELECT status FROM cards WHERE id=?", (card_id,))
        row = c.fetchone()
        if not row:
            raise RuntimeError("Card not found")
        if row[0] != "Lost":
            raise RuntimeError("Card is not marked as Lost")
        c.execute("UPDATE cards SET status='Available' WHERE id=?", (card_id,))
        conn.commit()

def add_card(label: str, code: Optional[str], home_location: Optional[str]):
    code = code.strip() if code else None
    home_location = home_location.strip() if home_location else None
    if code and not re.fullmatch(r"\d{4}", code):
        raise RuntimeError("Card ID must be exactly 4 digits (or leave blank).")
    with connect_db() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO cards(label,status,code,home_location) VALUES(?, 'Available', ?, ?)",
                  (label.strip(), code, home_location))
        conn.commit()

def edit_card(card_id: int, label: str, code: Optional[str], home_location: Optional[str]):
    code = code.strip() if code else None
    home_location = home_location.strip() if home_location else None
    if code and not re.fullmatch(r"\d{4}", code):
        raise RuntimeError("Card ID must be exactly 4 digits (or leave blank).")
    with connect_db() as conn:
        c = conn.cursor()
        c.execute("UPDATE cards SET label=?, code=?, home_location=? WHERE id=?",
                  (label.strip(), code, home_location, card_id))
        conn.commit()

def remove_card(card_id: int):
    with connect_db() as conn:
        c = conn.cursor()
        c.execute("SELECT status FROM cards WHERE id=?", (card_id,))
        row = c.fetchone()
        if not row:
            raise RuntimeError("Card not found")
        if row[0] == "Out":
            raise RuntimeError("Card is currently Out. Return it first.")
        c.execute("DELETE FROM cards WHERE id=?", (card_id,))
        conn.commit()

def fetch_history(card_label_filter: str = "", holder_filter: str = "") -> List[tuple]:
    with connect_db() as conn:
        c = conn.cursor()
        base = """
            SELECT card_label, holder, signed_out_at, IFNULL(returned_at,''), IFNULL(notes,'')
              FROM history
        """
        params = []
        if card_label_filter or holder_filter:
            base += " WHERE 1=1"
            if card_label_filter:
                base += " AND card_label LIKE ?"
                params.append(f"%{card_label_filter}%")
            if holder_filter:
                base += " AND holder LIKE ?"
                params.append(f"%{holder_filter}%")
        base += " ORDER BY id DESC"
        c.execute(base, params)
        return c.fetchall()

# UI
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("980x560")
        self.minsize(900, 480)

        try:
            self.iconbitmap(resource_path("icon.ico"))
        except Exception:
            pass

        self._build_menu()
        self._build_toolbar()
        self._build_table()
        self.refresh()

    # Menus / toolbar
    def _build_menu(self):
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Add Card…", command=self.add_card_dialog)
        filemenu.add_command(label="Edit Selected Card…", command=self.edit_selected)
        filemenu.add_command(label="Remove Selected Card…", command=self.remove_selected)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=filemenu)

        viewmenu = tk.Menu(menubar, tearoff=0)
        viewmenu.add_command(label="History", command=self.open_history)
        menubar.add_cascade(label="View", menu=viewmenu)

        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="How to Use", command=self.show_help)
        menubar.add_cascade(label="Help", menu=helpmenu)

        self.config(menu=menubar)

    def _build_toolbar(self):
        bar = tk.Frame(self); bar.pack(fill="x", padx=8, pady=6)

        tk.Label(bar, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(bar, textvariable=self.search_var, width=30)
        self.search_entry.pack(side="left", padx=(4, 12))
        self.search_entry.bind("<Return>", lambda e: self.refresh())

        tk.Button(bar, text="Refresh", command=self.refresh).pack(side="left", padx=2)
        tk.Button(bar, text="Sign Out", command=self.sign_out_selected).pack(side="left", padx=2)
        tk.Button(bar, text="Return", command=self.return_selected).pack(side="left", padx=2)
        tk.Button(bar, text="Mark Lost", command=self.mark_lost_selected).pack(side="left", padx=2)
        tk.Button(bar, text="Mark Found", command=self.mark_found_selected).pack(side="left", padx=2)
        tk.Button(bar, text="Edit", command=self.edit_selected).pack(side="left", padx=12)
        tk.Button(bar, text="Remove", command=self.remove_selected).pack(side="left", padx=2)
        tk.Button(bar, text="History", command=self.open_history).pack(side="right", padx=2)

    def _build_table(self):
        cols = ("dbid","code","label","status","holder","signed_out_at","notes")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        self.tree.heading("code", text="ID");        self.tree.column("code", width=70, anchor="center")
        self.tree.heading("label", text="Card");     self.tree.column("label", width=220, anchor="w")
        self.tree.heading("status", text="Status");  self.tree.column("status", width=100, anchor="w")
        self.tree.heading("holder", text="Holder");  self.tree.column("holder", width=180, anchor="w")
        self.tree.heading("signed_out_at", text="Signed Out At"); self.tree.column("signed_out_at", width=150, anchor="w")
        self.tree.heading("notes", text="Notes / Location"); self.tree.column("notes", width=280, anchor="w")
        # hide dbid
        self.tree.heading("dbid", text="dbid"); self.tree.column("dbid", width=0, minwidth=0, stretch=False)
        self.tree.pack(fill="both", expand=True, padx=8, pady=(0,8))
        self.tree.bind("<Double-1>", self.on_double_click)

        style = ttk.Style(self)
        style.map("Treeview", background=[("selected", "#cce5ff")])
        self.tree.tag_configure("out",  background="#fff3cd")  # light amber
        self.tree.tag_configure("lost", background="#f8d7da")  # light red

    # Actions
    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        rows = fetch_cards(self.search_var.get())
        for r in rows:
            dbid, code, label, status, holder, signed_out_at, display_notes, _home = r
            tags = []
            if status == "Out":
                tags.append("out")
            elif status == "Lost":
                tags.append("lost")

            tag_tuple = tuple(tags) if tags else ()
            self.tree.insert(
                "",
                "end",
                values=(dbid, code, label, status, holder, signed_out_at, display_notes),
                tags=tag_tuple
            )

    def _get_selected_dbid(self) -> Optional[int]:
        sel = self.tree.selection()
        if not sel:
            return None
        vals = self.tree.item(sel[0], "values")
        return int(vals[0]) if vals else None

    def on_double_click(self, _event=None):
        dbid = self._get_selected_dbid()
        if not dbid:
            return
        with connect_db() as conn:
            c = conn.cursor()
            c.execute("SELECT label, status FROM cards WHERE id=?", (dbid,))
            row = c.fetchone()
        if not row:
            return
        _label, status = row
        if status == "Available":
            self.sign_out_selected()
        elif status == "Out":
            self.return_selected()

    def sign_out_selected(self):
        dbid = self._get_selected_dbid()
        if not dbid:
            messagebox.showwarning("No selection", "Select a card first.")
            return
        with connect_db() as conn:
            c = conn.cursor()
            c.execute("SELECT label, status FROM cards WHERE id=?", (dbid,))
            row = c.fetchone()
        if not row:
            messagebox.showerror("Error", "Card not found.")
            return
        label, status = row
        if status != "Available":
            messagebox.showwarning("Unavailable", f"{label} is {status}.")
            return
        # Dialog
        dlg = tk.Toplevel(self); dlg.title(f"Sign Out {label}")
        tk.Label(dlg, text=f"Card: {label}").grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10,5))
        tk.Label(dlg, text="Holder name:").grid(row=1, column=0, sticky="e", padx=10, pady=5)
        tk.Label(dlg, text="Notes (optional):").grid(row=2, column=0, sticky="e", padx=10, pady=5)
        holder_var = tk.StringVar(); notes_var = tk.StringVar()
        tk.Entry(dlg, textvariable=holder_var, width=35).grid(row=1, column=1, sticky="w", padx=10, pady=5)
        tk.Entry(dlg, textvariable=notes_var, width=35).grid(row=2, column=1, sticky="w", padx=10, pady=5)
        def do_ok():
            holder = holder_var.get().strip()
            if not holder:
                messagebox.showerror("Missing name", "Please enter a holder name.", parent=dlg)
                return
            try:
                sign_out_card(dbid, holder, notes_var.get().strip())
                dlg.destroy()
                self.refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=dlg)
        tk.Button(dlg, text="Cancel", command=dlg.destroy).grid(row=3, column=0, pady=10)
        tk.Button(dlg, text="Sign Out", command=do_ok).grid(row=3, column=1, pady=10, sticky="e")
        dlg.grab_set(); dlg.wait_window()

    def return_selected(self):
        dbid = self._get_selected_dbid()
        if not dbid:
            messagebox.showwarning("No selection", "Select a card first.")
            return
        if messagebox.askyesno("Return Card", "Mark this card as returned?"):
            try:
                return_card(dbid)
                self.refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def mark_lost_selected(self):
        dbid = self._get_selected_dbid()
        if not dbid:
            messagebox.showwarning("No selection", "Select a card first.")
            return
        if messagebox.askyesno("Mark Lost", "Mark this card as LOST?"):
            try:
                mark_lost(dbid)
                self.refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def mark_found_selected(self):
        dbid = self._get_selected_dbid()
        if not dbid:
            messagebox.showwarning("No selection", "Select a card first.")
            return
        try:
            mark_found(dbid)
            self.refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def add_card_dialog(self):
        dlg = tk.Toplevel(self); dlg.title("Add Card")
        tk.Label(dlg, text="Card Label:").grid(row=0, column=0, sticky="e", padx=10, pady=(12,6))
        tk.Label(dlg, text="Card ID (4 digits):").grid(row=1, column=0, sticky="e", padx=10, pady=6)
        tk.Label(dlg, text="Home Location:").grid(row=2, column=0, sticky="e", padx=10, pady=6)
        label_var = tk.StringVar(); code_var = tk.StringVar(); home_var = tk.StringVar()
        tk.Entry(dlg, textvariable=label_var, width=36).grid(row=0, column=1, sticky="w", padx=10, pady=(12,6))
        tk.Entry(dlg, textvariable=code_var, width=12).grid(row=1, column=1, sticky="w", padx=10, pady=6)
        tk.Entry(dlg, textvariable=home_var, width=36).grid(row=2, column=1, sticky="w", padx=10, pady=6)
        def do_save():
            label = label_var.get().strip()
            code  = code_var.get().strip() or None
            home  = home_var.get().strip() or None
            try:
                add_card(label, code, home)
                dlg.destroy()
                self.refresh()
            except sqlite3.IntegrityError as e:
                if "UNIQUE constraint failed: cards.label" in str(e):
                    messagebox.showerror("Duplicate", f"A card named '{label}' already exists.", parent=dlg)
                elif "idx_cards_code_unique" in str(e) or "cards.code" in str(e):
                    messagebox.showerror("Duplicate", f"A card with ID '{code}' already exists.", parent=dlg)
                else:
                    messagebox.showerror("Error", str(e), parent=dlg)
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=dlg)
        tk.Button(dlg, text="Cancel", command=dlg.destroy).grid(row=3, column=0, pady=12)
        tk.Button(dlg, text="Save", command=do_save).grid(row=3, column=1, pady=12, sticky="e")
        dlg.grab_set(); dlg.wait_window()

    def edit_selected(self):
        dbid = self._get_selected_dbid()
        if not dbid:
            messagebox.showwarning("No selection", "Select a card first.")
            return
        with connect_db() as conn:
            c = conn.cursor()
            c.execute("SELECT label, IFNULL(code,''), IFNULL(home_location,'') FROM cards WHERE id=?", (dbid,))
            row = c.fetchone()
        if not row:
            messagebox.showerror("Error", "Card not found.")
            return
        cur_label, cur_code, cur_home = row
        dlg = tk.Toplevel(self); dlg.title("Edit Card")
        tk.Label(dlg, text="Card Label:").grid(row=0, column=0, sticky="e", padx=10, pady=(12,6))
        tk.Label(dlg, text="Card ID (4 digits):").grid(row=1, column=0, sticky="e", padx=10, pady=6)
        tk.Label(dlg, text="Home Location:").grid(row=2, column=0, sticky="e", padx=10, pady=6)
        label_var = tk.StringVar(value=cur_label)
        code_var  = tk.StringVar(value=cur_code)
        home_var  = tk.StringVar(value=cur_home)
        tk.Entry(dlg, textvariable=label_var, width=36).grid(row=0, column=1, sticky="w", padx=10, pady=(12,6))
        tk.Entry(dlg, textvariable=code_var,  width=12).grid(row=1, column=1, sticky="w", padx=10, pady=6)
        tk.Entry(dlg, textvariable=home_var,  width=36).grid(row=2, column=1, sticky="w", padx=10, pady=6)
        def do_save():
            label = label_var.get().strip()
            code  = code_var.get().strip() or None
            home  = home_var.get().strip() or None
            try:
                edit_card(dbid, label, code, home)
                dlg.destroy()
                self.refresh()
            except sqlite3.IntegrityError as e:
                if "UNIQUE constraint failed: cards.label" in str(e):
                    messagebox.showerror("Duplicate", f"A card named '{label}' already exists.", parent=dlg)
                elif "idx_cards_code_unique" in str(e) or "cards.code" in str(e):
                    messagebox.showerror("Duplicate", f"A card with ID '{code}' already exists.", parent=dlg)
                else:
                    messagebox.showerror("Error", str(e), parent=dlg)
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=dlg)
        tk.Button(dlg, text="Cancel", command=dlg.destroy).grid(row=3, column=0, pady=12)
        tk.Button(dlg, text="Save", command=do_save).grid(row=3, column=1, pady=12, sticky="e")
        dlg.grab_set(); dlg.wait_window()

    def remove_selected(self):
        dbid = self._get_selected_dbid()
        if not dbid:
            messagebox.showwarning("No selection", "Select a card first.")
            return
        if not messagebox.askyesno("Remove Card", "Remove this card from the list? History is kept."):
            return
        try:
            remove_card(dbid)
            self.refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def open_history(self):
        HistoryWindow(self)

    def show_help(self):
        message = (
            f"{APP_NAME}\n"
            "Quick Guide\n\n"

            "This app tracks visitor and lab access cards, who has them, when they were signed out, and when they return.\n\n"

            "Basic Use\n"
            "- Double-click a card row:\n"
            "   - If Available: opens Sign Out (enter name + optional notes)\n"
            "   - If Out: marks it as Returned\n"
            "- Use the Search box to filter by Card Label, Holder, ID, Notes, or Location.\n\n"

            "Toolbar Actions\n"
            "- Refresh: Reload the card list\n"
            "- Sign Out: Sign out selected card (same as double-click)\n"
            "- Return: Mark selected card as returned\n"
            "- Mark Lost / Mark Found: Toggle card status\n"
            "- Edit / Remove: Manage card details or delete (if not Out)\n"
            "- History: View and export all sign-out records\n\n"

            "Notes Column\n"
            "- When Available: hows Home Location (where the card is stored)\n"
            "- When Out: shows Notes entered by user\n\n"

            "Row Colors\n"
            "- Out  = light amber\n"
            "- Lost = light red\n\n"

            "Database Info\n"
            "- All data is stored in 'cards.db' in the same folder as this app.\n"
            "- You can place the entire app folder on a shared drive, everyone using the same EXE shares one database.\n"
            "- If you see 'database is locked', someone else is saving, try again shortly.\n\n"

            "History Window\n"
            "- View all sign-outs/returns\n"
            "- Filter by Card or Holder\n"
            "- Export results to CSV for records or reports\n\n"

            "Backup Tips\n"
            "- To back up: copy 'cards.db' when app is closed or idle\n"
            "- To restore: replace 'cards.db' with a backup file\n\n"

            "Created for CETI Lab - Built with Python + Tkinter"
        )
        messagebox.showinfo("How to Use", message)


class HistoryWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("History")
        self.geometry("820x420")

        top = tk.Frame(self); top.pack(fill="x", pady=5, padx=8)
        tk.Label(top, text="Filter: Card").pack(side="left")
        self.card_filter = tk.Entry(top, width=20); self.card_filter.pack(side="left", padx=(4,12))
        tk.Label(top, text="Holder").pack(side="left")
        self.holder_filter = tk.Entry(top, width=20); self.holder_filter.pack(side="left", padx=(4,12))
        tk.Button(top, text="Apply", command=self.refresh).pack(side="left")
        tk.Button(top, text="Export CSV", command=self.export_csv).pack(side="right")

        cols = ("card_label","holder","signed_out_at","returned_at","notes")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c.replace("_"," ").title())
            self.tree.column(c, width=150 if c!="notes" else 220, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=8, pady=(0,8))

        self.refresh()

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        rows = fetch_history(self.card_filter.get().strip(), self.holder_filter.get().strip())
        for r in rows:
            self.tree.insert("", "end", values=r)

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")], title="Export history to CSV")
        if not path:
            return
        rows = fetch_history(self.card_filter.get().strip(), self.holder_filter.get().strip())
        import csv
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["card_label","holder","signed_out_at","returned_at","notes"])
            w.writerows(rows)
        messagebox.showinfo("Exported", f"Saved: {path}")

def main():
    ensure_db()
    app = App()

    # show first-run popup only if DB empty
    if is_first_run():
        app.after(500, lambda: ask_first_time_popup(app))

    app.mainloop()

if __name__ == "__main__":
    main()
