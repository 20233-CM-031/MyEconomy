#!/usr/bin/env python3
"""Generate a deterministic, linked, India-oriented synthetic economic demo dataset.

No real customer data is read. All identifiers, names and contacts are fabricated.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import shutil
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

AS_OF = date(2026, 11, 3)
START = date(2026, 1, 1)
END = date(2026, 10, 31)
SEED_DEFAULT = 20261103

FIRST_NAMES = ["Aarav", "Aanya", "Aarohi", "Adil", "Aisha", "Akash", "Amara", "Arjun", "Diya", "Farhan", "Fatima", "Harsh", "Ibrahim", "Ishita", "Kabir", "Kavya", "Meera", "Mira", "Neha", "Nikhil", "Nisha", "Pranav", "Rahul", "Riya", "Sana", "Sara", "Sameer", "Tanvi", "Varun", "Zoya", "Yusuf", "Rehan", "Anaya", "Dev", "Imran", "Jhanvi", "Kiran", "Manav", "Noor", "Omar"]
LAST_NAMES = ["Mehta", "Reddy", "Khan", "Sharma", "Iyer", "Patel", "Das", "Rao", "Shaikh", "Nair", "Kapoor", "Verma", "Fernandes", "Joshi", "Kulkarni", "Ahmed", "Thomas", "Bhat", "Gupta", "Mishra", "Qureshi", "Menon", "Pillai", "D'Souza"]
CITY_ZONES = {
    "Hyderabad": ["West Hyderabad Cluster", "Central Hyderabad Cluster", "Secunderabad Cluster", "South Hyderabad Cluster"],
    "Bengaluru": ["East Bengaluru Cluster", "Central Bengaluru Cluster", "North Bengaluru Cluster"],
    "Pune": ["West Pune Cluster", "Central Pune Cluster", "East Pune Cluster"],
    "Chennai": ["South Chennai Cluster", "Central Chennai Cluster"],
    "Mumbai": ["Western Mumbai Cluster", "Central Mumbai Cluster"],
    "Jaipur": ["Central Jaipur Cluster", "North Jaipur Cluster"],
    "Lucknow": ["Central Lucknow Cluster", "East Lucknow Cluster"],
    "Kolkata": ["South Kolkata Cluster", "Central Kolkata Cluster"],
}
PERSONAS = ["SALARIED_EMPLOYEE", "GIG_WORKER", "SMALL_MERCHANT", "STUDENT_ADULT", "FREELANCER", "HOMEMAKER", "SELF_EMPLOYED_PROFESSIONAL"]
LANGUAGES = ["Telugu", "Hindi", "English", "Urdu", "Kannada", "Tamil", "Marathi", "Bengali"]
CATEGORIES = ["groceries", "rent", "electricity", "internet", "mobile", "transport", "fuel", "healthcare", "education", "dining", "shopping", "insurance", "utilities", "personal_care"]

TABLES: dict[str, list[dict[str, Any]]] = {}


def money(value: Decimal | int | float | str) -> str:
    return str(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def iso_dt(d: date, hour: int = 12) -> str:
    return datetime(d.year, d.month, d.day, hour, 0, tzinfo=timezone.utc).isoformat()


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def make_id(prefix: str, n: int, width: int = 5) -> str:
    return f"{prefix}{n:0{width}d}"


def choose_month_day(rng: random.Random, month: int, day_min: int = 1, day_max: int = 26) -> date:
    return date(2026, month, rng.randint(day_min, min(day_max, 28)))


def month_range() -> list[int]:
    return list(range(1, 11))


def make_providers() -> list[dict[str, Any]]:
    kinds = ["UTILITY", "TELECOM", "EDUCATION", "HEALTHCARE", "GROCERY", "TRANSPORT", "SKILL_TRAINING", "EQUIPMENT", "LOCAL_SERVICES"]
    rows = []
    for i in range(1, 36):
        kind = kinds[(i - 1) % len(kinds)]
        city = list(CITY_ZONES)[(i - 1) % len(CITY_ZONES)]
        rows.append({
            "provider_id": make_id("PRV", i),
            "provider_name": f"Demo {kind.replace('_', ' ').title()} Partner {i:02d}",
            "provider_type": kind,
            "service_city": city,
            "service_zone": CITY_ZONES[city][(i - 1) % len(CITY_ZONES[city])],
            "verification_status": "DEMO_VERIFIED_FIXTURE" if i % 5 else "PENDING_DEMO_REVIEW",
            "partner_status": "SIMULATED_PARTNER",
            "settlement_currency": "INR",
            "data_class": "SYNTHETIC_FIXTURE",
        })
    return rows


def generate(out_dir: Path, customers_count: int, seed: int) -> dict[str, Any]:
    rng = random.Random(seed)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    for sub in ["csv", "jsonl", "json", "sql", "source_documents/invoices", "source_documents/offer_terms", "api_scenarios", "metadata"]:
        (out_dir / sub).mkdir(parents=True, exist_ok=True)

    # Customer base and households
    customers: list[dict[str, Any]] = []
    households: list[dict[str, Any]] = []
    memberships: list[dict[str, Any]] = []
    customer_household: dict[str, str] = {}
    customer_attrs: dict[str, dict[str, Any]] = {}
    idx = 1
    hh_idx = 1
    while idx <= customers_count:
        size = min(rng.choices([1, 2, 3, 4], weights=[22, 43, 25, 10])[0], customers_count - idx + 1)
        hh_id = make_id("HH", hh_idx)
        city = rng.choice(list(CITY_ZONES))
        zone = rng.choice(CITY_ZONES[city])
        household_type = rng.choice(["SINGLE_ADULT", "COUPLE", "FAMILY_WITH_CHILDREN", "SHARED_ADULTS", "EXTENDED_FAMILY"])
        members = []
        for _ in range(size):
            cid = make_id("CUS", idx)
            persona = rng.choices(PERSONAS, weights=[38, 14, 10, 8, 12, 7, 11])[0]
            age = rng.randint(21, 64)
            income_mid = {
                "SALARIED_EMPLOYEE": rng.randint(28000, 125000),
                "GIG_WORKER": rng.randint(12000, 60000),
                "SMALL_MERCHANT": rng.randint(22000, 150000),
                "STUDENT_ADULT": rng.randint(4000, 20000),
                "FREELANCER": rng.randint(18000, 110000),
                "HOMEMAKER": rng.randint(0, 12000),
                "SELF_EMPLOYED_PROFESSIONAL": rng.randint(30000, 180000),
            }[persona]
            fname = FIRST_NAMES[(idx * 7 + rng.randrange(len(FIRST_NAMES))) % len(FIRST_NAMES)]
            lname = LAST_NAMES[(idx * 11 + rng.randrange(len(LAST_NAMES))) % len(LAST_NAMES)]
            goal = rng.choice(["REDUCE_MONTHLY_COSTS", "EDUCATION_FUND", "EMERGENCY_BUFFER", "INCREASE_INCOME", "START_SMALL_BUSINESS", "HEALTHCARE_PLANNING", "DEBT_REPAYMENT"])
            pressure = rng.choices(["STABLE", "TIGHT_CASHFLOW", "EDUCATION_EXPENSE", "HEALTHCARE_EXPENSE", "INCOME_VOLATILITY"], weights=[48, 22, 11, 9, 10])[0]
            row = {
                "customer_id": cid,
                "display_name": f"{fname} {lname}",
                "email": f"{cid.lower()}@example.invalid",
                "phone": f"+91-00000-{idx:05d}",
                "age_years": age,
                "age_band": "21-29" if age < 30 else "30-39" if age < 40 else "40-49" if age < 50 else "50-64",
                "city": city,
                "locality_cluster": zone,
                "persona": persona,
                "employment_status": "STUDENT" if persona == "STUDENT_ADULT" else "SELF_EMPLOYED" if persona in ["GIG_WORKER", "SMALL_MERCHANT", "FREELANCER", "SELF_EMPLOYED_PROFESSIONAL"] else "HOMEMAKER" if persona == "HOMEMAKER" else "EMPLOYED",
                "primary_language": rng.choice(LANGUAGES),
                "monthly_income_inr_estimate": money(income_mid),
                "income_volatility": "HIGH" if persona in ["GIG_WORKER", "SMALL_MERCHANT", "FREELANCER"] else "MEDIUM" if persona == "SELF_EMPLOYED_PROFESSIONAL" else "LOW",
                "dependants_count": rng.choices([0, 1, 2, 3, 4], [22, 18, 35, 18, 7])[0],
                "primary_goal": goal,
                "economic_context": pressure,
                "kyc_status_fixture": rng.choice(["NOT_COLLECTED", "DEMO_PENDING", "DEMO_STATUS_ONLY"]),
                "identity_document_status": "NO_REAL_ID_DOCUMENTS_IN_FIXTURE",
                "account_status": "ACTIVE" if rng.random() > 0.04 else "LIMITED_DEMO",
                "synthetic": True,
                "data_class": "SYNTHETIC_FIXTURE",
            }
            customers.append(row)
            customer_attrs[cid] = {**row, "household_id": hh_id}
            customer_household[cid] = hh_id
            members.append(cid)
            idx += 1
        households.append({
            "household_id": hh_id,
            "display_label": f"Demo Household {hh_idx:03d}",
            "city": city,
            "locality_cluster": zone,
            "household_type": household_type,
            "member_count": len(members),
            "owner_customer_id": members[0],
            "shared_financial_profile_enabled": False,
            "data_class": "SYNTHETIC_FIXTURE",
        })
        for j, cid in enumerate(members):
            memberships.append({
                "membership_id": f"HMB-{hh_idx:04d}-{j+1:02d}",
                "household_id": hh_id,
                "customer_id": cid,
                "role": "OWNER" if j == 0 else "MEMBER",
                "status": "ACTIVE",
                "joined_at": iso_dt(date(2026, 1, rng.randint(1, 25))),
                "financial_data_access": "NOT_GRANTED_BY_MEMBERSHIP",
                "data_class": "SYNTHETIC_FIXTURE",
            })
        hh_idx += 1

    providers = make_providers()
    provider_by_type: dict[str, list[str]] = defaultdict(list)
    for p in providers:
        provider_by_type[p["provider_type"]].append(p["provider_id"])

    # Accounts
    accounts: list[dict[str, Any]] = []
    account_ids: dict[str, dict[str, str]] = {}
    aidx = 1
    for c in customers:
        cid = c["customer_id"]
        primary = make_id("ACC", aidx); aidx += 1
        accounts.append({"account_id": primary, "customer_id": cid, "institution_code": f"DEMO-BANK-{(aidx % 7)+1:02d}", "account_type": "BANK_DEPOSIT", "currency": "INR", "masked_reference": f"SYNTH-ACCT-{aidx:06d}", "account_status": "ACTIVE", "opening_balance_inr": money(rng.randint(8000, 160000)), "balance_semantics": "DEMO_OPENING_BALANCE_ONLY", "data_class": "SYNTHETIC_FIXTURE"})
        ids = {"bank": primary}
        if rng.random() < 0.48:
            ids["wallet"] = make_id("ACC", aidx); accounts.append({"account_id": ids["wallet"], "customer_id": cid, "institution_code": "DEMO-UPI-WALLET", "account_type": "UPI_WALLET", "currency": "INR", "masked_reference": f"SYNTH-WALLET-{aidx:06d}", "account_status": "ACTIVE", "opening_balance_inr": money(rng.randint(500, 12000)), "balance_semantics": "DEMO_OPENING_BALANCE_ONLY", "data_class": "SYNTHETIC_FIXTURE"}); aidx += 1
        if rng.random() < 0.42:
            ids["card"] = make_id("ACC", aidx); accounts.append({"account_id": ids["card"], "customer_id": cid, "institution_code": "DEMO-CARD-ISSUER", "account_type": "CREDIT_CARD", "currency": "INR", "masked_reference": f"SYNTH-CARD-{aidx:06d}", "account_status": "ACTIVE", "opening_balance_inr": "0.00", "balance_semantics": "OUTSTANDING_LIABILITY_FIXTURE", "data_class": "SYNTHETIC_FIXTURE"}); aidx += 1
        account_ids[cid] = ids

    # Explicit consents: only consented customers generate Commons signals.
    consents: list[dict[str, Any]] = []
    active_consent: dict[tuple[str, str], bool] = {}
    purposes = [
        ("PERSONAL_FINANCIAL_ANALYSIS", ["USER_SUBMITTED_FINANCIAL_ENTRIES"]),
        ("BENEFIT_MATCHING", ["PROFILE_ATTRIBUTES", "BENEFIT_REQUIREMENTS"]),
        ("OPPORTUNITY_MATCHING", ["SKILLS", "AVAILABILITY", "CITY_CLUSTER"]),
        ("PARTNER_OFFER_MATCHING", ["SERVICE_CATEGORY", "CITY_CLUSTER", "PRICE_BAND"]),
        ("COMMONS_DEMAND_AGGREGATION", ["SERVICE_CATEGORY", "CITY_CLUSTER", "QUANTITY_BAND"]),
        ("RESEARCH_AGGREGATION", ["DEIDENTIFIED_AGGREGATE_OUTCOME"]),
        ("RESOURCE_EXCHANGE_LISTING", ["RESOURCE_TYPE", "CITY_CLUSTER", "CAPACITY_BAND"]),
    ]
    consent_idx = 1
    for c in customers:
        cid = c["customer_id"]
        for purpose, scopes in purposes:
            probability = {"PERSONAL_FINANCIAL_ANALYSIS": .88, "BENEFIT_MATCHING": .72, "OPPORTUNITY_MATCHING": .70, "PARTNER_OFFER_MATCHING": .48, "COMMONS_DEMAND_AGGREGATION": .55, "RESEARCH_AGGREGATION": .20, "RESOURCE_EXCHANGE_LISTING": .30}[purpose]
            granted = rng.random() < probability
            revoked = granted and rng.random() < (0.10 if purpose != "COMMONS_DEMAND_AGGREGATION" else 0.16)
            status = "REVOKED" if revoked else "GRANTED" if granted else "NOT_GRANTED"
            grant_date = date(2026, rng.randint(1, 9), rng.randint(1, 25)) if granted else None
            revoked_date = date(2026, 10, rng.randint(1, 28)) if revoked else None
            consents.append({
                "consent_id": make_id("CNS", consent_idx), "customer_id": cid,
                "purpose": purpose, "data_categories_json": compact_json(scopes),
                "recipient": "MYECONOMY_PERSONAL_SERVICE" if purpose.startswith("PERSONAL") else "DEMO_MATCHING_ENGINE" if purpose in ["BENEFIT_MATCHING", "OPPORTUNITY_MATCHING"] else "DEMO_PARTNER_ROUTER" if purpose == "PARTNER_OFFER_MATCHING" else "DEMO_COMMONS_AGGREGATOR" if purpose == "COMMONS_DEMAND_AGGREGATION" else "DEMO_RESEARCH_PIPELINE",
                "status": status, "granted_at": iso_dt(grant_date) if grant_date else "",
                "expires_at": iso_dt(grant_date + timedelta(days=180)) if grant_date else "",
                "revoked_at": iso_dt(revoked_date) if revoked_date else "",
                "notice_version": "SYNTHETIC_NOTICE_V1", "consent_receipt": f"SYNTH-CONSENT-{consent_idx:06d}",
                "withdrawal_channel": "DEMO_SETTINGS_SCREEN", "data_class": "SYNTHETIC_FIXTURE",
            })
            expires_on = grant_date + timedelta(days=180) if grant_date else None
            revoked_before_asof = bool(revoked_date and revoked_date <= AS_OF)
            expired_asof = bool(expires_on and expires_on < AS_OF)
            status = "REVOKED" if revoked_before_asof else "EXPIRED" if expired_asof else "GRANTED" if granted else "NOT_GRANTED"
            consents[-1]["status"] = status
            active_consent[(cid, purpose)] = status == "GRANTED"
            event_day = date(2026, 10, 20)
            active_consent[(cid, purpose, "2026-10-20")] = bool(granted and grant_date <= event_day and (expires_on is None or expires_on >= event_day) and (revoked_date is None or revoked_date > event_day))
            consent_idx += 1

    # Obligations
    obligations: list[dict[str, Any]] = []
    obligation_map: dict[str, list[dict[str, Any]]] = defaultdict(list)
    oid = 1
    for c in customers:
        cid = c["customer_id"]
        monthly = Decimal(c["monthly_income_inr_estimate"])
        candidates = [
            ("RENT", "HOUSING", monthly * Decimal(str(rng.uniform(.12, .28))), "DEMO-LOCAL-LESSOR", 5),
            ("ELECTRICITY", "UTILITY", Decimal(rng.randint(650, 2600)), "DEMO-POWER-UTILITY", 12),
            ("INTERNET", "TELECOM", Decimal(rng.randint(499, 1299)), "DEMO-BROADBAND", 18),
            ("MOBILE", "TELECOM", Decimal(rng.randint(199, 799)), "DEMO-MOBILE", 20),
            ("EDUCATION_FEE", "EDUCATION", Decimal(rng.randint(0, 9500)), "DEMO-EDU-PROVIDER", 8),
        ]
        for kind, category, amount, vendor, due_day in candidates:
            if amount <= 0 or (kind == "EDUCATION_FEE" and rng.random() < .6):
                continue
            row = {"obligation_id": make_id("OBL", oid), "customer_id": cid, "obligation_type": kind, "category": category, "payee_label": vendor, "expected_amount_inr": money(amount), "frequency": "MONTHLY", "due_day": due_day, "autopay_enabled": rng.random() < .35, "essential": kind in ["RENT", "ELECTRICITY", "INTERNET", "MOBILE", "EDUCATION_FEE"], "status": "ACTIVE", "first_due_date": "2026-01-01", "data_class": "SYNTHETIC_FIXTURE"}
            obligations.append(row); obligation_map[cid].append(row); oid += 1

    # Loans and schedules
    loans: list[dict[str, Any]] = []
    installments: list[dict[str, Any]] = []
    loans_by_customer: dict[str, list[dict[str, Any]]] = defaultdict(list)
    lidx = 1; inst_idx = 1
    for c in customers:
        if rng.random() > .36:
            continue
        cid = c["customer_id"]
        principal = Decimal(rng.randrange(40000, 800001, 1000))
        annual_rate = Decimal(str(round(rng.uniform(9.5, 19.5), 2)))
        tenure = rng.choice([12, 18, 24, 36, 48])
        monthly_rate = annual_rate / Decimal(1200)
        growth = (Decimal(1) + monthly_rate) ** tenure
        emi_unrounded = principal * monthly_rate * growth / (growth - Decimal(1))
        emi = emi_unrounded.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        start_month = rng.randint(1, 4)
        outstanding = principal
        schedule_rows = []
        for m in range(start_month, 11):
            due = date(2026, m, 5)
            interest = (outstanding * monthly_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            principal_component = min(outstanding, max(Decimal("0"), emi - interest))
            total_due = principal_component + interest
            outstanding = max(Decimal("0"), outstanding - principal_component)
            status = "PAID" if due.month <= 9 or rng.random() > .16 else "LATE"
            if due.month == 10 and rng.random() < .15: status = "PENDING_DEMO"
            paid_date = (due + timedelta(days=rng.randint(0, 5))).isoformat() if status in ["PAID", "LATE"] else ""
            schedule_rows.append({"installment_id": make_id("INS", inst_idx), "loan_id": make_id("LON", lidx), "customer_id": cid, "installment_number": m-start_month+1, "due_date": due.isoformat(), "principal_component_inr": money(principal_component), "interest_component_inr": money(interest), "total_due_inr": money(total_due), "status": status, "paid_date": paid_date, "late_fee_inr": money(rng.choice([0, 0, 0, 150, 250]) if status == "LATE" else 0), "data_class": "SYNTHETIC_FIXTURE"}); inst_idx += 1
        loan = {"loan_id": make_id("LON", lidx), "customer_id": cid, "loan_type": rng.choice(["PERSONAL_LOAN", "VEHICLE_LOAN", "EDUCATION_LOAN", "SMALL_BUSINESS_LOAN"]), "lender_label": f"DEMO-LENDER-{rng.randint(1,8):02d}", "principal_inr": money(principal), "annual_interest_rate_percent": str(annual_rate), "tenure_months": tenure, "emi_inr": money(emi), "start_date": date(2026, start_month, 5).isoformat(), "loan_status": "ACTIVE", "remaining_principal_fixture_inr": money(outstanding), "secured_status": "UNSECURED_FIXTURE" if "PERSONAL" in "PERSONAL_LOAN" else "DEMO_CLASSIFICATION", "data_class": "SYNTHETIC_FIXTURE"}
        loans.append(loan); loans_by_customer[cid].append(loan); installments.extend(schedule_rows)
        lidx += 1

    # Subscriptions
    subscriptions: list[dict[str, Any]] = []
    sub_by_customer: dict[str, list[dict[str, Any]]] = defaultdict(list)
    sidx = 1
    for c in customers:
        if rng.random() < .60:
            for _ in range(rng.choice([1, 1, 2])):
                sub = {"subscription_id": make_id("SUB", sidx), "customer_id": c["customer_id"], "service_name": rng.choice(["DEMO-MUSIC-PLAN", "DEMO-VIDEO-PLAN", "DEMO-CLOUD-STORAGE", "DEMO-LEARNING-APP", "DEMO-NEWS-PLAN", "DEMO-PRODUCTIVITY-APP"]), "billing_cycle": "MONTHLY", "current_price_inr": money(rng.choice([99, 149, 199, 299, 399, 499, 699])), "start_date": date(2025, rng.randint(1, 12), 10).isoformat(), "next_renewal_date": date(2026, 11, rng.randint(5, 25)).isoformat(), "status": rng.choice(["ACTIVE", "ACTIVE", "CANCELLED", "TRIAL_FIXTURE"]), "auto_renew": rng.choice([True, True, False]), "price_change_flag": rng.random() < .18, "price_before_change_inr": money(rng.randint(79, 449)), "cancellation_channel": "DEMO_SETTINGS" if rng.random() < .5 else "PROVIDER_PORTAL_FIXTURE", "data_class": "SYNTHETIC_FIXTURE"}
                subscriptions.append(sub); sub_by_customer[c["customer_id"]].append(sub); sidx += 1

    # Providers, benefit catalogues and opportunities
    benefits = [
        ("DEMO-EDU-001", "Education Fee Support Pilot", "EDUCATION", 65000, {"persona_any": ["SALARIED_EMPLOYEE", "GIG_WORKER", "STUDENT_ADULT", "HOMEMAKER"], "income_max": 90000, "dependants_min": 1}),
        ("DEMO-HEALTH-001", "Unexpected Medical Expense Pilot", "HEALTHCARE", 40000, {"healthcare_expense_flag": True, "income_max": 85000}),
        ("DEMO-SKILL-001", "Skill Certification Voucher Pilot", "SKILL_TRAINING", 12000, {"age_min": 18, "income_max": 70000}),
        ("DEMO-MICRO-001", "Micro Enterprise Equipment Pilot", "ENTERPRISE", 50000, {"persona_any": ["SMALL_MERCHANT", "SELF_EMPLOYED_PROFESSIONAL"], "income_max": 140000}),
        ("DEMO-ENERGY-001", "Household Utility Relief Pilot", "UTILITIES", 9000, {"income_max": 50000}),
        ("DEMO-CARE-001", "Caregiver Support Pilot", "CARE", 18000, {"dependants_min": 2}),
        ("DEMO-WORK-001", "Work Transition Support Pilot", "EMPLOYMENT", 25000, {"economic_context_any": ["INCOME_VOLATILITY", "TIGHT_CASHFLOW"]}),
        ("DEMO-TRANSPORT-001", "Mobility Access Pilot", "TRANSPORT", 8000, {"income_max": 65000}),
        ("DEMO-FOOD-001", "Food Essentials Coupon Pilot", "GROCERIES", 5000, {"income_max": 45000}),
        ("DEMO-DIGITAL-001", "Digital Access Support Pilot", "TELECOM", 6000, {"income_max": 60000}),
        ("DEMO-HOUSING-001", "Housing Deposit Assistance Pilot", "HOUSING", 30000, {"income_max": 75000, "dependants_min": 1}),
        ("DEMO-START-001", "Starter Business Mentoring Pilot", "ENTERPRISE", 15000, {"persona_any": ["SMALL_MERCHANT", "FREELANCER", "SELF_EMPLOYED_PROFESSIONAL"]}),
    ]
    benefit_programs = []
    for code, name, category, cap, rule in benefits:
        benefit_programs.append({"benefit_program_id": code, "program_name": name, "benefit_category": category, "max_support_inr": money(cap), "eligibility_rule_json": compact_json(rule), "source_type": "SYNTHETIC_DEMO_PROGRAM_NOT_GOVERNMENT_SCHEME", "external_source_url": "", "application_channel": "DEMO_ONLY", "program_status": "SIMULATED", "last_rule_reviewed": "2026-11-03", "disclaimer": "Fictional demo fixture; not a real government, employer or insurer benefit.", "data_class": "SYNTHETIC_FIXTURE"})

    skills: list[dict[str, Any]] = []
    skill_by_customer: dict[str, set[str]] = defaultdict(set)
    skill_vocab = ["TUTORING", "EXCEL_ANALYSIS", "GRAPHIC_DESIGN", "VIDEO_EDITING", "CODING_PYTHON", "CODING_WEB", "TAILORING", "FOOD_PREPARATION", "ACCOUNTING", "REPAIR_ELECTRONICS", "CONTENT_WRITING", "TRANSLATION", "SALES", "CUSTOMER_SUPPORT", "DATA_ENTRY", "DIGITAL_MARKETING", "PHOTOGRAPHY", "BEAUTY_SERVICES", "DELIVERY_LOGISTICS", "FARMING_KNOWLEDGE"]
    skidx = 1
    for c in customers:
        for sk in rng.sample(skill_vocab, rng.randint(1, 3)):
            skill_by_customer[c["customer_id"]].add(sk)
            skills.append({"skill_id": make_id("SKL", skidx), "customer_id": c["customer_id"], "skill_code": sk, "skill_label": sk.replace("_", " ").title(), "proficiency_level": rng.choice(["BEGINNER", "INTERMEDIATE", "ADVANCED"]), "evidence_status": rng.choice(["SELF_DECLARED", "PORTFOLIO_LINK_FIXTURE", "DEMO_ASSESSED"]), "available_hours_weekly": rng.choice([2, 4, 6, 8, 10, 15]), "monetization_consent": active_consent.get((c["customer_id"], "OPPORTUNITY_MATCHING"), False), "data_class": "SYNTHETIC_FIXTURE"}); skidx += 1

    opportunities = []
    opp_vocab = ["TUTORING", "EXCEL_ANALYSIS", "GRAPHIC_DESIGN", "VIDEO_EDITING", "CODING_PYTHON", "CODING_WEB", "TAILORING", "FOOD_PREPARATION", "ACCOUNTING", "REPAIR_ELECTRONICS", "CONTENT_WRITING", "TRANSLATION", "SALES", "CUSTOMER_SUPPORT", "DATA_ENTRY", "DIGITAL_MARKETING", "PHOTOGRAPHY", "BEAUTY_SERVICES", "DELIVERY_LOGISTICS", "FARMING_KNOWLEDGE"]
    for i in range(1, 81):
        skill = opp_vocab[(i * 7) % len(opp_vocab)]
        city = list(CITY_ZONES)[(i * 3) % len(CITY_ZONES)]
        opportunities.append({"opportunity_id": make_id("OPP", i), "title": f"Demo {skill.replace('_',' ').title()} Opportunity {i:03d}", "required_skill_code": skill, "opportunity_type": rng.choice(["MICRO_PROJECT", "PART_TIME", "TUTORING", "SERVICE_GIG", "REMOTE_PROJECT"]), "city": city, "remote_allowed": rng.random() < .45, "estimated_pay_inr": money(rng.randint(800, 18000)), "time_commitment_hours": rng.choice([2, 4, 6, 8, 12]), "status": "SIMULATED_OPEN", "application_deadline": date(2026, 11, rng.randint(10, 28)).isoformat(), "provider_id": rng.choice(providers)["provider_id"], "source_type": "SYNTHETIC_OPPORTUNITY_FIXTURE", "data_class": "SYNTHETIC_FIXTURE"})

    # Offers and their net-value calculations
    offers = []
    for i in range(1, 91):
        provider = rng.choice(providers)
        ref = Decimal(rng.randrange(500, 20001, 50))
        discount = (ref * Decimal(str(rng.uniform(.05, .24)))).quantize(Decimal("0.01"))
        extra = Decimal(rng.choice([0, 0, 0, 250, 500, 1000, 2500]))
        fee = Decimal(rng.choice([0, 0, 49, 99, 149]))
        recurring = Decimal(rng.choice([0, 0, 0, 299, 499, 999]))
        sponsor = Decimal(rng.choice([0, 0, 100, 250, 500, 1000]))
        net = discount + sponsor - extra - fee - recurring
        offer = {"offer_id": make_id("OFF", i), "provider_id": provider["provider_id"], "offer_title": f"Demo {provider['provider_type'].replace('_',' ').title()} Offer {i:03d}", "service_category": provider["provider_type"], "city": provider["service_city"], "reference_price_inr": money(ref), "offer_price_inr": money(ref-discount), "discount_value_inr": money(discount), "sponsor_credit_inr": money(sponsor), "required_incremental_spend_inr": money(extra), "fees_inr": money(fee), "recurring_commitment_cost_inr": money(recurring), "estimated_net_benefit_inr": money(net), "min_group_size": rng.choice([1, 1, 3, 5, 8, 10]), "valid_until": date(2026, 12, rng.randint(1, 28)).isoformat(), "decision_fixture": "RECOMMEND" if net > 0 else "REJECT_NEGATIVE_NET_VALUE", "decision_rule": "discount + sponsor_credit - incremental_spend - fees - recurring_commitment", "terms_status": "SYNTHETIC_TERMS_FIXTURE", "data_class": "SYNTHETIC_FIXTURE"}
        offers.append(offer)

    # Recurring obligations to bill fixtures and docs
    bills: list[dict[str, Any]] = []
    bill_lines: list[dict[str, Any]] = []
    bill_by_customer: dict[str, list[dict[str, Any]]] = defaultdict(list)
    bidx = 1; line_idx = 1
    anomaly_types = ["NONE"] * 72 + ["POSSIBLE_DUPLICATE_LINE_ITEM"] * 10 + ["UNEXPECTED_FEE"] * 8 + ["PRICE_SPIKE_VS_PRIOR_PERIOD"] * 10
    rng.shuffle(anomaly_types)
    for c in customers:
        cid = c["customer_id"]
        for bill_n in range(2):
            month = rng.randint(1, 10)
            issue_date = choose_month_day(rng, month, 1, 20)
            due_date = issue_date + timedelta(days=rng.randint(10, 20))
            btype = rng.choice(["ELECTRICITY", "TELECOM", "INTERNET", "EDUCATION", "HEALTHCARE", "INSURANCE"])
            provider_type = "UTILITY" if btype == "ELECTRICITY" else "TELECOM" if btype in ["TELECOM", "INTERNET"] else "EDUCATION" if btype == "EDUCATION" else "HEALTHCARE" if btype == "HEALTHCARE" else "LOCAL_SERVICES"
            prov_id = rng.choice(provider_by_type[provider_type])
            anomaly = anomaly_types[(bidx - 1) % len(anomaly_types)]
            base = Decimal(rng.randint(450, 7500))
            lines = [
                ("BASE_SERVICE", base),
                ("TAX", (base * Decimal("0.18")).quantize(Decimal("0.01"))),
            ]
            if anomaly == "POSSIBLE_DUPLICATE_LINE_ITEM":
                lines.append(("REPEATED_SERVICE_LINE", base * Decimal("0.20")))
            elif anomaly == "UNEXPECTED_FEE":
                lines.append(("UNEXPLAINED_PROCESSING_FEE", Decimal(rng.randint(150, 550))))
            elif anomaly == "PRICE_SPIKE_VS_PRIOR_PERIOD":
                lines[0] = ("BASE_SERVICE", base * Decimal("1.35"))
            total = sum((v for _, v in lines), Decimal("0"))
            bill_id = make_id("BIL", bidx)
            doc_path = f"source_documents/invoices/{bill_id}.html"
            bill = {"bill_id": bill_id, "customer_id": cid, "provider_id": prov_id, "bill_type": btype, "invoice_number": f"SYNTH-INV-{bidx:07d}", "issue_date": issue_date.isoformat(), "due_date": due_date.isoformat(), "currency": "INR", "subtotal_inr": money(sum((v for k,v in lines if k != "TAX"), Decimal("0"))), "tax_inr": money(sum((v for k,v in lines if k == "TAX"), Decimal("0"))), "total_due_inr": money(total), "amount_paid_inr": money(total if rng.random() < .78 else Decimal("0")), "status": "PAID_FIXTURE" if rng.random() < .72 else "OPEN_FIXTURE", "anomaly_label": anomaly, "prior_period_total_inr": money(total / Decimal("1.35")) if anomaly == "PRICE_SPIKE_VS_PRIOR_PERIOD" else "", "source_document_path": doc_path, "document_authenticity": "SYNTHETIC_DEMO_DOCUMENT_NOT_A_REAL_BILL", "data_class": "SYNTHETIC_FIXTURE"}
            bills.append(bill); bill_by_customer[cid].append(bill)
            for label, amount in lines:
                bill_lines.append({"bill_line_id": make_id("BLN", line_idx), "bill_id": bill_id, "description_code": label, "description": label.replace("_", " ").title(), "quantity": "1", "unit_price_inr": money(amount), "line_total_inr": money(amount), "taxable": label != "TAX", "synthetic": True, "data_class": "SYNTHETIC_FIXTURE"}); line_idx += 1
            html = f'''<!doctype html><html><head><meta charset="utf-8"><title>Synthetic invoice {bill_id}</title><style>body{{font-family:Arial,sans-serif;margin:36px;color:#202b3c}}.banner{{background:#fff1cc;border:2px solid #b7791f;padding:12px;font-weight:bold}}table{{border-collapse:collapse;width:100%;margin-top:24px}}td,th{{border:1px solid #ccd3dd;padding:9px;text-align:left}}.right{{text-align:right}}</style></head><body><div class="banner">SYNTHETIC DEMO DOCUMENT — NOT A REAL CUSTOMER BILL OR PAYMENT REQUEST</div><h1>{provider_type.replace('_',' ').title()} Statement</h1><p><b>Demo supplier:</b> {next(p['provider_name'] for p in providers if p['provider_id']==prov_id)}</p><p><b>Invoice:</b> {bill['invoice_number']} &nbsp; <b>Customer:</b> {cid}</p><p><b>Issue date:</b> {issue_date.isoformat()} &nbsp; <b>Due date:</b> {due_date.isoformat()}</p><table><tr><th>Line item</th><th class="right">Amount (INR)</th></tr>{''.join(f'<tr><td>{label.replace("_"," ").title()}</td><td class="right">{money(amount)}</td></tr>' for label,amount in lines)}<tr><th>Total due</th><th class="right">₹{money(total)}</th></tr></table><p>Fixture anomaly label: <b>{anomaly}</b></p><p>All data on this page was generated for software testing and demonstration. No payment should be made.</p></body></html>'''
            (out_dir / doc_path).write_text(html, encoding="utf-8")
            bidx += 1

    # Benefit eligibility assessments/applications (transparent demo rule evaluation)
    assessments: list[dict[str, Any]] = []
    applications: list[dict[str, Any]] = []
    asidx = 1; appidx = 1
    for c in customers:
        income = Decimal(c["monthly_income_inr_estimate"])
        for program in rng.sample(benefit_programs, 3):
            rule = json.loads(program["eligibility_rule_json"])
            checks = []
            if "income_max" in rule: checks.append(("income_within_max", income <= Decimal(str(rule["income_max"]))))
            if "age_min" in rule: checks.append(("age_minimum", int(c["age_years"]) >= rule["age_min"]))
            if "dependants_min" in rule: checks.append(("dependants_minimum", int(c["dependants_count"]) >= rule["dependants_min"]))
            if "persona_any" in rule: checks.append(("persona_match", c["persona"] in rule["persona_any"]))
            if "economic_context_any" in rule: checks.append(("context_match", c["economic_context"] in rule["economic_context_any"]))
            if "healthcare_expense_flag" in rule: checks.append(("healthcare_need_signal", c["economic_context"] == "HEALTHCARE_EXPENSE"))
            positives = sum(1 for _, passed in checks if passed)
            if not checks or positives == len(checks): status = "POTENTIAL_MATCH"
            elif positives > 0: status = "INSUFFICIENT_INFORMATION"
            else: status = "RULE_MISMATCH"
            assessment_id = make_id("BAS", asidx)
            assessments.append({"assessment_id": assessment_id, "customer_id": c["customer_id"], "benefit_program_id": program["benefit_program_id"], "assessment_date": "2026-10-28", "assessment_status": status, "rule_checks_json": compact_json({k: v for k,v in checks}), "matched_rule_count": positives, "total_rule_count": len(checks), "estimated_support_cap_inr": program["max_support_inr"] if status == "POTENTIAL_MATCH" else "0.00", "official_confirmation": "NOT_CONFIRMED_EXTERNAL_AUTHORITY", "data_class": "SYNTHETIC_FIXTURE"})
            if status == "POTENTIAL_MATCH" and rng.random() < .40:
                applications.append({"application_id": make_id("BAP", appidx), "assessment_id": assessment_id, "customer_id": c["customer_id"], "benefit_program_id": program["benefit_program_id"], "application_status": rng.choice(["DRAFT", "DOCUMENTS_PENDING", "SUBMITTED_SIMULATION", "UNDER_REVIEW_SIMULATION"]), "submission_mode": "SIMULATED_NOT_SUBMITTED_TO_REAL_BODY", "required_documents_json": compact_json(["identity_proof_fixture", "income_proof_fixture"]), "submitted_at": "" if rng.random() < .5 else iso_dt(date(2026, 10, rng.randint(1, 28))), "decision_status": "NO_OFFICIAL_DECISION", "data_class": "SYNTHETIC_FIXTURE"}); appidx += 1
            asidx += 1

    # Opportunity matches
    opp_matches: list[dict[str, Any]] = []
    match_idx = 1
    for c in customers:
        if not active_consent.get((c["customer_id"], "OPPORTUNITY_MATCHING"), False):
            continue
        sks = skill_by_customer[c["customer_id"]]
        candidates = [o for o in opportunities if o["required_skill_code"] in sks and (o["remote_allowed"] or o["city"] == c["city"])]
        for o in candidates[:5]:
            score = min(99, 55 + (15 if o["required_skill_code"] in sks else 0) + (15 if o["remote_allowed"] or o["city"] == c["city"] else 0) + rng.randint(0, 12))
            opp_matches.append({"match_id": make_id("MAT", match_idx), "customer_id": c["customer_id"], "opportunity_id": o["opportunity_id"], "match_score": score, "score_components_json": compact_json({"skill_match": True, "location_compatible": bool(o["remote_allowed"] or o["city"] == c["city"]), "availability_check": "REVIEW_REQUIRED"}), "match_status": "SUGGESTED_NOT_APPLIED", "requires_user_review": True, "data_class": "SYNTHETIC_FIXTURE"}); match_idx += 1

    # Resource listings and collective demand / campaigns
    resources = []
    resource_idx = 1
    for c in customers:
        if not active_consent.get((c["customer_id"], "RESOURCE_EXCHANGE_LISTING"), False):
            continue
        i = resource_idx
        resource_idx += 1
        resources.append({"resource_id": make_id("RES", i), "owner_customer_id": c["customer_id"], "resource_type": rng.choice(["TUTOR_HOURS", "EQUIPMENT", "STORAGE_SPACE", "TRANSPORT_CAPACITY", "SURPLUS_INVENTORY", "FOOD_SERVICE_CAPACITY", "WORKSPACE_SEAT", "REPAIR_SERVICE"]), "description": f"Synthetic resource capacity listing {i:03d}", "city": c["city"], "locality_cluster": c["locality_cluster"], "capacity_quantity": rng.randint(1, 30), "capacity_unit": rng.choice(["hours_per_week", "units", "seats", "slots"]), "availability_window": "WEEKDAYS_EVENINGS" if i % 2 else "WEEKENDS", "verification_status": "DEMO_UNVERIFIED_LISTING", "listing_status": rng.choice(["ACTIVE_FIXTURE", "PAUSED_FIXTURE"]), "data_class": "SYNTHETIC_FIXTURE"})

    demand_signals = []
    for i, c in enumerate(customers, 1):
        if not active_consent.get((c["customer_id"], "COMMONS_DEMAND_AGGREGATION", "2026-10-20"), False):
            continue
        demand_signals.append({"demand_signal_id": make_id("DEM", len(demand_signals)+1), "customer_id": c["customer_id"], "consent_purpose": "COMMONS_DEMAND_AGGREGATION", "service_category": rng.choice(["EDUCATION", "BROADBAND", "HEALTHCARE", "GROCERIES", "TRANSPORT", "SKILL_TRAINING", "WORKSPACE"]), "city": c["city"], "locality_cluster": c["locality_cluster"], "quantity_band": rng.choice(["1", "2-3", "4-5"]), "price_band_inr": rng.choice(["0-500", "500-1500", "1500-5000", "5000+"]), "aggregatable": True, "raw_transaction_data_included": False, "signal_date": "2026-10-20", "status": "ACTIVE_FIXTURE", "data_class": "SYNTHETIC_FIXTURE"})

    campaigns = []
    campaign_participants = []
    eligible_signals_by_cat: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for signal in demand_signals: eligible_signals_by_cat[signal["service_category"]].append(signal)
    campaign_categories = ["EDUCATION", "BROADBAND", "HEALTHCARE", "GROCERIES", "TRANSPORT", "SKILL_TRAINING"]
    campaign_idx = 1
    for category in campaign_categories:
        candidates = eligible_signals_by_cat.get(category, [])
        if not candidates: continue
        location_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for candidate in candidates:
            location_groups[(candidate["city"], candidate["locality_cluster"])].append(candidate)
        location, same_area = max(location_groups.items(), key=lambda item: (len(item[1]), item[0]))
        chosen = same_area[:min(len(same_area), rng.randint(4, 10))]
        min_size = 5
        campaign_status = "QUORUM_REACHED_SIMULATION" if len(chosen) >= min_size else "GATHERING_DEMAND_SIMULATION"
        offer = next((o for o in offers if o["service_category"] in [category, "LOCAL_SERVICES"]), rng.choice(offers))
        campaign_id = make_id("CAM", campaign_idx)
        campaigns.append({"campaign_id": campaign_id, "campaign_title": f"Demo Collective {category.replace('_',' ').title()} Opportunity {campaign_idx:02d}", "service_category": category, "city": location[0], "locality_cluster": location[1], "minimum_participants": min_size, "participant_count_fixture": len(chosen), "campaign_status": campaign_status, "linked_offer_id": offer["offer_id"], "funding_source": "SIMULATED_PROVIDER_SPONSOR", "aggregate_only": True, "individual_income_or_transactions_exposed": False, "data_class": "SYNTHETIC_FIXTURE"})
        for signal in chosen:
            campaign_participants.append({"campaign_participant_id": f"CMP-{campaign_idx:03d}-{len(campaign_participants)+1:05d}", "campaign_id": campaign_id, "customer_id": signal["customer_id"], "demand_signal_id": signal["demand_signal_id"], "consent_purpose": signal["consent_purpose"], "participation_status": "OPTED_IN_FIXTURE", "individual_data_disclosed_to_provider": False, "data_class": "SYNTHETIC_FIXTURE"})
        campaign_idx += 1

    # Transactions with consistent cashflow treatment and linked obligations/bills/loans/subscriptions.
    transactions: list[dict[str, Any]] = []
    tidx = 1
    payment_rails = ["UPI_DEMO", "IMPS_DEMO", "NEFT_DEMO", "CARD_DEMO", "CASH_DEMO", "BANK_AUTOPAY_DEMO"]
    for c in customers:
        cid = c["customer_id"]
        bank = account_ids[cid]["bank"]
        for month in month_range():
            mday = date(2026, month, rng.randint(1, 3))
            persona = c["persona"]
            income = Decimal(c["monthly_income_inr_estimate"]) * Decimal(str(rng.uniform(.88, 1.12)))
            income = income.quantize(Decimal("0.01"))
            income_type = "SALARY_CREDIT" if persona == "SALARIED_EMPLOYEE" else "GIG_INCOME" if persona in ["GIG_WORKER", "FREELANCER"] else "BUSINESS_INCOME" if persona in ["SMALL_MERCHANT", "SELF_EMPLOYED_PROFESSIONAL"] else "FAMILY_ALLOWANCE" if persona == "STUDENT_ADULT" else "HOUSEHOLD_CONTRIBUTION"
            transactions.append({"transaction_id": make_id("TXN", tidx, 7), "customer_id": cid, "account_id": bank, "transaction_date": mday.isoformat(), "posted_at": iso_dt(mday, 10), "direction": "CREDIT", "transaction_type": income_type, "cashflow_treatment": "INCOME", "category": "income", "amount_inr": money(income), "currency": "INR", "counterparty_label": "DEMO-EMPLOYER-OR-PAYER", "provider_id": "", "obligation_id": "", "bill_id": "", "loan_installment_id": "", "subscription_id": "", "transfer_group_id": "", "payment_rail": rng.choice(["NEFT_DEMO", "UPI_DEMO"]), "status": "POSTED_FIXTURE", "reference": f"SYNTH-TXN-{tidx:08d}", "data_class": "SYNTHETIC_FIXTURE"}); tidx += 1
            # Day-to-day spending rows
            n_exp = rng.randint(6, 10)
            for k in range(n_exp):
                cat = rng.choice(CATEGORIES)
                amount_ranges = {"groceries": (600, 4500), "rent": (3500, 25000), "electricity": (450, 2400), "internet": (399, 1299), "mobile": (149, 699), "transport": (250, 2800), "fuel": (500, 3500), "healthcare": (200, 6500), "education": (500, 8000), "dining": (180, 2200), "shopping": (250, 7000), "insurance": (500, 4500), "utilities": (250, 1800), "personal_care": (150, 2000)}
                amount = Decimal(rng.randint(*amount_ranges[cat]))
                day = date(2026, month, rng.randint(3, 26))
                matched_bill = next((b for b in bill_by_customer[cid] if b["issue_date"].startswith(f"2026-{month:02d}") and ((cat == "electricity" and b["bill_type"] == "ELECTRICITY") or (cat == "internet" and b["bill_type"] == "INTERNET") or (cat == "mobile" and b["bill_type"] == "TELECOM"))), None)
                matched_obl = next((o for o in obligation_map[cid] if o["obligation_type"].lower().startswith(cat.upper().split("_")[0]) or o["category"].lower() == cat), None)
                use_card = "card" in account_ids[cid] and rng.random() < .30
                account = account_ids[cid].get("card") if use_card else bank
                transactions.append({"transaction_id": make_id("TXN", tidx, 7), "customer_id": cid, "account_id": account, "transaction_date": day.isoformat(), "posted_at": iso_dt(day, rng.randint(8, 22)), "direction": "DEBIT", "transaction_type": "PURCHASE" if cat not in ["electricity", "internet", "mobile", "insurance"] else "BILL_PAYMENT", "cashflow_treatment": "EXPENSE", "category": cat, "amount_inr": money(amount), "currency": "INR", "counterparty_label": f"DEMO-{cat.upper()}-MERCHANT", "provider_id": matched_bill["provider_id"] if matched_bill else "", "obligation_id": matched_obl["obligation_id"] if matched_obl else "", "bill_id": matched_bill["bill_id"] if matched_bill else "", "loan_installment_id": "", "subscription_id": "", "transfer_group_id": "", "payment_rail": rng.choice(payment_rails), "status": "POSTED_FIXTURE", "reference": f"SYNTH-TXN-{tidx:08d}", "data_class": "SYNTHETIC_FIXTURE"}); tidx += 1
            # Monthly loan installment if an installment schedule exists.
            for ins in [x for x in installments if x["customer_id"] == cid and int(x["due_date"][5:7]) == month and x["status"] in ["PAID", "LATE"]]:
                transactions.append({"transaction_id": make_id("TXN", tidx, 7), "customer_id": cid, "account_id": bank, "transaction_date": ins["paid_date"] or ins["due_date"], "posted_at": iso_dt(date.fromisoformat(ins["paid_date"] or ins["due_date"])), "direction": "DEBIT", "transaction_type": "LOAN_EMI_PAYMENT", "cashflow_treatment": "EXPENSE", "category": "loan_emi", "amount_inr": ins["total_due_inr"], "currency": "INR", "counterparty_label": "DEMO-LENDER", "provider_id": "", "obligation_id": "", "bill_id": "", "loan_installment_id": ins["installment_id"], "subscription_id": "", "transfer_group_id": "", "payment_rail": "BANK_AUTOPAY_DEMO", "status": "POSTED_FIXTURE", "reference": f"SYNTH-TXN-{tidx:08d}", "data_class": "SYNTHETIC_FIXTURE"}); tidx += 1
            # Subscription billing
            for sub in sub_by_customer[cid]:
                if sub["status"] == "ACTIVE" and rng.random() < .82:
                    day = date(2026, month, rng.randint(5, 24))
                    transactions.append({"transaction_id": make_id("TXN", tidx, 7), "customer_id": cid, "account_id": bank, "transaction_date": day.isoformat(), "posted_at": iso_dt(day), "direction": "DEBIT", "transaction_type": "SUBSCRIPTION_RENEWAL", "cashflow_treatment": "EXPENSE", "category": "subscription", "amount_inr": sub["current_price_inr"], "currency": "INR", "counterparty_label": sub["service_name"], "provider_id": "", "obligation_id": "", "bill_id": "", "loan_installment_id": "", "subscription_id": sub["subscription_id"], "transfer_group_id": "", "payment_rail": "CARD_DEMO", "status": "POSTED_FIXTURE", "reference": f"SYNTH-TXN-{tidx:08d}", "data_class": "SYNTHETIC_FIXTURE"}); tidx += 1
            if rng.random() < .07:
                refund_day = date(2026, month, rng.randint(10, 28))
                refund = Decimal(rng.randint(100, 1200))
                transactions.append({"transaction_id": make_id("TXN", tidx, 7), "customer_id": cid, "account_id": bank, "transaction_date": refund_day.isoformat(), "posted_at": iso_dt(refund_day), "direction": "CREDIT", "transaction_type": "MERCHANT_REFUND", "cashflow_treatment": "REFUND", "category": "refund", "amount_inr": money(refund), "currency": "INR", "counterparty_label": "DEMO-MERCHANT-REFUND", "provider_id": "", "obligation_id": "", "bill_id": "", "loan_installment_id": "", "subscription_id": "", "transfer_group_id": "", "payment_rail": "UPI_DEMO", "status": "POSTED_FIXTURE", "reference": f"SYNTH-TXN-{tidx:08d}", "data_class": "SYNTHETIC_FIXTURE"}); tidx += 1

    # Guardian cases and supporting document references
    guardian_cases = []
    evidence_documents = []
    gidx = 1; evid_idx = 1
    for b in bills:
        if b["anomaly_label"] == "NONE": continue
        guardian_cases.append({"guardian_case_id": make_id("GUA", gidx), "customer_id": b["customer_id"], "bill_id": b["bill_id"], "case_type": b["anomaly_label"], "severity": "MEDIUM" if b["anomaly_label"] != "POSSIBLE_DUPLICATE_LINE_ITEM" else "HIGH", "case_status": rng.choice(["DETECTED", "EVIDENCE_READY", "DRAFT_PREPARED", "AWAITING_USER_APPROVAL"]), "finding_summary": f"Synthetic fixture flags {b['anomaly_label'].replace('_',' ').lower()} for review.", "model_confidence_fixture": str(round(rng.uniform(.72, .97), 3)), "evidence_required": True, "external_complaint_submitted": False, "outcome_status": "NOT_RESOLVED_FIXTURE", "data_class": "SYNTHETIC_FIXTURE"})
        evidence_documents.append({"evidence_document_id": make_id("EVD", evid_idx), "customer_id": b["customer_id"], "guardian_case_id": make_id("GUA", gidx), "bill_id": b["bill_id"], "document_type": "INVOICE_HTML_FIXTURE", "source_path": b["source_document_path"], "sha256": "GENERATED_AFTER_FILE_WRITE", "provenance": "SYNTHETIC_GENERATOR", "ingestion_status": "AVAILABLE_FIXTURE", "data_class": "SYNTHETIC_FIXTURE"})
        gidx += 1; evid_idx += 1

    # Durable agent missions with checkpoints and non-repeatable side-effect states.
    missions = []
    mission_steps = []
    step_idx = 1
    mission_types = ["BILL_GUARDIAN_REVIEW", "BENEFIT_DISCOVERY", "OPPORTUNITY_DISCOVERY", "COMMONS_MATCHING", "CRISIS_REPLAN", "ENTERPRISE_LAUNCH_PLAN", "SUBSCRIPTION_AUDIT", "RESOURCE_EXCHANGE_MATCH"]
    for i, mtype in enumerate(mission_types, 1):
        customer = customers[(i * 11) % len(customers)]
        state = rng.choice(["COMPLETED_FIXTURE", "PAUSED_AT_CHECKPOINT", "AWAITING_USER_APPROVAL", "FAILED_RETRYABLE_FIXTURE"])
        nsteps = rng.randint(5, 9)
        completed = nsteps if state == "COMPLETED_FIXTURE" else rng.randint(2, nsteps-1)
        mid = make_id("MIS", i)
        missions.append({"mission_id": mid, "customer_id": customer["customer_id"], "mission_type": mtype, "mission_status": state, "created_at": iso_dt(date(2026, 10, rng.randint(1, 25))), "last_checkpoint_number": completed, "total_steps": nsteps, "idempotency_scope": f"MISSION-{mid}", "resume_policy": "RESUME_FROM_LAST_VALID_CHECKPOINT_NO_DUPLICATE_SIDE_EFFECTS", "approval_required": state == "AWAITING_USER_APPROVAL", "simulated_external_actions": True, "data_class": "SYNTHETIC_FIXTURE"})
        for seq in range(1, nsteps + 1):
            st = "COMPLETED_FIXTURE" if seq <= completed else "WAITING" if seq == completed + 1 else "NOT_STARTED"
            if state == "AWAITING_USER_APPROVAL" and seq == completed + 1: st = "AWAITING_APPROVAL"
            mission_steps.append({"mission_step_id": make_id("MST", step_idx, 6), "mission_id": mid, "step_number": seq, "step_key": f"{mtype.lower()}_STEP_{seq}", "step_status": st, "idempotency_key": f"{mid}:STEP:{seq}", "input_ref": f"FIXTURE-INPUT-{mid}-{seq}", "output_ref": f"FIXTURE-OUTPUT-{mid}-{seq}" if st == "COMPLETED_FIXTURE" else "", "checkpoint_hash": hashlib.sha256(f"{seed}:{mid}:{seq}".encode()).hexdigest() if st == "COMPLETED_FIXTURE" else "", "external_side_effect_state": "NOT_APPLICABLE" if seq <= 3 else "SIMULATED_NOT_SENT", "retry_count": rng.randint(0, 2), "data_class": "SYNTHETIC_FIXTURE"}); step_idx += 1

    # Demonstration-only economic value ledger (never real verified value)
    value_events = []
    for i in range(1, 46):
        c = customers[(i * 13) % len(customers)]
        kind = rng.choice(["MONEY_RECOVERED", "EXPENDITURE_SAVING", "ADDITIONAL_EARNING", "BENEFIT_RECEIVED", "FEE_PREVENTED"])
        est = Decimal(rng.randint(150, 5000))
        status = rng.choice(["ESTIMATE_ONLY", "ACTION_PREPARED", "SIMULATED_OUTCOME_RECORDED"])
        value_events.append({"value_event_id": make_id("VIV", i), "customer_id": c["customer_id"], "value_type": kind, "gross_value_inr": money(est), "additional_cost_inr": money(rng.choice([0, 0, 49, 99, 150])), "net_value_inr": money(max(Decimal("0"), est-Decimal("99"))), "outcome_status": status, "verification_level": "SYNTHETIC_FIXTURE_ONLY", "evidence_ref": f"FIXTURE-EVIDENCE-{i:04d}" if status == "SIMULATED_OUTCOME_RECORDED" else "", "external_provider_confirmation": False, "deduplication_key": f"SYNTH-VALUE-{c['customer_id']}-{kind}-{i}", "data_class": "SYNTHETIC_FIXTURE"})

    # Personal financial planning: one October plan per customer plus three envelopes.
    budget_plans = []
    budget_envelopes = []
    financial_goals = []
    budget_idx = 1
    envelope_idx = 1
    goal_idx = 1
    for c in customers:
        cid = c["customer_id"]
        income_oct = sum((Decimal(t["amount_inr"]) for t in transactions if t["customer_id"] == cid and t["transaction_date"].startswith("2026-10") and t["cashflow_treatment"] == "INCOME"), Decimal("0"))
        expenses_oct = [t for t in transactions if t["customer_id"] == cid and t["transaction_date"].startswith("2026-10") and t["cashflow_treatment"] == "EXPENSE"]
        needs_cats = {"rent", "groceries", "electricity", "internet", "mobile", "healthcare", "education", "insurance", "loan_emi", "utilities"}
        needs_spent = sum((Decimal(t["amount_inr"]) for t in expenses_oct if t["category"] in needs_cats), Decimal("0"))
        growth_spent = sum((Decimal(t["amount_inr"]) for t in expenses_oct if t["category"] in {"education", "personal_care"}), Decimal("0"))
        flex_spent = sum((Decimal(t["amount_inr"]) for t in expenses_oct if t["category"] not in needs_cats), Decimal("0"))
        budget_total = (income_oct * Decimal("0.92")).quantize(Decimal("0.01"))
        plan_id = make_id("BPL", budget_idx)
        budget_plans.append({"budget_plan_id": plan_id, "customer_id": cid, "period_start": "2026-10-01", "period_end": "2026-10-31", "currency": "INR", "income_reference_inr": money(income_oct), "planned_total_inr": money(budget_total), "plan_status": "SYNTHETIC_REVIEWABLE_PLAN", "method": "DEMO_ENVELOPE_ALLOCATION_NOT_FINANCIAL_ADVICE", "data_class": "SYNTHETIC_FIXTURE"})
        for envelope_type, ratio, spent in [("NEEDS", Decimal("0.60"), needs_spent), ("GROWTH", Decimal("0.15"), growth_spent), ("FLEXIBLE", Decimal("0.25"), flex_spent)]:
            planned = (budget_total * ratio).quantize(Decimal("0.01"))
            budget_envelopes.append({"budget_envelope_id": make_id("BEN", envelope_idx), "budget_plan_id": plan_id, "customer_id": cid, "envelope_type": envelope_type, "planned_amount_inr": money(planned), "actual_spend_inr": money(spent), "remaining_amount_inr": money(planned-spent), "overspent": spent > planned, "allocation_ratio_percent": money(ratio*100), "data_class": "SYNTHETIC_FIXTURE"})
            envelope_idx += 1
        for _ in range(2 if rng.random() < .35 else 1):
            goal_type = rng.choice(["EMERGENCY_BUFFER", "EDUCATION_FUND", "DEBT_REPAYMENT", "BUSINESS_EQUIPMENT", "HEALTHCARE_RESERVE", "SKILL_CERTIFICATION"])
            target = Decimal(rng.randrange(5000, 250001, 1000))
            current = (target * Decimal(str(rng.uniform(.03, .68)))).quantize(Decimal("0.01"))
            financial_goals.append({"financial_goal_id": make_id("FGO", goal_idx), "customer_id": cid, "goal_type": goal_type, "target_amount_inr": money(target), "current_progress_inr": money(current), "target_date": date(2027, rng.randint(1, 12), 15).isoformat(), "priority": rng.choice(["HIGH", "MEDIUM", "LOW"]), "goal_status": "ACTIVE_FIXTURE", "data_class": "SYNTHETIC_FIXTURE"}); goal_idx += 1
        budget_idx += 1

    # Tax obligations: user-entered fixture amounts only; no tax-engine claim.
    tax_obligations = []
    tax_idx = 1
    for c in rng.sample(customers, 36):
        tax_obligations.append({"tax_obligation_id": make_id("TAX", tax_idx), "customer_id": c["customer_id"], "tax_period_label": "FY2026-27_DEMO", "tax_type": rng.choice(["ADVANCE_TAX_REMINDER", "SELF_ASSESSMENT_REMINDER", "GST_OBLIGATION_REMINDER"]), "estimated_amount_inr": money(rng.randint(1000, 45000)), "due_date": date(2026, 12, rng.randint(1, 28)).isoformat(), "estimate_source": "USER_ENTERED_SYNTHETIC_FIXTURE", "tax_rule_engine": "NOT_USED", "status": rng.choice(["PLANNED", "REMINDER_PENDING", "DOCUMENTS_TO_REVIEW"]), "disclaimer": "Not a tax calculation, filing instruction or tax advice.", "data_class": "SYNTHETIC_FIXTURE"}); tax_idx += 1

    # Insurance policies and claims (claims remain simulations, never submitted externally).
    insurance_policies = []
    insurance_claims = []
    policy_idx = 1; claim_idx = 1
    for c in customers:
        if rng.random() < .42:
            policy = {"insurance_policy_id": make_id("POL", policy_idx), "customer_id": c["customer_id"], "policy_type": rng.choice(["HEALTH", "TERM_LIFE", "VEHICLE", "PERSONAL_ACCIDENT"]), "insurer_label": f"DEMO-INSURER-{rng.randint(1,7):02d}", "coverage_amount_inr": money(rng.randint(100000, 2500000)), "premium_amount_inr": money(rng.randint(900, 18000)), "premium_frequency": rng.choice(["MONTHLY", "QUARTERLY", "ANNUAL"]), "renewal_date": date(2027, rng.randint(1, 12), 15).isoformat(), "policy_status": "ACTIVE_FIXTURE", "policy_document_status": "NO_REAL_POLICY_DOCUMENT", "data_class": "SYNTHETIC_FIXTURE"}
            insurance_policies.append(policy)
            if rng.random() < .40:
                insurance_claims.append({"insurance_claim_id": make_id("ICL", claim_idx), "insurance_policy_id": policy["insurance_policy_id"], "customer_id": c["customer_id"], "claim_type": rng.choice(["HOSPITALIZATION", "ACCIDENT", "VEHICLE_REPAIR", "REIMBURSEMENT"]), "claim_amount_inr": money(rng.randint(2500, 125000)), "claim_status": rng.choice(["DRAFT_FIXTURE", "DOCUMENTS_PENDING", "SUBMISSION_READY", "SUBMITTED_SIMULATION", "UNDER_REVIEW_SIMULATION"]), "submission_mode": "NOT_SENT_TO_INSURER", "evidence_status": "SYNTHETIC_DOCUMENTS_ONLY", "data_class": "SYNTHETIC_FIXTURE"}); claim_idx += 1
            policy_idx += 1

    # Crisis Shield scenarios with explicit human review and no loan-first recommendation.
    crisis_cases = []
    crisis_idx = 1
    for c in [x for x in customers if x["economic_context"] in ["TIGHT_CASHFLOW", "HEALTHCARE_EXPENSE", "INCOME_VOLATILITY"]][:28]:
        crisis_cases.append({"crisis_case_id": make_id("CRI", crisis_idx), "customer_id": c["customer_id"], "trigger_type": c["economic_context"], "estimated_shortfall_inr": money(rng.randint(1000, 28000)), "urgency": rng.choice(["HIGH", "MEDIUM", "LOW"]), "recommended_sequence_json": compact_json(["verify obligations", "identify reversible expense reductions", "check official relief or benefits", "identify safe income options", "request human approval for commitments"]), "loan_first_strategy": False, "case_status": rng.choice(["DETECTED_FIXTURE", "PLAN_PREPARED", "AWAITING_USER_REVIEW"]), "external_aid_requested": False, "data_class": "SYNTHETIC_FIXTURE"}); crisis_idx += 1

    # Economic Defence risk signals: indicators and safe next steps, not a fraud verdict.
    risk_signals = []
    risk_idx = 1
    risk_types = ["URGENT_PAYMENT_PRESSURE", "UNVERIFIED_BENEFICIARY", "SUSPICIOUS_LINK_INDICATOR", "UNEXPECTED_RECURRING_CHARGE", "CONTRACT_FEE_AMBIGUITY", "ACCOUNT_CREDENTIAL_REQUEST"]
    for c in rng.sample(customers, 42):
        rtype = rng.choice(risk_types)
        risk_signals.append({"risk_signal_id": make_id("RSK", risk_idx), "customer_id": c["customer_id"], "source_type": rng.choice(["SYNTHETIC_SMS", "SYNTHETIC_OFFER_TERMS", "SYNTHETIC_TRANSACTION_PATTERN"]), "signal_type": rtype, "synthetic_message_or_evidence": f"DEMO ALERT: {rtype.replace('_',' ').lower()}. This fixture is not a real message or payment request.", "risk_level": rng.choice(["LOW", "MEDIUM", "HIGH"]), "model_signal_confidence_fixture": str(round(rng.uniform(.60, .98), 3)), "deterministic_indicators_json": compact_json({"unknown_recipient": rtype in ["UNVERIFIED_BENEFICIARY", "ACCOUNT_CREDENTIAL_REQUEST"], "urgency_language": rtype == "URGENT_PAYMENT_PRESSURE", "unexpected_recurring": rtype == "UNEXPECTED_RECURRING_CHARGE"}), "recommended_action": "VERIFY_USING_OFFICIAL_CHANNEL_AND_DO_NOT_SHARE_CREDENTIALS", "fraud_verdict": "NOT_CONFIRMED_REQUIRES_REVIEW", "automated_payment_blocked": False, "data_class": "SYNTHETIC_FIXTURE"}); risk_idx += 1

    # One-person enterprise: fictional business profiles, catalogue items and order flows.
    micro_enterprises = []
    enterprise_products = []
    enterprise_orders = []
    ent_idx = 1; product_idx = 1; order_idx = 1
    enterprise_candidates = [c for c in customers if c["persona"] in ["SMALL_MERCHANT", "FREELANCER", "SELF_EMPLOYED_PROFESSIONAL"]]
    for c in enterprise_candidates[:min(35, len(enterprise_candidates))]:
        ent_id = make_id("ENT", ent_idx)
        business_type = rng.choice(["HOME_FOOD", "TUTORING", "DESIGN_SERVICE", "REPAIR_SERVICE", "TAILORING", "LOCAL_RETAIL", "DIGITAL_SERVICE", "BEAUTY_SERVICE"])
        rev = Decimal(rng.randint(12000, 220000))
        fixed = (rev * Decimal(str(rng.uniform(.12, .36)))).quantize(Decimal("0.01"))
        variable = (rev * Decimal(str(rng.uniform(.20, .52)))).quantize(Decimal("0.01"))
        micro_enterprises.append({"enterprise_id": ent_id, "owner_customer_id": c["customer_id"], "business_name": f"Synthetic {business_type.replace('_',' ').title()} Studio {ent_idx:03d}", "business_type": business_type, "city": c["city"], "locality_cluster": c["locality_cluster"], "monthly_revenue_estimate_inr": money(rev), "fixed_cost_estimate_inr": money(fixed), "variable_cost_estimate_inr": money(variable), "estimated_contribution_margin_inr": money(rev-fixed-variable), "capacity_per_week": rng.randint(4, 70), "enterprise_stage": rng.choice(["IDEA", "VALIDATING", "EARLY_REVENUE", "OPERATING"]), "external_business_registration": "NOT_ASSERTED_SYNTHETIC_FIXTURE", "data_class": "SYNTHETIC_FIXTURE"})
        for _ in range(rng.randint(2, 4)):
            price = Decimal(rng.randint(150, 8500)); cost = (price * Decimal(str(rng.uniform(.25, .70)))).quantize(Decimal("0.01"))
            enterprise_products.append({"enterprise_product_id": make_id("EPR", product_idx), "enterprise_id": ent_id, "product_or_service_name": f"Demo {business_type.replace('_',' ').title()} SKU {product_idx:03d}", "unit_price_inr": money(price), "estimated_unit_cost_inr": money(cost), "estimated_unit_margin_inr": money(price-cost), "catalog_status": "SIMULATED_LISTING", "data_class": "SYNTHETIC_FIXTURE"}); product_idx += 1
        for _ in range(rng.randint(2, 5)):
            product = rng.choice([p for p in enterprise_products if p["enterprise_id"] == ent_id])
            qty = rng.randint(1, 5); total = Decimal(product["unit_price_inr"]) * qty
            enterprise_orders.append({"enterprise_order_id": make_id("EOR", order_idx), "enterprise_id": ent_id, "enterprise_product_id": product["enterprise_product_id"], "customer_order_label": f"DEMO-ORDER-{order_idx:06d}", "order_date": date(2026, rng.randint(7, 10), rng.randint(1, 25)).isoformat(), "quantity": qty, "order_total_inr": money(total), "order_status": rng.choice(["ENQUIRY", "CONFIRMED_SIMULATION", "FULFILLED_SIMULATION", "CANCELLED_FIXTURE"]), "payment_status": "NOT_CONNECTED_TO_PAYMENT_RAIL", "data_class": "SYNTHETIC_FIXTURE"}); order_idx += 1
        ent_idx += 1

    partner_settlements = []
    for i, offer in enumerate(offers[:24], 1):
        gross = Decimal(rng.randint(100, 3500))
        refunds = Decimal(rng.choice([0, 0, 100]))
        taxes = (gross * Decimal("0.18")).quantize(Decimal("0.01"))
        costs = Decimal(rng.randint(0, 75))
        net = max(Decimal("0"), gross-refunds-taxes-costs)
        user_share = (net * Decimal("0.50")).quantize(Decimal("0.01"))
        partner_settlements.append({"settlement_id": make_id("SET", i), "provider_id": offer["provider_id"], "offer_id": offer["offer_id"], "gross_commission_inr": money(gross), "refunds_inr": money(refunds), "taxes_inr": money(taxes), "processing_costs_inr": money(costs), "eligible_net_revenue_inr": money(net), "user_share_percent": "50.00", "user_share_inr": money(user_share), "platform_share_inr": money(net-user_share), "settlement_status": "SIMULATED_CALCULATION_ONLY", "contract_approved": False, "payout_executed": False, "data_class": "SYNTHETIC_FIXTURE"})

    # Audit events: explicit consent lifecycle, login, household membership and data access decisions.
    audit_events = []
    aid = 1
    for c in customers[:min(customers_count, 90)]:
        for event in ["ACCOUNT_REGISTERED_FIXTURE", "EMAIL_VERIFIED_FIXTURE", "PERSONAL_ANALYSIS_CONSENT_CHECK", "HOUSEHOLD_MEMBERSHIP_CHECK"]:
            audit_events.append({"audit_event_id": make_id("AUD", aid, 7), "actor_customer_id": c["customer_id"], "event_type": event, "resource_type": "CUSTOMER_PROFILE", "resource_id": c["customer_id"], "purpose": "ACCOUNT_SECURITY_OR_PERSONAL_SERVICE", "decision": "ALLOW_FIXTURE" if event != "HOUSEHOLD_MEMBERSHIP_CHECK" else "MEMBERSHIP_ONLY_NO_FINANCIAL_ACCESS", "occurred_at": iso_dt(date(2026, 10, rng.randint(1, 31))), "correlation_id": f"CORR-{aid:08d}", "ip_address": "192.0.2.10", "data_class": "SYNTHETIC_FIXTURE"}); aid += 1

    # Assemble all normalized entities.
    TABLES.clear()
    TABLES.update({
        "customers": customers, "households": households, "household_memberships": memberships,
        "consents": consents, "providers": providers, "accounts": accounts,
        "recurring_obligations": obligations, "loans": loans, "loan_installments": installments,
        "bills": bills, "bill_line_items": bill_lines, "subscriptions": subscriptions,
        "transactions": transactions, "benefit_programs": benefit_programs,
        "benefit_assessments": assessments, "benefit_applications": applications,
        "skills": skills, "opportunities": opportunities, "opportunity_matches": opp_matches,
        "offers": offers, "resource_listings": resources, "demand_signals": demand_signals,
        "commons_campaigns": campaigns, "commons_participants": campaign_participants,
        "guardian_cases": guardian_cases, "evidence_documents": evidence_documents,
        "agent_missions": missions, "agent_mission_steps": mission_steps,
        "value_events": value_events, "budget_plans": budget_plans, "budget_envelopes": budget_envelopes,
        "financial_goals": financial_goals, "tax_obligations": tax_obligations,
        "insurance_policies": insurance_policies, "insurance_claims": insurance_claims,
        "crisis_cases": crisis_cases, "risk_signals": risk_signals,
        "micro_enterprises": micro_enterprises, "enterprise_products": enterprise_products,
        "enterprise_orders": enterprise_orders, "partner_settlements": partner_settlements,
        "audit_events": audit_events,
    })

    # Update source document evidence hashes now documents exist.
    evidence_by_path = {b["source_document_path"]: hashlib.sha256((out_dir / b["source_document_path"]).read_bytes()).hexdigest() for b in bills}
    for e in evidence_documents:
        e["sha256"] = evidence_by_path[e["source_path"]]

    # Provider offer terms, explicitly fictional.
    for offer in offers:
        html = f'''<!doctype html><html><head><meta charset="utf-8"><title>{offer['offer_id']} demo terms</title></head><body><h1>SYNTHETIC DEMO OFFER TERMS</h1><p>Offer: {offer['offer_title']}</p><p>Provider: {offer['provider_id']}</p><p>Reference price: INR {offer['reference_price_inr']}</p><p>Offer price: INR {offer['offer_price_inr']}</p><p>Sponsor credit: INR {offer['sponsor_credit_inr']}</p><p>Additional spend: INR {offer['required_incremental_spend_inr']}</p><p>Fees: INR {offer['fees_inr']}</p><p>Recurring commitment: INR {offer['recurring_commitment_cost_inr']}</p><p>Calculated net benefit: INR {offer['estimated_net_benefit_inr']}</p><p>Decision fixture: {offer['decision_fixture']}</p><p>FAKE TERMS FOR TESTING ONLY. Not an actual offer or contract.</p></body></html>'''
        (out_dir / "source_documents" / "offer_terms" / f"{offer['offer_id']}.html").write_text(html, encoding="utf-8")

    # Derive schema/type metadata.
    json_columns = {"data_categories_json", "rule_checks_json", "eligibility_rule_json", "required_documents_json", "score_components_json"}
    type_overrides: dict[str, str] = {}
    integer_cols = {"age_years", "dependants_count", "member_count", "quantity", "capacity_quantity", "matched_rule_count", "total_rule_count", "min_group_size", "minimum_participants", "participant_count_fixture", "match_score", "tenure_months", "installment_number", "step_number", "last_checkpoint_number", "total_steps", "retry_count", "available_hours_weekly"}
    bool_cols = {"synthetic", "essential", "autopay_enabled", "auto_renew", "price_change_flag", "monetization_consent", "remote_allowed", "requires_user_review", "aggregatable", "raw_transaction_data_included", "individual_data_disclosed_to_provider", "aggregate_only", "individual_income_or_transactions_exposed", "evidence_required", "external_complaint_submitted", "external_provider_confirmation", "contract_approved", "payout_executed", "approval_required", "simulated_external_actions", "taxable", "shared_financial_profile_enabled"}
    date_cols = {"age_years"}
    date_fields = {"issue_date", "due_date", "paid_date", "start_date", "next_renewal_date", "first_due_date", "application_deadline", "assessment_date", "signal_date", "valid_until", "joined_at", "created_at", "granted_at", "expires_at", "revoked_at", "occurred_at", "transaction_date"}
    timestamp_fields = {"posted_at", "created_at", "granted_at", "expires_at", "revoked_at", "occurred_at", "joined_at"}
    # Numeric money and rate fields; stored as strings to preserve exact decimal representation.
    decimal_fields = {col for rows in TABLES.values() for row in rows for col in row if col.endswith("_inr") or col in ["annual_interest_rate_percent", "user_share_percent", "model_confidence_fixture"]}
    # CSV/JSON serialization
    def serializable(v: Any) -> Any:
        return v
    dictionary_rows = []
    for table_name, rows in TABLES.items():
        if not rows:
            continue
        headers = list(rows[0].keys())
        with (out_dir / "csv" / f"{table_name}.csv").open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
            writer.writeheader(); writer.writerows(rows)
        with (out_dir / "jsonl" / f"{table_name}.jsonl").open("w", encoding="utf-8") as f:
            for row in rows: f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        (out_dir / "json" / f"{table_name}.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        for col in headers:
            if col == "data_class" or col == "synthetic": continue
            typ = "JSON" if col.endswith("_json") or col == "data_categories_json" else "DECIMAL_STRING" if col in decimal_fields else "INTEGER" if col in integer_cols else "BOOLEAN" if col in bool_cols else "DATE_OR_TIMESTAMP" if col in date_fields or col in timestamp_fields else "STRING"
            dictionary_rows.append({"table_name": table_name, "column_name": col, "logical_type": typ, "nullable": "YES" if any(row.get(col) in [None, ""] for row in rows) else "NO", "description": col.replace("_", " ").capitalize(), "synthetic_note": "All values in this dataset are generated fixtures."})

    # Schema catalog and data dictionary
    with (out_dir / "metadata" / "data_dictionary.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(dictionary_rows[0].keys())); w.writeheader(); w.writerows(dictionary_rows)
    rels = {
        "household_memberships.household_id": "households.household_id", "household_memberships.customer_id": "customers.customer_id",
        "accounts.customer_id": "customers.customer_id", "consents.customer_id": "customers.customer_id",
        "recurring_obligations.customer_id": "customers.customer_id", "loans.customer_id": "customers.customer_id",
        "loan_installments.loan_id": "loans.loan_id", "loan_installments.customer_id": "customers.customer_id",
        "bills.customer_id": "customers.customer_id", "bills.provider_id": "providers.provider_id",
        "bill_line_items.bill_id": "bills.bill_id", "subscriptions.customer_id": "customers.customer_id",
        "transactions.customer_id": "customers.customer_id", "transactions.account_id": "accounts.account_id",
        "benefit_assessments.customer_id": "customers.customer_id", "benefit_assessments.benefit_program_id": "benefit_programs.benefit_program_id",
        "benefit_applications.assessment_id": "benefit_assessments.assessment_id", "benefit_applications.customer_id": "customers.customer_id",
        "skills.customer_id": "customers.customer_id", "opportunity_matches.customer_id": "customers.customer_id", "opportunity_matches.opportunity_id": "opportunities.opportunity_id",
        "offers.provider_id": "providers.provider_id", "resource_listings.owner_customer_id": "customers.customer_id",
        "demand_signals.customer_id": "customers.customer_id", "commons_participants.campaign_id": "commons_campaigns.campaign_id", "commons_participants.customer_id": "customers.customer_id",
        "commons_participants.demand_signal_id": "demand_signals.demand_signal_id", "guardian_cases.customer_id": "customers.customer_id", "guardian_cases.bill_id": "bills.bill_id",
        "evidence_documents.customer_id": "customers.customer_id", "evidence_documents.guardian_case_id": "guardian_cases.guardian_case_id", "evidence_documents.bill_id": "bills.bill_id",
        "agent_missions.customer_id": "customers.customer_id", "agent_mission_steps.mission_id": "agent_missions.mission_id", "value_events.customer_id": "customers.customer_id",
        "budget_plans.customer_id": "customers.customer_id", "budget_envelopes.budget_plan_id": "budget_plans.budget_plan_id", "budget_envelopes.customer_id": "customers.customer_id", "financial_goals.customer_id": "customers.customer_id", "tax_obligations.customer_id": "customers.customer_id",
        "insurance_policies.customer_id": "customers.customer_id", "insurance_claims.insurance_policy_id": "insurance_policies.insurance_policy_id", "insurance_claims.customer_id": "customers.customer_id", "crisis_cases.customer_id": "customers.customer_id", "risk_signals.customer_id": "customers.customer_id",
        "micro_enterprises.owner_customer_id": "customers.customer_id", "enterprise_products.enterprise_id": "micro_enterprises.enterprise_id", "enterprise_orders.enterprise_id": "micro_enterprises.enterprise_id", "enterprise_orders.enterprise_product_id": "enterprise_products.enterprise_product_id",
        "partner_settlements.provider_id": "providers.provider_id", "partner_settlements.offer_id": "offers.offer_id", "audit_events.actor_customer_id": "customers.customer_id",
    }
    schema = {"dataset_name": "MyEconomy Synthetic Economic Demo Dataset", "version": "1.0.0", "as_of_date": AS_OF.isoformat(), "generation_seed": seed, "synthetic_only": True, "tables": {}, "relationships": rels}
    for table_name, rows in TABLES.items():
        schema["tables"][table_name] = {"row_count": len(rows), "columns": list(rows[0].keys()) if rows else []}
    (out_dir / "metadata" / "schema_catalog.json").write_text(json.dumps(schema, indent=2), encoding="utf-8")

    # SQL schema and seed: PostgreSQL, no application migrations overwritten.
    sql_types: dict[str, str] = {}
    for col in ["age_years", "dependants_count", "member_count", "quantity", "capacity_quantity", "matched_rule_count", "total_rule_count", "min_group_size", "minimum_participants", "participant_count_fixture", "match_score", "tenure_months", "installment_number", "step_number", "last_checkpoint_number", "total_steps", "retry_count", "available_hours_weekly"]: sql_types[col] = "INTEGER"
    for col in bool_cols: sql_types[col] = "BOOLEAN"
    for col in decimal_fields: sql_types[col] = "NUMERIC(20,2)"
    sql_types["annual_interest_rate_percent"] = "NUMERIC(8,4)"; sql_types["user_share_percent"] = "NUMERIC(5,2)"; sql_types["model_confidence_fixture"] = "NUMERIC(5,3)"
    for col in ["issue_date", "due_date", "paid_date", "start_date", "next_renewal_date", "first_due_date", "application_deadline", "assessment_date", "signal_date", "valid_until", "transaction_date"]: sql_types[col] = "DATE"
    for col in timestamp_fields: sql_types[col] = "TIMESTAMPTZ"
    for col in json_columns: sql_types[col] = "JSONB"
    primary_keys = {"customers":"customer_id", "households":"household_id", "household_memberships":"membership_id", "consents":"consent_id", "providers":"provider_id", "accounts":"account_id", "recurring_obligations":"obligation_id", "loans":"loan_id", "loan_installments":"installment_id", "bills":"bill_id", "bill_line_items":"bill_line_id", "subscriptions":"subscription_id", "transactions":"transaction_id", "benefit_programs":"benefit_program_id", "benefit_assessments":"assessment_id", "benefit_applications":"application_id", "skills":"skill_id", "opportunities":"opportunity_id", "opportunity_matches":"match_id", "offers":"offer_id", "resource_listings":"resource_id", "demand_signals":"demand_signal_id", "commons_campaigns":"campaign_id", "commons_participants":"campaign_participant_id", "guardian_cases":"guardian_case_id", "evidence_documents":"evidence_document_id", "agent_missions":"mission_id", "agent_mission_steps":"mission_step_id", "value_events":"value_event_id", "budget_plans":"budget_plan_id", "budget_envelopes":"budget_envelope_id", "financial_goals":"financial_goal_id", "tax_obligations":"tax_obligation_id", "insurance_policies":"insurance_policy_id", "insurance_claims":"insurance_claim_id", "crisis_cases":"crisis_case_id", "risk_signals":"risk_signal_id", "micro_enterprises":"enterprise_id", "enterprise_products":"enterprise_product_id", "enterprise_orders":"enterprise_order_id", "partner_settlements":"settlement_id", "audit_events":"audit_event_id"}
    fk_map = defaultdict(list)
    for key, target in rels.items():
        t, col = key.split("."); rt, rc = target.split("."); fk_map[t].append((col, rt, rc))
    create_stmts = ["-- MyEconomy synthetic demo fixtures. Never use as production customer data.", "-- PostgreSQL 15+ compatible DDL. All personal-looking values are generated placeholders.", "BEGIN;", "SET client_min_messages TO WARNING;"]
    for table_name, rows in TABLES.items():
        headers = list(rows[0].keys()) if rows else []
        cols = []
        for col in headers:
            typ = sql_types.get(col, "TEXT")
            nullable = " NOT NULL" if col == primary_keys[table_name] else ""
            cols.append(f'  "{col}" {typ}{nullable}')
        cols.append(f'  PRIMARY KEY ("{primary_keys[table_name]}")')
        for col, rt, rc in fk_map[table_name]:
            cols.append(f'  FOREIGN KEY ("{col}") REFERENCES "{rt}"("{rc}")')
        if table_name == "household_memberships": cols.append('  UNIQUE ("household_id", "customer_id")')
        create_stmts.append(f'CREATE TABLE IF NOT EXISTS "{table_name}" (\n' + ",\n".join(cols) + "\n);")
    create_stmts.append("COMMIT;")
    (out_dir / "sql" / "schema.sql").write_text("\n\n".join(create_stmts) + "\n", encoding="utf-8")

    def sql_literal(value: Any, col: str) -> str:
        if value is None or value == "": return "NULL"
        typ = sql_types.get(col, "TEXT")
        if typ == "BOOLEAN": return "TRUE" if bool(value) else "FALSE"
        if typ in ["INTEGER", "NUMERIC(20,2)", "NUMERIC(8,4)", "NUMERIC(5,2)", "NUMERIC(5,3)"]:
            return str(value)
        s = str(value).replace("'", "''")
        if typ == "JSONB": return f"'{s}'::jsonb"
        if typ == "DATE": return f"'{s}'::date"
        if typ == "TIMESTAMPTZ": return f"'{s}'::timestamptz"
        return f"'{s}'"
    insert_path = out_dir / "sql" / "seed.sql"
    with insert_path.open("w", encoding="utf-8") as f:
        f.write("-- Synthetic-only data seed. Load schema.sql first.\nBEGIN;\n")
        for table_name, rows in TABLES.items():
            if not rows: continue
            cols = list(rows[0].keys())
            col_list = ", ".join(f'"{c}"' for c in cols)
            for row in rows:
                vals = ", ".join(sql_literal(row.get(c), c) for c in cols)
                f.write(f'INSERT INTO "{table_name}" ({col_list}) VALUES ({vals});\n')
        f.write("COMMIT;\n")

    # Rule catalogue for deterministic demo logic.
    rules = {
        "dataset_safety": ["Never treat this fixture as a real person, bank account, bill, offer, partner or benefit.", "Only .invalid email and 00000 phone placeholders are present.", "No Aadhaar, PAN, bank credentials, card PAN, UPI PIN or real account numbers are generated."],
        "consent": ["Household membership never implies financial-data access.", "A personal or Commons data use requires a current explicit purpose-specific grant.", "Revoked or expired grants must fail closed.", "Commons demand signals may expose only service category, city/locality cluster, quantity band and price band; never raw transaction or income data."],
        "cashflow": ["All money amounts are INR decimal strings with two fractional digits unless rates or percentages.", "Only cashflow_treatment INCOME, EXPENSE and REFUND count toward cashflow; TRANSFER and IGNORE do not.", "Refunds must be represented separately from purchases and linked through evidence where available.", "A credit-card purchase is an expense; a bank-to-card payment is a transfer and must not double count spending."],
        "benefits": ["All DEMO-* benefit programs are fictional and not government schemes.", "POTENTIAL_MATCH is not confirmed eligibility or an award.", "Applications marked SIMULATED are not submitted to an authority."],
        "offers": ["net_benefit = discount_value + sponsor_credit - required_incremental_spend - fees - recurring_commitment_cost.", "Reject any offer with net benefit <= 0 or unresolved material conditions.", "Do not optimize for commission at the expense of customer net value."],
        "commons": ["Only a customer with active COMMONS_DEMAND_AGGREGATION consent can contribute a signal.", "Aggregate at or above min_group_size before asking providers for a group quote.", "Provider-facing signals contain no raw financial transactions, exact income or individual identity.", "A campaign is simulated until provider, price, terms and fulfilment are independently verified."],
        "agent_workflows": ["Persist step state and checkpoint hashes.", "Use idempotency keys for side effects.", "Resume only after verifying current external state; never replay a completed side effect blindly.", "Consequential actions require an explicit human approval bound to the action, recipient, amount and expiry."],
        "vivc": ["VIVC counts only realized, externally evidenced value less incremental costs.", "Synthetic outcomes must remain verification_level SYNTHETIC_FIXTURE_ONLY and cannot be reported as real value."],
    }
    (out_dir / "metadata" / "business_rules.json").write_text(json.dumps(rules, indent=2), encoding="utf-8")

    # API demo payloads
    sample_customer = customers[0]
    sample_bill = next((b for b in bills if b["anomaly_label"] != "NONE"), bills[0])
    sample_case = next((g for g in guardian_cases if g["bill_id"] == sample_bill["bill_id"]), guardian_cases[0] if guardian_cases else None)
    sample_campaign = campaigns[0] if campaigns else None
    scenarios = {
        "01_day_one_personal_power.json": {"scenario_name": "Day-one personal power discovery", "synthetic": True, "customer_id": sample_customer["customer_id"], "steps": ["Upload sample bill or enter obligations", "Extract only user-authorized details", "Calculate deterministic totals", "Show potential actions with evidence", "Ask user to choose next action"], "expected_safety": "No bank connection or Commons participation required."},
        "02_guardian_bill_review.json": {"scenario_name": "Guardian invoice anomaly review", "synthetic": True, "customer_id": sample_bill["customer_id"], "bill_id": sample_bill["bill_id"], "guardian_case_id": sample_case["guardian_case_id"] if sample_case else None, "document": sample_bill["source_document_path"], "expected_action": "Prepare a draft only; never submit a complaint automatically."},
        "03_collective_commons.json": {"scenario_name": "Small-cohort Commons opportunity", "synthetic": True, "campaign": sample_campaign, "expected_safety": "All participants hold explicit Commons demand consent; no raw income or transactions shared."},
        "04_agent_checkpoint_resume.json": {"scenario_name": "Resume long-running agent mission", "synthetic": True, "mission": missions[1], "steps": [r for r in mission_steps if r["mission_id"] == missions[1]["mission_id"]], "expected_safety": "Resume after last valid checkpoint and do not duplicate completed external side effects."},
        "05_offer_net_value_rejection.json": {"scenario_name": "Reject a negative net-benefit offer", "synthetic": True, "offers": sorted(offers, key=lambda o: Decimal(o["estimated_net_benefit_inr"]))[:5], "expected_rule": "Reject net benefit <= 0 and disclose all costs/commitments."},
    }
    for name, payload in scenarios.items(): (out_dir / "api_scenarios" / name).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # Dataset README and compliance guidance
    readme = f'''# MyEconomy Synthetic Economic Demo Dataset v1.0.0

**Generated:** {AS_OF.isoformat()}  
**Seed:** {seed}  
**Customers:** {len(customers)}  
**Households:** {len(households)}  
**Transactions:** {len(transactions):,}  
**All records are synthetic fixtures.** No production customer data, bank statement, Aadhaar, PAN, card number, UPI credential, real bill, real provider, government benefit or actual partner quote is included.

## What is included

- `csv/`: normalized CSV exports for every entity table.
- `jsonl/`: JSON Lines exports for streaming/ETL and embedding pipelines.
- `json/`: complete JSON array per entity.
- `sql/schema.sql` and `sql/seed.sql`: PostgreSQL-oriented DDL and seed data.
- `source_documents/invoices/`: synthetic HTML invoices, including clearly labelled anomaly fixtures.
- `source_documents/offer_terms/`: synthetic offer terms for multimodal and RAG ingestion tests.
- `api_scenarios/`: coherent pre-selected journeys for demo orchestration.
- `metadata/schema_catalog.json`: tables, columns and relationships.
- `metadata/data_dictionary.csv`: column-level dictionary.
- `metadata/business_rules.json`: consent, finance, offer, Commons, agent and VIVC rules.
- Additional financial and edge-feature tables cover budgets, goals, tax reminders, insurance, claims, crisis cases, risk defence and one-person enterprise operations.
- `metadata/validation_report.json`: machine validation results.
- `generate_synthetic_dataset.py`: deterministic generator; standard-library only.
- `validate_dataset.py`: reproducible integrity checks.

## Reproduce

```bash
python generate_synthetic_dataset.py --out ./synthetic_v1 --customers 120 --seed 20261103
python validate_dataset.py ./synthetic_v1
```

## Demo ethics and boundaries

All customer contacts use `.invalid` email domains and clearly invalid phone placeholders. Locations use broad locality clusters, not home addresses. KYC status is descriptive fixture metadata only; no government ID values are generated. Programmes and merchants are fictional. A match or benefit assessment is not an official eligibility decision. Provider offers, campaign participation, settlements, user value and mission outputs are simulations only. The dataset must never be used to contact anyone, request real payments, underwrite a loan or infer facts about a real person.

## Reconciliation and lifecycle semantics

Money is stored as decimal strings to avoid JSON/CSV binary floating-point ambiguity. Every row carries `data_class=SYNTHETIC_FIXTURE` or an equivalent synthetic flag. Foreign-key identifiers are stable within a seed. Transaction `cashflow_treatment` separates income, expense, refund and transfer so card repayments are not double-counted as new purchases. Consent grants are independent from household membership. Commons participants are backed by an active purpose-specific demand consent at signal time.

## Intended use

Use this dataset for local demo, schema validation, model evaluation, agent workflow replay, retrieval tests, dashboard prototyping and integration contract tests. Never present it as a live customer base or measured product impact.
'''
    (out_dir / "README.md").write_text(readme, encoding="utf-8")

    regulatory = f'''# Regulatory-aware dataset and workflow rules (India-oriented)

**Research snapshot:** {AS_OF.isoformat()} (Asia/Kolkata). This is engineering guidance, not legal advice or a compliance certification. Actual applicability depends on the product role, processing, sectoral status, partner contracts, data location, users and current notifications. Re-check official sources before deployment.

## DPDP Act and Rules — staged commencement matters

The Digital Personal Data Protection Act, 2023 commencement notification G.S.R. 843(E), dated 13 November 2025, uses staged commencement. As of 3 November 2026, the Act's provisions in sections 1(2), 2, 18–26, 35, 38–43 and sections 44(1) and 44(3) commenced on publication; section 6(9) and section 27(1)(d) are scheduled one year after publication (13 November 2026); and sections 3–5, sections 6(1)–6(8) and 6(10), sections 7–17, section 27 except clause (d), sections 28–34, 36–37 and section 44(2) are scheduled eighteen months after publication (13 May 2027). The DPDP Rules, 2025 notification G.S.R. 846(E) has a corresponding staged commencement: Rules 1, 2 and 17–21 commenced on publication; Rule 4 is scheduled one year after publication (13 November 2026); Rules 3, 5–16, 22 and 23 are scheduled eighteen months after publication (13 May 2027).

**Engineering posture:** build toward the complete notice, purpose limitation, specific consent, withdrawal, rights handling, security safeguards, breach handling, retention/deletion, processor governance and audit expectations now. Do not incorrectly state that every substantive DPDP provision/rule is already in force on the snapshot date. This timing is based on the cited commencement notifications; legal counsel should validate amendments/corrigenda and applicability before launch.

## RBI Account Aggregator framework

The RBI NBFC-AA Directions require explicit customer consent and a standardised consent artefact with the customer's identity, type of financial information, purpose, recipient, notification address, creation/expiry and AA identity/signature; the directions also include revocation and auditability requirements. The Government's Account Aggregator Framework page says data is not retrieved/shared/transferred without explicit customer consent and describes FIPs and FIUs; FIUs are entities registered with and regulated by a financial sector regulator.

**Architecture implication:** MyEconomy must not pretend it can directly scrape bank credentials or act as an Account Aggregator. Bank-data retrieval must go through an appropriately authorised AA/FIU partnership and a valid consent artefact; role eligibility and licensing need legal review. AA is a data-sharing framework, not permission for a new app to initiate transactions. Keep consent scope, recipient, purpose, duration, notification and revocation in a dedicated ledger.

## RBI digital lending guidance (conditional)

RBI's 2 September 2022 Digital Lending Guidelines require regulated entities to ensure need-based data collection with prior explicit borrower consent and audit trail; borrower discretion over specific data, third-party disclosure, retention and revocation; explicit third-party sharing consent; and controls over personal-data storage. This project is not a lender in the current scope. If any future feature intermediates, arranges or supports digital lending, map the exact regulated-entity/LSP/DLA role and applicable current RBI requirements before building it. Do not generate loan offers or underwriting decisions from this dataset.

## KYC and identity

Do not create realistic-looking Aadhaar, PAN, bank-account, card or UPI identifiers. The dataset intentionally contains none. KYC requirements belong to the relevant regulated entity and partner flow; a status field in a demo fixture is not KYC verification. Consult the current RBI KYC Direction and the responsible regulated entity before integrating.

## Safe fixture rules

- Every record is labelled synthetic; no record is sourced from a real individual.
- Email domain `.invalid`; phone numbers use deliberately invalid `+91-00000-xxxxx` placeholders.
- Fictional provider/benefit/offer names are prefixed `DEMO` or `SYNTH`.
- No precise residential addresses, identity documents or credentials.
- Do not send fixture data to providers or real payment systems.
- Consent, Commons quorum, value ledger, offer net-benefit and workflow-retry rules are encoded separately in `metadata/business_rules.json`.

## Official and primary references

1. DPDP Act commencement notification G.S.R. 843(E), 13 Nov 2025: https://www.meity.gov.in/static/uploads/2025/11/c56ceae6c383460ca69577428d36828b.pdf
2. DPDP Rules notification G.S.R. 846(E), 13 Nov 2025: https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf
3. MeitY DPDP Rules and enforcement timeline portal: https://www.meity.gov.in/documents/act-and-policies/digital-personal-data-protection-rules-2025-gDOxUjMtQWa?pageTitle=Digital-Personal-Data-Protection-Rules-2025%3B
4. Department of Financial Services — Account Aggregator framework: https://www.financialservices.gov.in/account-aggregator-framework
5. RBI Master Direction — NBFC Account Aggregator Directions, 2016 (updated 6 Sep 2024): https://systemhealth.rbi.org.in/Scripts/BS_ViewMasDirections.aspx_id%3D10598%281%29.html
6. RBI Guidelines on Digital Lending, 2 Sep 2022: https://systemhealth.rbi.org.in/Scripts/NotificationUser.aspx_Id%3D12382%26Mode%3D0.html
7. RBI Master Direction — KYC Direction, 2016 (current update should be checked at integration time): https://old.rbi.org.in/commonman/English/Scripts/MasterDirection.aspx
'''
    (out_dir / "REGULATORY_AND_DATA_RULES.md").write_text(regulatory, encoding="utf-8")

    # Machine validation: referential integrity, uniqueness, amount math, consent, synthetic labels.
    def ids(table: str, col: str) -> set[str]: return {str(r[col]) for r in TABLES[table] if r.get(col) not in [None, ""]}
    checks: dict[str, Any] = {}
    fk_checks = []
    for field, target in rels.items():
        t, col = field.split("."); rt, rc = target.split(".")
        target_ids = ids(rt, rc)
        missing = [r.get(col) for r in TABLES[t] if r.get(col) not in [None, ""] and r.get(col) not in target_ids]
        fk_checks.append({"relationship": field + " -> " + target, "missing_count": len(missing), "passed": len(missing) == 0})
    checks["foreign_keys"] = {"passed": all(x["passed"] for x in fk_checks), "checks": fk_checks}
    unique_checks = []
    for table, pk in primary_keys.items():
        vals = [r[pk] for r in TABLES[table]]
        unique_checks.append({"table": table, "pk": pk, "unique": len(vals) == len(set(vals)), "row_count": len(vals)})
    checks["primary_keys"] = {"passed": all(x["unique"] for x in unique_checks), "checks": unique_checks}
    offer_bad = []
    for o in offers:
        expected = Decimal(o["discount_value_inr"]) + Decimal(o["sponsor_credit_inr"]) - Decimal(o["required_incremental_spend_inr"]) - Decimal(o["fees_inr"]) - Decimal(o["recurring_commitment_cost_inr"])
        if expected != Decimal(o["estimated_net_benefit_inr"]): offer_bad.append(o["offer_id"])
    checks["offer_net_benefit"] = {"passed": not offer_bad, "mismatches": offer_bad, "formula": "discount + sponsor_credit - incremental_spend - fees - recurring_commitment"}
    tx_bad = [t["transaction_id"] for t in transactions if (t["cashflow_treatment"] in ["INCOME", "REFUND"] and t["direction"] != "CREDIT") or (t["cashflow_treatment"] == "EXPENSE" and t["direction"] != "DEBIT")]
    checks["transaction_direction"] = {"passed": not tx_bad, "mismatches": len(tx_bad)}
    bill_bad = []
    for b in bills:
        line_sum = sum((Decimal(x["line_total_inr"]) for x in bill_lines if x["bill_id"] == b["bill_id"]), Decimal("0"))
        if line_sum != Decimal(b["total_due_inr"]): bill_bad.append(b["bill_id"])
    checks["bill_line_reconciliation"] = {"passed": not bill_bad, "mismatches": bill_bad}
    campaign_bad = [c["campaign_id"] for c in campaigns if c["participant_count_fixture"] != sum(1 for p in campaign_participants if p["campaign_id"] == c["campaign_id"]) or c["minimum_participants"] != 5]
    checks["commons_campaign_counts"] = {"passed": not campaign_bad, "mismatches": campaign_bad}

    consent_lookup = {(r["customer_id"], r["purpose"]): r for r in consents}
    signal_day = date(2026, 10, 20)
    def is_active_on_signal(consent_row: dict[str, Any] | None) -> bool:
        if not consent_row or consent_row.get("status") == "NOT_GRANTED": return False
        granted = date.fromisoformat(consent_row["granted_at"][:10]) if consent_row.get("granted_at") else None
        expiry = date.fromisoformat(consent_row["expires_at"][:10]) if consent_row.get("expires_at") else None
        revoked = date.fromisoformat(consent_row["revoked_at"][:10]) if consent_row.get("revoked_at") else None
        return bool(granted and granted <= signal_day and (expiry is None or expiry >= signal_day) and (revoked is None or revoked > signal_day))
    commons_bad = [d["demand_signal_id"] for d in demand_signals if not is_active_on_signal(consent_lookup.get((d["customer_id"], "COMMONS_DEMAND_AGGREGATION")))]
    checks["commons_consent"] = {"passed": not commons_bad, "unauthorized_signal_count": len(commons_bad)}
    synthetic_bad = [name for name, rows in TABLES.items() for r in rows if r.get("data_class") != "SYNTHETIC_FIXTURE"]
    checks["synthetic_labeling"] = {"passed": not synthetic_bad, "unlabelled_rows": len(synthetic_bad)}
    no_identity_ids = not any(k.lower() in ["aadhaar", "pan_number", "upi_pin", "card_number", "bank_password"] for rows in TABLES.values() for r in rows for k in r)
    checks["no_real_identifiers"] = {"passed": no_identity_ids}
    checks["dataset_date_window"] = {"start": START.isoformat(), "end": END.isoformat(), "as_of": AS_OF.isoformat()}
    report = {"dataset": "MyEconomy Synthetic Economic Demo Dataset", "version": "1.0.0", "generated_at": iso_dt(AS_OF), "seed": seed, "synthetic_only": True, "passed": all(v.get("passed", True) for v in checks.values() if isinstance(v, dict)), "checks": checks, "row_counts": {k: len(v) for k,v in TABLES.items()}}
    (out_dir / "metadata" / "validation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Hash manifest of all data files before manifest itself.
    manifest_items = []
    for p in sorted(out_dir.rglob("*")):
        if p.is_file() and p.name != "manifest.json":
            b = p.read_bytes()
            manifest_items.append({"path": str(p.relative_to(out_dir)), "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()})
    manifest = {"dataset": "MyEconomy Synthetic Economic Demo Dataset", "version": "1.0.0", "synthetic_only": True, "seed": seed, "generated_date": AS_OF.isoformat(), "files": manifest_items, "table_counts": report["row_counts"], "total_rows": sum(report["row_counts"].values())}
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {"report": report, "manifest": manifest, "counts": report["row_counts"]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("synthetic_v1"))
    parser.add_argument("--customers", type=int, default=120)
    parser.add_argument("--seed", type=int, default=SEED_DEFAULT)
    args = parser.parse_args()
    result = generate(args.out, args.customers, args.seed)
    print(json.dumps({"output": str(args.out), "passed": result["report"]["passed"], "counts": result["counts"], "total_rows": result["manifest"]["total_rows"]}, indent=2))
    if not result["report"]["passed"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
