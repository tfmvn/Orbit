"""Simple entry point demonstrating token.py usage."""

from __future__ import annotations

from token import (
    TokenError,
    create_token,
    list_active_tokens,
    refresh_token,
    revoke_token,
    verify_token,
)


def main() -> None:
    secret = "dev-secret-please-change"
    payload = {"sub": "user:42", "role": "tester"}

    print("Creating token...")
    token = create_token(payload, secret, expire_seconds=30)
    print(token)

    print("\nVerifying token...")
    try:
        claims = verify_token(token, secret)
        print(claims)
    except TokenError as exc:
        print(f"Verification failed: {exc}")
        return

    print("\nRefreshing token...")
    refreshed_token = refresh_token(token, secret, expire_seconds=60)
    print(refreshed_token)

    print("\nRevoking original token...")
    revoked = revoke_token(token)
    print(f"revoked={revoked}")

    print("\nChecking active tokens...")
    print(list_active_tokens())


if __name__ == "__main__":
    main()
