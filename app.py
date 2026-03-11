"""
THE BOOK WORM — Library Management System
Full-stack Flask app with SQLite (no MySQL install needed)
Fixed all bugs from original code
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
import sqlite3, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "bookworm-secret-2024"
DB = "library.db"

# ── DATABASE SETUP ────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db(); c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS BookRecord (
        BookID TEXT PRIMARY KEY,
        BookName TEXT NOT NULL,
        Author TEXT NOT NULL,
        Publisher TEXT NOT NULL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS UserRecord (
        UserID TEXT PRIMARY KEY,
        UserName TEXT NOT NULL,
        Password TEXT NOT NULL,
        BookID TEXT,
        FOREIGN KEY (BookID) REFERENCES BookRecord(BookID)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS AdminRecord (
        AdminID TEXT PRIMARY KEY,
        Password TEXT NOT NULL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS Feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        FeedbackText TEXT NOT NULL,
        Rating INTEGER NOT NULL,
        submitted_at TEXT
    )""")
    # Seed default admins
    for aid, pwd in [("Kunal1020","123"),("Siddesh510","786"),("Vishal305","675")]:
        c.execute("INSERT OR IGNORE INTO AdminRecord VALUES (?,?)", (aid, pwd))
    # Seed default users
    for uid, uname, pwd in [("101","Kunal","1234"),("102","Vishal","3050"),("103","Siddhesh","5010")]:
        c.execute("INSERT OR IGNORE INTO UserRecord VALUES (?,?,?,NULL)", (uid, uname, pwd))
    # Seed sample books
    for bid, bname, auth, pub in [
        ("B001","The Alchemist","Paulo Coelho","HarperCollins"),
        ("B002","To Kill a Mockingbird","Harper Lee","J.B. Lippincott"),
        ("B003","1984","George Orwell","Secker & Warburg"),
        ("B004","Pride and Prejudice","Jane Austen","T. Egerton"),
        ("B005","The Great Gatsby","F. Scott Fitzgerald","Scribner"),
    ]:
        c.execute("INSERT OR IGNORE INTO BookRecord VALUES (?,?,?,?)", (bid, bname, auth, pub))
    conn.commit(); conn.close()

init_db()

# ── AUTH DECORATORS ───────────────────────────────────────────────────────────
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "admin":
            return jsonify({"success": False, "error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

def user_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") not in ("admin", "user"):
            return jsonify({"success": False, "error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

# ── PAGES ─────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

# ── AUTH APIs ─────────────────────────────────────────────────────────────────
@app.route("/api/login/admin", methods=["POST"])
def admin_login():
    d = request.json
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT Password FROM AdminRecord WHERE AdminID=?", (d.get("adminID",""),))
    row = c.fetchone(); conn.close()
    if row and row["Password"] == d.get("password",""):
        session["role"]    = "admin"
        session["user_id"] = d.get("adminID")
        return jsonify({"success": True, "name": d.get("adminID")})
    return jsonify({"success": False, "error": "Invalid AdminID or Password"}), 401

@app.route("/api/login/user", methods=["POST"])
def user_login():
    d = request.json
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT UserName, Password FROM UserRecord WHERE UserID=?", (d.get("userID",""),))
    row = c.fetchone(); conn.close()
    if row and row["Password"] == d.get("password",""):
        session["role"]    = "user"
        session["user_id"] = d.get("userID")
        return jsonify({"success": True, "name": row["UserName"]})
    return jsonify({"success": False, "error": "Invalid UserID or Password"}), 401

@app.route("/api/register/user", methods=["POST"])
def register_user():
    d = request.json
    uid   = d.get("userID","").strip()
    uname = d.get("userName","").strip()
    pwd   = d.get("password","").strip()
    if not uid or not uname or not pwd:
        return jsonify({"success": False, "error": "All fields required"}), 400
    conn = get_db(); c = conn.cursor()
    try:
        c.execute("INSERT INTO UserRecord VALUES (?,?,?,NULL)", (uid, uname, pwd))
        conn.commit()
        return jsonify({"success": True, "message": "Account created! Please login."})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "error": "UserID already exists"}), 400
    finally:
        conn.close()

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})

