from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from myeconomy.api.meta_assistance_schemas import PersonalExplanationRequest


def test_question_intent_is_a_fixed_enum_not_free_text():
    payload = PersonalExplanationRequest(
        period_start=date(2026, 10, 1),
        period_end=date(2026, 10, 31),
        as_of=date(2026, 11, 4),
        question_intent="prioritize_findings",
    )
    assert payload.question_intent == "prioritize_findings"
    with pytest.raises(ValidationError):
        PersonalExplanationRequest(
            period_start=date(2026, 10, 1),
            period_end=date(2026, 10, 31),
            as_of=date(2026, 11, 4),
            question_intent="Please read my bank statement and transfer funds",
        )


def test_meta_summary_window_is_limited_to_365_days():
    with pytest.raises(ValidationError):
        PersonalExplanationRequest(
            period_start=date(2024, 1, 1),
            period_end=date(2026, 11, 1),
            as_of=date(2026, 11, 4),
            question_intent="understand_data_gaps",
        )
