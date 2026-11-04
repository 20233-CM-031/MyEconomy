"""Authenticated Guardian evidence intake and invoice-review workflow."""

from __future__ import annotations

from datetime import UTC
from io import BytesIO
from pathlib import PurePosixPath
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from myeconomy.api.dependencies import AuthContext, require_verified_authentication
from myeconomy.api.guardian_schemas import (
    DraftApprovalRequest,
    EvidenceDocumentResponse,
    GuardianCaseResponse,
    InvoiceReviewRequest,
)
from myeconomy.application.audit import record_audit_event
from myeconomy.application.guardian import (
    approve_case_draft,
    create_case_action_draft,
    create_invoice_review_case,
    get_evidence_document,
    get_guardian_case,
    list_guardian_cases,
    store_evidence_document,
)
from myeconomy.domain.errors import FinancialDataValidationError, ServiceUnavailableError
from myeconomy.infrastructure.database import get_db
from myeconomy.infrastructure.document_storage import (
    DocumentStorageError,
    LocalPrivateDocumentStore,
)
from myeconomy.infrastructure.models import GuardianCase, GuardianEvidenceDocument

router = APIRouter(prefix="/api/v1/guardian", tags=["guardian"])
MAX_EVIDENCE_BYTES = 5 * 1024 * 1024
DOCUMENT_STORE = LocalPrivateDocumentStore()
_ALLOWED_SIGNATURES = {
    "application/pdf": lambda data: data.startswith(b"%PDF-"),
    "image/png": lambda data: data.startswith(b"\x89PNG\r\n\x1a\n"),
    "image/jpeg": lambda data: data.startswith(b"\xff\xd8\xff"),
}


def _filename(value: str) -> str:
    cleaned = value.replace("\\", "/")
    name = PurePosixPath(cleaned).name
    name = "".join(char for char in name if char.isprintable() and char not in '"<>|')
    name = name.strip().strip(".")
    return (name or "evidence-upload")[:160]


def _document_response(
    item: GuardianEvidenceDocument, replayed: bool = False
) -> EvidenceDocumentResponse:
    created = (
        item.created_at.replace(tzinfo=UTC) if item.created_at.tzinfo is None else item.created_at
    )
    return EvidenceDocumentResponse(
        id=item.id,
        original_filename=item.original_filename,
        media_type=item.media_type,
        byte_size=item.byte_size,
        sha256=item.sha256,
        status=item.status,
        created_at=created,
        replayed=replayed,
    )


def _case_response(item: GuardianCase, replayed: bool = False) -> GuardianCaseResponse:
    created = (
        item.created_at.replace(tzinfo=UTC) if item.created_at.tzinfo is None else item.created_at
    )
    updated = (
        item.updated_at.replace(tzinfo=UTC) if item.updated_at.tzinfo is None else item.updated_at
    )
    return GuardianCaseResponse(
        id=item.id,
        case_type=item.case_type,
        invoice_id=item.invoice_id,
        provider_key=item.provider_key,
        currency=item.currency,
        issue_date=item.issue_date,
        disposition=item.disposition,
        status=item.status,
        evidence_document_id=item.evidence_document_id,
        source_document_sha256=item.review_snapshot["source_document_sha256"],
        findings=item.review_snapshot["findings"],
        disclaimer=item.review_snapshot["disclaimer"],
        action_draft=item.action_draft,
        created_at=created,
        updated_at=updated,
        replayed=replayed,
    )


@router.post(
    "/evidence-documents",
    response_model=EvidenceDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_evidence_document(
    request: Request,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=128),
    filename: str = Header(default="evidence.bin", alias="X-Filename", max_length=512),
    auth: AuthContext = Depends(require_verified_authentication),
    db: Session = Depends(get_db),
) -> EvidenceDocumentResponse:
    media_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if media_type not in _ALLOWED_SIGNATURES:
        raise FinancialDataValidationError("Only PDF, PNG and JPEG evidence files are accepted.")
    length = request.headers.get("content-length")
    if length and length.isdigit() and int(length) > MAX_EVIDENCE_BYTES:
        raise FinancialDataValidationError("Evidence file exceeds the 5 MiB limit.")
    content = bytearray()
    async for chunk in request.stream():
        if len(content) + len(chunk) > MAX_EVIDENCE_BYTES:
            raise FinancialDataValidationError("Evidence file exceeds the 5 MiB limit.")
        content.extend(chunk)
    raw = bytes(content)
    if not raw or not _ALLOWED_SIGNATURES[media_type](raw):
        raise FinancialDataValidationError(
            "File content does not match the declared PDF, PNG or JPEG type."
        )
    try:
        item, replayed = store_evidence_document(
            db,
            owner_user_id=auth.user.id,
            idempotency_key=idempotency_key,
            filename=_filename(filename),
            media_type=media_type,
            content=raw,
            storage=DOCUMENT_STORE,
        )
    except DocumentStorageError as exc:
        raise ServiceUnavailableError("Private evidence storage is unavailable.") from exc
    return _document_response(item, replayed)