@app.route("/api/me")
def me():
    if session.get("role"):
        return jsonify({"role": session["role"], "user_id": session["user_id"]})
    return jsonify({"role": None})

# ── BOOK APIs (Admin) ─────────────────────────────────────────────────────────
@app.route("/api/books", methods=["GET"])
@user_required
def get_books():
    conn = get_db(); c = conn.cursor()
    c.execute("""SELECT b.BookID, b.BookName, b.Author, b.Publisher,
                        u.UserName as IssuedBy, u.UserID as IssuedByID
                 FROM BookRecord b
                 LEFT JOIN UserRecord u ON b.BookID = u.BookID
                 ORDER BY b.BookName""")
    rows = [dict(r) for r in c.fetchall()]; conn.close()
    return jsonify(rows)

@app.route("/api/books", methods=["POST"])
@admin_required
def add_book():
    d = request.json
    bid   = d.get("bookID","").strip()
    bname = d.get("bookName","").strip()
    auth  = d.get("author","").strip()
    pub   = d.get("publisher","").strip()
    if not all([bid, bname, auth, pub]):
        return jsonify({"success": False, "error": "All fields required"}), 400
    conn = get_db(); c = conn.cursor()
    try:
        c.execute("INSERT INTO BookRecord VALUES (?,?,?,?)", (bid, bname, auth, pub))
        conn.commit()
        return jsonify({"success": True, "message": f"'{bname}' added successfully!"})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "error": "BookID already exists"}), 400
    finally:
        conn.close()

@app.route("/api/books/<bid>", methods=["PUT"])
@admin_required
def update_book(bid):
    d = request.json
    conn = get_db(); c = conn.cursor()
    c.execute("UPDATE BookRecord SET BookName=?, Author=?, Publisher=? WHERE BookID=?",
              (d.get("bookName"), d.get("author"), d.get("publisher"), bid))
    conn.commit(); conn.close()
    return jsonify({"success": True, "message": "Book updated successfully!"})

@app.route("/api/books/<bid>", methods=["DELETE"])
@admin_required
def delete_book(bid):
    conn = get_db(); c = conn.cursor()
    # Clear issued books first
    c.execute("UPDATE UserRecord SET BookID=NULL WHERE BookID=?", (bid,))
    c.execute("DELETE FROM BookRecord WHERE BookID=?", (bid,))
    conn.commit(); conn.close()
    return jsonify({"success": True, "message": "Book deleted!"})

@app.route("/api/books/search/<query>")
@user_required
def search_books(query):
    conn = get_db(); c = conn.cursor()
    q = f"%{query}%"
    c.execute("""SELECT b.BookID, b.BookName, b.Author, b.Publisher,
                        u.UserName as IssuedBy, u.UserID as IssuedByID
                 FROM BookRecord b
                 LEFT JOIN UserRecord u ON b.BookID = u.BookID
                 WHERE b.BookID LIKE ? OR b.BookName LIKE ? OR b.Author LIKE ?""",
              (q, q, q))
    rows = [dict(r) for r in c.fetchall()]; conn.close()
    return jsonify(rows)

# ── USER APIs (Admin) ─────────────────────────────────────────────────────────
@app.route("/api/users", methods=["GET"])
@admin_required
def get_users():
    conn = get_db(); c = conn.cursor()
    c.execute("""SELECT u.UserID, u.UserName, u.Password,
                        b.BookName, b.BookID as BookIssued
                 FROM UserRecord u
                 LEFT JOIN BookRecord b ON u.BookID = b.BookID
                 ORDER BY u.UserName""")
    rows = [dict(r) for r in c.fetchall()]; conn.close()
    return jsonify(rows)

