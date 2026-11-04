"""Typed API contracts for the Guardian evidence-review vertical slice."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EvidenceRefRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field_name: str = Field(min_length=1, max_length=80)
    locator: str = Field(min_length=1, max_length=160)
    confidence: Decimal = Field(ge=0, le=1)


class InvoiceLineRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: str = Field(min_length=1, max_length=256)
    quantity: Decimal = Field(gt=0, le=1_000_000)
    unit_price: Decimal = Field(ge=0, le=10_000_000_000)
    declared_total: Decimal = Field(ge=0, le=10_000_000_000)


class InvoiceReviewRequest(BaseModel):
    """User-reviewed structured fields; model extraction is not claimed in Iteration 04."""

    model_config = ConfigDict(extra="forbid")
    evidence_document_id: UUID
    invoice_id: str = Field(min_length=1, max_length=128)
    provider_key: str = Field(min_length=1, max_length=128)
    currency: str = Field(min_length=3, max_length=3, pattern=r"^[A-Za-z]{3}$")
    issue_date: date
    due_date: date | None = None
    lines: list[InvoiceLineRequest] = Field(min_length=1, max_length=100)
    declared_subtotal: Decimal = Field(ge=0, le=10_000_000_000)
    tax: Decimal = Field(default=Decimal("0"), ge=0, le=10_000_000_000)
    fees: Decimal = Field(default=Decimal("0"), ge=0, le=10_000_000_000)
    credits: Decimal = Field(default=Decimal("0"), ge=0, le=10_000_000_000)
    declared_total_due: Decimal = Field(ge=0, le=10_000_000_000)
    extraction_confidence: Decimal = Field(ge=0, le=1)
    evidence: list[EvidenceRefRequest] = Field(default_factory=list, max_length=500)


class EvidenceDocumentResponse(BaseModel):
    id: UUID
    original_filename: str
    media_type: str
    byte_size: int
    sha256: str
    status: str
    created_at: datetime
    replayed: bool = False


class GuardianFindingResponse(BaseModel):
    code: str
    severity: str
    message: str
    evidence_fields: list[str]
    expected_amount: str | None = None
    observed_amount: str | None = None


class GuardianCaseResponse(BaseModel):
    id: UUID
    case_type: str
    invoice_id: str
    provider_key: str
    currency: str
    issue_date: date
    disposition: str
    status: str
    evidence_document_id: UUID
    source_document_sha256: str
    findings: list[GuardianFindingResponse]
    disclaimer: str
    action_draft: str | None = None
    created_at: datetime
    updated_at: datetime
    replayed: bool = False


class DraftApprovalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    confirm: Literal[True]
