import json
import os
from src.backend.security.auth import get_password_hash

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USERS_FILE = os.path.join(BASE_DIR, "users.json")

def _load_users():
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def get_user_by_email(email: str):
    users = _load_users()
    for u in users:
        if u["email"] == email:
            return u
    return None

def get_all_users():
    return _load_users()

def create_user(email: str, full_name: str, role: str, password: str):
    users = _load_users()
    if any(u["email"] == email for u in users):
        return None

    scopes_map = {
        "admin": ["admin:all", "patients:read", "patients:write", "appointments:read", "appointments:write", "practitioners:read", "practitioners:write", "audit:read", "audit:delete"],
        "medico": ["patients:read", "appointments:read", "appointments:write", "practitioners:read"],
        "recepcionista": ["patients:read", "patients:write", "appointments:read", "appointments:write", "practitioners:read"],
    }

    new_user = {
        "email": email,
        "full_name": full_name,
        "role": role,
        "hashed_password": get_password_hash(password),
        "scopes": scopes_map.get(role, ["patients:read"]),
    }
    users.append(new_user)
    _save_users(users)
    return new_user

def delete_user(email: str):
    users = _load_users()
    filtered = [u for u in users if u["email"] != email]
    if len(filtered) == len(users):
        return False
    _save_users(filtered)
    return True

def reset_user_password(email: str) -> str | None:
    import secrets, string
    users = _load_users()
    for u in users:
        if u["email"] == email:
            new_password = ''.join(secrets.choice(string.ascii_letters + string.digits + '!@#$%') for _ in range(14))
            u["hashed_password"] = get_password_hash(new_password)
            _save_users(users)
            return new_password
    return None
