from flask import Flask, render_template, request, redirect, url_for, abort
import secrets
import time

app = Flask(__name__)
app.secret_key = "YOUR_SECRET_KEY_HERE"

PASSWORDS = {
    "1": "pass1",
    "2": "pass2",
    "3": "pass3",
    "4": "pass4"
}

TOKENS = {}
TOKEN_EXPIRATION_SECONDS = 30


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/profile/<id>")
def profile(id):
    if id not in PASSWORDS:
        abort(404)
    return render_template(f"profile{id}.html", id=id)


@app.route("/protected/<id>", methods=["GET", "POST"])
def protected(id):
    error = None
    show_content = False

    # Clean expired tokens
    now = time.time()
    for t in list(TOKENS):
        _, exp = TOKENS[t]
        if exp < now:
            TOKENS.pop(t, None)

    if request.method == "POST":
        pw = request.form.get("password")
        if pw == PASSWORDS.get(id):
            token = secrets.token_urlsafe(16)
            TOKENS[token] = (id, time.time() + TOKEN_EXPIRATION_SECONDS)
            return redirect(url_for("protected_with_token", id=id, token=token))
        else:
            error = "Incorrect password"
        return render_template("protected.html", id=id, error=error, show_content=False)

    # GET always shows form
    return render_template("protected.html", id=id, error=error, show_content=False)


@app.route("/protected/<id>/<token>")
def protected_with_token(id, token):
    now = time.time()
    for t in list(TOKENS):
        _, exp = TOKENS[t]
        if exp < now:
            TOKENS.pop(t, None)

    data = TOKENS.pop(token, None)
    if not data:
        return redirect(url_for("protected", id=id))
    token_user, _ = data
    if token_user != id:
        return redirect(url_for("protected", id=id))

    return render_template("protected.html", id=id, error=None, show_content=True)


@app.after_request
def add_no_cache_headers(response):
    # Hardcore BFCache prevention
    response.headers["Cache-Control"] = (
        "no-store, no-cache, must-revalidate, max-age=0, private, no-transform"
    )
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["Vary"] = "*"
    return response


if __name__ == "__main__":
    app.run(debug=True)