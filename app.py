from flask import Flask, render_template, request, redirect, url_for, make_response, session, flash

app = Flask(__name__)
app.secret_key = "YOUR_SECRET_KEY_HERE"   # Change this!

# Simple passwords for each profile (you can replace with a database later)
PASSWORDS = {
    "1": "pass1",
    "2": "pass2",
    "3": "pass3",
    "4": "pass4"
}

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
    authorized = False
    error = None

    # If POST, check password
    if request.method == "POST":
        password = request.form.get("password")
        if password == PASSWORDS.get(id):
            # Redirect to GET with a temporary query param
            return redirect(url_for("protected", id=id, authorized="1"))
        else:
            error = "Incorrect password"

    # GET request
    if request.method == "GET" and request.args.get("authorized") == "1":
        authorized = True

    return render_template("protected.html", id=id, authorized=authorized, error=error)

@app.after_request
def add_no_cache_headers(response):
    if request.path.startswith("/protected"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response