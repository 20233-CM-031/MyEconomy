from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from myeconomy.infrastructure.models import AuditEvent, GuardianCase, GuardianEvidenceDocument


def register_verified(client, email: str, name: str) -> dict:
    registered = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "A-Long-Unique-Passphrase-2026!", "display_name": name},
    )
    assert registered.status_code == 201, registered.text
    token = client.app.state.verification_tokens[email]
    verified = client.post("/api/v1/auth/verify-email", json={"token": token})
    assert verified.status_code == 200, verified.text
    return registered.json()


def headers(token: str, **extra: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", **extra}


def upload(client, token: str, payload: bytes, key: str = "evidence-001"):
    return client.post(
        "/api/v1/guardian/evidence-documents",
        headers=headers(
            token,
            **{
                "Content-Type": "application/pdf",
                "Idempotency-Key": key,
                "X-Filename": "../../synthetic-invoice.pdf",
            },
        ),
        content=payload,
    )


def invoice_payload(
    document_id: str, *, total: str = "1180.00", confidence: str = "0.99", evidence: bool = True
):
    refs = []
    if evidence:
        refs = [
            {"field_name": field, "locator": f"page=1;field={field}", "confidence": "0.99"}
            for field in [
                "invoice_id",
                "provider",
                "currency",
                "issue_date",
                "total_due",
                "line[1].quantity",
                "line[1].unit_price",
                "line[1].total",
            ]
        ]
    return {
        "evidence_document_id": document_id,
        "invoice_id": "INV-DEMO-1042",
        "provider_key": "deccan-broadband-demo",
        "currency": "INR",
        "issue_date": "2026-11-01",
        "due_date": "2026-11-15",
        "lines": [
            {
                "description": "Fibre broadband monthly plan",
                "quantity": "1",
                "unit_price": "1000.00",
                "declared_total": "1000.00",
            }
        ],
        "declared_subtotal": "1000.00",
        "tax": "180.00",
        "fees": "0.00",
        "credits": "0.00",
        "declared_total_due": "1180.00",
        "extraction_confidence": confidence,
        "evidence": refs,
    }


def test_guardian_evidence_upload_review_draft_and_approval_are_owner_scoped(test_environment):
    client, session_factory = test_environment
    alice = register_verified(client, "guardian-alice@example.com", "Alice")
    bob = register_verified(client, "guardian-bob@example.com", "Bob")
    pdf = b"%PDF-1.4\n% SYNTHETIC AwnNORA invoice test file\n%%EOF"

    uploaded = upload(client, alice["access_token"], pdf)
    assert uploaded.status_code == 201, uploaded.text
    document = uploaded.json()
    assert document["status"] == "STORED_UNSCANNED"
    assert document["sha256"]
    assert "../" not in document["original_filename"]
    assert document["replayed"] is False

    replay = upload(client, alice["access_token"], pdf)
    assert replay.status_code == 201
    assert replay.json()["id"] == document["id"]
    assert replay.json()["replayed"] is True

    changed = upload(client, alice["access_token"], pdf + b"changed")
    assert changed.status_code == 409
    assert changed.json()["error"]["code"] == "idempotency_conflict"

    inaccessible = client.get(
        f"/api/v1/guardian/evidence-documents/{document['id']}/download",
        headers=headers(bob["access_token"]),
    )
    assert inaccessible.status_code == 404
    downloaded = client.get(
        f"/api/v1/guardian/evidence-documents/{document['id']}/download",
        headers=headers(alice["access_token"]),
    )
    assert downloaded.status_code == 200
    assert downloaded.content == pdf
    assert downloaded.headers["cache-control"] == "private, no-store"
    listed_docs = client.get(
        "/api/v1/guardian/evidence-documents", headers=headers(alice["access_token"])
    )
    assert listed_docs.status_code == 200
    assert len(listed_docs.json()) == 1

    reviewed = client.post(
        "/api/v1/guardian/invoice-reviews",
        headers=headers(alice["access_token"], **{"Idempotency-Key": "invoice-review-001"}),
        json=invoice_payload(document["id"]),
    )
    assert reviewed.status_code == 201, reviewed.text
    case = reviewed.json()
    assert case["disposition"] == "CONSISTENT"
    assert case["status"] == "REVIEWED"
    assert case["findings"] == []
    replay = client.post(
        "/api/v1/guardian/invoice-reviews",
        headers=headers(alice["access_token"], **{"Idempotency-Key": "invoice-review-001"}),
        json=invoice_payload(document["id"]),
    )
    assert replay.status_code == 201
    assert replay.json()["id"] == case["id"]
    assert replay.json()["replayed"] is True
    changed_payload = invoice_payload(document["id"])
    changed_payload["declared_total_due"] = "1181.00"
    collision = client.post(
        "/api/v1/guardian/invoice-reviews",
        headers=headers(alice["access_token"], **{"Idempotency-Key": "invoice-review-001"}),
        json=changed_payload,
    )
    assert collision.status_code == 409

    draft = client.post(
        f"/api/v1/guardian/cases/{case['id']}/draft", headers=headers(alice["access_token"])
    )
    assert draft.status_code == 200, draft.text
    assert draft.json()["status"] == "DRAFT_READY"
    assert "DRAFT ONLY — not sent" in draft.json()["action_draft"]

    approved = client.post(
        f"/api/v1/guardian/cases/{case['id']}/approve-draft",
        headers=headers(alice["access_token"]),
        json={"confirm": True},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "APPROVED_FOR_USER_TO_SEND"

    bob_case = client.get(
        f"/api/v1/guardian/cases/{case['id']}", headers=headers(bob["access_token"])
    )
    assert bob_case.status_code == 404
    own_cases = client.get("/api/v1/guardian/cases", headers=headers(alice["access_token"]))
    assert own_cases.status_code == 200
    assert len(own_cases.json()) == 1

    with session_factory() as db:
        assert (
            db.scalar(
                select(GuardianEvidenceDocument).where(
                    GuardianEvidenceDocument.id == UUID(document["id"])
                )
            )
            is not None
        )
        assert (
            db.scalar(select(GuardianCase).where(GuardianCase.id == UUID(case["id"]))) is not None
        )
        actions = set(db.scalars(select(AuditEvent.action)).all())
        assert "guardian.evidence_document.stored" in actions
        assert "guardian.evidence_document.downloaded" in actions
        assert "guardian.invoice_review.completed" in actions
        assert "guardian.case.draft_approved_by_user" in actions


def test_guardian_draft_approval_requires_explicit_true_confirmation(test_environment):
    client, _ = test_environment
    owner = register_verified(client, "guardian-approval@example.com", "Approval User")
    document = upload(client, owner["access_token"], b"%PDF-1.4\nsynthetic\n%%EOF").json()
    review = client.post(
        "/api/v1/guardian/invoice-reviews",
        headers=headers(owner["access_token"], **{"Idempotency-Key": "approval-review"}),
        json=invoice_payload(document["id"]),
    )
    assert review.status_code == 201
    case_id = review.json()["id"]
    draft = client.post(
        f"/api/v1/guardian/cases/{case_id}/draft", headers=headers(owner["access_token"])
    )
    assert draft.status_code == 200
    rejected = client.post(
        f"/api/v1/guardian/cases/{case_id}/approve-draft",
        headers=headers(owner["access_token"]),
        json={"confirm": False},
    )
    assert rejected.status_code == 422
    assert "detail" in rejected.json()
    fetched = client.get(
        f"/api/v1/guardian/cases/{case_id}", headers=headers(owner["access_token"])
    )
    assert fetched.status_code == 200
    assert fetched.json()["status"] == "DRAFT_READY"


def test_guardian_rejects_mime_spoofing_and_oversized_upload(test_environment):
    client, _ = test_environment
    alice = register_verified(client, "guardian-invalid@example.com", "Alice")
    bad = client.post(
        "/api/v1/guardian/evidence-documents",
        headers=headers(
            alice["access_token"], **{"Content-Type": "application/pdf", "Idempotency-Key": "bad"}
        ),
        content=b"not a PDF",
    )
    assert bad.status_code == 422
    assert "does not match" in bad.json()["error"]["message"]
    oversized = client.post(
        "/api/v1/guardian/evidence-documents",
        headers=headers(
            alice["access_token"], **{"Content-Type": "application/pdf", "Idempotency-Key": "large"}
        ),
        content=b"%PDF-" + (b"0" * (5 * 1024 * 1024)),
    )
    assert oversized.status_code == 422


def test_guardian_abstains_when_evidence_is_missing_or_confidence_is_low(test_environment):
    client, _ = test_environment
    alice = register_verified(client, "guardian-abstain@example.com", "Alice")
    doc = upload(client, alice["access_token"], b"%PDF-1.4\nsynthetic\n%%EOF").json()
    response = client.post(
        "/api/v1/guardian/invoice-reviews",
        headers=headers(alice["access_token"], **{"Idempotency-Key": "invoice-review-abstain"}),
        json=invoice_payload(doc["id"], confidence="0.4", evidence=False),
    )
    assert response.status_code == 201, response.text
    assert response.json()["disposition"] == "ABSTAIN"
    codes = {finding["code"] for finding in response.json()["findings"]}
    assert "MISSING_EVIDENCE" in codes
    assert "LOW_EXTRACTION_CONFIDENCE" in codes


def test_guardian_detects_unusual_comparable_invoice_increase(test_environment):
    client, _ = test_environment
    alice = register_verified(client, "guardian-prior@example.com", "Alice")
    first_doc = upload(
        client, alice["access_token"], b"%PDF-1.4\nfirst synthetic invoice\n%%EOF", "first-doc"
    ).json()
    first = invoice_payload(first_doc["id"], total="800.00")
    first.update(
        {
            "invoice_id": "INV-PRIOR-001",
            "issue_date": "2026-10-01",
            "declared_subtotal": "800.00",
            "tax": "0.00",
            "declared_total_due": "800.00",
            "lines": [
                {
                    "description": "Broadband plan",
                    "quantity": "1",
                    "unit_price": "800.00",
                    "declared_total": "800.00",
                }
            ],
        }
    )
    assert (
        client.post(
            "/api/v1/guardian/invoice-reviews",
            headers=headers(alice["access_token"], **{"Idempotency-Key": "prior-invoice-001"}),
            json=first,
        ).status_code
        == 201
    )

    next_doc = upload(
        client, alice["access_token"], b"%PDF-1.4\nsecond synthetic invoice\n%%EOF", "second-doc"
    ).json()
    second = invoice_payload(next_doc["id"], total="1180.00")
    second.update({"invoice_id": "INV-CURRENT-002", "issue_date": "2026-11-01"})
    current = client.post(
        "/api/v1/guardian/invoice-reviews",
        headers=headers(alice["access_token"], **{"Idempotency-Key": "current-invoice-002"}),
        json=second,
    )
    assert current.status_code == 201, current.text
    assert current.json()["disposition"] == "REVIEW_REQUIRED"
    assert "UNUSUAL_INCREASE" in {finding["code"] for finding in current.json()["findings"]}
