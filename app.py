from flask import Flask, render_template, request, redirect, url_for, abort, flash, session
import sqlite3
import smtplib
from email.mime.text import MIMEText
import time
import json
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = "YOUR_SECRET_KEY_HERE"

# ---- LOAD HASHED PASSWORD FROM config.json ----
with open("config.json") as f:
    config = json.load(f)


# ---- Email recipients for each profile ----
RECIPIENT_EMAILS = {
    "1": "cspahn21@outlook.com",
    "2": "cspahn21@outlook.com",
    "3": "cspahn21@outlook.com",
    "4": "cspahn21@outlook.com",
}

SENDER_EMAIL = "floor142589436@gmail.com"
SENDER_PASSWORD = "hfxl foyr gdmr qhxv"

# ---- Database ----
DB_FILE = "messages.db"


# --------------------------------------------------
# DATABASE SETUP
# --------------------------------------------------

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()


# ---- Store Message ----
def store_message(user_id, message):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO messages (user_id, message, timestamp) VALUES (?, ?, datetime('now'))",
              (user_id, message))
    conn.commit()
    conn.close()


# ---- Get Messages for a user ----
def get_messages(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT message, timestamp FROM messages WHERE user_id=? ORDER BY id ASC",
              (user_id,))
    results = c.fetchall()
    conn.close()
    return results


# ---- Send Email ----
def send_email_message(user_id, message_text):
    recipient = RECIPIENT_EMAILS.get(user_id)
    if not recipient:
        return

    msg = MIMEText(message_text)
    msg["Subject"] = f"New website message for User {user_id}"
    msg["From"] = SENDER_EMAIL
    msg["To"] = recipient

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print("Email send failed:", e)


# --------------------------------------------------
# ROUTES
# --------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/profile/<id>", methods=["GET", "POST"])
def profile(id):
    if id not in ["1", "2", "3", "4"]:
        abort(404)

    if request.method == "POST":
        message = request.form.get("message")
        if message:
            store_message(id, message)
            send_email_message(id, message)
            flash("Your message was sent successfully!")
            return redirect(url_for("profile", id=id))

    return render_template(f"profile{id}.html", id=id)


# --------------------------------------------------
# PASSWORD-PROTECTED AREA (SESSION-BASED)
# --------------------------------------------------

@app.route("/protected", methods=["GET", "POST"])
def protected():
    error = None

    # Already logged in? Go to menu
    if session.get("authenticated"):
        return redirect(url_for("protected_menu"))

    if request.method == "POST":
        pw = request.form.get("password")

        # --- HASH CHECK HERE ---
        if check_password_hash(config["protected_password_hash"], pw):
            session["authenticated"] = True
            return redirect(url_for("protected_menu"))
        else:
            error = "Incorrect password"

    return render_template("protected.html", error=error)


@app.route("/protected/menu")
def protected_menu():
    if not session.get("authenticated"):
        return redirect(url_for("protected"))
    return render_template("protected_menu.html")


@app.route("/protected/user/<user_id>")
def protected_user(user_id):
    if not session.get("authenticated"):
        return redirect(url_for("protected"))

    msgs = get_messages(user_id)
    return render_template("protected_user.html",
                           user_id=user_id,
                           messages=msgs)


# --------------------------------------------------
# AUTO-LOGOUT WHEN LEAVING PROTECTED AREA
# --------------------------------------------------

@app.before_request
def auto_logout_when_leaving_protected():
    if session.get("authenticated"):
        protected_paths = ("/protected", "/protected/menu", "/protected/user/")
        if not request.path.startswith(protected_paths):
            session.pop("authenticated", None)


# ---- Prevent Browser Caching ----
@app.after_request
def no_cache(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


if __name__ == "__main__":
    app.run(debug=True)