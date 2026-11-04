"""Guardian application use cases: private evidence, invoice review and human-approved drafts."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from hashlib import sha256
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from myeconomy.application.audit import record_audit_event
from myeconomy.domain.economic_intelligence import (
    EconomicRuleError,
    EvidenceRef,
    InvoiceLine,
    InvoiceReviewInput,
    PriorInvoice,
    review_invoice,
)
from myeconomy.domain.errors import (
    ConflictError,
    FinancialDataValidationError,
    IdempotencyConflictError,
    NotFoundError,
)
from myeconomy.infrastructure.document_storage import LocalPrivateDocumentStore
from myeconomy.infrastructure.models import GuardianCase, GuardianEvidenceDocument


def store_evidence_document(
    db: Session,
    *,
    owner_user_id: UUID,
    idempotency_key: str,
    filename: str,
    media_type: str,
    content: bytes,
    storage: LocalPrivateDocumentStore,
) -> tuple[GuardianEvidenceDocument, bool]:
    digest = sha256(content).hexdigest()
    existing = db.scalar(
        select(GuardianEvidenceDocument).where(
            GuardianEvidenceDocument.owner_user_id == owner_user_id,
            GuardianEvidenceDocument.idempotency_key == idempotency_key,
        )
    )
    if existing is not None:
        if existing.sha256 != digest:
            raise IdempotencyConflictError(
                "The evidence idempotency key was already used with different file bytes."
            )
        return existing, True

    document_id = uuid4()
    storage.put(owner_id=owner_user_id, document_id=document_id, content=content)
    item = GuardianEvidenceDocument(
        id=document_id,
        owner_user_id=owner_user_id,
        idempotency_key=idempotency_key,
        original_filename=filename,
        media_type=media_type,
        byte_size=len(content),
        sha256=digest,
        status="STORED_UNSCANNED",
    )
    db.add(item)
    record_audit_event(
        db,
        actor_user_id=owner_user_id,
        action="guardian.evidence_document.stored",
        subject_type="guardian_evidence_document",
        subject_id=str(document_id),
        details={
            "sha256": digest,
            "byte_size": len(content),
            "media_type": media_type,
            "status": "STORED_UNSCANNED",
        },
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        storage.delete(owner_id=owner_user_id, document_id=document_id)
        raced = db.scalar(
            select(GuardianEvidenceDocument).where(
                GuardianEvidenceDocument.owner_user_id == owner_user_id,
                GuardianEvidenceDocument.idempotency_key == idempotency_key,
            )
        )
        if raced is not None and raced.sha256 == digest:
            return raced, True
        raise IdempotencyConflictError(
            "The evidence upload conflicts with an existing idempotency key."
        ) from None
    except Exception:
        db.rollback()
        storage.delete(owner_id=owner_user_id, document_id=document_id)
        raise
    db.refresh(item)
    return item, False


def get_evidence_document(
    db: Session, *, owner_user_id: UUID, document_id: UUID
) -> GuardianEvidenceDocument:
    item = db.scalar(
        select(GuardianEvidenceDocument).where(
            GuardianEvidenceDocument.id == document_id,
            GuardianEvidenceDocument.owner_user_id == owner_user_id,
        )
    )
    if item is None:
        raise NotFoundError("Evidence document was not found.")
    return item


def _decimal_text(value: Decimal | None) -> str | None:
    return str(value) if value is not None else None


def _snapshot(invoice: InvoiceReviewInput) -> dict[str, object]:
    return {
        "invoice_id": invoice.invoice_id,
        "provider_key": invoice.provider_key,
        "currency": invoice.currency.upper(),
        "issue_date": invoice.issue_date.isoformat(),
        "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
        "lines": [
            {
                "description": line.description,
                "quantity": str(line.quantity),
                "unit_price": str(line.unit_price),
                "declared_total": str(line.declared_total),
            }
            for line in invoice.lines
        ],
        "declared_subtotal": str(invoice.declared_subtotal),
        "tax": str(invoice.tax),
        "fees": str(invoice.fees),
        "credits": str(invoice.credits),
        "declared_total_due": str(invoice.declared_total_due),
        "extraction_confidence": str(invoice.extraction_confidence),
        "evidence": [
            {
                "field_name": ref.field_name,
                "document_sha256": ref.document_sha256,
                "locator": ref.locator,
                "confidence": str(ref.confidence),
            }
            for ref in invoice.evidence
        ],
        "input_source": "USER_SUBMITTED_STRUCTURED_FIELDS",
    }


def _review_snapshot(result: object) -> dict[str, object]:
    return {
        "invoice_id": result.invoice_id,
        "currency": result.currency,
        "disposition": result.disposition.value,
        "source_document_sha256": result.source_document_sha256,
        "disclaimer": result.disclaimer,
        "findings": [
            {
                "code": finding.code.value,
                "severity": finding.severity,
                "message": finding.message,
                "evidence_fields": list(finding.evidence_fields),
                "expected_amount": _decimal_text(finding.expected_amount),
                "observed_amount": _decimal_text(finding.observed_amount),
            }
            for finding in result.findings
        ],
    }


def create_invoice_review_case(
    db: Session,
    *,
    owner_user_id: UUID,
    evidence_document_id: UUID,
    idempotency_key: str,
    invoice_id: str,
    provider_key: str,
    currency: str,
    issue_date: date,
    due_date: date | None,
    lines: list[dict[str, object]],
    declared_subtotal: Decimal,
    tax: Decimal,
    fees: Decimal,
    credits: Decimal,
    declared_total_due: Decimal,
    extraction_confidence: Decimal,
    evidence: list[dict[str, object]],
) -> tuple[GuardianCase, bool]:
    document = get_evidence_document(
        db, owner_user_id=owner_user_id, document_id=evidence_document_id
    )
    # Only the owner may submit the structured extraction. The document remains
    # STORED_UNSCANNED: the app does not parse it or send it to a model in this iteration.
    if document.status != "STORED_UNSCANNED":
        raise ConflictError("The evidence document is not available for review.")
    canonical_payload = {
        "evidence_document_id": str(evidence_document_id),
        "evidence_sha256": document.sha256,
        "invoice_id": invoice_id,
        "provider_key": provider_key,
        "currency": currency.upper(),
        "issue_date": issue_date.isoformat(),
        "due_date": due_date.isoformat() if due_date else None,
        "lines": [{key: str(value) for key, value in line.items()} for line in lines],
        "declared_subtotal": str(declared_subtotal),
        "tax": str(tax),
        "fees": str(fees),
        "credits": str(credits),
        "declared_total_due": str(declared_total_due),
        "extraction_confidence": str(extraction_confidence),
        "evidence": [{key: str(value) for key, value in ref.items()} for ref in evidence],
    }
    request_digest = sha256(
        json.dumps(canonical_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    prior_request = db.scalar(
        select(GuardianCase).where(
            GuardianCase.owner_user_id == owner_user_id,
            GuardianCase.review_idempotency_key == idempotency_key,
        )
    )
    if prior_request is not None:
        if prior_request.request_sha256 != request_digest:
            raise IdempotencyConflictError(
                "The Guardian review idempotency key was already used with different review data."
            )
        return prior_request, True
    previous_cases = db.scalars(
        select(GuardianCase)
        .where(
            GuardianCase.owner_user_id == owner_user_id,
            GuardianCase.provider_key == provider_key,
            GuardianCase.currency == currency.upper(),
            GuardianCase.issue_date < issue_date,
        )
        .order_by(GuardianCase.issue_date.desc())
        .limit(12)
    ).all()
    prior_invoices = tuple(
        PriorInvoice(
            provider_key=case.provider_key,
            currency=case.currency,
            issue_date=case.issue_date,
            total_due=Decimal(str(case.invoice_snapshot["declared_total_due"])),
        )
        for case in previous_cases
    )
    known_hashes = frozenset(
        db.scalars(
            select(GuardianEvidenceDocument.sha256).where(
                GuardianEvidenceDocument.owner_user_id == owner_user_id,
                GuardianEvidenceDocument.id != evidence_document_id,
            )
        ).all()
    )
    try:
        evidence_items = tuple(
            EvidenceRef(
                field_name=str(ref["field_name"]),
                document_sha256=document.sha256,
                locator=str(ref["locator"]),
                confidence=Decimal(str(ref["confidence"])),
            )
            for ref in evidence
        )
        invoice = InvoiceReviewInput(
            invoice_id=invoice_id,
            provider_key=provider_key,
            currency=currency.upper(),
            source_document_sha256=document.sha256,
            issue_date=issue_date,
            due_date=due_date,
            lines=tuple(
                InvoiceLine(
                    description=str(line["description"]),
                    quantity=Decimal(str(line["quantity"])),
                    unit_price=Decimal(str(line["unit_price"])),
                    declared_total=Decimal(str(line["declared_total"])),
                )
                for line in lines
            ),
            declared_subtotal=declared_subtotal,
            tax=tax,
            fees=fees,
            credits=credits,
            declared_total_due=declared_total_due,
            extraction_confidence=extraction_confidence,
            evidence=evidence_items,
        )
        result = review_invoice(
            invoice, known_document_hashes=known_hashes, prior_invoices=prior_invoices
        )
    except EconomicRuleError as exc:
        raise FinancialDataValidationError(str(exc)) from exc
    item = GuardianCase(
        owner_user_id=owner_user_id,
        evidence_document_id=evidence_document_id,
        review_idempotency_key=idempotency_key,
        request_sha256=request_digest,
        invoice_id=invoice_id,
        provider_key=provider_key,
        currency=currency.upper(),
        issue_date=issue_date,
        disposition=result.disposition.value,
        status="REVIEWED",
        invoice_snapshot=_snapshot(invoice),
        review_snapshot=_review_snapshot(result),
    )
    db.add(item)
    record_audit_event(
        db,
        actor_user_id=owner_user_id,
        action="guardian.invoice_review.completed",
        subject_type="guardian_case",
        subject_id=str(item.id),
        details={
            "disposition": result.disposition.value,
            "finding_count": len(result.findings),
            "evidence_document_id": str(evidence_document_id),
        },
    )
    try:
        # Flush is inside the guarded transaction: unique-key races can fail here,
        # before commit, especially on SQLite and under concurrent API requests.
        db.flush()
        db.commit()
    except IntegrityError:
        db.rollback()
        raced = db.scalar(
            select(GuardianCase).where(
                GuardianCase.owner_user_id == owner_user_id,
                GuardianCase.review_idempotency_key == idempotency_key,
            )
        )
        if raced is not None and raced.request_sha256 == request_digest:
            return raced, True
        raise IdempotencyConflictError(
            "The Guardian review conflicts with an existing request key."
        ) from None
    db.refresh(item)
    return item, False


def get_guardian_case(db: Session, *, owner_user_id: UUID, case_id: UUID) -> GuardianCase:
    item = db.scalar(
        select(GuardianCase).where(
            GuardianCase.id == case_id, GuardianCase.owner_user_id == owner_user_id
        )
    )
    if item is None:
        raise NotFoundError("Guardian case was not found.")
    return item


def list_guardian_cases(
    db: Session, *, owner_user_id: UUID, limit: int = 100
) -> list[GuardianCase]:
    return list(
        db.scalars(
            select(GuardianCase)
            .where(GuardianCase.owner_user_id == owner_user_id)
            .order_by(GuardianCase.created_at.desc())
            .limit(limit)
        ).all()
    )


def create_case_action_draft(db: Session, *, owner_user_id: UUID, case_id: UUID) -> GuardianCase:
    item = get_guardian_case(db, owner_user_id=owner_user_id, case_id=case_id)
    if item.action_draft is not None:
        return item
    finding_lines = [
        f"- {entry['message']} Fields to verify: "
        f"{', '.join(entry['evidence_fields']) or 'source document'}."
        for entry in item.review_snapshot.get("findings", [])
    ]
    findings_text = (
        "\n".join(finding_lines) or "- Please confirm the invoice total and itemized charges."
    )
    item.action_draft = (
        f"Subject: Request for clarification — invoice {item.invoice_id}\n\n"
        f"Dear {item.provider_key},\n\n"
        f"I am reviewing invoice {item.invoice_id}, dated {item.issue_date.isoformat()}, "
        f"for {item.currency} {item.invoice_snapshot['declared_total_due']}. "
        "Please review and clarify the following items against the original invoice:\n\n"
        f"{findings_text}\n\n"
        "Please provide an itemized explanation and any corrected statement, if applicable. "
        "This request is for clarification and does not allege fraud or a legal violation.\n\n"
        "Regards,\n[Your name]\n\n"
        "DRAFT ONLY — not sent. Verify recipient, facts and attachments before sending."
    )
    item.status = "DRAFT_READY"
    record_audit_event(
        db,
        actor_user_id=owner_user_id,
        action="guardian.case.draft_created",
        subject_type="guardian_case",
        subject_id=str(item.id),
        details={"delivery": "NONE", "status": item.status},
    )
    db.commit()
    db.refresh(item)
    return item


def approve_case_draft(db: Session, *, owner_user_id: UUID, case_id: UUID) -> GuardianCase:
    item = get_guardian_case(db, owner_user_id=owner_user_id, case_id=case_id)
    if item.status != "DRAFT_READY" or not item.action_draft:
        raise ConflictError("Only an existing draft can be approved.")
    item.status = "APPROVED_FOR_USER_TO_SEND"
    record_audit_event(
        db,
        actor_user_id=owner_user_id,
        action="guardian.case.draft_approved_by_user",
        subject_type="guardian_case",
        subject_id=str(item.id),
        details={"delivery": "NONE", "status": item.status},
    )
    db.commit()
    db.refresh(item)
    return item
