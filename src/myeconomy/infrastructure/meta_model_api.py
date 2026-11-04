"""Narrow Meta Model API adapter for AwnNORA personal-summary explanations.

This adapter has no tools, browser, file, or provider access. It sends only an
aggregate financial summary after a purpose-specific consent check in the API.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Callable
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

META_API_BASE = "https://api.meta.ai/v1"
META_MODEL_ID = "muse-spark-1.3"  # Standard mode only; never accept Contributor IDs.
MAX_RESPONSE_BYTES = 128 * 1024
_UNSUPPORTED_OUTCOME_CLAIM = re.compile(
    r"\b(?:the|your)\s+(?:refund|payment|benefit|claim|job|order)\s+"
    r"(?:has been|was|is now)\s+(?:paid|credited|approved|settled|confirmed|completed)\b"
    r"|\b(?:fraud|a legal violation)\s+(?:is|was)\s+confirmed\b"
    r"|\b(?:awnnora|we|the provider)\s+(?:have|has)\s+"
    r"(?:paid|submitted|contacted|cancelled|canceled|approved)\b",
    re.IGNORECASE,
)
_CURRENCY_AMOUNT = re.compile(r"(?:₹|\bINR\s*)\s*[0-9][0-9,]*(?:\.[0-9]{1,2})?", re.IGNORECASE)


class MetaModelUnavailable(RuntimeError):
    """The Meta API was not configured or did not return a safe response."""


def _response_schema() -> dict[str, Any]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "awnnora_personal_explanation",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "actions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "finding_id": {"type": "string"},
                                "why_it_matters": {"type": "string"},
                                "next_step": {"type": "string"},
                                "uncertainty": {"type": "string"},
                            },
                            "required": [
                                "finding_id",
                                "why_it_matters",
                                "next_step",
                                "uncertainty",
                            ],
                            "additionalProperties": False,
                        },
                    },
                    "limitations": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["summary", "actions", "limitations"],
                "additionalProperties": False,
            },
        },
    }


def _extract_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise MetaModelUnavailable("Meta Model API returned no completion choices.")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        fragments = [
            item.get("text", "")
            for item in content
            if isinstance(item, dict) and item.get("type") in {"text", "output_text"}
        ]
        joined = "".join(str(item) for item in fragments)
        if joined:
            return joined
    raise MetaModelUnavailable("Meta Model API returned no structured text content.")


def call_personal_explanation(
    *,
    question: str,
    personal_summary: dict[str, Any],
    allowed_finding_ids: set[str],
    api_key: str | None = None,
    opener: Callable[..., Any] = urlopen,
    timeout_seconds: float = 18.0,
) -> dict[str, Any]:
    """Request a schema-constrained explanation without granting model tools.

    The caller must provide a previously minimized summary. This function enforces
    a fixed Standard-mode model ID and rejects any model references to unknown IDs.
    It never accepts or emits model-generated monetary facts.
    """
    token = (api_key or os.getenv("MODEL_API_KEY", "")).strip()
    if not token:
        raise MetaModelUnavailable("MODEL_API_KEY is not configured on the server.")
    if len(question) > 500 or not question.strip():
        raise MetaModelUnavailable("Question must contain 1 to 500 characters.")
    if not allowed_finding_ids:
        # Explanations about report gaps are still valid; the schema may return no actions.
        allowed_finding_ids = set()

    instructions = (
        "You are the explanation layer of AwnNORA, a human economic intelligence system. "
        "Explain the supplied deterministic report; do not recalculate money or invent facts. "
        "Use only the supplied findings and exact finding_id values. Do not claim a refund, "
        "saving, benefit award, job, payment, fraud, legal violation, or provider action occurred. "
        "Do not provide legal, investment, credit, or medical advice. Do not execute actions. "
        "When evidence is incomplete, say so and recommend a reversible verification step. "
        "Do not quote or calculate monetary amounts; the deterministic report panel owns all "
        "money values. Do not claim that a refund, payment, benefit, job, claim, provider action "
        "or fraud finding is complete or confirmed. "
        "Keep the explanation plain, calm, and actionable. "
        "Do not request personal identifiers."
    )
    body = {
        "model": META_MODEL_ID,
        "store": False,
        "temperature": 0.2,
        "reasoning_effort": "medium",
        "max_completion_tokens": 900,
        "messages": [
            {"role": "system", "content": instructions},
            {
                "role": "user",
                "content": json.dumps(
                    {"question": question.strip(), "personal_summary": personal_summary},
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
            },
        ],
        "response_format": _response_schema(),
    }
    request = Request(
        f"{META_API_BASE}/chat/completions",
        data=json.dumps(body, separators=(",", ":")).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with opener(request, timeout=timeout_seconds) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        # Do not surface provider response content; it may contain internal details.
        raise MetaModelUnavailable(f"Meta Model API returned HTTP {exc.code}.") from None
    except (URLError, TimeoutError, OSError) as exc:
        raise MetaModelUnavailable("Meta Model API could not be reached.") from exc
    if len(raw) > MAX_RESPONSE_BYTES:
        raise MetaModelUnavailable("Meta Model API response exceeded the configured limit.")
    try:
        provider_payload = json.loads(raw.decode("utf-8"))
        model_text = _extract_text(provider_payload)
        result = json.loads(model_text)
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, KeyError) as exc:
        raise MetaModelUnavailable("Meta Model API returned invalid structured output.") from exc

    if not isinstance(result, dict):
        raise MetaModelUnavailable("Meta Model API response must be an object.")
    summary = result.get("summary")
    actions = result.get("actions")
    limitations = result.get("limitations")
    if not isinstance(summary, str) or not summary.strip() or len(summary) > 2400:
        raise MetaModelUnavailable("Meta Model API summary was outside the allowed shape.")
    prose = [summary]
    for candidate in actions if isinstance(actions, list) else []:
        if isinstance(candidate, dict):
            prose.extend(
                str(candidate.get(key, ""))
                for key in ("why_it_matters", "next_step", "uncertainty")
            )
    if any(_UNSUPPORTED_OUTCOME_CLAIM.search(item) for item in prose):
        raise MetaModelUnavailable("Meta Model API attempted to claim an unverified outcome.")
    if any(_CURRENCY_AMOUNT.search(item) for item in prose):
        raise MetaModelUnavailable("Meta Model API attempted to restate a monetary amount.")
    if not isinstance(actions, list) or len(actions) > 4:
        raise MetaModelUnavailable("Meta Model API returned too many actions.")
    if not isinstance(limitations, list) or len(limitations) > 8:
        raise MetaModelUnavailable("Meta Model API returned invalid limitations.")

    normalized_actions: list[dict[str, str]] = []
    for action in actions:
        if not isinstance(action, dict):
            raise MetaModelUnavailable("Meta Model API returned an invalid action.")
        finding_id = action.get("finding_id")
        if not isinstance(finding_id, str) or finding_id not in allowed_finding_ids:
            raise MetaModelUnavailable("Meta Model API referenced an unknown finding.")
        fields = {key: action.get(key) for key in ("why_it_matters", "next_step", "uncertainty")}
        if any(
            not isinstance(value, str) or not value.strip() or len(value) > 700
            for value in fields.values()
        ):
            raise MetaModelUnavailable("Meta Model API returned an invalid action description.")
        normalized_actions.append({"finding_id": finding_id, **fields})

    if any(
        not isinstance(item, str) or not item.strip() or len(item) > 500 for item in limitations
    ):
        raise MetaModelUnavailable("Meta Model API returned an invalid limitation.")
    return {
        "summary": summary.strip(),
        "actions": normalized_actions,
        "limitations": [item.strip() for item in limitations],
        "model": META_MODEL_ID,
        "mode": "STANDARD",
        "external_actions_taken": False,
    }
