import tkinter as tk
import ttkbootstrap as ttk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageOps

# For QR Generation Logic (Requires Active Internet)
import urllib.parse
import urllib.request
import base64

from datetime import datetime, timedelta
import random

from db_setup import DatabaseManager

# Initialize Database
db = DatabaseManager()
BOOKS = db.get_all_books()
TRANSACTIONS = [] # Kept for compatibility reasons (Just incase transaction process fails)

# Books are now loaded from database

# Time and Late Fee Logic
BORROW_LIMIT_DAYS = 15
GRACE_PERIOD_DAYS = 3
LATE_FEE_PER_DAYS = 0.50

def show_info(title, msg): messagebox.showinfo(title, msg)
def show_error(title, msg): messagebox.showerror(title, msg)

class CodXCloudApp:
    def __init__(self, root: ttk.Window):
        self.root = root
        self.root.title("CodXCloud - Library System")
        self.root.geometry("1280x900")
        self.current_user = None
        self._card_imgs = []
        self._timer_widgets = []  # To store active countdown references

        self._build_header()
        self._build_content_area()
        self.root.withdraw()
        self.create_login_window()

    def _build_header(self):
        header = ttk.Frame(self.root, padding=8)
        header.pack(side="top", fill="x")

        try:
            image_path = "codxcloud_dvlp/codxcloud logo 3 up.png"
            original_image = Image.open(image_path)
            resized_image = original_image.resize((150, 75), Image.Resampling.LANCZOS)
            self.header_logo = ImageTk.PhotoImage(resized_image)
            logo_image = self.header_logo
        except:
            logo_image = None

        title_btn = ttk.Button(
            header,
            text="CodXCloud" if not logo_image else "",
            image=logo_image,
            bootstyle="link",
            command=lambda: self.show_view("search")
        )
        title_btn.pack(side="left", padx=5, pady=5)

        right = ttk.Frame(header)
        right.pack(side="right", padx=20)
        menu_btn = ttk.Menubutton(right, text="☰ Menu", bootstyle="secondary-outline")
        menu_btn.pack(side="right")
        menu = tk.Menu(menu_btn, tearoff=0)
        menu.add_command(label="Search", command=lambda: self.show_view("search"))
        menu.add_command(label="Borrow/Return", command=lambda: self.show_view("borrow"))

        menu.add_separator()
        menu.add_command(label="Profile", command=lambda: self.show_view("profile"))
        menu.add_command(label="Top Up Wallet", command=lambda: self.show_view("topup"))
        menu.add_command(label="Transactions", command=lambda: self.show_view("transactions"))

        menu.add_separator()
        menu.add_command(label="Donate", command=lambda: self.show_view("donate"))
        menu.add_separator()
        menu.add_command(label="Logout", command=self._logout_action)
        menu_btn["menu"] = menu

    def _build_content_area(self):
        self.content_frame = ttk.Frame(self.root, padding=20)
        self.content_frame.pack(fill="both", expand=True)

    def clear_content(self):
        for w in self.content_frame.winfo_children(): w.destroy()

    def show_view(self, view_name):
        self.clear_content()
        if view_name == "search":
            self._view_search_cards()
        elif view_name == "borrow":
            self._view_borrow_return()
        elif view_name == "profile":
            self._view_profile()
        elif view_name == "topup":
            self._view_topup()
        elif view_name == "donate":
            self._view_donation()
        elif view_name == "transactions":
            self._view_transactions()
        else:
            self._view_search_cards()

    # Search Card Layout
    def _view_search_cards(self):
        top = ttk.Frame(self.content_frame)
        top.pack(fill="x", pady=(0, 10))
        ttk.Label(top, text="Search Books", font=("Helvetica", 20, "bold"), bootstyle="info").pack(side="left", padx=10,
                                                                                                   pady=10)
        search_entry = ttk.Entry(top, width=50)
        search_entry.pack(side="left", padx=10)
        search_type = tk.StringVar(value="Title")
        ttk.Radiobutton(top, text="Title", variable=search_type, value="Title", bootstyle="info-toolbutton").pack(
            side="left", padx=4)
        ttk.Radiobutton(top, text="Author", variable=search_type, value="Author", bootstyle="info-toolbutton").pack(
            side="left", padx=4)

        container = ttk.Frame(self.content_frame)
        container.pack(fill="both", expand=True)

        # Canvas
        canvas = tk.Canvas(container, highlightthickness=0)

        # Scrollbars (Vertical & Horizontal)
        v_scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        h_scrollbar = ttk.Scrollbar(container, orient="horizontal", command=canvas.xview)  # New Horizontal Bar

        scrollable = ttk.Frame(canvas)
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=scrollable, anchor="nw")

        # Configure Canvas to use both scrollbars
        canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Pack (Layout Order)
        h_scrollbar.pack(side="bottom", fill="x")  # Pack bottom scrollbar first
        v_scrollbar.pack(side="right", fill="y")  # Pack vertical scrollbar right
        canvas.pack(side="left", fill="both", expand=True)  # Canvas fills the rest

        def _on_mousewheel(event):
            if event.delta: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        # Horizontal scrolling with Shift + MouseWheel
        def _on_shift_mousewheel(event):
            if event.delta: canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Shift-MouseWheel>", _on_shift_mousewheel)

        card_counter = {"i": 0}

        def clear_cards():
            for c in scrollable.winfo_children(): c.destroy()
            self._card_imgs.clear()

        def borrow_book(bid, btn):
            book = BOOKS.get(bid)
            if not self.current_user: show_error("Error", "Please login first"); return
            if book and book["available"]:
                book["available"] = False
                book["borrowed_by"] = self.current_user
                book["borrow_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                db.update_book_status(bid, False, self.current_user, book["borrow_date"])
                btn.configure(text="Borrowed", state="disabled", bootstyle="danger")
                show_info("Success", f"Borrowed {book['title']}\nDue in 15 days.")
            else:
                show_error("Error", "Not available")

        def make_card(parent, bid, book):
            r = card_counter["i"] // 2
            c = card_counter["i"] % 2
            card = ttk.Frame(parent, padding=(15, 15), relief="raised", bootstyle="secondary")
            card.grid(row=r, column=c, padx=30, pady=30, sticky="nsew")
            parent.grid_columnconfigure(0, weight=1)
            parent.grid_columnconfigure(1, weight=1)
            parent.grid_rowconfigure(r, weight=1, uniform="cards")

            left = ttk.Frame(card, width=150)
            left.pack(side="left", padx=(0, 15))
            
            img_path = book.get("image_path")
            img_obj = None
            
            if img_path:
                try:
                    # Attempts to open image
                    pil_img = Image.open(img_path)
                    
                    # Resize and crop to fill
                    final_img = ImageOps.fit(pil_img, (150, 200), Image.Resampling.LANCZOS)
                    
                    img_obj = ImageTk.PhotoImage(final_img)
                    self._card_imgs.append(img_obj) # Keep reference
                except Exception as e:
                    print(f"Error loading image for {book['title']}: {e}")
                    img_obj = None

            if img_obj:
                lbl_img = ttk.Label(left, image=img_obj)
                lbl_img.pack()
            else:
                placeholder = tk.Canvas(left, width=100, height=150, highlightthickness=0)
                placeholder.create_rectangle(0, 0, 100, 150, fill="#f1f1f1", outline="#999999")
                placeholder.create_text(50, 75, text="No\nImage", justify="center", font=("Helvetica", 10))
                placeholder.pack()

            middle = ttk.Frame(card)
            middle.pack(side="left", fill="both", expand=True)
            ttk.Label(middle, text=book["title"], font=("Helvetica", 16, "bold")).pack(anchor="w", padx=(10, 0),
                                                                                       pady=(10, 0))
            ttk.Label(middle, text=f"Author: {book['author']}", font=("Helvetica", 12)).pack(anchor="w", padx=(10, 0),
                                                                                             pady=(0, 5))
            st = "Available" if book["available"] else f"Borrowed by {book['borrowed_by']}"
            ttk.Label(middle, text=f"Status: \n{st}", font=("Helvetica", 10)).pack(anchor="w", padx=(10, 0),
                                                                                   pady=(0, 50))

            right = ttk.Frame(card, width=150)
            right.pack(side="right", fill="y")
            right_inner = ttk.Frame(right)
            right_inner.place(relx=0.5, rely=0.5, anchor="center")
            borrow_btn = ttk.Button(right_inner, text="Borrow", width=14, bootstyle="danger")
            if not book["available"]: borrow_btn.configure(text="Not Available", state="disabled",
                                                           bootstyle="secondary")
            borrow_btn.pack(pady=10)
            borrow_btn.configure(command=lambda bid=bid, btn=borrow_btn: borrow_book(bid, btn))
            card_counter["i"] += 1


        def perform_search(q, mode):
            clear_cards()
            card_counter["i"] = 0
            q = (q or "").strip().lower()
            results = []
            for k, v in BOOKS.items():
                if not q or (mode == "Title" and q in v["title"].lower()) or (
                        mode == "Author" and q in v["author"].lower()):
                    results.append((k, v))
            if not results:
                ttk.Label(scrollable, text="No results found.", font=("Helvetica", 12)).grid(row=0, column=0,
                                                                                             columnspan=2, pady=20)
                return
            for bid, book in results: make_card(scrollable, bid, book)
            scrollable.update_idletasks()
            canvas.config(scrollregion=canvas.bbox("all"))

        ttk.Button(top, text="Search", bootstyle="primary",
                   command=lambda: perform_search(search_entry.get(), search_type.get())).pack(side="left", padx=10)
        perform_search("", "Title")

    def _calculate_overdue_info(self, book):
        """Helper: Returns (fee, days_held, overdue_days) for a specific book."""
        borrowed_date_str = book.get("borrow_date")
        if not borrowed_date_str:
            return 0.0, 0, 0

        try:
            b_date = datetime.strptime(borrowed_date_str, "%Y-%m-%d %H:%M:%S")
            now_date = datetime.now()
            diff = now_date - b_date
            days_held = diff.days

            cutoff_days = BORROW_LIMIT_DAYS + GRACE_PERIOD_DAYS

            if days_held > cutoff_days:
                overdue_days = days_held - BORROW_LIMIT_DAYS
                fee = overdue_days * LATE_FEE_PER_DAYS
                return fee, days_held, overdue_days
            return 0.0, days_held, 0
        except ValueError:
            return 0.0, 0, 0

    # Borrow & Return
    def _view_borrow_return(self):
        # Header
        ttk.Label(self.content_frame, text="Borrow / Return Books", font=("Helvetica", 24, "bold"),
                  bootstyle="primary").pack(pady=(0, 10))

        # Manual Selection (Quick Borrow/Return)
        top_frame = ttk.Labelframe(self.content_frame, text="Manual Action", padding=15, bootstyle="secondary")
        top_frame.pack(fill="x", pady=10)

        ttk.Label(top_frame, text="Book ID:", font=("Helvetica", 12)).pack(side="left", padx=5)
        entry_bid = ttk.Entry(top_frame, width=15)
        entry_bid.pack(side="left", padx=5)

        # Forward declaration so manual actions can refresh the table
        def refresh_overdue_table():
            pass

        def manual_borrow():
            bid = entry_bid.get().strip()
            book = BOOKS.get(bid)
            if not self.current_user:
                show_error("Error", "Please log in.")
                return

            if book and book["available"]:
                book["available"] = False
                book["borrowed_by"] = self.current_user
                book["borrow_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                book["fee_cleared"] = False # Reset fee status on new borrow
                db.update_book_status(bid, False, self.current_user, book["borrow_date"], False)

                show_info("Success", f"Borrowed: {book['title']}")
                entry_bid.delete(0, tk.END)
                refresh_overdue_table()
            else:
                show_error("Error", "Book unavailable or Invalid ID.")

        def manual_return():
            bid = entry_bid.get().strip()
            book = BOOKS.get(bid)
            if not self.current_user:
                show_error("Error", "Please log in.")
                return

            if book and not book["available"] and book["borrowed_by"] == self.current_user:
                # Calculate if there is a fee
                fee, _, _ = self._calculate_overdue_info(book)

                # Check if Fee exists and has not been paid yet
                if fee > 0 and not book.get("fee_cleared", False):
                    show_error("Overdue Restriction",
                               f"This book has an unpaid overdue fee of ${fee:.2f}.\n\n"
                               "Please select the book in the list below and click 'Pay Overdue Fee' "
                               "using your wallet balance before returning.")
                    return

                # Process Return
                book["available"] = True
                book["borrowed_by"] = None
                book["borrow_date"] = None
                book["fee_cleared"] = False  # Reset for next person
                db.update_book_status(bid, True, None, None, False)

                show_info("Success", f"Returned: {book['title']}")
                entry_bid.delete(0, tk.END)
                refresh_overdue_table()
            else:
                show_error("Error", "Invalid ID or not borrowed by you.")

        ttk.Button(top_frame, text="Borrow", bootstyle="success", command=manual_borrow).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Quick Return", bootstyle="warning", command=manual_return).pack(side="left", padx=5)

       # Overdue Fee & Active Borrow Lists
        ttk.Separator(self.content_frame, orient="horizontal").pack(fill="x", pady=20)

        # Header with Wallet Balance display
        list_header = ttk.Frame(self.content_frame)
        list_header.pack(fill="x")
        ttk.Label(list_header, text="Active Borrow and Overdue Fees List", font=("Helvetica", 16, "bold"),
                  bootstyle="danger").pack(side="left")

        user_data = db.get_user(self.current_user)
        curr_bal = user_data["balance"] if user_data else 0.00
        self.lbl_balance_mini = ttk.Label(list_header, text=f"My Wallet: ${curr_bal:.2f}",
                                          font=("Helvetica", 12, "bold"), bootstyle="success")
        self.lbl_balance_mini.pack(side="right")

        # Table Container
        table_frame = ttk.Frame(self.content_frame)
        table_frame.pack(fill="both", expand=True, pady=5)

        cols = ("bid", "title", "due", "fee", "status")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=8, bootstyle="danger")

        tree.heading("bid", text="ID", anchor="center")
        tree.heading("title", text="Title", anchor="w")
        tree.heading("due", text="Days Overdue", anchor="center")
        tree.heading("fee", text="Late Fee", anchor="e")
        tree.heading("status", text="Payment Status", anchor="center")

        tree.column("bid", width=50, anchor="center", stretch=False)
        tree.column("title", width=300, anchor="w", stretch=True)
        tree.column("due", width=150, anchor="center", stretch=False)
        tree.column("fee", width=100, anchor="e", stretch=False)
        tree.column("status", width=180, anchor="center", stretch=False)

        v_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=v_scroll.set)
        tree.pack(side="left", fill="both", expand=True)
        v_scroll.pack(side="right", fill="y")

        # Action Buttons (Pay Fee)
        action_frame = ttk.Frame(self.content_frame)
        action_frame.pack(fill="x", pady=10)

        # Pay button
        btn_pay = ttk.Button(action_frame, text="Pay Overdue Fee", state="disabled", bootstyle="danger")
        btn_pay.pack(side="right", padx=5)

        # Logic Functions for Table & Payment
        def process_pay_fee(bid, amount):
            """Deducts balance and marks book as cleared."""
            user_obj = db.get_user(self.current_user)

            if float(user_obj["balance"]) >= amount:
                # Deduct Balance
                new_balance = float(user_obj["balance"]) - amount
                user_obj["balance"] = new_balance

                # Record Transaction
                tx_id = f"FEE{random.randint(1000, 9999)}"
                db.add_transaction(tx_id, self.current_user, -amount, "Late Fee Payment", datetime.now().strftime("%Y-%m-%d %H:%M"))
                db.update_user_balance(self.current_user, user_obj["balance"])

                # Mark book as cleared in database
                # Handle potential string / integers mismatch for keys
                if bid in BOOKS:
                    BOOKS[bid]["fee_cleared"] = True
                    db.update_book_status(bid, BOOKS[bid]["available"], BOOKS[bid]["borrowed_by"], BOOKS[bid]["borrow_date"], True)
                elif int(bid) in BOOKS:  # Fallback if IDs are integers
                    BOOKS[int(bid)]["fee_cleared"] = True

                messagebox.showinfo("Payment Successful",
                                    f"Paid ${amount:.2f} overdue fee.\n"
                                    "Status updated to PAID. You can now return this book.")

                # Refresh UI
                refresh_overdue_table()
            else:
                show_error("Insufficient Funds",
                           f"Fee Required: ${amount:.2f}\n"
                           f"Your Balance: ${user_obj['balance']:.2f}\n\n"
                           "Please go to the 'Top Up Wallet' menu.")

        def on_tree_select(event):
            """Enables/Disables button based on selection status."""
            selected = tree.selection()
            if not selected:
                btn_pay.configure(state="disabled")
                return

            item = tree.item(selected[0])
            val = item["values"]

            # Extract data from columns
            bid = str(vals[0])
            # Remove currency symbol for calculation
            fee_str = str(val[3]).replace("$", "")
            status = val[4]

            try:
                fee = float(fee_str)
            except ValueError:
                fee = 0.0

            # Process Logic: Unlock PAY button only if Fee > 0 AND it is NOT paid yet
            if fee > 0 and "UNPAID" in status:
                btn_pay.configure(state="normal",
                                  text=f"Pay ${fee:.2f}",
                                  command=lambda: process_pay_fee(bid, fee))
            else:
                btn_pay.configure(state="disabled", text="Pay Overdue Fee")

        def refresh_overdue_table():
            """Reloads the treeview and updates mini-balance label."""
            # Clear current items
            for item in tree.get_children():
                tree.delete(item)

            if not self.current_user: return

            # Update Mini Balance Label
            u_data = db.get_user(self.current_user)
            bal = u_data["balance"] if u_data else 0.00
            self.lbl_balance_mini.configure(text=f"My Wallet: ${bal:.2f}")

            # Populate rows
            for bid, book in BOOKS.items():
                if book.get("borrowed_by") == self.current_user:
                    fee, _, overdue_days = self._calculate_overdue_info(book)
                    is_cleared = book.get("fee_cleared", False)

                    # Determine Status Text
                    if fee > 0:
                        if is_cleared:
                            status_txt = "PAID (Ready to Return)"
                            fee_txt = f"${fee:.2f}"
                            # Text based indicator for late payment indication
                        else:
                            status_txt = "UNPAID"
                            fee_txt = f"${fee:.2f}"
                    else:
                        status_txt = "On Time"
                        fee_txt = "$0.00"

                    tree.insert("", "end",
                                values=(bid, book["title"],
                                        overdue_days if overdue_days > 0 else "-",
                                        fee_txt,
                                        status_txt))

            # Reset Button
            btn_pay.configure(state="disabled", text="Pay Overdue Fee")

        # Bind Click Event
        tree.bind("<<TreeviewSelect>>", on_tree_select)

        # Initial Load
        refresh_overdue_table()

        def on_tree_select(event):
            selected = tree.selection()
            if not selected: return

            item = tree.item(selected[0])
            vals = item["values"]  # (bid, title, days, fee, status)
            bid = str(vals[0])
            status = vals[4]
            fee_str = vals[3].replace("$", "")
            fee = float(fee_str)

            # Logic to unlock Return Button
            # Return Button: Unlocked if Fee is 0 OR Status contains "PAID" or "On Time"
            if fee == 0 or "PAID" in status or "On Time" in status:
                btn_pay.configure(state="disabled")  # No need to pay
            else:
                # Pay Button: Unlocked if Fee > 0 AND Status is UNPAID
                btn_pay.configure(state="normal", command=lambda: process_pay_fee(bid, fee))

        def process_pay_fee(bid, amount):
            user_obj = db.get_user(self.current_user)
            if float(user_obj["balance"]) >= amount:
                # Deduct
                new_balance = float(user_obj["balance"]) - amount
                user_obj["balance"] = new_balance

                # Record Transaction
                tx_id = f"FEE{random.randint(1000, 9999)}"
                db.add_transaction(tx_id, self.current_user, -amount, "Late Fee", datetime.now().strftime("%Y-%m-%d %H:%M"))
                db.update_user_balance(self.current_user, user_obj["balance"])

                # Mark book as cleared in memory
                if bid in BOOKS:
                    BOOKS[bid]["fee_cleared"] = True

                messagebox.showinfo("Payment Successful",
                                    f"Paid ${amount:.2f} overdue fee.\nYou can now return the book.")
                refresh_overdue_table()  # Refresh to update status to PAID
            else:
                show_error("Insufficient Funds",
                           f"Required: ${amount:.2f}\nBalance: ${user_obj['balance']:.2f}\nPlease Top Up.")

        tree.bind("<<TreeviewSelect>>", on_tree_select)

        # Initial reload
        refresh_overdue_table()

    def _view_profile(self):
        ttk.Label(self.content_frame, text="My Profile", font=("Helvetica", 24, "bold"), bootstyle="primary").pack(
            pady=(0, 10))
        if not self.current_user: ttk.Label(self.content_frame, text="Please login first.").pack(); return

        user_data = db.get_user(self.current_user)
        bal = user_data["balance"] if user_data else 0.00

        info_frame = ttk.Frame(self.content_frame, padding=20)
        info_frame.pack(fill="x", pady=10)

        ttk.Label(info_frame, text=f"User: {self.current_user}", font=("Helvetica", 16, "bold")).pack(anchor="w")
        ttk.Label(info_frame, text=f"Wallet Balance: ${bal:.2f}", font=("Helvetica", 16, "bold"),
                  bootstyle="success").pack(anchor="w")

        ttk.Label(self.content_frame, text="Borrowed Books:", font=("Helvetica", 12, "bold")).pack(pady=(20, 5),
                                                                                                   anchor="w")

        self._timer_widgets = []
        books_frame = ttk.Frame(self.content_frame)
        books_frame.pack(fill="both", expand=True, padx=20)

        found_books = False
        for bid, book in BOOKS.items():
            if book.get("borrowed_by") == self.current_user:
                found_books = True
                row = ttk.Frame(books_frame, padding=5)
                row.pack(fill="x", pady=5)
                ttk.Label(row, text=f"{bid} - {book['title']}", font=("Helvetica", 11)).pack(side="left")
                timer_lbl = ttk.Label(row, text="--", font=("Consolas", 10, "bold"), bootstyle="info")
                timer_lbl.pack(side="right")

                if book.get("borrow_date"):
                    try:
                        start_date = datetime.strptime(book["borrow_date"], "%Y-%m-%d %H:%M:%S")
                        due_date = start_date + timedelta(days=BORROW_LIMIT_DAYS)
                        self._timer_widgets.append((timer_lbl, due_date))
                    except ValueError:
                        timer_lbl.configure(text="Date Error")
                else:
                    timer_lbl.configure(text="No Date")

        if found_books:
            self._update_timers()
        else:
            ttk.Label(books_frame, text="No books borrowed.", font=("Helvetica", 12, "italic")).pack(anchor="w")

    def _update_timers(self):
        if not self._timer_widgets or not self._timer_widgets[0][0].winfo_exists(): return
        now = datetime.now()
        for lbl, due_date in self._timer_widgets:
            if not lbl.winfo_exists(): continue
            remaining = due_date - now
            if remaining.total_seconds() > 0:
                d = remaining.days
                h, rem = divmod(remaining.seconds, 3600)
                m, s = divmod(rem, 60)
                lbl.configure(text=f"Due in: {d}d {h:02}h {m:02}m {s:02}s", bootstyle="warning")
            else:
                overdue = abs(remaining)
                d_over = overdue.days
                lbl.configure(text=f"OVERDUE by {d_over} days", bootstyle="danger")
        self.root.after(1000, self._update_timers)


    # Top Up Wallet View
    def _view_topup(self):
        ttk.Label(self.content_frame, text="Top Up Wallet", font=("Helvetica", 24, "bold"), bootstyle="primary").pack(
            pady=(0, 20))
        if not self.current_user:
            ttk.Label(self.content_frame, text="Please login to top up.", font=("Helvetica", 14)).pack();
            return

        main_frame = ttk.Frame(self.content_frame, padding=10)
        main_frame.pack(fill="both", expand=True, padx=20)

        curr_bal = db.get_user(self.current_user)["balance"]
        ttk.Label(main_frame, text=f"Current Balance: ${curr_bal:.2f}", font=("Helvetica", 18),
                  bootstyle="success").pack(pady=10)

        amount_frame = ttk.Labelframe(main_frame, text="1. Select Top Up Amount", padding=15, bootstyle="success")
        amount_frame.pack(fill="x", pady=10)

        self.topup_amount = tk.StringVar(value="10")
        btn_grid = ttk.Frame(amount_frame)
        btn_grid.pack(fill="x", pady=5)

        def set_amount(val):
            self.topup_amount.set(val)

        for i, amt in enumerate(["10", "20", "50", "100"]):
            ttk.Button(btn_grid, text=f"${amt}", bootstyle="outline-success",
                       command=lambda a=amt: set_amount(a)).pack(side="left", expand=True, fill="x", padx=5)

        custom_frame = ttk.Frame(amount_frame)
        custom_frame.pack(fill="x", pady=10)
        ttk.Label(custom_frame, text="Custom Amount: $").pack(side="left")
        ttk.Entry(custom_frame, textvariable=self.topup_amount, width=10).pack(side="left", padx=5)

        ttk.Label(main_frame, text="2. Select Payment Method", font=("Helvetica", 10, "bold")).pack(anchor="w",
                                                                                                    pady=(10, 5))
        payment_tabs = ttk.Notebook(main_frame, bootstyle="success")
        payment_tabs.pack(fill="both", expand=True, pady=5)

        card_tab = ttk.Frame(payment_tabs, padding=15)
        payment_tabs.add(card_tab, text="Credit / Debit Card")
        form_frame = ttk.Frame(card_tab)
        form_frame.pack(expand=True)
        my_font = ("Helvetica", 12)

        ttk.Label(form_frame, text="Card Type:", font=my_font).grid(row=0, column=0, sticky="e", padx=5, pady=10)
        c_type = ttk.Combobox(form_frame, values=["Visa", "MasterCard", "PayPal"], state="readonly", width=28,
                              font=my_font)
        c_type.current(0)
        c_type.grid(row=0, column=1, sticky="w", padx=5, pady=10)

        ttk.Label(form_frame, text="Card Number:", font=my_font).grid(row=1, column=0, sticky="e", padx=5, pady=10)
        card_entry = ttk.Entry(form_frame, width=30, font=my_font)
        card_entry.grid(row=1, column=1, sticky="w", padx=5, pady=10)

        row3 = ttk.Frame(form_frame)
        row3.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Label(row3, text="Exp: (MM/YY)", font=my_font).pack(side="left", padx=(5, 5))
        ttk.Entry(row3, width=8, font=my_font).pack(side="left", padx=5)
        ttk.Label(row3, text="CVC / CVV:", font=my_font).pack(side="left", padx=(15, 5))
        ttk.Entry(row3, width=5, show="*", font=my_font).pack(side="left", padx=5)

        qr_tab = ttk.Frame(payment_tabs, padding=15)
        payment_tabs.add(qr_tab, text="QR Pay / E-Wallet")
        qr_content = ttk.Frame(qr_tab)
        qr_content.pack(expand=True, fill="both")
        qr_info = ttk.Frame(qr_content)
        qr_info.pack(side="left", expand=True, fill="both", padx=10)
        ttk.Label(qr_info, text="Scan to Top Up", font=("Helvetica", 18, "bold")).pack(anchor="w")
        ttk.Label(qr_info, text="• DuitNow QR\n• Touch 'n Go\n• SarawakPay\n• ShopeePay\n• GrabPay\n• Atome", font=("Helvetica", 14), justify="left").pack(
            anchor="w", pady=5)

        qr_visual = ttk.Frame(qr_content)
        qr_visual.pack(side="right", padx=20)
        try:
            encoded_data = urllib.parse.quote("https://codxcloud.com/wallet/topup")
            api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={encoded_data}"
            with urllib.request.urlopen(api_url, timeout=5) as u:
                raw_data = u.read()
            b64_data = base64.encodebytes(raw_data)
            qr_image = tk.PhotoImage(data=b64_data)
            qr_label = ttk.Label(qr_visual, image=qr_image)
            qr_label.image = qr_image
            qr_label.pack()
        except:
            fallback = tk.Canvas(qr_visual, width=150, height=150, bg="white")
            fallback.pack()
            fallback.create_text(75, 75, text="QR Offline")
        ttk.Label(qr_visual, text="QR Payment", font=("Helvetica", 12), justify="center").pack()

        # Process for topup
        def process_topup():
            try:
                amt = float(self.topup_amount.get())
                if amt <= 0: raise ValueError
            except ValueError:
                show_error("Error", "Invalid Amount");
                return

            current_tab_index = payment_tabs.index(payment_tabs.select())
            payment_method = "Card" if current_tab_index == 0 else "QR Payment"

            if current_tab_index == 0:
                if len(card_entry.get()) < 16:
                    show_error("Payment Error", "Invalid Card Number.");
                    return

            pay_btn.configure(state="disabled", text="Processing...")
            pb = ttk.Progressbar(main_frame, mode='indeterminate', length=300, bootstyle="success-striped")
            pb.pack(pady=10)
            pb.start(10)

            def on_success():
                pb.stop()
                pb.destroy()
                pay_btn.configure(state="normal", text="Confirm Top Up")
                db.update_user_balance(self.current_user, float(db.get_user(self.current_user)["balance"]) + amt)
                
                tx_id = f"TOP{random.randint(10000, 99999)}"
                db.add_transaction(tx_id, self.current_user, amt, payment_method, datetime.now().strftime("%Y-%m-%d %H:%M"))
                msg = f"Successfully received ${amt:.2f} via {payment_method}!\nTransaction Recorded."
                show_info("Top Up Successful", msg)
                self.show_view("topup")

            # Simulate online delay
            self.root.after(3500, on_success)

        pay_btn = ttk.Button(main_frame, text="Confirm Top Up", bootstyle="success", width=25, command=process_topup)
        pay_btn.pack(pady=20)

    # Transaction Table
    def _view_transactions(self):
        ttk.Label(self.content_frame, text="Transaction History", font=("Helvetica", 24, "bold"),
                  bootstyle="primary").pack(pady=(0, 20))
        if not self.current_user: ttk.Label(self.content_frame, text="Please login.").pack(); return
        user_txns = db.get_transactions(self.current_user)
        if not user_txns: ttk.Label(self.content_frame, text="No transactions found.",
                                    font=("Helvetica", 12, "italic")).pack(); return

        table_frame = ttk.Frame(self.content_frame)
        table_frame.pack(fill="both", expand=True, padx=50)
        scroll = ttk.Scrollbar(table_frame)
        scroll.pack(side="right", fill="y")
        columns = ("date", "id", "method", "amount")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", yscrollcommand=scroll.set, bootstyle="light")
        tree.heading("date", text="Date / Time");
        tree.heading("id", text="ID");
        tree.heading("method", text="Method");
        tree.heading("amount", text="Amount")
        tree.column("date", width=200, anchor="center");
        tree.column("id", width=150, anchor="center");
        tree.column("method", width=100, anchor="center");
        tree.column("amount", width=100, anchor="center")
        scroll.config(command=tree.yview)
        tree.pack(fill="both", expand=True)
        for txn in user_txns:
            tree.insert("", tk.END, values=(txn["date"], txn["id"], txn["method"], f"${txn['amount']:.2f}"))

    # Donation / Payment Page
    def _view_donation(self):
        center_frame = ttk.Frame(self.content_frame)
        center_frame.pack(expand=True, fill="both", padx=20)
        ttk.Label(center_frame, text="Support CodXCloud", font=("Helvetica", 24, "bold"), bootstyle="primary").pack(
            pady=(0, 10))
        ttk.Label(center_frame, text="Your support helps the community and the eco-friendly environment!", font=("Helvetica", 12)).pack(
            pady=(0, 20))
        amount_frame = ttk.Labelframe(center_frame, text="1. Select Amount", padding=15, bootstyle="info")
        amount_frame.pack(fill="x", pady=10)
        self.donation_amount = tk.StringVar(value="10")
        btn_grid = ttk.Frame(amount_frame)
        btn_grid.pack(fill="x", pady=5)
        for i, amt in enumerate(["5", "10", "20", "50"]):
            ttk.Button(btn_grid, text=f"${amt}", bootstyle="outline-info",
                       command=lambda a=amt: self.donation_amount.set(a)).pack(side="left", expand=True, fill="x",
                                                                               padx=5)
        custom_frame = ttk.Frame(amount_frame)
        custom_frame.pack(fill="x", pady=10)
        ttk.Label(custom_frame, text="Custom Amount: $").pack(side="left")
        ttk.Entry(custom_frame, textvariable=self.donation_amount, width=10).pack(side="left", padx=5)
        ttk.Label(center_frame, text="2. Select Payment Method", font=("Helvetica", 10, "bold")).pack(anchor="w",
                                                                                                      pady=(10, 5))
        payment_tabs = ttk.Notebook(center_frame, bootstyle="primary")
        payment_tabs.pack(fill="both", expand=True, pady=5)
        card_tab = ttk.Frame(payment_tabs, padding=15);
        payment_tabs.add(card_tab, text="Credit / Debit Card")
        form_frame = ttk.Frame(card_tab);
        form_frame.pack(expand=True);
        my_font = ("Helvetica", 12)
        ttk.Label(form_frame, text="Card Type:", font=my_font).grid(row=0, column=0, sticky="e", padx=5, pady=10)
        c_type = ttk.Combobox(form_frame, values=["Visa", "MasterCard", "PayPal"], state="readonly", width=28,
                              font=my_font);
        c_type.current(0);
        c_type.grid(row=0, column=1, sticky="w", padx=5, pady=10)
        ttk.Label(form_frame, text="Card Number:", font=my_font).grid(row=1, column=0, sticky="e", padx=5, pady=10)
        card_entry = ttk.Entry(form_frame, width=30, font=my_font);
        card_entry.grid(row=1, column=1, sticky="w", padx=5, pady=10)
        row3 = ttk.Frame(form_frame);
        row3.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Label(row3, text="Exp: (MM/YY)", font=my_font).pack(side="left", padx=(5, 5));
        ttk.Entry(row3, width=8, font=my_font).pack(side="left", padx=5)
        ttk.Label(row3, text="CVC / CVV:", font=my_font).pack(side="left", padx=(15, 5));
        ttk.Entry(row3, width=5, show="*", font=my_font).pack(side="left", padx=5)
        qr_tab = ttk.Frame(payment_tabs, padding=15);
        payment_tabs.add(qr_tab, text="QR Pay / E-Wallet")
        qr_content = ttk.Frame(qr_tab);
        qr_content.pack(expand=True, fill="both")
        qr_info = ttk.Frame(qr_content);
        qr_info.pack(side="left", expand=True, fill="both", padx=10)
        ttk.Label(qr_info, text="Scan with:", font=("Helvetica", 18, "bold")).pack(anchor="w")
        ttk.Label(qr_info, text="• DuitNow QR\n• Touch 'n Go\n• SarawakPay\n• ShopeePay\n• GrabPay\n• Atome",
                  font=("Helvetica", 14), justify="left").pack(anchor="w", pady=5)

        qr_visual = ttk.Frame(qr_content);
        qr_visual.pack(side="right", padx=20)
        try:
            encoded_data = urllib.parse.quote("https://codxcloud.com/donation")
            api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={encoded_data}"
            with urllib.request.urlopen(api_url, timeout=5) as u:
                raw_data = u.read()
            b64_data = base64.encodebytes(raw_data);
            qr_image = tk.PhotoImage(data=b64_data)
            qr_label = ttk.Label(qr_visual, image=qr_image);
            qr_label.image = qr_image;
            qr_label.pack()
        except Exception as e:
            print(f"QR Gen Error: {e}");
            fallback_canvas = tk.Canvas(qr_visual, width=120, height=120, bg="white", highlightthickness=1,
                                        highlightbackground="black");
            fallback_canvas.pack();
            fallback_canvas.create_text(60, 60, text="QR Unavailable\n(Offline)", justify="center")
        ttk.Label(qr_visual, text="QR Payment", font=("Helvetica", 12), justify="center").pack()

        # Process
        def process_payment():
            amount = self.donation_amount.get()
            if not amount or not amount.replace('.', '', 1).isdigit(): show_error("Error",
                                            "Please enter a valid amount."); return
            current_tab_index = payment_tabs.index(payment_tabs.select())
            payment_method = "Card" if current_tab_index == 0 else "QR Pay"
            if payment_method == "Card":
                if len(card_entry.get()) < 16: show_error("Payment Error", "Invalid Card Number."); return
            pay_btn.configure(state="disabled", text="Processing...")
            pb = ttk.Progressbar(center_frame, mode='indeterminate', length=300, bootstyle="success-striped")
            pb.pack(pady=10);
            pb.start(10)

            def on_success():
                pb.stop();
                pb.destroy();
                pay_btn.configure(state="normal", text="Donate Now")
                if self.current_user:
                    tx_id = f"DNT{random.randint(10000, 99999)}"
                    now = datetime.now().strftime("%Y-%m-%d %H:%M")
                    db.add_transaction(tx_id, self.current_user, float(amount), payment_method, now)
                msg = f"Successfully received ${amount} via {payment_method}!\nTransaction Recorded."
                show_info("Donation Successful", msg);
                self.show_view("transaction")

            # Simulate online delay
            self.root.after(2000, on_success)

        pay_btn = ttk.Button(center_frame, text="Confirm Donation", bootstyle="success", width=25,
                             command=process_payment);
        pay_btn.pack(pady=20)

    # Login Window
    # Create Login Window
    def create_login_window(self):
        self.login_win = tk.Toplevel(self.root)
        self.login_win.title("Login - CodXCloud")
        self.login_win.geometry("650x320")
        self.login_win.resizable(True, True)
        self.login_win.protocol("WM_DELETE_WINDOW", self.root.quit)

        frm = ttk.Frame(self.login_win, padding=12)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="CodXCloud Login", font=("Bahnschrift", 28, "bold"), bootstyle="primary").pack(pady=8)

        form = ttk.Frame(frm)
        form.pack(pady=6)

        # Username Input
        ttk.Label(form, text="Student ID:", font=("Helvetica", 12)).grid(row=0, column=0, sticky="w", padx=10,
                                                                         pady=(14, 0))
        self.username_entry = ttk.Entry(form, width=26)
        self.username_entry.grid(row=0, column=1, padx=10, pady=(14, 0))

        # Username Error Label
        self.user_error_lbl = ttk.Label(form, text="", font=("Helvetica", 8), bootstyle="danger")
        self.user_error_lbl.grid(row=1, column=1, sticky="w", padx=14, pady=(0, 5))

        # Password Input
        ttk.Label(form, text="Password:", font=("Helvetica", 12)).grid(row=2, column=0, sticky="w", padx=10,
                                                                       pady=(1, 0))
        self.password_entry = ttk.Entry(form, width=26, show="*")
        self.password_entry.grid(row=2, column=1, padx=10, pady=(1, 0))

        def toggle_password(): #To toggle visibility of password
            if self.password_entry.cget('show') == '*':
                self.password_entry.config(show='')
                self.eye_btn.config(text='👁')
            else:
                self.password_entry.config(show='*')
                self.eye_btn.config(text='👁')
        self.eye_btn = ttk.Button(form, text='👁', width=2, command=toggle_password, bootstyle="secondary-outline")
        self.eye_btn.grid(row=2, column=2, padx=(0, 10), pady=(1, 0))

        # Password Error Label
        self.pass_error_lbl = ttk.Label(form, text="", font=("Helvetica", 8), bootstyle="danger")
        self.pass_error_lbl.grid(row=3, column=1, sticky="w", padx=10, pady=(0, 5))

        btnf = ttk.Frame(frm)
        btnf.pack(pady=8)

        # Added command helper to clear errors
        self.username_entry.bind("<Key>", lambda e: self.user_error_lbl.config(text=""))
        self.password_entry.bind("<Key>", lambda e: self.pass_error_lbl.config(text=""))

        self.login_win.bind("<Return>", self._login_action)

        ttk.Button(btnf, text="Login", bootstyle="success-outline", command=self._login_action).grid(row=0, column=0,
                                                                                                     padx=6)
        ttk.Button(btnf, text="Register", bootstyle="primary-outline", command=self._register_action).grid(row=0,
                                                                                                           column=1,
                                                                                                           padx=6)

        self.login_win.focus_set()
        self.login_win.grab_set()
        self.username_entry.focus_set()

    def _clear_errors(self):
        # Helper to wipe error
        self.user_error_lbl.config(text="")
        self.pass_error_lbl.config(text="")

    def _login_action(self, event=None):
        self._clear_errors()

        x = self.username_entry.get().strip()
        y = self.password_entry.get().strip()

        user = db.get_user(x)
        if user and user["password"] == y:
            self.current_user = x
            self.login_win.destroy()
            self.root.deiconify()
            self.show_view("search")
        else:
            self.pass_error_lbl.config(text="Invalid ID or Password")

    def _register_action(self):
        self._clear_errors()
        x, y = self.username_entry.get().strip(), self.password_entry.get().strip()

        # To check specific fields and update specific labels
        has_error = False
        if not x:
            self.user_error_lbl.config(text="Student ID is required")
            has_error = True
        if not y:
            self.pass_error_lbl.config(text="Password is required")
            has_error = True

        if has_error: return

        if db.get_user(x):
            self.user_error_lbl.config(text="User already exists")
            return

        # Register logic
        db.create_user(x, y)

        # inline (green text):
        self.pass_error_lbl.config(text="Registered! Please Login.", bootstyle="success")

        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        self.username_entry.focus_set()

    def _logout_action(self):
        if messagebox.askyesno("Logout", "Are you sure you want to log out?"):
            self.current_user = None
            self.root.withdraw()
            self.create_login_window()


if __name__ == "__main__":
    root = ttk.Window(themename="cosmo")
    app = CodXCloudApp(root)
    root.mainloop()