@app.route("/api/users", methods=["POST"])
@admin_required
def add_user():
    d = request.json
    uid   = d.get("userID","").strip()
    uname = d.get("userName","").strip()
    pwd   = d.get("password","").strip()
    if not all([uid, uname, pwd]):
        return jsonify({"success": False, "error": "All fields required"}), 400
    conn = get_db(); c = conn.cursor()
    try:
        c.execute("INSERT INTO UserRecord VALUES (?,?,?,NULL)", (uid, uname, pwd))
        conn.commit()
        return jsonify({"success": True, "message": f"User '{uname}' added!"})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "error": "UserID already exists"}), 400
    finally:
        conn.close()

@app.route("/api/users/<uid>", methods=["PUT"])
@admin_required
def update_user(uid):
    d = request.json
    conn = get_db(); c = conn.cursor()
    c.execute("UPDATE UserRecord SET UserName=?, Password=? WHERE UserID=?",
              (d.get("userName"), d.get("password"), uid))
    conn.commit(); conn.close()
    return jsonify({"success": True, "message": "User updated!"})

@app.route("/api/users/<uid>", methods=["DELETE"])
@admin_required
def delete_user(uid):
    conn = get_db(); c = conn.cursor()
    c.execute("DELETE FROM UserRecord WHERE UserID=?", (uid,))
    conn.commit(); conn.close()
    return jsonify({"success": True, "message": "User deleted!"})

@app.route("/api/users/search/<query>")
@admin_required
def search_users(query):
    conn = get_db(); c = conn.cursor()
    q = f"%{query}%"
    c.execute("""SELECT u.UserID, u.UserName, u.Password,
                        b.BookName, b.BookID as BookIssued
                 FROM UserRecord u
                 LEFT JOIN BookRecord b ON u.BookID = b.BookID
                 WHERE u.UserID LIKE ? OR u.UserName LIKE ?""", (q, q))
    rows = [dict(r) for r in c.fetchall()]; conn.close()
    return jsonify(rows)

# ── ADMIN APIs ────────────────────────────────────────────────────────────────
@app.route("/api/admins", methods=["GET"])
@admin_required
def get_admins():
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT AdminID, Password FROM AdminRecord ORDER BY AdminID")
    rows = [dict(r) for r in c.fetchall()]; conn.close()
    return jsonify(rows)

@app.route("/api/admins", methods=["POST"])
@admin_required
def add_admin():
    d = request.json
    aid = d.get("adminID","").strip()
    pwd = d.get("password","").strip()
    if not aid or not pwd:
        return jsonify({"success": False, "error": "All fields required"}), 400
    conn = get_db(); c = conn.cursor()
    try:
        c.execute("INSERT INTO AdminRecord VALUES (?,?)", (aid, pwd))
        conn.commit()
        return jsonify({"success": True, "message": f"Admin '{aid}' added!"})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "error": "AdminID already exists"}), 400
    finally:
        conn.close()

@app.route("/api/admins/<aid>", methods=["PUT"])
@admin_required
def update_admin(aid):
    d = request.json
    conn = get_db(); c = conn.cursor()
    c.execute("UPDATE AdminRecord SET Password=? WHERE AdminID=?", (d.get("password"), aid))
    conn.commit(); conn.close()
    return jsonify({"success": True, "message": "Admin updated!"})

@app.route("/api/admins/<aid>", methods=["DELETE"])
@admin_required
def delete_admin(aid):
    if aid == session.get("user_id"):
        return jsonify({"success": False, "error": "Cannot delete your own account!"}), 400
    conn = get_db(); c = conn.cursor()
    c.execute("DELETE FROM AdminRecord WHERE AdminID=?", (aid,))
    conn.commit(); conn.close()
    return jsonify({"success": True, "message": "Admin deleted!"})

