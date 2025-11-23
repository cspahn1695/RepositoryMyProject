from flask import Flask, render_template, request, redirect, url_for, session

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
    if request.method == "POST":
        password = request.form.get("password")
        if password == PASSWORDS.get(id):
            session[f"auth_{id}"] = True
            return render_template("protected.html", id=id)
        else:
            return render_template("protected.html", id=id, error="Incorrect password")

    # If user already logged in
    if session.get(f"auth_{id}"):
        return render_template("protected.html", id=id)

    return render_template("protected.html", id=id)