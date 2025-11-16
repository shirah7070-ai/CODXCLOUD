# codxcloud_fullwidth_cards.py
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from tkinter import ttk as native_ttk
from PIL import Image, ImageTk
import os

USERS = {"admin": "admin123", "user1": "password1"}
BOOKS = {
    "001": {"title": "Python Programming", "author": "John Smith", "available": True, "borrowed_by": None},
    "002": {"title": "Data Structures", "author": "Jane Doe", "available": True, "borrowed_by": None},
    "003": {"title": "Algorithms", "author": "Alan Turing", "available": False, "borrowed_by": "admin"},
    "004": {"title": "Computer Networks", "author": "E. Tanenbaum", "available": True, "borrowed_by": None},
    "005": {"title": "Machine Learning", "author": "A. Ng", "available": True, "borrowed_by": None},
}

def show_info(title, msg): messagebox.showinfo(title, msg)
def show_error(title, msg): messagebox.showerror(title, msg)

class CodXCloudApp:
    def __init__(self, root: ttk.Window):
        self.root = root
        self.root.title("CodXCloud - Fullwidth Cards")
        self.root.geometry("1200x800")
        self.current_user = None

        self._build_header()
        self._build_content_area()
        self.root.withdraw()
        self.create_login_window()

    def _build_header(self):
        header = ttk.Frame(self.root, padding=8)
        header.pack(side="top", fill="x")

        # Left title
        ttk.Label(header, text="CodXCloud", font=("Helvetica", 22, "bold"), bootstyle="primary").pack(side="left", padx=20)

        # Right dropdown menu
        right = ttk.Frame(header)
        right.pack(side="right", padx=20)
        menu_btn = ttk.Menubutton(right, text="☰ Menu", bootstyle="secondary-outline")
        menu_btn.pack(side="right")
        menu = tk.Menu(menu_btn, tearoff=0)
        menu.add_command(label="Search", command=lambda: self.show_view("search"))
        menu.add_command(label="Borrow/Return", command=lambda: self.show_view("borrow"))
        menu.add_command(label="Profile", command=lambda: self.show_view("profile"))
        menu.add_separator()
        menu.add_command(label="Logout", command=self._logout_action)
        menu_btn["menu"] = menu

    def _build_content_area(self):
        self.content_frame = ttk.Frame(self.root, padding=20)
        self.content_frame.pack(fill="both", expand=True)
        self.show_view("search")

    def clear_content(self):
        for w in self.content_frame.winfo_children(): w.destroy()

    def show_view(self, view_name):
        self.clear_content()
        if view_name == "search": self._view_search_cards()
        elif view_name == "borrow": self._view_borrow_return()
        elif view_name == "profile": self._view_profile()
        else: self._view_search_cards()

    # -------------------------
    # Search Card Layout (full width)
    # -------------------------
    def _view_search_cards(self):
        top = ttk.Frame(self.content_frame)
        top.pack(fill="x", pady=(0,10))
        ttk.Label(top, text="Search Books", font=("Helvetica", 20, "bold"), bootstyle="info").pack(side="left", padx=15)
        search_entry = ttk.Entry(top, width=50)
        search_entry.pack(side="left", padx=10)
        search_type = tk.StringVar(value="Title")
        ttk.Radiobutton(top, text="Title", variable=search_type, value="Title", bootstyle="info-toolbutton").pack(side="left", padx=4)
        ttk.Radiobutton(top, text="Author", variable=search_type, value="Author", bootstyle="info-toolbutton").pack(side="left", padx=4)
        ttk.Button(top, text="Search", bootstyle="primary",
                   command=lambda: perform_search(search_entry.get(), search_type.get())).pack(side="left", padx=10)

        # scrollable area for cards
        container = ttk.Frame(self.content_frame)
        container.pack(fill="both", expand=True)
        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._card_imgs = []

        def clear_cards():
            for c in scrollable.winfo_children(): c.destroy()
            self._card_imgs.clear()

        def borrow_book(bid, btn):
            book = BOOKS.get(bid)
            if not self.current_user:
                show_error("Error", "Please login first")
                return
            if book and book["available"]:
                book["available"] = False
                book["borrowed_by"] = self.current_user
                btn.configure(text="Borrowed", state="disabled", bootstyle="danger")
                show_info("Success", f"Borrowed {book['title']}")
            else:
                show_error("Error", "Not available")

        def make_card(parent, bid, book):
            # outer card full width (small side padding; fills the main content width)
            card = ttk.Frame(parent, padding=(20, 22), relief="raised", bootstyle="secondary")
            card.pack(fill="x", pady=18, padx=20)  # fills horizontally almost to screen edge

            # left: image (placeholder)
            left = ttk.Frame(card, width=140)
            left.pack(side="left", padx=(0,20))
            placeholder = tk.Canvas(left, width=120, height=160, highlightthickness=0)
            placeholder.create_rectangle(0,0,120,160, fill="#f1f1f1", outline="#999999")
            placeholder.create_text(60,80, text="No\nImage", justify="center")
            placeholder.pack()

            # middle: details (EXPAND)
            middle = ttk.Frame(card)
            middle.pack(side="left", fill="both", expand=True)
            ttk.Label(middle, text=book["title"], font=("Helvetica", 16, "bold")).pack(anchor="w")
            ttk.Label(middle, text=f"Author: {book['author']}", font=("Helvetica", 11)).pack(anchor="w", pady=(6,0))
            st = "Available" if book["available"] else f"Borrowed by {book['borrowed_by']}"
            ttk.Label(middle, text=f"Status: {st}", font=("Helvetica", 11)).pack(anchor="w", pady=(10,0))

            # right: borrow button aligned right-center
            right = ttk.Frame(card, width=140)
            right.pack(side="right", fill="y")
            right_inner = ttk.Frame(right)
            right_inner.place(relx=0.5, rely=0.5, anchor="center")
            borrow_btn = ttk.Button(right_inner, text="Borrow", width=12, bootstyle="danger")
            if not book["available"]:
                borrow_btn.configure(text="Not Available", state="disabled", bootstyle="secondary")
            borrow_btn.pack()
            borrow_btn.configure(command=lambda: borrow_book(bid, borrow_btn))

        def perform_search(q, mode):
            clear_cards()
            q = (q or "").strip().lower()
            results = []
            for k,v in BOOKS.items():
                if not q or (mode=="Title" and q in v["title"].lower()) or (mode=="Author" and q in v["author"].lower()):
                    results.append((k,v))
            if not results:
                ttk.Label(scrollable, text="No results found.", font=("Helvetica", 12)).pack(pady=20)
                return
            for bid, book in results:
                make_card(scrollable, bid, book)

        perform_search("", "Title")

    # -------------------------
    # Borrow & Profile simplified
    # -------------------------
    def _view_borrow_return(self):
        ttk.Label(self.content_frame, text="Borrow / Return Books", font=("Helvetica", 18, "bold")).pack(pady=20)
        form = ttk.Frame(self.content_frame)
        form.pack(pady=10)
        ttk.Label(form, text="Book ID:").grid(row=0, column=0, padx=6)
        entry = ttk.Entry(form, width=12)
        entry.grid(row=0, column=1, padx=6)
        def borrow():
            bid = entry.get().strip()
            if bid in BOOKS and BOOKS[bid]["available"]:
                BOOKS[bid]["available"] = False
                BOOKS[bid]["borrowed_by"] = self.current_user
                show_info("Success", f"Borrowed {BOOKS[bid]['title']}")
            else: show_error("Error", "Invalid or unavailable")
        ttk.Button(form, text="Borrow", bootstyle="danger", command=borrow).grid(row=0, column=2, padx=6)

    def _view_profile(self):
        ttk.Label(self.content_frame, text="My Profile", font=("Helvetica", 20, "bold")).pack(pady=15)
        if not self.current_user:
            ttk.Label(self.content_frame, text="Please login first.").pack()
            return
        ttk.Label(self.content_frame, text=f"Welcome, {self.current_user}", font=("Helvetica", 14)).pack(pady=6)
        ttk.Label(self.content_frame, text="Borrowed Books:", font=("Helvetica", 12, "bold")).pack(pady=(20,0))
        for bid,b in BOOKS.items():
            if b.get("borrowed_by")==self.current_user:
                ttk.Label(self.content_frame, text=f"{bid} - {b['title']}").pack(anchor="w", padx=40)

    # -------------------------
    # Login Window
    # -------------------------
    def create_login_window(self):
        self.login_win = tk.Toplevel(self.root)
        self.login_win.title("Login - CodXCloud")
        self.login_win.geometry("360x260")
        self.login_win.resizable(False, False)
        self.login_win.protocol("WM_DELETE_WINDOW", self.root.quit)
        frm = ttk.Frame(self.login_win, padding=12)
        frm.pack(fill="both", expand=True)
        ttk.Label(frm, text="CodXCloud Login", font=("Helvetica", 16, "bold"), bootstyle="primary").pack(pady=8)
        form = ttk.Frame(frm)
        form.pack(pady=6)
        ttk.Label(form, text="Student ID:").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        self.username_entry = ttk.Entry(form, width=26)
        self.username_entry.grid(row=0, column=1, padx=6, pady=6)
        ttk.Label(form, text="Password:").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        self.password_entry = ttk.Entry(form, width=26, show="*")
        self.password_entry.grid(row=1, column=1, padx=6, pady=6)
        btnf = ttk.Frame(frm); btnf.pack(pady=8)
        ttk.Button(btnf, text="Login", bootstyle="success", command=self._login_action).grid(row=0, column=0, padx=6)
        ttk.Button(btnf, text="Register", bootstyle="info", command=self._register_action).grid(row=0, column=1, padx=6)

    def _login_action(self):
        u, p = self.username_entry.get().strip(), self.password_entry.get().strip()
        if USERS.get(u) == p:
            self.current_user = u
            show_info("Welcome", f"Welcome, {u}!")
            self.login_win.destroy()
            self.root.deiconify()
            self.show_view("search")
        else:
            show_error("Error", "Invalid credentials")

    def _register_action(self):
        u, p = self.username_entry.get().strip(), self.password_entry.get().strip()
        if not u or not p:
            show_error("Error", "Enter credentials"); return
        if u in USERS:
            show_error("Error", "User exists"); return
        USERS[u]=p; show_info("Success","Registered! You can login now.")

    def _logout_action(self):
        if messagebox.askyesno("Logout", "Logout?"):
            self.current_user=None
            self.root.withdraw()
            self.create_login_window()

if __name__ == "__main__":
    root = ttk.Window(themename="cosmo")
    app = CodXCloudApp(root)
    root.mainloop()
    
JHNVSJDGJKAGDSKGAS