# ── BOOK ISSUE / RETURN (User) ────────────────────────────────────────────────
@app.route("/api/issue", methods=["POST"])
@user_required
def issue_book():
    d    = request.json
    uid  = d.get("userID","").strip()
    bid  = d.get("bookID","").strip()
    conn = get_db(); c = conn.cursor()

    # Check user already has a book
    c.execute("SELECT BookID FROM UserRecord WHERE UserID=?", (uid,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({"success": False, "error": "User not found"}), 404
    if row["BookID"]:
        conn.close()
        return jsonify({"success": False, "error": "You already have a book issued. Return it first!"}), 400

    # Check book is available
    c.execute("SELECT BookID FROM UserRecord WHERE BookID=?", (bid,))
    if c.fetchone():
        conn.close()
        return jsonify({"success": False, "error": "This book is already issued to someone else!"}), 400

    c.execute("UPDATE UserRecord SET BookID=? WHERE UserID=?", (bid, uid))
    conn.commit()

    c.execute("SELECT BookName FROM BookRecord WHERE BookID=?", (bid,))
    brow = c.fetchone(); conn.close()
    bname = brow["BookName"] if brow else bid
    return jsonify({"success": True, "message": f"'{bname}' issued successfully!"})

@app.route("/api/return", methods=["POST"])
@user_required
def return_book():
    d    = request.json
    uid  = d.get("userID","").strip()
    bid  = d.get("bookID","").strip()
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT BookID FROM UserRecord WHERE UserID=? AND BookID=?", (uid, bid))
    if not c.fetchone():
        conn.close()
        return jsonify({"success": False, "error": "This book is not issued to this user"}), 400
    c.execute("UPDATE UserRecord SET BookID=NULL WHERE UserID=? AND BookID=?", (uid, bid))
    conn.commit(); conn.close()
    return jsonify({"success": True, "message": "Book returned successfully!"})

@app.route("/api/mybook/<uid>")
@user_required
def my_book(uid):
    conn = get_db(); c = conn.cursor()
    c.execute("""SELECT u.UserID, u.UserName, b.BookID, b.BookName, b.Author
                 FROM UserRecord u
                 INNER JOIN BookRecord b ON u.BookID = b.BookID
                 WHERE u.UserID=?""", (uid,))
    row = c.fetchone(); conn.close()
    if row:
        return jsonify({"has_book": True, "book": dict(row)})
    return jsonify({"has_book": False})

# ── FEEDBACK APIs ─────────────────────────────────────────────────────────────
@app.route("/api/feedback", methods=["GET"])
@admin_required
def get_feedback():
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT * FROM Feedback ORDER BY submitted_at DESC")
    rows = [dict(r) for r in c.fetchall()]; conn.close()
    return jsonify(rows)

@app.route("/api/feedback", methods=["POST"])
@user_required
def add_feedback():
    d    = request.json
    text = d.get("feedback","").strip()
    rate = d.get("rating")
    if not text or not rate:
        return jsonify({"success": False, "error": "Feedback and Rating required"}), 400
    try:
        rating = int(rate)
        if not 1 <= rating <= 10:
            raise ValueError
    except ValueError:
        return jsonify({"success": False, "error": "Rating must be 1–10"}), 400
    conn = get_db(); c = conn.cursor()
    c.execute("INSERT INTO Feedback (FeedbackText, Rating, submitted_at) VALUES (?,?,?)",
              (text, rating, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit(); conn.close()
    return jsonify({"success": True, "message": "Thank you for your feedback! 🙏"})

# ── DASHBOARD STATS ───────────────────────────────────────────────────────────
@app.route("/api/stats")
@user_required
def get_stats():
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT COUNT(*) as n FROM BookRecord"); total_books = c.fetchone()["n"]
    c.execute("SELECT COUNT(*) as n FROM UserRecord WHERE BookID IS NOT NULL"); issued = c.fetchone()["n"]
    c.execute("SELECT COUNT(*) as n FROM UserRecord"); total_users = c.fetchone()["n"]
    c.execute("SELECT COUNT(*) as n FROM AdminRecord"); total_admins = c.fetchone()["n"]
    c.execute("SELECT COUNT(*) as n FROM Feedback"); total_feedback = c.fetchone()["n"]
    c.execute("SELECT AVG(Rating) as avg FROM Feedback"); avg_rating = c.fetchone()["avg"]
    conn.close()
    return jsonify({
        "total_books": total_books,
        "issued_books": issued,
        "available_books": total_books - issued,
        "total_users": total_users,
        "total_admins": total_admins,
        "total_feedback": total_feedback,
        "avg_rating": round(avg_rating, 1) if avg_rating else 0
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
