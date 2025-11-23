from flask import Flask, render_template, request, redirect, url_for, abort, flash
import secrets
import time
import sqlite3
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = "YOUR_SECRET_KEY_HERE"

# --- Passwords for protected pages ---
PASSWORDS = {
    "1": "pass1",
    "2": "pass2",
    "3": "pass3",
    "4": "pass4"
}

# --- Token management ---
TOKENS = {}
TOKEN_EXPIRATION_SECONDS = 30

# --- Email recipients for each profile ---
RECIPIENT_EMAILS = {
    "1": "user1@example.com",
    "2": "user2@example.com",
    "3": "user3@example.com",
    "4": "user4@example.com"
}

SENDER_EMAIL = "YOUR_EMAIL@gmail.com"
SENDER_PASSWORD = "YOUR_APP_PASSWORD"

# --- SQLite database ---
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

# --- Store message in DB ---
def store_message(user_id, message):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO messages (user_id, message, timestamp) VALUES (?, ?, datetime('now'))",
              (user_id, message))
    conn.commit()
    conn.close()

# --- Retrieve messages for protected page ---
def get_messages(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT message, timestamp FROM messages WHERE user_id=? ORDER BY id ASC", (user_id,))
    results = c.fetchall()
    conn.close()
    return results

# --- Send email ---
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

# --- ROUTES ---

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/profile/<id>", methods=["GET", "POST"])
def profile(id):
    if id not in PASSWORDS:
        abort(404)

    if request.method == "POST":
        message = request.form.get("message")
        if message:
            store_message(id, message)
            send_email_message(id, message)
            flash("Your message was sent!")
            return redirect(url_for("profile", id=id))

    return render_template(f"profile{id}.html", id=id)


@app.route("/protected/<id>", methods=["GET", "POST"])
def protected(id):
    error = None

    # Clean expired tokens
    now = time.time()
    for t in list(TOKENS):
        _, exp = TOKENS[t]
        if exp < now:
            TOKENS.pop(t, None)

    # Handle form submit
    if request.method == "POST":
        pw = request.form.get("password")
        if pw == PASSWORDS.get(id):
            token = secrets.token_urlsafe(16)
            TOKENS[token] = (id, time.time() + TOKEN_EXPIRATION_SECONDS)
            return redirect(url_for("protected_with_token", id=id, token=token))
        else:
            error = "Incorrect password"
            return render_template("protected.html", id=id, error=error, show_content=False, messages=[])

    # GET always shows password form
    return render_template("protected.html", id=id, error=None, show_content=False, messages=[])


@app.route("/protected/<id>/<token>")
def protected_with_token(id, token):
    now = time.time()

    # Clean expired tokens
    for t in list(TOKENS):
        _, exp = TOKENS[t]
        if exp < now:
            TOKENS.pop(t, None)

    # --- IMPORTANT: pop token immediately (prevents forward button access) ---
    data = TOKENS.pop(token, None)

    # Invalid or missing token
    if not data:
        return redirect(url_for("protected", id=id))

    token_user, _ = data

    # Token user mismatch
    if token_user != id:
        return redirect(url_for("protected", id=id))

    # Token valid → show protected content
    messages = get_messages(id)
    return render_template("protected.html", id=id, error=None, show_content=True, messages=messages)


@app.after_request
def no_cache(response):
    # Strong BFCache / caching prevention
    response.headers["Cache-Control"] = (
        "no-store, no-cache, must-revalidate, max-age=0, private, no-transform"
    )
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["Vary"] = "*"
    return response


if __name__ == "__main__":
    app.run(debug=True)