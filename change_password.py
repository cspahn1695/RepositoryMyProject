import json
import secrets
import string
import sys
print("Running with:", sys.executable)
from werkzeug.security import generate_password_hash



def generate_password(length=12):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


new_password = generate_password()
hashed = generate_password_hash(new_password)

with open("config.json", "r") as f:
    data = json.load(f)

data["protected_password_hash"] = hashed

with open("config.json", "w") as f:
    json.dump(data, f, indent=4)

print("New password generated:", new_password)
print("Upload config.json to the server.")