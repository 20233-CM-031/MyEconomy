"""Run the local, synthetic-only Guardian document-review demo."""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = Path(__file__).resolve().parent
BASE_URL = os.getenv("AWNNORA_DEMO_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
TOKEN = os.getenv("AWNNORA_DEMO_BEARER_TOKEN", "").strip()


def call(
    path: str,
    *,
    method: str = "GET",
    body: bytes | None = None,
    content_type: str = "application/json",
    idempotency_key: str | None = None,
) -> dict:
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": content_type}
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    request = Request(BASE_URL + path, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=20) as response:
            payload = response.read()
            return json.loads(payload) if payload else {}
    except HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} returned HTTP {exc.code}: {message}") from exc
    except URLError as exc:
        raise RuntimeError(f"Cannot reach AwnNORA API at {BASE_URL}: {exc.reason}") from exc


def upload_document(filename: str, key: str) -> dict:
    path = ROOT / "source_documents" / "guardian" / filename
    if not path.is_file():
        raise FileNotFoundError(path)
    raw = path.read_bytes()
    request = Request(
        BASE_URL + "/api/v1/guardian/evidence-documents",
        data=raw,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/pdf",
            "Idempotency-Key": key,
            "X-Filename": filename,
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read())
    except HTTPError as exc:
        raise RuntimeError(
            f"Upload {filename} returned HTTP {exc.code}: {exc.read().decode(errors='replace')}"
        ) from exc
    except URLError as exc:
        raise RuntimeError(f"Cannot reach AwnNORA API at {BASE_URL}: {exc.reason}") from exc


def main() -> None:
    if not TOKEN:
        raise SystemExit(
            "Set AWNNORA_DEMO_BEARER_TOKEN to a verified local/demo user token first. "
            "Never use a production or real customer's bearer token for this fixture."
        )
    payloads = json.loads((WORKFLOW / "invoice_payloads.json").read_text(encoding="utf-8"))
    scenarios = [
        (
            "guardian_previous_bill.pdf",
            "guardian-doc-prior-001",
            "guardian-case-prior-001",
            "previous_bill",
        ),
        (
            "guardian_current_bill_anomaly.pdf",
            "guardian-doc-current-001",
            "guardian-case-current-001",
            "current_bill_anomaly",
        ),
        (
            "guardian_arithmetic_mismatch.pdf",
            "guardian-doc-arithmetic-001",
            "guardian-case-arithmetic-001",
            "arithmetic_mismatch",
        ),
    ]
    cases: dict[str, dict] = {}
    for filename, upload_key, case_key, payload_name in scenarios:
        document = upload_document(filename, upload_key)
        invoice = dict(payloads[payload_name])
        invoice["evidence_document_id"] = document["id"]
        case = call(
            "/api/v1/guardian/invoice-reviews",
            method="POST",
            body=json.dumps(invoice).encode("utf-8"),
            idempotency_key=case_key,
        )
        cases[payload_name] = case
        print(
            f"{payload_name}: case={case['id']} disposition={case['disposition']} "
            f"findings={[item['code'] for item in case['findings']]}"
        )
        if case["disposition"] != "CONSISTENT":
            draft = call(
                f"/api/v1/guardian/cases/{case['id']}/draft",
                method="POST",
                body=b"{}",
            )
            print(f"  draft state={draft['status']} delivery=NONE")

    print("\nDemo complete. No provider was contacted; drafts have not been sent or approved.")
    print("Inspect all cases at GET /api/v1/guardian/cases using the same local bearer token.")


if __name__ == "__main__":
    main()
