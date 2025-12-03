import json
import secrets
import string

def generate_password(length=12):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

new_password = generate_password()

# Load config
with open("config.json", "r") as f:
    data = json.load(f)

# Replace password
data["protected_password"] = new_password

# Save new config
with open("config.json", "w") as f:
    json.dump(data, f, indent=4)

print("New password generated:", new_password)
print("Upload the updated config.json to your server.")