"""Deterministic state machine for AwnNORA's personal economic casebook."""

from __future__ import annotations

from enum import StrEnum


class CaseTransitionError(ValueError):
    """Raised when a requested case state transition is not permitted."""


class PersonalCaseStatus(StrEnum):
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    ACTION_READY = "ACTION_READY"
    WAITING_FOR_USER = "WAITING_FOR_USER"
    WAITING_EXTERNAL = "WAITING_EXTERNAL"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


_ALLOWED_TRANSITIONS: dict[PersonalCaseStatus, frozenset[PersonalCaseStatus]] = {
    PersonalCaseStatus.OPEN: frozenset({PersonalCaseStatus.IN_REVIEW, PersonalCaseStatus.CLOSED}),
    PersonalCaseStatus.IN_REVIEW: frozenset(
        {
            PersonalCaseStatus.ACTION_READY,
            PersonalCaseStatus.WAITING_FOR_USER,
            PersonalCaseStatus.CLOSED,
        }
    ),
    PersonalCaseStatus.ACTION_READY: frozenset(
        {
            PersonalCaseStatus.IN_REVIEW,
            PersonalCaseStatus.WAITING_FOR_USER,
            PersonalCaseStatus.WAITING_EXTERNAL,
            PersonalCaseStatus.CLOSED,
        }
    ),
    PersonalCaseStatus.WAITING_FOR_USER: frozenset(
        {
            PersonalCaseStatus.IN_REVIEW,
            PersonalCaseStatus.ACTION_READY,
            PersonalCaseStatus.CLOSED,
        }
    ),
    PersonalCaseStatus.WAITING_EXTERNAL: frozenset(
        {PersonalCaseStatus.IN_REVIEW, PersonalCaseStatus.RESOLVED, PersonalCaseStatus.CLOSED}
    ),
    PersonalCaseStatus.RESOLVED: frozenset({PersonalCaseStatus.CLOSED}),
    PersonalCaseStatus.CLOSED: frozenset(),
}


def allowed_next_statuses(status: str | PersonalCaseStatus) -> tuple[PersonalCaseStatus, ...]:
    """Return the ordered set of legal next statuses for a known case state."""
    try:
        current = PersonalCaseStatus(status)
    except ValueError as exc:
        raise CaseTransitionError("Unknown personal case status.") from exc
    return tuple(sorted(_ALLOWED_TRANSITIONS[current], key=lambda item: item.value))


def transition_case_status(
    current_status: str | PersonalCaseStatus,
    requested_status: str | PersonalCaseStatus,
) -> PersonalCaseStatus:
    """Validate a state transition. This function performs no persistence or side effect."""
    try:
        current = PersonalCaseStatus(current_status)
        requested = PersonalCaseStatus(requested_status)
    except ValueError as exc:
        raise CaseTransitionError("Unknown personal case status.") from exc
    if requested not in _ALLOWED_TRANSITIONS[current]:
        allowed = ", ".join(item.value for item in allowed_next_statuses(current)) or "none"
        raise CaseTransitionError(
            "Cannot move a case from "
            f"{current.value} to {requested.value}. Allowed next states: {allowed}."
        )
    return requested
