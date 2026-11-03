#!/usr/bin/env python3
"""Independent integrity validator for MyEconomy Synthetic Demo Dataset."""
from __future__ import annotations
import csv, json, sys, hashlib
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent

def rows(name):
    with (ROOT / "csv" / f"{name}.csv").open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

schema=json.loads((ROOT/"metadata"/"schema_catalog.json").read_text(encoding="utf-8"))
rels=schema["relationships"]
counts={name:len(rows(name)) for name in schema["tables"]}
checks={}
# Primary keys from the catalogue + known entity key naming convention.
for table, records in schema["tables"].items():
    key=next((c for c in records["columns"] if c.endswith("_id") and c not in ["customer_id","provider_id","account_id","household_id","bill_id","loan_id","offer_id","campaign_id","mission_id","enterprise_id"]), None)
    # Use generated table name convention as robust fallback.
    primary={"customers":"customer_id","households":"household_id","household_memberships":"membership_id","consents":"consent_id","providers":"provider_id","accounts":"account_id","recurring_obligations":"obligation_id","loans":"loan_id","loan_installments":"installment_id","bills":"bill_id","bill_line_items":"bill_line_id","subscriptions":"subscription_id","transactions":"transaction_id","benefit_programs":"benefit_program_id","benefit_assessments":"assessment_id","benefit_applications":"application_id","skills":"skill_id","opportunities":"opportunity_id","opportunity_matches":"match_id","offers":"offer_id","resource_listings":"resource_id","demand_signals":"demand_signal_id","commons_campaigns":"campaign_id","commons_participants":"campaign_participant_id","guardian_cases":"guardian_case_id","evidence_documents":"evidence_document_id","agent_missions":"mission_id","agent_mission_steps":"mission_step_id","value_events":"value_event_id","budget_plans":"budget_plan_id","budget_envelopes":"budget_envelope_id","financial_goals":"financial_goal_id","tax_obligations":"tax_obligation_id","insurance_policies":"insurance_policy_id","insurance_claims":"insurance_claim_id","crisis_cases":"crisis_case_id","risk_signals":"risk_signal_id","micro_enterprises":"enterprise_id","enterprise_products":"enterprise_product_id","enterprise_orders":"enterprise_order_id","partner_settlements":"settlement_id","audit_events":"audit_event_id"}
    pk=primary[table]; values=[r[pk] for r in rows(table)]
    checks[f"unique:{table}.{pk}"]=len(values)==len(set(values))
# Foreign keys
for field,target in rels.items():
    table,col=field.split("."); rt,rc=target.split(".")
    target_ids={r[rc] for r in rows(rt)}
    checks[f"fk:{field}->{target}"]=all((not r.get(col)) or r[col] in target_ids for r in rows(table))
# Synthetic-only labels and unusable contact values
unlabelled=[]
for table in schema["tables"]:
    for r in rows(table):
        if r.get("data_class") != "SYNTHETIC_FIXTURE": unlabelled.append((table,r))
checks["all_rows_synthetic_labeled"]=not unlabelled
customers=rows("customers")
checks["all_customer_emails_non_deliverable"]=all(c["email"].endswith("@example.invalid") for c in customers)
checks["all_customer_phone_placeholders_invalid"]=all(c["phone"].startswith("+91-00000-") for c in customers)
checks["no_direct_identity_document_values"]=not any(k.lower() in {"aadhaar","aadhaar_number","pan","pan_number","upi_pin","card_pan","bank_password"} for t in schema["tables"] for k in schema["tables"][t]["columns"])
# Transaction side rules
bad_tx=[]
for t in rows("transactions"):
    if t["cashflow_treatment"] in ["INCOME","REFUND"] and t["direction"]!="CREDIT": bad_tx.append(t["transaction_id"])
    if t["cashflow_treatment"]=="EXPENSE" and t["direction"]!="DEBIT": bad_tx.append(t["transaction_id"])
    if Decimal(t["amount_inr"])<=0: bad_tx.append(t["transaction_id"])
checks["transaction_direction_and_positive_amount"]=not bad_tx
# Bill line reconciliation
line_totals=defaultdict(lambda:Decimal("0"))
for l in rows("bill_line_items"): line_totals[l["bill_id"]]+=Decimal(l["line_total_inr"])
bill_mismatches=[b["bill_id"] for b in rows("bills") if line_totals[b["bill_id"]]!=Decimal(b["total_due_inr"])]
checks["bill_line_totals_reconcile"]=not bill_mismatches
# Offer economics
offer_mismatches=[]
for o in rows("offers"):
    net=Decimal(o["discount_value_inr"])+Decimal(o["sponsor_credit_inr"])-Decimal(o["required_incremental_spend_inr"])-Decimal(o["fees_inr"])-Decimal(o["recurring_commitment_cost_inr"])
    if net!=Decimal(o["estimated_net_benefit_inr"]): offer_mismatches.append(o["offer_id"])
    if (net>0)!=(o["decision_fixture"]=="RECOMMEND"): offer_mismatches.append(o["offer_id"])
checks["offer_net_benefit_and_decision"]=not offer_mismatches
# Commons: event-time consent, category/location groups and privacy fields.
consents={(c["customer_id"],c["purpose"]):c for c in rows("consents")}
signal_date=date(2026,10,20)
def active_on(r, when):
    if not r or not r.get("granted_at"): return False
    granted=date.fromisoformat(r["granted_at"][:10]); expiry=date.fromisoformat(r["expires_at"][:10]) if r.get("expires_at") else None; revoked=date.fromisoformat(r["revoked_at"][:10]) if r.get("revoked_at") else None
    return granted<=when and (expiry is None or expiry>=when) and (revoked is None or revoked>when)