@router.get("/evidence-documents", response_model=list[EvidenceDocumentResponse])
def list_evidence_documents(
    limit: int = Query(default=50, ge=1, le=100),
    auth: AuthContext = Depends(require_verified_authentication),
    db: Session = Depends(get_db),
) -> list[EvidenceDocumentResponse]:
    from sqlalchemy import select

    items = db.scalars(
        select(GuardianEvidenceDocument)
        .where(GuardianEvidenceDocument.owner_user_id == auth.user.id)
        .order_by(GuardianEvidenceDocument.created_at.desc())
        .limit(limit)
    ).all()
    return [_document_response(item) for item in items]


@router.get("/evidence-documents/{document_id}/download")
def download_evidence_document(
    document_id: UUID,
    auth: AuthContext = Depends(require_verified_authentication),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    item = get_evidence_document(db, owner_user_id=auth.user.id, document_id=document_id)
    try:
        raw = DOCUMENT_STORE.get(owner_id=auth.user.id, document_id=document_id)
    except DocumentStorageError as exc:
        raise ServiceUnavailableError("Private evidence storage is unavailable.") from exc
    record_audit_event(
        db,
        actor_user_id=auth.user.id,
        action="guardian.evidence_document.downloaded",
        subject_type="guardian_evidence_document",
        subject_id=str(document_id),
        details={"sha256": item.sha256, "byte_size": item.byte_size},
    )
    db.commit()
    safe_name = item.original_filename.replace("\r", "").replace("\n", "").replace('"', "")
    return StreamingResponse(
        BytesIO(raw),
        media_type=item.media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{safe_name}"',
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post(
    "/invoice-reviews", response_model=GuardianCaseResponse, status_code=status.HTTP_201_CREATED
)
def create_invoice_review(
    payload: InvoiceReviewRequest,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=128),
    auth: AuthContext = Depends(require_verified_authentication),
    db: Session = Depends(get_db),
) -> GuardianCaseResponse:
    item, replayed = create_invoice_review_case(
        db,
        owner_user_id=auth.user.id,
        evidence_document_id=payload.evidence_document_id,
        idempotency_key=idempotency_key,
        invoice_id=payload.invoice_id,
        provider_key=payload.provider_key,
        currency=payload.currency,
        issue_date=payload.issue_date,
        due_date=payload.due_date,
        lines=[line.model_dump() for line in payload.lines],
        declared_subtotal=payload.declared_subtotal,
        tax=payload.tax,
        fees=payload.fees,
        credits=payload.credits,
        declared_total_due=payload.declared_total_due,
        extraction_confidence=payload.extraction_confidence,
        evidence=[ref.model_dump() for ref in payload.evidence],
    )
    return _case_response(item, replayed=replayed)


@router.get("/cases", response_model=list[GuardianCaseResponse])
def list_cases(
    limit: int = Query(default=50, ge=1, le=100),
    auth: AuthContext = Depends(require_verified_authentication),
    db: Session = Depends(get_db),
) -> list[GuardianCaseResponse]:
    return [
        _case_response(item)
        for item in list_guardian_cases(db, owner_user_id=auth.user.id, limit=limit)
    ]


@router.get("/cases/{case_id}", response_model=GuardianCaseResponse)
def get_case(
    case_id: UUID,
    auth: AuthContext = Depends(require_verified_authentication),
    db: Session = Depends(get_db),
) -> GuardianCaseResponse:
    return _case_response(get_guardian_case(db, owner_user_id=auth.user.id, case_id=case_id))


@router.post("/cases/{case_id}/draft", response_model=GuardianCaseResponse)
def draft_case_action(
    case_id: UUID,
    auth: AuthContext = Depends(require_verified_authentication),
    db: Session = Depends(get_db),
) -> GuardianCaseResponse:
    return _case_response(create_case_action_draft(db, owner_user_id=auth.user.id, case_id=case_id))


@router.post("/cases/{case_id}/approve-draft", response_model=GuardianCaseResponse)
def approve_case_action_draft(
    case_id: UUID,
    payload: DraftApprovalRequest,
    auth: AuthContext = Depends(require_verified_authentication),
    db: Session = Depends(get_db),
) -> GuardianCaseResponse:
    if payload.confirm is not True:
        raise FinancialDataValidationError("Explicit draft approval is required.")
    return _case_response(approve_case_draft(db, owner_user_id=auth.user.id, case_id=case_id))
