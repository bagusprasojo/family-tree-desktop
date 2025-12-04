from __future__ import annotations

import hashlib
import os
import secrets


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return salt.hex() + ":" + hashed.hex()


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, hash_hex = stored.split(":")
    except ValueError:
        return False
    salt = bytes.fromhex(salt_hex)
    new_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return secrets.compare_digest(hash_hex, new_hash.hex())

