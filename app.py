from flask import Flask, render_template, request, redirect, url_for, abort, flash
import secrets
import time
import sqlite3
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = "YOUR_SECRET_KEY_HERE"

# ---- ONE PASSWORD ONLY ----
PROTECTED_PASSWORD = "YOUR_SINGLE_PASSWORD"

# ---- Token Management ----
TOKENS = {}
TOKEN_EXPIRATION_SECONDS = 30

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


# ---- SINGLE PROTECTED PAGE ----
@app.route("/protected", methods=["GET", "POST"])
def protected():
    error = None

    # Clean expired tokens
    now = time.time()
    for t in list(TOKENS):
        _, exp = TOKENS[t]
        if exp < now:
            TOKENS.pop(t, None)

    if request.method == "POST":
        pw = request.form.get("password")
        if pw == PROTECTED_PASSWORD:
            token = secrets.token_urlsafe(16)
            TOKENS[token] = ("ALL", time.time() + TOKEN_EXPIRATION_SECONDS)
            return redirect(url_for("protected_with_token", token=token))
        else:
            error = "Incorrect password"

    return render_template("protected.html", error=error, show_content=False, grouped_messages={})


@app.route("/protected/<token>")
def protected_with_token(token):
    now = time.time()

    # Clean expired tokens
    for t in list(TOKENS):
        _, exp = TOKENS[t]
        if exp < now:
            TOKENS.pop(t, None)

    data = TOKENS.pop(token, None)
    if not data or data[0] != "ALL":
        return redirect(url_for("protected"))

    grouped_messages = {
        "1": get_messages("1"),
        "2": get_messages("2"),
        "3": get_messages("3"),
        "4": get_messages("4"),
    }

    return render_template("protected.html",
                           error=None,
                           show_content=True,
                           grouped_messages=grouped_messages)


# ---- Prevent Browser Caching (IMPORTANT) ----
@app.after_request
def no_cache(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


if __name__ == "__main__":
    app.run(debug=True)