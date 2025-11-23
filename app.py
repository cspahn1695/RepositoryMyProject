from flask import Flask, render_template, request, redirect, url_for
import secrets
import time

app = Flask(__name__)
app.secret_key = "YOUR_SECRET_KEY_HERE"  # Replace with a strong secret

# Simple passwords for each profile
PASSWORDS = {
    "1": "pass1",
    "2": "pass2",
    "3": "pass3",
    "4": "pass4"
}

# One-time tokens stored in memory: {token: (user_id, expiration_time)}
TOKENS = {}
TOKEN_EXPIRATION_SECONDS = 30  # Token valid for 30 seconds

# --- ROUTES ---

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/profile/<id>")
def profile(id):
    if id not in ["1", "2", "3", "4"]:
        return "Profile not found", 404
    return render_template(f"profile{id}.html", id=id)

@app.route("/protected/<id>", methods=["GET", "POST"])
def protected(id):
    error = None
    show_content = False

    # Clean up expired tokens
    now = time.time()
    expired_tokens = [t for t, (_, exp) in TOKENS.items() if exp < now]
    for t in expired_tokens:
        del TOKENS[t]

    if request.method == "POST":
        password = request.form.get("password")
        if password == PASSWORDS.get(id):
            # Generate a one-time token
            token = secrets.token_urlsafe(16)
            TOKENS[token] = (id, time.time() + TOKEN_EXPIRATION_SECONDS)
            # Redirect to GET with token
            return redirect(url_for("protected", id=id, token=token))
        else:
            error = "Incorrect password"

    # GET request with token
    token = request.args.get("token")
    if token and token in TOKENS:
        token_user, exp = TOKENS[token]
        if token_user == id:
            show_content = True
            # Immediately invalidate the token
            del TOKENS[token]

    return render_template("protected.html", id=id, error=error, show_content=show_content)

# --- NO-CACHE HEADERS ---
@app.after_request
def add_no_cache_headers(response):
    if request.path.startswith("/protected"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

if __name__ == "__main__":
    app.run(debug=True)