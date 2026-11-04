import pytest

from myeconomy.domain.casebook import (
    CaseTransitionError,
    PersonalCaseStatus,
    allowed_next_statuses,
    transition_case_status,
)


def test_open_case_can_enter_review_or_close():
    assert set(allowed_next_statuses("OPEN")) == {
        PersonalCaseStatus.IN_REVIEW,
        PersonalCaseStatus.CLOSED,
    }
    assert transition_case_status("OPEN", "IN_REVIEW") is PersonalCaseStatus.IN_REVIEW


def test_waiting_external_can_resolve_but_open_cannot_resolve_directly():
    assert transition_case_status("WAITING_EXTERNAL", "RESOLVED") is PersonalCaseStatus.RESOLVED
    with pytest.raises(CaseTransitionError):
        transition_case_status("OPEN", "RESOLVED")


def test_closed_is_terminal_and_unknown_status_rejected():
    assert allowed_next_statuses("CLOSED") == ()
    with pytest.raises(CaseTransitionError):
        transition_case_status("CLOSED", "OPEN")
    with pytest.raises(CaseTransitionError):
        transition_case_status("NOT_A_STATUS", "OPEN")


def test_case_response_serializes_minor_units_as_exact_integer_string():
    from datetime import UTC, datetime
    from uuid import uuid4

    from myeconomy.api.casebook_schemas import PersonalCaseResponse

    now = datetime.now(UTC)
    amount = "9000000000000000000"
    response = PersonalCaseResponse(
        id=uuid4(),
        source_engine="PERSONAL",
        source_finding_id="CASH-001",
        title="Exact amount",
        source_snapshot={},
        currency="INR",
        amount_minor=amount,
        status="OPEN",
        state_version=1,
        created_at=now,
        updated_at=now,
    )
    assert response.model_dump(mode="json")["amount_minor"] == amount


def test_case_create_schema_rejects_unsupported_currency_and_invalid_period():
    from datetime import date

    from pydantic import ValidationError

    from myeconomy.api.casebook_schemas import CaseFromFindingRequest

    valid = {
        "finding_id": "DATA-001",
        "period_start": date(2026, 10, 1),
        "period_end": date(2026, 10, 31),
        "as_of": date(2026, 11, 4),
        "currency": "inr",
    }
    assert CaseFromFindingRequest.model_validate(valid).currency == "INR"
    with pytest.raises(ValidationError):
        CaseFromFindingRequest.model_validate({**valid, "currency": "ZZZ"})
    with pytest.raises(ValidationError):
        CaseFromFindingRequest.model_validate({**valid, "period_start": date(2026, 11, 1)})
