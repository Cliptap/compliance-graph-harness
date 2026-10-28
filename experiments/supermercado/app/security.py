"""Password, RUT and masking helpers for the target system."""
from __future__ import annotations

import hashlib
import hmac
import re
import secrets

RUT_RE = re.compile(r"^\s*(\d{1,2}\.?\d{3}\.?\d{3})-?([\dkK])\s*$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PBKDF2_ROUNDS = 120_000


def normalize_rut(raw: str | None) -> str:
    """Return the canonical RUT (digits plus verifier) or an empty string."""
    if not raw:
        return ""
    match = RUT_RE.match(str(raw))
    if not match:
        return ""
    body = re.sub(r"\D", "", match.group(1))
    return f"{body}{match.group(2).upper()}"


def is_valid_rut(raw: str | None) -> bool:
    rut = normalize_rut(raw)
    if len(rut) < 2:
        return False
    body, verifier = rut[:-1], rut[-1]
    if not body.isdigit():
        return False
    total, factor = 0, 2
    for digit in reversed(body):
        total += int(digit) * factor
        factor = 2 if factor == 7 else factor + 1
    remainder = 11 - (total % 11)
    expected = "0" if remainder == 11 else "K" if remainder == 10 else str(remainder)
    return hmac.compare_digest(expected, verifier)


def mask_rut(raw: str | None) -> str:
    rut = normalize_rut(raw)
    if len(rut) < 3:
        return ""
    return f"{rut[:2]}.***.***-{rut[-1]}"


def is_valid_email(raw: str | None) -> bool:
    return bool(raw and EMAIL_RE.match(raw.strip()))


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("ascii"), PBKDF2_ROUNDS)
    return f"pbkdf2${PBKDF2_ROUNDS}${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, rounds, salt, digest = stored.split("$", 3)
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("ascii"), int(rounds))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(candidate.hex(), digest)
