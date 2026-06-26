from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import struct
import time
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import quote

from fastapi import Request

from app.services.db_store import db

SESSION_COOKIE = "plantops_session"
SESSION_DAYS = 7
DEFAULT_DEMO_PASSWORD = "plantops"


class AuthService:
    def ensure_seed_user(self) -> None:
        if not db.user_exists("owner"):
            db.create_user(
                username="owner",
                display_name="John Owner",
                role="admin",
                password_hash=self.hash_password(DEFAULT_DEMO_PASSWORD),
            )
            db.audit("system", "auth.seed_user", "owner", {"role": "admin"})

    def hash_password(self, password: str, salt: str | None = None) -> str:
        salt = salt or secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
        return f"pbkdf2_sha256${salt}${digest.hex()}"

    def verify_password(self, password: str, stored_hash: str) -> bool:
        try:
            scheme, salt, expected = stored_hash.split("$", 2)
        except ValueError:
            return False
        if scheme != "pbkdf2_sha256":
            return False
        actual = self.hash_password(password, salt).split("$", 2)[2]
        return hmac.compare_digest(actual, expected)

    def authenticate(self, username: str, password: str, totp_code: str | None = None) -> tuple[bool, str, dict[str, Any] | None]:
        user = db.get_user(username)
        if not user or not self.verify_password(password, user["password_hash"]):
            return False, "Invalid username or password.", None
        if user.get("totp_enabled"):
            if not totp_code or not self.verify_totp(user.get("totp_secret") or "", totp_code):
                return False, "Valid TOTP code required.", None
        return True, "Login successful.", user

    def login(self, username: str) -> str:
        token = secrets.token_urlsafe(32)
        expires = datetime.now() + timedelta(days=SESSION_DAYS)
        db.create_session(token, username, expires.isoformat(timespec="seconds"))
        db.audit(username, "auth.login", username)
        return token

    def logout(self, request: Request) -> None:
        token = request.cookies.get(SESSION_COOKIE)
        user = self.get_user_from_request(request)
        if token:
            db.delete_session(token)
        db.audit(user.get("username", "anonymous"), "auth.logout", user.get("username", "anonymous"))

    def get_user_from_request(self, request: Request) -> dict[str, Any]:
        token = request.cookies.get(SESSION_COOKIE)
        if token:
            user = db.get_session_user(token)
            if user:
                return self.public_user(user)
        return {
            "username": "demo",
            "display_name": "Demo Operator",
            "role": "admin",
            "authenticated": False,
            "totp_enabled": False,
        }

    def public_user(self, user: dict[str, Any]) -> dict[str, Any]:
        return {
            "username": user.get("username"),
            "display_name": user.get("display_name"),
            "role": user.get("role"),
            "authenticated": True,
            "totp_enabled": bool(user.get("totp_enabled")),
        }

    def audit_name(self, request: Request) -> str:
        return self.get_user_from_request(request).get("username", "demo")

    def generate_totp_secret(self) -> str:
        return base64.b32encode(os.urandom(20)).decode("utf-8").replace("=", "")

    def totp_uri(self, username: str, secret: str, issuer: str = "PlantOps") -> str:
        return f"otpauth://totp/{quote(issuer)}:{quote(username)}?secret={secret}&issuer={quote(issuer)}&digits=6&period=30"

    def verify_totp(self, secret: str, code: str, window: int = 1) -> bool:
        code = "".join(ch for ch in str(code) if ch.isdigit())
        if len(code) != 6 or not secret:
            return False
        now_counter = int(time.time() // 30)
        for offset in range(-window, window + 1):
            if hmac.compare_digest(self._totp_at(secret, now_counter + offset), code):
                return True
        return False

    def _totp_at(self, secret: str, counter: int) -> str:
        padded = secret + "=" * ((8 - len(secret) % 8) % 8)
        key = base64.b32decode(padded, casefold=True)
        msg = struct.pack(">Q", counter)
        digest = hmac.new(key, msg, hashlib.sha1).digest()
        offset = digest[-1] & 0x0F
        value = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
        return f"{value % 1_000_000:06d}"


auth_service = AuthService()
