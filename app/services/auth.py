from __future__ import annotations
import base64
import hashlib
import hmac
import secrets
from threading import BoundedSemaphore

SCRYPT_N = 1 << 15
SCRYPT_R = 8
SCRYPT_P = 1
_HASH_SLOTS = BoundedSemaphore(2)


def digest_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    with _HASH_SLOTS:
        key = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, dklen=32, maxmem=64 * 1024 * 1024)
    b64 = lambda value: base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${b64(salt)}${b64(key)}"

def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, n, r, p, salt_text, hash_text = encoded.split("$")
        if scheme != "scrypt":
            return False
        decode = lambda value: base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
        salt, expected = decode(salt_text), decode(hash_text)
        with _HASH_SLOTS:
            actual = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=int(n), r=int(r), p=int(p), dklen=len(expected), maxmem=64 * 1024 * 1024)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, MemoryError):
        return False

def new_session_token() -> str:
    return secrets.token_urlsafe(32)

def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)
