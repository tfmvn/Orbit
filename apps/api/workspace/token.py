"""
Simple token utilities for testing and local development.

This module implements a minimal JWT-like token generator and verifier
using HMAC-SHA256 and base64url encoding. It includes an in-memory
token store to support revocation and refreshing for test/demo use.

Intended for hooking into main.py during development/testing only.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import threading
from typing import Dict, Optional, Any

_STORE_LOCK = threading.Lock()
_IN_MEMORY_STORE: Dict[str, Dict[str, Any]] = {}


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def _sign(message: bytes, secret: bytes) -> str:
    sig = hmac.new(secret, message, hashlib.sha256).digest()
    return _b64url_encode(sig)


def create_token(payload: Dict[str, Any], secret: str, expire_seconds: int = 3600) -> str:
    """Create a compact JWT-like token.

    payload: dictionary payload. A copy will be extended with 'exp' epoch.
    secret: shared secret string.
    expire_seconds: TTL in seconds.
    """
    header = {"alg": "HS256", "typ": "JWT"}
    body = dict(payload)
    body.setdefault("iat", int(time.time()))
    body["exp"] = int(time.time()) + int(expire_seconds)

    header_b = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    body_b = _b64url_encode(json.dumps(body, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b}.{body_b}".encode("ascii")
    signature = _sign(signing_input, secret.encode("utf-8"))
    token = f"{header_b}.{body_b}.{signature}"

    # store metadata for testing (allows revocation/refresh)
    with _STORE_LOCK:
        _IN_MEMORY_STORE[token] = {"payload": body, "revoked": False}

    return token


class TokenError(Exception):
    pass


def verify_token(token: str, secret: str, allow_expired: bool = False) -> Dict[str, Any]:
    """Verify token signature and expiration. Return payload if valid.

    Raises TokenError on failure.
    """
    try:
        header_b, body_b, signature = token.split(".")
    except ValueError:
        raise TokenError("invalid_token_format")

    signing_input = f"{header_b}.{body_b}".encode("ascii")
    expected_sig = _sign(signing_input, secret.encode("utf-8"))
    if not hmac.compare_digest(expected_sig, signature):
        raise TokenError("invalid_signature")

    try:
        body_raw = _b64url_decode(body_b)
        payload = json.loads(body_raw.decode("utf-8"))
    except Exception:
        raise TokenError("invalid_payload")

    if not allow_expired:
        exp = payload.get("exp")
        if exp is None:
            raise TokenError("no_expiration")
        if int(time.time()) > int(exp):
            raise TokenError("token_expired")

    with _STORE_LOCK:
        meta = _IN_MEMORY_STORE.get(token)
        if meta and meta.get("revoked"):
            raise TokenError("token_revoked")

    return payload


def revoke_token(token: str) -> bool:
    """Mark a token as revoked in the in-memory store. Returns True if found."""
    with _STORE_LOCK:
        meta = _IN_MEMORY_STORE.get(token)
        if not meta:
            return False
        meta["revoked"] = True
        return True


def refresh_token(token: str, secret: str, expire_seconds: int = 3600) -> str:
    """Refresh a valid token by creating a new token with same payload and new exp.

    Revokes the old token in the store. Raises TokenError if original invalid.
    """
    payload = verify_token(token, secret)
    # remove issued-at and exp so new token recalculates them
    payload.pop("iat", None)
    payload.pop("exp", None)

    new_token = create_token(payload, secret, expire_seconds=expire_seconds)
    revoke_token(token)
    return new_token


def list_active_tokens() -> Dict[str, Dict[str, Any]]:
    """Return a shallow copy of current in-memory store (for tests)."""
    with _STORE_LOCK:
        return dict(_IN_MEMORY_STORE)


if __name__ == "__main__":
    # Demo / quick test when invoked directly. This mimics hooking into main.py
    SECRET = "dev-secret-please-change"
    user_payload = {"sub": "user:42", "role": "tester"}
    token = create_token(user_payload, SECRET, expire_seconds=30)
    print("Generated token:\n", token)
    print("Verifying...")
    try:
        claims = verify_token(token, SECRET)
        print("Valid claims:", claims)
    except TokenError as e:
        print("Verification failed:", e)

    print("Refreshing token...")
    new_token = refresh_token(token, SECRET, expire_seconds=60)
    print("New token:\n", new_token)
    print("Old token revoked:", list_active_tokens()[token]["revoked"])
