"""Consent vocabulary and deterministic purpose/category policy.

This module is deliberately independent of persistence and HTTP frameworks.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from myeconomy.domain.errors import ConsentScopeError


class ConsentPurpose(StrEnum):
    HOUSEHOLD_SHARING = "household_sharing"
    COMMONS_AGGREGATION = "commons_aggregation"
    OPPORTUNITY_MATCHING = "opportunity_matching"
    BENEFITS_DISCOVERY = "benefits_discovery"
    PARTNER_OFFER_PERSONALIZATION = "partner_offer_personalization"
    RESEARCH_PARTICIPATION = "research_participation"
    SUPPORT_CASE_PROCESSING = "support_case_processing"
    ECONOMIC_DEFENCE = "economic_defence"
    ENTERPRISE_ASSISTANCE = "enterprise_assistance"
    AI_ASSISTANCE = "ai_assistance"


class DataCategory(StrEnum):
    FINANCIAL_SUMMARY = "financial_summary"
    TRANSACTION_RECORDS = "transaction_records"
    HOUSEHOLD_OBLIGATIONS = "household_obligations"
    PROFILE = "profile"
    SKILLS = "skills"
    AVAILABILITY = "availability"
    COARSE_LOCATION = "coarse_location"
    BENEFIT_DOCUMENTS = "benefit_documents"
    SUPPORT_CASE_EVIDENCE = "support_case_evidence"
    CONTACT_INFORMATION = "contact_information"
    BUSINESS_RECORDS = "business_records"


class RecipientType(StrEnum):
    SERVICE = "service"
    HOUSEHOLD = "household"
    PARTNER = "partner"
    RESEARCH = "research"


_ALLOWED_CATEGORIES: dict[ConsentPurpose, frozenset[DataCategory]] = {
    ConsentPurpose.HOUSEHOLD_SHARING: frozenset(
        {
            DataCategory.FINANCIAL_SUMMARY,
            DataCategory.TRANSACTION_RECORDS,
            DataCategory.HOUSEHOLD_OBLIGATIONS,
            DataCategory.PROFILE,
            DataCategory.SKILLS,
            DataCategory.AVAILABILITY,
        }
    ),
    ConsentPurpose.COMMONS_AGGREGATION: frozenset(
        {
            DataCategory.FINANCIAL_SUMMARY,
            DataCategory.HOUSEHOLD_OBLIGATIONS,
            DataCategory.SKILLS,
            DataCategory.COARSE_LOCATION,
        }
    ),
    ConsentPurpose.OPPORTUNITY_MATCHING: frozenset(
        {
            DataCategory.PROFILE,
            DataCategory.SKILLS,
            DataCategory.AVAILABILITY,
            DataCategory.COARSE_LOCATION,
        }
    ),
    ConsentPurpose.BENEFITS_DISCOVERY: frozenset(
        {
            DataCategory.PROFILE,
            DataCategory.FINANCIAL_SUMMARY,
            DataCategory.HOUSEHOLD_OBLIGATIONS,
            DataCategory.BENEFIT_DOCUMENTS,
            DataCategory.COARSE_LOCATION,
        }
    ),
    ConsentPurpose.PARTNER_OFFER_PERSONALIZATION: frozenset(
        {
            DataCategory.FINANCIAL_SUMMARY,
            DataCategory.HOUSEHOLD_OBLIGATIONS,
            DataCategory.COARSE_LOCATION,
        }
    ),
    ConsentPurpose.RESEARCH_PARTICIPATION: frozenset(
        {
            DataCategory.FINANCIAL_SUMMARY,
            DataCategory.SKILLS,
            DataCategory.COARSE_LOCATION,
        }
    ),
    ConsentPurpose.SUPPORT_CASE_PROCESSING: frozenset(
        {
            DataCategory.PROFILE,
            DataCategory.TRANSACTION_RECORDS,
            DataCategory.HOUSEHOLD_OBLIGATIONS,
            DataCategory.SUPPORT_CASE_EVIDENCE,
            DataCategory.CONTACT_INFORMATION,
        }
    ),
    ConsentPurpose.ECONOMIC_DEFENCE: frozenset(
        {
            DataCategory.PROFILE,
            DataCategory.TRANSACTION_RECORDS,
            DataCategory.SUPPORT_CASE_EVIDENCE,
            DataCategory.CONTACT_INFORMATION,
        }
    ),
    ConsentPurpose.ENTERPRISE_ASSISTANCE: frozenset(
        {
            DataCategory.PROFILE,
            DataCategory.SKILLS,
            DataCategory.AVAILABILITY,
            DataCategory.BUSINESS_RECORDS,
        }
    ),
    ConsentPurpose.AI_ASSISTANCE: frozenset(
        {DataCategory.FINANCIAL_SUMMARY, DataCategory.HOUSEHOLD_OBLIGATIONS}
    ),
}

_REQUIRED_RECIPIENT_TYPES: dict[ConsentPurpose, RecipientType] = {
    ConsentPurpose.HOUSEHOLD_SHARING: RecipientType.HOUSEHOLD,
    ConsentPurpose.COMMONS_AGGREGATION: RecipientType.SERVICE,
    ConsentPurpose.OPPORTUNITY_MATCHING: RecipientType.SERVICE,
    ConsentPurpose.BENEFITS_DISCOVERY: RecipientType.SERVICE,
    ConsentPurpose.PARTNER_OFFER_PERSONALIZATION: RecipientType.PARTNER,
    ConsentPurpose.RESEARCH_PARTICIPATION: RecipientType.RESEARCH,
    ConsentPurpose.SUPPORT_CASE_PROCESSING: RecipientType.SERVICE,
    ConsentPurpose.ECONOMIC_DEFENCE: RecipientType.SERVICE,
    ConsentPurpose.ENTERPRISE_ASSISTANCE: RecipientType.SERVICE,
    ConsentPurpose.AI_ASSISTANCE: RecipientType.SERVICE,
}


def validate_consent_scope(
    *,
    purpose: ConsentPurpose,
    categories: list[DataCategory],
    recipient_type: RecipientType,
    recipient_id: str,
) -> None:
    """Reject over-broad or purpose-incompatible consent before persistence."""
    if not categories:
        raise ConsentScopeError("At least one data category must be selected.")
    if len(categories) != len(set(categories)):
        raise ConsentScopeError("Data categories must not contain duplicates.")
    if recipient_type != _REQUIRED_RECIPIENT_TYPES[purpose]:
        raise ConsentScopeError(
            f"Purpose '{purpose.value}' requires recipient type "
            f"'{_REQUIRED_RECIPIENT_TYPES[purpose].value}'."
        )

    disallowed = set(categories) - _ALLOWED_CATEGORIES[purpose]
    if disallowed:
        names = ", ".join(sorted(item.value for item in disallowed))
        raise ConsentScopeError(
            f"Purpose '{purpose.value}' cannot authorize these data categories: {names}."
        )

    normalized_recipient = recipient_id.strip()
    if not normalized_recipient or len(normalized_recipient) > 128:
        raise ConsentScopeError("A valid, bounded recipient identifier is required.")
    if purpose == ConsentPurpose.COMMONS_AGGREGATION and normalized_recipient != "commons":
        raise ConsentScopeError("Commons aggregation must target the 'commons' service.")
    if purpose == ConsentPurpose.AI_ASSISTANCE and normalized_recipient != "meta-model-api":
        raise ConsentScopeError("AI assistance must target the 'meta-model-api' service.")


@dataclass(frozen=True)
class ConsentTerms:
    purpose: ConsentPurpose
    version: str
    title: str
    summary: str
    revocation_note: str


CONSENT_TERMS_VERSION = "2026-11-03.1"
_CONSENT_TERMS: dict[ConsentPurpose, ConsentTerms] = {
    ConsentPurpose.HOUSEHOLD_SHARING: ConsentTerms(
        purpose=ConsentPurpose.HOUSEHOLD_SHARING,
        version=CONSENT_TERMS_VERSION,
        title="Share selected information with this household",
        summary=(
            "Authorize the named household to access only the data categories you select. "
            "Household membership by itself never grants access to personal or financial records."
        ),
        revocation_note=(
            "Revocation blocks future access through this system. It cannot automatically recall "
            "information already disclosed to another household member."
        ),
    ),
    ConsentPurpose.COMMONS_AGGREGATION: ConsentTerms(
        purpose=ConsentPurpose.COMMONS_AGGREGATION,
        version=CONSENT_TERMS_VERSION,
        title="Contribute selected signals to the Commons network",
        summary=(
            "Authorize the Commons service to use selected summary, obligation, skill or coarse "
            "location categories to discover group opportunities. Raw transaction records, contact "
            "details and support documents are not allowed in this purpose."
        ),
        revocation_note=(
            "Revocation blocks future inclusion/access. Previously created aggregates may not be "
            "individually reversible; no Commons transmission is implemented in this iteration."
        ),
    ),
    ConsentPurpose.OPPORTUNITY_MATCHING: ConsentTerms(
        purpose=ConsentPurpose.OPPORTUNITY_MATCHING,
        version=CONSENT_TERMS_VERSION,
        title="Use selected skills and availability to find opportunities",
        summary=(
            "Authorize the opportunity service to match the selected profile, skills, availability "
            "and/or coarse location categories. It does not authorize employers or clients to see "
            "your private profile automatically."
        ),
        revocation_note=(
            "Revocation blocks future matching with this grant; submitted applications "
            "are separate actions."
        ),
    ),
    ConsentPurpose.BENEFITS_DISCOVERY: ConsentTerms(
        purpose=ConsentPurpose.BENEFITS_DISCOVERY,
        version=CONSENT_TERMS_VERSION,
        title="Use selected information to discover benefits",
        summary=(
            "Authorize the benefits service to evaluate selected profile, financial summary, "
            "household obligation, benefit document and/or coarse location categories "
            "for discovery. "
            "This does not submit an application or confirm eligibility."
        ),
        revocation_note=(
            "Revocation blocks future discovery access; an application already submitted "
            "is a separate record/action."
        ),
    ),
    ConsentPurpose.PARTNER_OFFER_PERSONALIZATION: ConsentTerms(
        purpose=ConsentPurpose.PARTNER_OFFER_PERSONALIZATION,
        version=CONSENT_TERMS_VERSION,
        title="Share selected signals with a named partner for offers",
        summary=(
            "Authorize only the named partner to use selected financial summary, household "
            "obligation "
            "and/or coarse location categories for offer personalization. No raw transactions or "
            "contact details are allowed in this purpose."
        ),
        revocation_note=(
            "Revocation blocks future access through this system; the partner may retain "
            "information already received under its own lawful retention rules."
        ),
    ),
    ConsentPurpose.RESEARCH_PARTICIPATION: ConsentTerms(
        purpose=ConsentPurpose.RESEARCH_PARTICIPATION,
        version=CONSENT_TERMS_VERSION,
        title="Contribute limited information to a named research programme",
        summary=(
            "Authorize only the named research programme to use selected financial summary, skills "
            "and/or coarse location categories. Raw transaction records and direct contact details "
            "are not allowed. Any aggregation or de-identification must be implemented "
            "and verified "
            "before data leaves the personal boundary."
        ),
        revocation_note=(
            "Revocation blocks future contributions; previously released aggregate research "
            "outputs may not be individually reversible."
        ),
    ),
    ConsentPurpose.SUPPORT_CASE_PROCESSING: ConsentTerms(
        purpose=ConsentPurpose.SUPPORT_CASE_PROCESSING,
        version=CONSENT_TERMS_VERSION,
        title="Use selected information to prepare a support case",
        summary=(
            "Authorize the support service to process only the selected profile, transaction, "
            "household obligation, evidence and/or contact categories for the named case workflow. "
            "Submitting or contacting an external party still requires separate approval."
        ),
        revocation_note=(
            "Revocation blocks future case processing through this grant; already submitted "
            "material cannot be recalled automatically."
        ),
    ),
    ConsentPurpose.ECONOMIC_DEFENCE: ConsentTerms(
        purpose=ConsentPurpose.ECONOMIC_DEFENCE,
        version=CONSENT_TERMS_VERSION,
        title="Use selected information to help protect against economic risk",
        summary=(
            "Authorize the named economic-defence service to analyze selected profile, "
            "transaction, "
            "evidence and/or contact categories for suspicious activity and user protection. The "
            "system will distinguish indicators from verified fraud."
        ),
        revocation_note=(
            "Revocation blocks future analysis under this grant; it does not delete records "
            "you keep in your own account."
        ),
    ),
    ConsentPurpose.ENTERPRISE_ASSISTANCE: ConsentTerms(
        purpose=ConsentPurpose.ENTERPRISE_ASSISTANCE,
        version=CONSENT_TERMS_VERSION,
        title="Use selected information to support your enterprise",
        summary=(
            "Authorize the named enterprise service to use selected profile, skills, availability "
            "and/or business-record categories to assist with planning and operations. External "
            "orders, payments, messages and contracts require separate authorization."
        ),
        revocation_note=(
            "Revocation blocks future enterprise-service access under this grant; completed "
            "external transactions remain separate."
        ),
    ),
    ConsentPurpose.AI_ASSISTANCE: ConsentTerms(
        purpose=ConsentPurpose.AI_ASSISTANCE,
        version="2026-11-04.1",
        title="Use a minimized report summary for optional Meta AI assistance",
        summary=(
            "Authorize AwnNORA to send only aggregate financial totals, essential-obligation "
            "totals and system-generated finding labels/text from the selected Personal Power "
            "Report to the Meta Model API "
            "using Muse Spark Standard mode. The request excludes names, account IDs, transaction "
            "rows, counterparties, contact details, uploaded documents and raw evidence. "
            "Contributor mode is not used. Model output is explanatory and cannot change records, "
            "calculate money, approve actions or contact providers."
        ),
        revocation_note=(
            "Revocation blocks future Meta assistance requests. It cannot recall a request already "
            "sent to the provider; AwnNORA uses store=false and does not persist the model prompt."
        ),
    ),
}


def get_consent_terms(purpose: ConsentPurpose) -> ConsentTerms:
    return _CONSENT_TERMS[purpose]


def list_consent_terms() -> list[ConsentTerms]:
    return [_CONSENT_TERMS[purpose] for purpose in ConsentPurpose]


def allowed_categories_for_purpose(purpose: ConsentPurpose) -> frozenset[DataCategory]:
    return _ALLOWED_CATEGORIES[purpose]


def required_recipient_type(purpose: ConsentPurpose) -> RecipientType:
    return _REQUIRED_RECIPIENT_TYPES[purpose]
