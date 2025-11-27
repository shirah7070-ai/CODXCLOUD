import mysql.connector
from mysql.connector import Error
from datetime import datetime
import time

# Data for Migration
INITIAL_USERS = {
    "admin": {"password": "admin123", "balance": 0.00},
}

INITIAL_BOOKS = {
    "001": {"title": "101: Python Language Fundamentals", "author": "C. Bryant", "available": True, "borrowed_by": None, "image_path": "book_cover\\B001.png"},
    "002": {"title": "Introduction to Data Structures", "author": "M. Amani", "available": True, "borrowed_by": None, "image_path": "book_cover\\B002.png"},
    "003": {"title": "CS Basics: Algorithms", "author": "N. Bashirah", "available": True, "borrowed_by": None, "image_path": "book_cover\\B003.png"},
    "004": {"title": "101: Computer Networking", "author": "H. Aldreson", "available": True, "borrowed_by": None, "image_path": "book_cover\\B004.png"},
    "005": {"title": "Understanding Machines", "author": "A. Ng", "available": True, "borrowed_by": None, "image_path": "book_cover\\B005.png"},
    "006": {"title": "Clean Code:\nA Handbook of Agile Software Craftsmanship", "author": "Robert C. Martin", "available": True, "borrowed_by": None, "image_path": "book_cover\\001.jpg"},
    "007": {"title": "The Pragmatic Programmer:\nYour Journey to Mastery", "author": "Andrew Hunt & David Thomas", "available": True, "borrowed_by": None, "image_path": "book_cover\\002.jpeg"},
    "008": {"title": "Code Complete", "author": "Steve McConnell", "available": True, "borrowed_by": None, "image_path": "book_cover\\003.jpeg"},
    "009": {"title": "Design Patterns:\nElements of Reusable Object-Oriented Software", "author": "Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides", "available": True, "borrowed_by": None, "image_path": "book_cover\\004.png"},
    "010": {"title": "Refactoring:\nImproving the Design of Existing Code", "author": "Martin Fowler", "available": True, "borrowed_by": None, "image_path": "book_cover\\005.png"},
    "011": {"title": "The Mythical Man-Month:\nEssays on Software Engineering", "author": "Frederick P. Brooks Jr.", "available": True, "borrowed_by": None, "image_path": "book_cover\\006.jpg"},
    "012": {"title": "Introduction to Algorithms", "author": "Thomas H. Cormen, et al.", "available": True, "borrowed_by": None, "image_path": "book_cover\\007.jpg"},
    "013": {"title": "The C Programming Language", "author": "Brian W. Kernighan & Dennis M. Ritchie", "available": True, "borrowed_by": None, "image_path": "book_cover\\008.jpeg"},
    "014": {"title": "Code:\nThe Hidden Language of Computer Hardware and Software", "author": "Charles Petzold", "available": True, "borrowed_by": None, "image_path": "book_cover\\009.jpeg"},
    "015": {"title": "Programming Pearls", "author": "Jon Bentley", "available": True, "borrowed_by": None, "image_path": "book_cover\\010.jpg"},
    "016": {"title": "Working Effectively with Legacy Code", "author": "Michael C. Feathers", "available": True, "borrowed_by": None, "image_path": "book_cover\\011.jpeg"},
    "017": {"title": "Structure and Interpretation of Computer Programs (SICP)", "author": "Harold Abelson & Gerald Jay Sussman", "available": True, "borrowed_by": None, "image_path": "book_cover\\012.jpg"},
    "018": {"title": "The Art of Computer Programming, Vol. 1–4", "author": "Donald E. Knuth", "available": True, "borrowed_by": None, "image_path": "book_cover\\013.png"},
    "019": {"title": "Grokking Algorithms:\nAn Illustrated Guide for Programmers", "author": "Aditya Bhargava", "available": True, "borrowed_by": None, "image_path": "book_cover\\014.png"},
    "020": {"title": "The Self-Taught Programmer", "author": "Cory Althoff", "available": True, "borrowed_by": None, "image_path": "book_cover\\015.jpeg"},
    "021": {"title": "Python Crash Course", "author": "Eric Matthes", "available": True, "borrowed_by": None, "image_path": "book_cover\\016.jpg"},
    "022": {"title": "Automate the Boring Stuff with Python", "author": "Al Sweigart", "available": True, "borrowed_by": None, "image_path": "book_cover\\017.webp"},
    "023": {"title": "Fluent Python:\nClear, Concise, and Effective Programming", "author": "Luciano Ramalho", "available": True, "borrowed_by": None, "image_path": "book_cover\\018.png"},
    "024": {"title": "Effective Java", "author": "Joshua Bloch", "available": True, "borrowed_by": None, "image_path": "book_cover\\019.png"},
    "025": {"title": "The C++ Programming Language", "author": "Bjarne Stroustrup", "available": True, "borrowed_by": None, "image_path": "book_cover\\020.png"},
    "026": {"title": "JavaScript: The Good Parts", "author": "Douglas Crockford", "available": True, "borrowed_by": None, "image_path": "book_cover\\021.jpeg"},
    "027": {"title": "Head First Design Patterns", "author": "Eric Freeman, et al.", "available": True, "borrowed_by": None, "image_path": "book_cover\\022.png"},
    "028": {"title": "Hacking:\nThe Art of Exploitation", "author": "Jon Erickson", "available": True, "borrowed_by": None, "image_path": "book_cover\\023.jpg"},
    "029": {"title": "The Web Application Hacker's Handbook", "author": "Dafydd Stuttard & Marcus Pinto", "available": True, "borrowed_by": None, "image_path": "book_cover\\024.jpg"},
    "030": {"title": "Metasploit: The Penetration Tester's Guide", "author": "David Kennedy, et al.", "available": True, "borrowed_by": None, "image_path": "book_cover\\025.png"},
    "031": {"title": "Penetration Testing:\nA Hands-On Introduction to Hacking", "author": "Georgia Weidman", "available": True, "borrowed_by": None, "image_path": "book_cover\\026.jpeg"},
    "032": {"title": "The Hacker Playbook 3:\nPractical Guide To Penetration Testing", "author": "Peter Kim", "available": True, "borrowed_by": None, "image_path": "book_cover\\027.jpg"},
    "033": {"title": "Black Hat Python:\nPython Programming for Hackers and Pentesters", "author": "Justin Seitz", "available": True, "borrowed_by": None, "image_path": "book_cover\\028.jpg"},
    "034": {"title": "Gray Hat Hacking:\nThe Ethical Hacker's Handbook", "author": "Shon Harris, et al.", "available": True, "borrowed_by": None, "image_path": "book_cover\\029.png"},
    "035": {"title": "Real-World Bug Hunting:\nA Field Guide to Web Hacking", "author": "Peter Yaworski", "available": True, "borrowed_by": None, "image_path": "book_cover\\030.jpg"},
    "036": {"title": "Linux Basics for Hackers", "author": "OccupyTheWeb", "available": True, "borrowed_by": None, "image_path": "book_cover\\031.jpg"},
    "037": {"title": "Security Engineering:\nA Guide to Building Dependable Distributed Systems", "author": "Ross Anderson", "available": True, "borrowed_by": None, "image_path": "book_cover\\032.png"},
    "038": {"title": "Practical Malware Analysis:\nThe Hands-On Guide to Dissecting Malicious Software", "author": "Michael Sikorski & Andrew Honig", "available": True, "borrowed_by": None, "image_path": "book_cover\\033.jpg"},
    "039": {"title": "Blue Team Field Manual (BTFM)", "author": "Alan J. White & Ben Clark", "available": True, "borrowed_by": None, "image_path": "book_cover\\034.jpg"},
    "040": {"title": "Threat Modeling:\nDesigning for Security", "author": "Adam Shostack", "available": True, "borrowed_by": None, "image_path": "book_cover\\035.jpeg"},
    "041": {"title": "The Practice of Network Security Monitoring", "author": "Richard Bejtlich", "available": True, "borrowed_by": None, "image_path": "book_cover\\036.jpg"},
    "042": {"title": "Defensive Security Handbook:\nBest Practices for Securing Infrastructure", "author": "Lee Brotherston & Amanda Berlin", "available": True, "borrowed_by": None, "image_path": "book_cover\\037.png"},
    "043": {"title": "Applied Cryptography:\nProtocols, Algorithms, and Source Code in C", "author": "Bruce Schneier", "available": True, "borrowed_by": None, "image_path": "book_cover\\038.png"},
    "044": {"title": "Cryptography Engineering", "author": "Niels Ferguson, Bruce Schneier, Tadayoshi Kohno", "available": True, "borrowed_by": None, "image_path": "book_cover\\039.jpg"},
    "045": {"title": "The Code Book:\nThe Science of Secrecy from Ancient Egypt to Quantum Cryptography", "author": "Simon Singh", "available": True, "borrowed_by": None, "image_path": "book_cover\\040.jpg"},
    "046": {"title": "Social Engineering:\nThe Science of Human Hacking", "author": "Christopher Hadnagy", "available": True, "borrowed_by": None, "image_path": "book_cover\\041.jpg"},
    "047": {"title": "The Art of Deception:\nControlling the Human Element of Security", "author": "Kevin Mitnick & William L. Simon", "available": True, "borrowed_by": None, "image_path": "book_cover\\042.jpg"},
    "048": {"title": "Ghost in the Wires:\nMy Adventures as the World's Most Wanted Hacker", "author": "Kevin Mitnick & William L. Simon", "available": True, "borrowed_by": None, "image_path": "book_cover\\043.jpg"},
    "049": {"title": "The Cuckoo's Egg:\nTracking a Spy Through the Maze of Computer Espionage", "author": "Clifford Stoll", "available": True, "borrowed_by": None, "image_path": "book_cover\\044.jpg"},
    "050": {"title": "Sandworm:\nA New Era of Cyberwar and the Hunt for the Kremlin's Most Dangerous Hackers", "author": "Andy Greenberg", "available": True, "borrowed_by": None, "image_path": "book_cover\\045.jpg"},
    "051": {"title": "Countdown to Zero Day:\nStuxnet and the Launch of the World's First Digital Weapon", "author": "Kim Zetter", "available": True, "borrowed_by": None, "image_path": "book_cover\\046.jpg"},
    "052": {"title": "This Is How They Tell Me the World Ends", "author": "Nicole Perlroth", "available": True, "borrowed_by": None, "image_path": "book_cover\\047.jpg"},
    "053": {"title": "Data and Goliath:\nThe Hidden Battles to Collect Your Data and Control Your World", "author": "Bruce Schneier", "available": True, "borrowed_by": None, "image_path": "book_cover\\048.jpg"},
    "054": {"title": "The Fifth Domain:\nDefending Our Country, Our Companies, and Ourselves in the Age of Cyber Threats", "author": "Richard A. Clarke & Robert K. Knake", "available": True, "borrowed_by": None, "image_path": "book_cover\\049.jpg"},
    "055": {"title": "Permanent Record", "author": "Edward Snowden", "available": True, "borrowed_by": None, "image_path": "book_cover\\050.jpeg"}
}

