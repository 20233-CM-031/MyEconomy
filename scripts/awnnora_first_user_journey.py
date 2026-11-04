#!/usr/bin/env python3
"""Exercise AwnNORA's local synthetic first-user flow through real application services."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]


def request_json(base: str, path: str, *, method: str = "GET", payload=None, token=None):
    headers = {"Accept": "application/json"}
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(base.rstrip("/") + path, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=25) as response:
            raw = response.read()
            return json.loads(raw) if raw else None
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path}: HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Cannot reach local AwnNORA API at {base}: {exc.reason}") from exc


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--email", required=True, help="Dedicated local email ending in @example.invalid"
    )
    parser.add_argument("--customer-id", default="CUS00001")
    parser.add_argument(
        "--base-url", default=os.getenv("AWNNORA_DEMO_BASE_URL", "http://127.0.0.1:8000")
    )
    parser.add_argument(
        "--register",
        action="store_true",
        help="Register account, then paste the verification token from the development mail log",
    )
    parser.add_argument("--display-name", default="AwnNORA Demo User")
    parser.add_argument("--period-start", type=date.fromisoformat, default=date(2026, 10, 1))
    parser.add_argument("--period-end", type=date.fromisoformat, default=date(2026, 10, 31))
    parser.add_argument("--as-of", type=date.fromisoformat, default=date(2026, 11, 4))
    parser.add_argument("--skip-seed", action="store_true")
    parser.add_argument(
        "--include-guardian-manual-demo",
        action="store_true",
        help="Optional manual-field Guardian fixture; it is not OCR and sends nothing",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("demo_output/first_user"))
    args = parser.parse_args()

    if os.getenv("APP_ENV", "development").strip().lower() not in {"development", "test", "demo"}:
        raise SystemExit("Synthetic journey is disabled outside development/test/demo.")
    parsed_base = urlparse(args.base_url)
    if parsed_base.scheme != "http" or parsed_base.hostname not in {
        "localhost",
        "127.0.0.1",
        "::1",
    }:
        raise SystemExit(
            "Synthetic first-user automation is restricted to a local loopback API URL."
        )
    if not args.email.strip().lower().endswith("@example.invalid"):
        raise SystemExit(
            "Use a dedicated non-deliverable local demo email ending in @example.invalid."
        )
    if args.period_end < args.period_start or args.period_end > args.as_of:
        raise SystemExit("Require period_start <= period_end <= as_of.")

    password = os.getenv("AWNNORA_LOCAL_DEMO_PASSWORD") or getpass.getpass(
        "Local demo password (not saved): "
    )
    if len(password) < 12:
        raise SystemExit("Password must be at least 12 characters.")

    if args.register:
        request_json(
            args.base_url,
            "/api/v1/auth/register",
            method="POST",
            payload={
                "email": args.email,
                "password": password,
                "display_name": args.display_name,
            },
        )
        print(
            "Account created. The local API development log contains the one-time "
            "verification token."
        )
        verification_token = input("Paste that verification token: ").strip()
        request_json(
            args.base_url,
            "/api/v1/auth/verify-email",
            method="POST",
            payload={"token": verification_token},
        )

    login = request_json(
        args.base_url,
        "/api/v1/auth/login",
        method="POST",
        payload={
            "email": args.email,
            "password": password,
        },
    )
    token = login["access_token"]
    me = request_json(args.base_url, "/api/v1/auth/me", token=token)
    if not me.get("email_verified"):
        raise SystemExit("The account must be email-verified before continuing.")

    seed_status = "SKIPPED"
    if not args.skip_seed:
        env = os.environ.copy()
        env["APP_ENV"] = "demo"
        command = [
            sys.executable,
            str(ROOT / "scripts/seed_synthetic_customer.py"),
            "--user-email",
            args.email,
            "--customer-id",
            args.customer_id,
            "--dataset-dir",
            str(ROOT / "demo_data/synthetic_v1"),
        ]
        completed = subprocess.run(command, cwd=ROOT, env=env, check=False)
        if completed.returncode:
            raise SystemExit(f"Synthetic persona seeding failed (exit {completed.returncode}).")
        seed_status = "COMPLETED_OR_IDEMPOTENT_REPLAY"

    accounts = request_json(args.base_url, "/api/v1/financial/accounts", token=token)
    obligations = request_json(args.base_url, "/api/v1/financial/obligations", token=token)
    query = urlencode(
        {
            "period_start": args.period_start.isoformat(),
            "period_end": args.period_end.isoformat(),
            "currency": "INR",
            "as_of": args.as_of.isoformat(),
            "obligation_horizon_days": 30,
        }
    )
    report = request_json(args.base_url, f"/api/v1/personal/power-report?{query}", token=token)

    guardian_status = "NOT_RUN"
    if args.include_guardian_manual_demo:
        env = os.environ.copy()
        env.update(
            {
                "APP_ENV": "demo",
                "AWNNORA_DEMO_BASE_URL": args.base_url,
                "AWNNORA_DEMO_BEARER_TOKEN": token,
            }
        )
        completed = subprocess.run(
            [sys.executable, str(ROOT / "demo_data/synthetic_v1/guardian_workflow/run_demo.py")],
            cwd=ROOT,
            env=env,
            check=False,
        )
        if completed.returncode:
            raise SystemExit("Optional Guardian manual-field demo failed.")
        guardian_status = "MANUAL_STRUCTURED_FIELDS_ONLY_NO_OCR_NO_PROVIDER_SEND"

    result = {
        "product": "AwnNORA",
        "journey": "FIRST_USER_PERSONAL_MODE",
        "environment": "SYNTHETIC_DEMO",
        "data_class": "SYNTHETIC_FIXTURE",
        "synthetic_persona_id": args.customer_id,
        "seed_status": seed_status,
        "personal_power_report": report,
        "application_snapshot": {
            "financial_account_count": len(accounts or []),
            "recurring_obligation_count": len(obligations or []),
        },
        "guardian_manual_demo": guardian_status,
        "security_and_truth": {
            "password_saved": False,
            "session_token_saved": False,
            "personal_records_shared_with_commons": False,
            "external_provider_calls": False,
            "payments_or_claims_performed": False,
            "verified_value_created_in_this_demo": "0.00 INR",
            "note": (
                "Synthetic fixture activity is not live user impact and is never counted as VIVC."
            ),
        },
    }
    destination_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / "first_user_report.json"
    destination.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(f"\nFirst-user journey complete. Report: {destination}")
    finding_count = len(report.get("findings", []))
    print(
        f"Accounts={len(accounts or [])}; obligations={len(obligations or [])}; "
        f"findings={finding_count}"
    )
    print(
        f"Verified value created={report.get('verified_value_created')} "
        "(synthetic demo must remain zero)."
    )
    print("No bank, merchant, employer, insurer, government or payment provider was contacted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
