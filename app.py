
#All code in this file was developed using the help of ChatGPT

from flask import Flask, render_template, request, redirect, url_for, abort, flash, session
import sqlite3
import smtplib
from email.mime.text import MIMEText
app = Flask(__name__)
app.secret_key = "YOUR_SECRET_KEY_HERE"
# ---- ONE PASSWORD ONLY ----
PROTECTED_PASSWORD = "Fall2025Lab3" # the mechanism to change the pw offline is just changing this variable
# ---- Email recipients for each profile ----
RECIPIENT_EMAILS = { # not needed
    "1": "cspahn21@outlook.com",
    "2": "cspahn21@outlook.com",
    "3": "cspahn21@outlook.com",
    "4": "cspahn21@outlook.com",
}
SENDER_EMAIL = "floor142589436@gmail.com" # everything related to sending emails isn't needed since this website doesn't actually have to send emails or text messages
SENDER_PASSWORD = "hfxl foyr gdmr qhxv"
# ---- Database ----
DB_FILE = "messages.db"

# --------------------------------------------------
# DATABASE SETUP
# --------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)  # initializes database (that messages will get sent to)
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
def store_message(user_id, message): # store a message in the above database (DB_FILE) along with the correct profile (user ID) and time
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO messages (user_id, message, timestamp) VALUES (?, ?, datetime('now'))",
        (user_id, message)
    )
    conn.commit()
    conn.close()

# ---- Get Messages for a user ----
def get_messages(user_id):
    conn = sqlite3.connect(DB_FILE) # retrieve all messages for a given user ID from the database (with timestamps)
    c = conn.cursor()
    c.execute(
        "SELECT message, timestamp FROM messages WHERE user_id=? ORDER BY id ASC",
        (user_id,)
    )
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
# PASSWORD-PROTECTED AREA
# --------------------------------------------------
@app.route("/protected", methods=["GET", "POST"]) #main password protected route
def protected():
    error = None
    # Already logged in?
    if session.get("authenticated"): # if already authenticated, go to protected menu
        return redirect(url_for("protected_menu"))
    if request.method == "POST": #check password
        pw = request.form.get("password")
        if pw == PROTECTED_PASSWORD: #if correct, set session variable and go to protected menu
            session["authenticated"] = True
            return redirect(url_for("protected_menu"))
        else:
            error = "Incorrect password" # otherwise go back to screen where you enter pw
    return render_template("protected.html", error=error)

@app.route("/protected/menu") #protected menu route
def protected_menu():
    if not session.get("authenticated"): # ir not authenticated, go back to pw entry screen
        return redirect(url_for("protected"))
    return render_template("protected_menu.html")

@app.route("/protected/user/<user_id>") #route to seee messages for a given user id
def protected_user(user_id):
    if not session.get("authenticated"):# if not authenticated, go back to pw entry screen
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
    # These paths DO NOT log the user out
    allowed_paths = [ #list of all paths that don't log the user out
        "/protected",
        "/protected/",
        "/protected/menu",
        "/protected/user/",
    ]
    if session.get("authenticated"): #if authenticated, check if the current path is allowed
        path = request.path
        # Allow only the protected paths or their subpaths
        if not any(path.startswith(p) for p in allowed_paths): #if not allowed, log the user out
            session.pop("authenticated", None)

# ---- Prevent Browser Caching ----
@app.after_request
def no_cache(response): #prevent caching for all routes to increase security
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

if __name__ == "__main__":
    app.run(debug=True)