class DatabaseManager:
    def __init__(self):
        self.host = "localhost"
        self.user = "root"
        self.password = "admin"
        self.database = "codxcloud_db"
        self.conn = None
        self.connect()
        self.setup_database()

    def connect(self):
        try:
            self.conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password
            )
            if self.conn.is_connected():
                cursor = self.conn.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
                self.conn.database = self.database
                print("Connected to database")
        except Error as e:
            print(f"Error connecting to MySQL: {e}")

    def setup_database(self):
        if not self.conn: return
        try:
            cursor = self.conn.cursor()
            
            # Users Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username VARCHAR(255) PRIMARY KEY,
                    password VARCHAR(255) NOT NULL,
                    balance DECIMAL(10, 2) DEFAULT 0.00
                )
            """)

            # Books Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS books (
                    id VARCHAR(10) PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    author VARCHAR(255) NOT NULL,
                    available BOOLEAN DEFAULT TRUE,
                    borrowed_by VARCHAR(255),
                    borrow_date DATETIME,
                    fee_cleared BOOLEAN DEFAULT FALSE,
                    image_path VARCHAR(255),
                    FOREIGN KEY (borrowed_by) REFERENCES users(username)
                )
            """)

            # Check if image_path column exists (for migration)
            cursor.execute("SHOW COLUMNS FROM books LIKE 'image_path'")
            if not cursor.fetchone():
                print("Migrating database: Adding image_path column to books table...")
                cursor.execute("ALTER TABLE books ADD COLUMN image_path VARCHAR(255)")

            # Transactions Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id VARCHAR(50) PRIMARY KEY,
                    user VARCHAR(255),
                    amount DECIMAL(10, 2),
                    method VARCHAR(50),
                    date DATETIME,
                    FOREIGN KEY (user) REFERENCES users(username)
                )
            """)
            
            self.conn.commit()
            self._populate_initial_data()
            
        except Error as e:
            print(f"Error creating tables: {e}")

    def _populate_initial_data(self):
        cursor = self.conn.cursor()
        
        # Check if users exist
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            print("Populating initial users...")
            for username, data in INITIAL_USERS.items():
                cursor.execute(
                    "INSERT INTO users (username, password, balance) VALUES (%s, %s, %s)",
                    (username, data["password"], data["balance"])
                )
        
        # Check if books exist
        cursor.execute("SELECT COUNT(*) FROM books")
        if cursor.fetchone()[0] == 0:
            print("Populating initial books...")
            for bid, book in INITIAL_BOOKS.items():
                borrow_date = None 
                cursor.execute(
                    "INSERT INTO books (id, title, author, available, borrowed_by, borrow_date, fee_cleared, image_path) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (bid, book["title"], book["author"], book["available"], book["borrowed_by"], None, False, book.get("image_path", ""))
                )
        
        self.conn.commit()

    def get_user(self, username):
        if not self.conn: return None
        cursor = self.conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        return cursor.fetchone()

    def update_user_balance(self, username, new_balance):
        if not self.conn: return
        cursor = self.conn.cursor()
        cursor.execute("UPDATE users SET balance = %s WHERE username = %s", (new_balance, username))
        self.conn.commit()

    def get_all_books(self):
        if not self.conn: return {}
        cursor = self.conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM books")
        rows = cursor.fetchall()
        books = {}
        for row in rows:
            # Convert DB row to match application dictionary structure
            books[row['id']] = {
                "title": row['title'],
                "author": row['author'],
                "available": bool(row['available']),
                "borrowed_by": row['borrowed_by'],
                "borrow_date": row['borrow_date'].strftime("%Y-%m-%d %H:%M:%S") if row['borrow_date'] else None,
                "fee_cleared": bool(row['fee_cleared']),
                "image_path": row.get('image_path', '')
            }
        return books

    def get_book(self, bid):
        if not self.conn: return None
        cursor = self.conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM books WHERE id = %s", (bid,))
        row = cursor.fetchone()
        if row:
            return {
                "title": row['title'],
                "author": row['author'],
                "available": bool(row['available']),
                "borrowed_by": row['borrowed_by'],
                "borrow_date": row['borrow_date'].strftime("%Y-%m-%d %H:%M:%S") if row['borrow_date'] else None,
                "fee_cleared": bool(row['fee_cleared']),
                "image_path": row.get('image_path', '')
            }
        return None

    def update_book_status(self, bid, available, borrowed_by, borrow_date, fee_cleared=False):
        if not self.conn: return
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE books 
            SET available = %s, borrowed_by = %s, borrow_date = %s, fee_cleared = %s 
            WHERE id = %s
        """, (available, borrowed_by, borrow_date, fee_cleared, bid))
        self.conn.commit()

    def add_transaction(self, tx_id, user, amount, method, date_str):
        if not self.conn: return
        cursor = self.conn.cursor()
        # Parse date string to datetime object
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        except ValueError:
             # Fallback or handle error
             date_obj = datetime.now()

        cursor.execute(
            "INSERT INTO transactions (id, user, amount, method, date) VALUES (%s, %s, %s, %s, %s)",
            (tx_id, user, amount, method, date_obj)
        )
        self.conn.commit()

    def create_user(self, username, password):
        if not self.conn: return False
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password, balance) VALUES (%s, %s, 0.00)",
                (username, password)
            )
            self.conn.commit()
            return True
        except Error as e:
            print(f"Error creating user: {e}")
            return False

    def get_transactions(self, username):
        if not self.conn: return []
        cursor = self.conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM transactions WHERE user = %s ORDER BY date DESC", (username,))
        rows = cursor.fetchall()
        txns = []
        for row in rows:
            txns.append({
                "id": row['id'],
                "user": row['user'],
                "amount": float(row['amount']),
                "method": row['method'],
                "date": row['date'].strftime("%Y-%m-%d %H:%M") if row['date'] else ""
            })
        return txns
