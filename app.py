from flask import Flask, render_template, request

app = Flask(__name__)
app.secret_key = "YOUR_SECRET_KEY_HERE"  # Replace with a strong secret

# Passwords for each profile
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
    error = None
    show_content = False

    # Only show protected content immediately after correct POST
    if request.method == "POST":
        password = request.form.get("password")
        if password == PASSWORDS.get(id):
            show_content = True
        else:
            error = "Incorrect password"

    return render_template("protected.html", id=id, error=error, show_content=show_content)

# --- NO-CACHE HEADERS ---
@app.after_request
def add_no_cache_headers(response):
    # Apply to all protected pages
    if request.path.startswith("/protected"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

if __name__ == "__main__":
    app.run(debug=True)