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

# --- Phone numbers / SMS gateway placeholders ---
# Format: "phone_number@carrier_sms_gateway"
# User1 fully implemented with T-Mobile; others are placeholders
PHONE_GATEWAYS = {
    "1": "6307796807@tmomail.net",  # Replace with real number
    "2": "user2_placeholder",       # Add later
    "3": "user3_placeholder",       # Add later
    "4": "user4_placeholder"        # Add later
}

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

# --- Helper to insert message ---
def store_message(user_id, message):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO messages (user_id, message, timestamp) VALUES (?, ?, datetime('now'))",
              (user_id, message))
    conn.commit()
    conn.close()

# --- Helper to retrieve messages for a user ---
def get_messages(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT message, timestamp FROM messages WHERE user_id=? ORDER BY id ASC", (user_id,))
    results = c.fetchall()
    conn.close()
    return results

# --- Helper to send SMS via email-to-SMS gateway ---
def send_sms_via_email(user_id, message_text):
    recipient = PHONE_GATEWAYS.get(user_id)
    if recipient is None or "placeholder" in recipient:
        # Skip sending if phone number not configured
        return

    # Configure email (you can use PythonAnywhere SMTP settings)
    # Replace with your actual sender email
    sender_email = "floor142589436@gmail.com"
    msg = MIMEText(message_text)
    msg['Subject'] = f"Message for User {user_id}"
    msg['From'] = sender_email
    msg['To'] = recipient

    try:
        # For PythonAnywhere, use their SMTP server
        with smtplib.SMTP("smtp.gmail.com", 587) as server:  # Or your SMTP host
            server.starttls()
            server.login("floor142589436@gmail.com", "hfxl foyr gdmr qhxv")
            server.send_message(msg)
    except Exception as e:
        print(f"Failed to send SMS/email: {e}")

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
            # Store in DB
            store_message(id, message)
            # Send SMS if phone configured
            send_sms_via_email(id, message)
            flash("Your message was sent successfully!")
            return redirect(url_for("profile", id=id))

    return render_template(f"profile{id}.html", id=id)

@app.route("/protected/<id>", methods=["GET", "POST"])
def protected(id):
    error = None
    show_content = False

    # Clean up expired tokens
    now = time.time()
    for t in list(TOKENS):
        _, exp = TOKENS[t]
        if exp < now:
            TOKENS.pop(t, None)

    if request.method == "POST":
        pw = request.form.get("password")
        if pw == PASSWORDS.get(id):
            # Generate token
            token = secrets.token_urlsafe(16)
            TOKENS[token] = (id, time.time() + 30)
            return redirect(url_for("protected_with_token", id=id, token=token))
        else:
            error = "Incorrect password"
        return render_template("protected.html", id=id, error=error, show_content=False, messages=[])

    # GET to /protected/<id> → show password form
    return render_template("protected.html", id=id, error=None, show_content=False, messages=[])

@app.route("/protected/<id>/<token>")
def protected_with_token(id, token):
    now = time.time()
    for t in list(TOKENS):
        _, exp = TOKENS[t]
        if exp < now:
            TOKENS.pop(t, None)

    data = TOKENS.pop(token, None)
    if not data or data[0] != id:
        return redirect(url_for("protected", id=id))

    # Fetch messages for this user
    messages = get_messages(id)
    return render_template("protected.html", id=id, error=None, show_content=True, messages=messages)

@app.after_request
def add_no_cache(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

if __name__ == "__main__":
    app.run(debug=True)