demand=rows("demand_signals")
checks["commons_signal_has_time_valid_consent"]=all(active_on(consents.get((d["customer_id"],"COMMONS_DEMAND_AGGREGATION")),signal_date) for d in demand)
checks["commons_signals_exclude_raw_financial_data"]=all(d["raw_transaction_data_included"]=="True" or d["raw_transaction_data_included"]=="False" for d in demand) and all(d["raw_transaction_data_included"]=="False" for d in demand)
participants=rows("commons_participants"); campaigns={c["campaign_id"]:c for c in rows("commons_campaigns")}
checks["commons_participant_foreign_and_quorum_count"]=all(p["campaign_id"] in campaigns for p in participants) and all(int(c["participant_count_fixture"])==sum(1 for p in participants if p["campaign_id"]==c["campaign_id"]) for c in campaigns.values())
checks["commons_campaign_one_locality"]=all(len({(p["city"],p["locality_cluster"]) for p in demand if any(x["demand_signal_id"]==p["demand_signal_id"] and x["campaign_id"]==c["campaign_id"] for x in participants)})<=1 for c in campaigns.values())
# Campaign counts, quorum states and candidate offer coherence.
campaign_rows=rows("commons_campaigns")
participant_rows=rows("commons_participants")
offers_by_id={o["offer_id"]:o for o in rows("offers")}
quorum_ok=True
campaign_offer_ok=True
for c in campaign_rows:
    actual=sum(1 for p in participant_rows if p["campaign_id"]==c["campaign_id"])
    quorum=int(c["minimum_participants"])
    if int(c["participant_count_fixture"]) != actual:
        quorum_ok=False
    if c["campaign_status"].startswith("QUORUM_REACHED") and actual < quorum:
        quorum_ok=False
    offer_id=c.get("linked_offer_id")
    if offer_id:
        o=offers_by_id.get(offer_id)
        if not o or o["service_category"] != c["service_category"] or o["city"] != c["city"]:
            campaign_offer_ok=False
checks["commons_campaign_counts_and_quorum_state"]=quorum_ok
checks["commons_linked_offer_category_and_city_match"]=campaign_offer_ok
# VIVC must never masquerade as real proof
checks["vivc_synthetic_only"]=all(v["verification_level"]=="SYNTHETIC_FIXTURE_ONLY" and v["external_provider_confirmation"]=="False" for v in rows("value_events"))
# Document manifest check
multi=json.loads((ROOT/"metadata"/"multimodal_document_manifest.json").read_text(encoding="utf-8"))
pdf_ok=True
for m in multi:
    p=ROOT/m["pdf_path"]
    pdf_ok &= p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==m["pdf_sha256"] and p.read_bytes().startswith(b"%PDF")
    png_path = ROOT / m.get("png_path", "")
    if m.get("png_path"):
        pdf_ok &= png_path.exists() and hashlib.sha256(png_path.read_bytes()).hexdigest()==m.get("png_sha256") and png_path.read_bytes().startswith(b"\x89PNG")
checks["multimodal_pdf_and_png_manifest_hashes"]=bool(pdf_ok)
# CSV/JSONL/JSON parity count
export_parity = True
for t in schema["tables"]:
    csv_file=ROOT/"csv"/f"{t}.csv"
    jsonl_file=ROOT/"jsonl"/f"{t}.jsonl"
    json_file=ROOT/"json"/f"{t}.json"
    if not (csv_file.exists() and jsonl_file.exists() and json_file.exists()):
        export_parity=False
        continue
    with csv_file.open(encoding="utf-8-sig", newline="") as f:
        csv_count=sum(1 for _ in csv.DictReader(f))
    jsonl_count=sum(1 for line in jsonl_file.read_text(encoding="utf-8").splitlines() if line.strip())
    json_count=len(json.loads(json_file.read_text(encoding="utf-8")))
    export_parity &= csv_count==jsonl_count==json_count==counts[t]
checks["all_export_formats_row_counts"]=export_parity
# Check the embedded SQLite artifact when it has been built.
sqlite_path=ROOT/"sqlite"/"myeconomy_synthetic_demo.sqlite3"
if sqlite_path.exists():
    import sqlite3
    db=sqlite3.connect(sqlite_path)
    integrity=db.execute("PRAGMA integrity_check").fetchone()[0]
    fk_violations=db.execute("PRAGMA foreign_key_check").fetchall()
    sqlite_counts={t:db.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in schema["tables"]}
    db.close()
    checks["sqlite_integrity_and_foreign_keys"]=integrity=="ok" and not fk_violations and all(sqlite_counts[t]==counts[t] for t in counts)
else:
    checks["sqlite_integrity_and_foreign_keys"]=False
report={"dataset":schema["dataset_name"],"version":schema["version"],"synthetic_only":True,"independent_validator":"validate_dataset.py","checks":checks,"passed":all(checks.values()),"table_counts":counts,"total_rows":sum(counts.values()),"multimodal_documents":len(multi)}
(ROOT/"metadata"/"independent_validation_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
(ROOT/"metadata"/"validation_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(report,indent=2))
if not report["passed"]: raise SystemExit(1)
