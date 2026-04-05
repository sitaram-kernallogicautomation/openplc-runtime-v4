#!/usr/bin/env python3
"""
Issue a signed Windows runtime license (RS256 JWT).

Usage (from repository root, with dependencies installed):
  ./venvs/runtime/bin/python3 scripts/issue_windows_license.py \\
      --private-key vendor_private.pem \\
      --fingerprint <64-char hex from print_windows_fingerprint.py> \\
      [--customer-id ID] [--days 365] [--output openplc.license]

The customer runs print_windows_fingerprint.py on the target PC and sends the
fingerprint; you sign it with your offline private key and return openplc.license.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt


def main() -> int:
    parser = argparse.ArgumentParser(description="Issue OpenPLC Windows runtime license JWT")
    parser.add_argument("--private-key", required=True, type=Path, help="Path to RSA private PEM")
    parser.add_argument("--fingerprint", required=True, help="SHA-256 hex from target machine")
    parser.add_argument("--customer-id", default="", help="Optional 'sub' claim")
    parser.add_argument(
        "--days",
        type=int,
        default=0,
        help="If > 0, add JWT exp claim (UTC) this many days from now",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write license to this file instead of stdout",
    )
    args = parser.parse_args()

    fp = args.fingerprint.strip().lower()
    if len(fp) != 64 or any(c not in "0123456789abcdef" for c in fp):
        print("Error: fingerprint must be 64 hex characters (sha256).", file=sys.stderr)
        return 1

    try:
        priv_pem = args.private_key.read_text(encoding="utf-8")
    except OSError as e:
        print(f"Error reading private key: {e}", file=sys.stderr)
        return 1

    claims: dict = {"fp": fp}
    if args.customer_id:
        claims["sub"] = str(args.customer_id)

    token_kwargs: dict = {"algorithm": "RS256"}
    if args.days > 0:
        exp = datetime.now(timezone.utc) + timedelta(days=args.days)
        claims["exp"] = exp

    try:
        token = jwt.encode(claims, priv_pem, **token_kwargs)
    except Exception as e:
        print(f"Error signing license: {e}", file=sys.stderr)
        return 1

    if isinstance(token, bytes):
        token_str = token.decode("ascii")
    else:
        token_str = token

    if args.output:
        args.output.write_text(token_str + "\n", encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(token_str)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
