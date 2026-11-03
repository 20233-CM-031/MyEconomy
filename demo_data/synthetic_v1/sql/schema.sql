-- MyEconomy synthetic demo fixtures. Never use as production customer data.

-- PostgreSQL 15+ compatible DDL. All personal-looking values are generated placeholders.

BEGIN;

SET client_min_messages TO WARNING;

CREATE TABLE IF NOT EXISTS "customers" (
  "customer_id" TEXT NOT NULL,
  "display_name" TEXT,
  "email" TEXT,
  "phone" TEXT,
  "age_years" INTEGER,
  "age_band" TEXT,
  "city" TEXT,
  "locality_cluster" TEXT,
  "persona" TEXT,
  "employment_status" TEXT,
  "primary_language" TEXT,
  "monthly_income_inr_estimate" TEXT,
  "income_volatility" TEXT,
  "dependants_count" INTEGER,
  "primary_goal" TEXT,
  "economic_context" TEXT,
  "kyc_status_fixture" TEXT,
  "identity_document_status" TEXT,
  "account_status" TEXT,
  "synthetic" BOOLEAN,
  "data_class" TEXT,
  PRIMARY KEY ("customer_id")
);

CREATE TABLE IF NOT EXISTS "households" (
  "household_id" TEXT NOT NULL,
  "display_label" TEXT,
  "city" TEXT,
  "locality_cluster" TEXT,
  "household_type" TEXT,
  "member_count" INTEGER,
  "owner_customer_id" TEXT,
  "shared_financial_profile_enabled" BOOLEAN,
  "data_class" TEXT,
  PRIMARY KEY ("household_id")
);

CREATE TABLE IF NOT EXISTS "household_memberships" (
  "membership_id" TEXT NOT NULL,
  "household_id" TEXT,
  "customer_id" TEXT,
  "role" TEXT,
  "status" TEXT,
  "joined_at" TIMESTAMPTZ,
  "financial_data_access" TEXT,
  "data_class" TEXT,
  PRIMARY KEY ("membership_id"),
  FOREIGN KEY ("household_id") REFERENCES "households"("household_id"),
  FOREIGN KEY ("customer_id") REFERENCES "customers"("customer_id"),
  UNIQUE ("household_id", "customer_id")
);

CREATE TABLE IF NOT EXISTS "consents" (
  "consent_id" TEXT NOT NULL,
  "customer_id" TEXT,
  "purpose" TEXT,
  "data_categories_json" JSONB,
  "recipient" TEXT,
  "status" TEXT,
  "granted_at" TIMESTAMPTZ,
  "expires_at" TIMESTAMPTZ,
  "revoked_at" TIMESTAMPTZ,
  "notice_version" TEXT,
  "consent_receipt" TEXT,
  "withdrawal_channel" TEXT,
  "data_class" TEXT,
  PRIMARY KEY ("consent_id"),
  FOREIGN KEY ("customer_id") REFERENCES "customers"("customer_id")
);

CREATE TABLE IF NOT EXISTS "providers" (
  "provider_id" TEXT NOT NULL,
  "provider_name" TEXT,
  "provider_type" TEXT,
  "service_city" TEXT,
  "service_zone" TEXT,
  "verification_status" TEXT,
  "partner_status" TEXT,
  "settlement_currency" TEXT,
  "data_class" TEXT,
  PRIMARY KEY ("provider_id")
);

CREATE TABLE IF NOT EXISTS "accounts" (
  "account_id" TEXT NOT NULL,
  "customer_id" TEXT,
  "institution_code" TEXT,
  "account_type" TEXT,
  "currency" TEXT,
  "masked_reference" TEXT,
  "account_status" TEXT,
  "opening_balance_inr" NUMERIC(20,2),
  "balance_semantics" TEXT,
  "data_class" TEXT,
  PRIMARY KEY ("account_id"),
  FOREIGN KEY ("customer_id") REFERENCES "customers"("customer_id")
);

CREATE TABLE IF NOT EXISTS "recurring_obligations" (
  "obligation_id" TEXT NOT NULL,
  "customer_id" TEXT,
  "obligation_type" TEXT,
  "category" TEXT,
  "payee_label" TEXT,
  "expected_amount_inr" NUMERIC(20,2),
  "frequency" TEXT,
  "due_day" TEXT,
  "autopay_enabled" BOOLEAN,
  "essential" BOOLEAN,
  "status" TEXT,
  "first_due_date" DATE,
  "data_class" TEXT,
  PRIMARY KEY ("obligation_id"),
  FOREIGN KEY ("customer_id") REFERENCES "customers"("customer_id")
);

CREATE TABLE IF NOT EXISTS "loans" (
  "loan_id" TEXT NOT NULL,
  "customer_id" TEXT,
  "loan_type" TEXT,
  "lender_label" TEXT,
  "principal_inr" NUMERIC(20,2),
  "annual_interest_rate_percent" NUMERIC(8,4),
  "tenure_months" INTEGER,
  "emi_inr" NUMERIC(20,2),
  "start_date" DATE,
  "loan_status" TEXT,
  "remaining_principal_fixture_inr" NUMERIC(20,2),
  "secured_status" TEXT,
  "data_class" TEXT,
  PRIMARY KEY ("loan_id"),
  FOREIGN KEY ("customer_id") REFERENCES "customers"("customer_id")
);

CREATE TABLE IF NOT EXISTS "loan_installments" (
  "installment_id" TEXT NOT NULL,
  "loan_id" TEXT,
  "customer_id" TEXT,
  "installment_number" INTEGER,
  "due_date" DATE,
  "principal_component_inr" NUMERIC(20,2),
  "interest_component_inr" NUMERIC(20,2),
  "total_due_inr" NUMERIC(20,2),
  "status" TEXT,
  "paid_date" DATE,
  "late_fee_inr" NUMERIC(20,2),
  "data_class" TEXT,
  PRIMARY KEY ("installment_id"),
  FOREIGN KEY ("loan_id") REFERENCES "loans"("loan_id"),
  FOREIGN KEY ("customer_id") REFERENCES "customers"("customer_id")
);

CREATE TABLE IF NOT EXISTS "bills" (
  "bill_id" TEXT NOT NULL,
  "customer_id" TEXT,
  "provider_id" TEXT,
  "bill_type" TEXT,
  "invoice_number" TEXT,
  "issue_date" DATE,
  "due_date" DATE,
  "currency" TEXT,
  "subtotal_inr" NUMERIC(20,2),
  "tax_inr" NUMERIC(20,2),
  "total_due_inr" NUMERIC(20,2),
  "amount_paid_inr" NUMERIC(20,2),
  "status" TEXT,
  "anomaly_label" TEXT,
  "prior_period_total_inr" NUMERIC(20,2),
  "source_document_path" TEXT,
  "document_authenticity" TEXT,
  "data_class" TEXT,
  PRIMARY KEY ("bill_id"),
  FOREIGN KEY ("customer_id") REFERENCES "customers"("customer_id"),
  FOREIGN KEY ("provider_id") REFERENCES "providers"("provider_id")
);

CREATE TABLE IF NOT EXISTS "bill_line_items" (
  "bill_line_id" TEXT NOT NULL,
  "bill_id" TEXT,
  "description_code" TEXT,
  "description" TEXT,
  "quantity" INTEGER,
  "unit_price_inr" NUMERIC(20,2),
  "line_total_inr" NUMERIC(20,2),
  "taxable" BOOLEAN,
  "synthetic" BOOLEAN,
  "data_class" TEXT,
  PRIMARY KEY ("bill_line_id"),
  FOREIGN KEY ("bill_id") REFERENCES "bills"("bill_id")
);

CREATE TABLE IF NOT EXISTS "subscriptions" (
  "subscription_id" TEXT NOT NULL,
  "customer_id" TEXT,
  "service_name" TEXT,
  "billing_cycle" TEXT,
  "current_price_inr" NUMERIC(20,2),
  "start_date" DATE,
  "next_renewal_date" DATE,
  "status" TEXT,
  "auto_renew" BOOLEAN,
  "price_change_flag" BOOLEAN,
  "price_before_change_inr" NUMERIC(20,2),
  "cancellation_channel" TEXT,
  "data_class" TEXT,
  PRIMARY KEY ("subscription_id"),
  FOREIGN KEY ("customer_id") REFERENCES "customers"("customer_id")
);

CREATE TABLE IF NOT EXISTS "transactions" (
  "transaction_id" TEXT NOT NULL,
  "customer_id" TEXT,
  "account_id" TEXT,
  "transaction_date" DATE,
  "posted_at" TIMESTAMPTZ,
  "direction" TEXT,
  "transaction_type" TEXT,
  "cashflow_treatment" TEXT,
  "category" TEXT,
  "amount_inr" NUMERIC(20,2),
  "currency" TEXT,
  "counterparty_label" TEXT,
  "provider_id" TEXT,
  "obligation_id" TEXT,
  "bill_id" TEXT,
  "loan_installment_id" TEXT,
  "subscription_id" TEXT,
  "transfer_group_id" TEXT,
  "payment_rail" TEXT,
  "status" TEXT,
  "reference" TEXT,
  "data_class" TEXT,
  PRIMARY KEY ("transaction_id"),
  FOREIGN KEY ("customer_id") REFERENCES "customers"("customer_id"),
  FOREIGN KEY ("account_id") REFERENCES "accounts"("account_id")
);

CREATE TABLE IF NOT EXISTS "benefit_programs" (
  "benefit_program_id" TEXT NOT NULL,
  "program_name" TEXT,
  "benefit_category" TEXT,
  "max_support_inr" NUMERIC(20,2),
  "eligibility_rule_json" JSONB,
  "source_type" TEXT,
  "external_source_url" TEXT,
  "application_channel" TEXT,
  "program_status" TEXT,
  "last_rule_reviewed" TEXT,
  "disclaimer" TEXT,
  "data_class" TEXT,
  PRIMARY KEY ("benefit_program_id")
);

CREATE TABLE IF NOT EXISTS "benefit_assessments" (
  "assessment_id" TEXT NOT NULL,
  "customer_id" TEXT,
  "benefit_program_id" TEXT,
  "assessment_date" DATE,
  "assessment_status" TEXT,
  "rule_checks_json" JSONB,
  "matched_rule_count" INTEGER,
  "total_rule_count" INTEGER,
  "estimated_support_cap_inr" NUMERIC(20,2),
  "official_confirmation" TEXT,
  "data_class" TEXT,
  PRIMARY KEY ("assessment_id"),
  FOREIGN KEY ("customer_id") REFERENCES "customers"("customer_id"),
  FOREIGN KEY ("benefit_program_id") REFERENCES "benefit_programs"("benefit_program_id")
);

CREATE TABLE IF NOT EXISTS "benefit_applications" (
  "application_id" TEXT NOT NULL,
  "assessment_id" TEXT,
  "customer_id" TEXT,
  "benefit_program_id" TEXT,
  "application_status" TEXT,
  "submission_mode" TEXT,
  "required_documents_json" JSONB,
  "submitted_at" TEXT,
  "decision_status" TEXT,
  "data_class" TEXT,
  PRIMARY KEY ("application_id"),
  FOREIGN KEY ("assessment_id") REFERENCES "benefit_assessments"("assessment_id"),
  FOREIGN KEY ("customer_id") REFERENCES "customers"("customer_id")
);

CREATE TABLE IF NOT EXISTS "skills" (
  "skill_id" TEXT NOT NULL,
  "customer_id" TEXT,
  "skill_code" TEXT,
  "skill_label" TEXT,
  "proficiency_level" TEXT,
  "evidence_status" TEXT,
  "available_hours_weekly" INTEGER,
  "monetization_consent" BOOLEAN,
  "data_class" TEXT,
  PRIMARY KEY ("skill_id"),
  FOREIGN KEY ("customer_id") REFERENCES "customers"("customer_id")
);

CREATE TABLE IF NOT EXISTS "opportunities" (
  "opportunity_id" TEXT NOT NULL,
  "title" TEXT,
  "required_skill_code" TEXT,
  "opportunity_type" TEXT,
  "city" TEXT,
  "remote_allowed" BOOLEAN,
  "estimated_pay_inr" NUMERIC(20,2),
  "time_commitment_hours" TEXT,
  "status" TEXT,
  "application_deadline" DATE,
  "provider_id" TEXT,
  "source_type" TEXT,
  "data_class" TEXT,
  PRIMARY KEY ("opportunity_id")
);

CREATE TABLE IF NOT EXISTS "opportunity_matches" (
  "match_id" TEXT NOT NULL,
  "customer_id" TEXT,
  "opportunity_id" TEXT,
  "match_score" INTEGER,
  "score_components_json" JSONB,
  "match_status" TEXT,
  "requires_user_review" BOOLEAN,
  "data_class" TEXT,
  PRIMARY KEY ("match_id"),
  FOREIGN KEY ("customer_id") REFERENCES "customers"("customer_id"),
  FOREIGN KEY ("opportunity_id") REFERENCES "opportunities"("opportunity_id")
);

CREATE TABLE IF NOT EXISTS "offers" (
  "offer_id" TEXT NOT NULL,
  "provider_id" TEXT,
  "offer_title" TEXT,
  "service_category" TEXT,
  "city" TEXT,
  "reference_price_inr" NUMERIC(20,2),
  "offer_price_inr" NUMERIC(20,2),
  "discount_value_inr" NUMERIC(20,2),
  "sponsor_credit_inr" NUMERIC(20,2),
  "required_incremental_spend_inr" NUMERIC(20,2),
  "fees_inr" NUMERIC(20,2),
  "recurring_commitment_cost_inr" NUMERIC(20,2),
  "estimated_net_benefit_inr" NUMERIC(20,2),
  "min_group_size" INTEGER,
  "valid_until" DATE,
  "decision_fixture" TEXT,
  "decision_rule" TEXT,
  "terms_status" TEXT,
  "data_class" TEXT,
  PRIMARY KEY ("offer_id"),
  FOREIGN KEY ("provider_id") REFERENCES "providers"("provider_id")
);

CREATE TABLE IF NOT EXISTS "resource_listings" (
  "resource_id" TEXT NOT NULL,
  "owner_customer_id" TEXT,
  "resource_type" TEXT,
  "description" TEXT,
  "city" TEXT,
  "locality_cluster" TEXT,
  "capacity_quantity" INTEGER,
  "capacity_unit" TEXT,
  "availability_window" TEXT,
  "verification_status" TEXT,
  "listing_status" TEXT,
  "data_class" TEXT,
  PRIMARY KEY ("resource_id"),
  FOREIGN KEY ("owner_customer_id") REFERENCES "customers"("customer_id")
);

CREATE TABLE IF NOT EXISTS "demand_signals" (
  "demand_signal_id" TEXT NOT NULL,
  "customer_id" TEXT,
  "consent_purpose" TEXT,
  "service_category" TEXT,
  "city" TEXT,
  "locality_cluster" TEXT,
  "quantity_band" TEXT,
  "price_band_inr" NUMERIC(20,2),
  "aggregatable" BOOLEAN,
  "raw_transaction_data_included" BOOLEAN,
  "signal_date" DATE,
  "status" TEXT,
  "data_class" TEXT,
  PRIMARY KEY ("demand_signal_id"),
  FOREIGN KEY ("customer_id") REFERENCES "customers"("customer_id")
);

CREATE TABLE IF NOT EXISTS "commons_campaigns" (
  "campaign_id" TEXT NOT NULL,
  "campaign_title" TEXT,
  "service_category" TEXT,
  "city" TEXT,
  "locality_cluster" TEXT,
  "minimum_participants" INTEGER,
  "participant_count_fixture" INTEGER,
  "campaign_status" TEXT,
  "linked_offer_id" TEXT,
  "funding_source" TEXT,
  "aggregate_only" BOOLEAN,
  "individual_income_or_transactions_exposed" BOOLEAN,
  "data_class" TEXT,
  PRIMARY KEY ("campaign_id")
);

CREATE TABLE IF NOT EXISTS "commons_participants" (
  "campaign_participant_id" TEXT NOT NULL,
  "campaign_id" TEXT,
  "customer_id" TEXT,
  "demand_signal_id" TEXT,
  "consent_purpose" TEXT,
  "participation_status" TEXT,
  "individual_data_disclosed_to_provider" BOOLEAN,
  "data_class" TEXT,
  PRIMARY KEY ("campaign_participant_id"),
  FOREIGN KEY ("campaign_id") REFERENCES "commons_campaigns"("campaign_id"),
  FOREIGN KEY ("customer_id") REFERENCES "customers"("customer_id"),
  FOREIGN KEY ("demand_signal_id") REFERENCES "demand_signals"("demand_signal_id")
);

CREATE TABLE IF NOT EXISTS "guardian_cases" (
  "guardian_case_id" TEXT NOT NULL,
  "customer_id" TEXT,
  "bill_id" TEXT,
  "case_type" TEXT,
  "severity" TEXT,
  "case_status" TEXT,
  "finding_summary" TEXT,
  "model_confidence_fixture" NUMERIC(5,3),
  "evidence_required" BOOLEAN,
  "external_complaint_submitted" BOOLEAN,
  "outcome_status" TEXT,
  "data_class" TEXT,
  PRIMARY KEY ("guardian_case_id"),
  FOREIGN KEY ("customer_id") REFERENCES "customers"("customer_id"),
  FOREIGN KEY ("bill_id") REFERENCES "bills"("bill_id")
);

CREATE TABLE IF NOT EXISTS "evidence_documents" (
  "evidence_document_id" TEXT NOT NULL,
  "customer_id" TEXT,
  "guardian_case_id" TEXT,
  "bill_id" TEXT,
  "document_type" TEXT,
  "source_path" TEXT,
  "sha256" TEXT,
  "provenance" TEXT,
  "ingestion_status" TEXT,
  "data_class" TEXT,
  PRIMARY KEY ("evidence_document_id"),
  FOREIGN KEY ("customer_id") REFERENCES "customers"("customer_id"),
  FOREIGN KEY ("guardian_case_id") REFERENCES "guardian_cases"("guardian_case_id"),
  FOREIGN KEY ("bill_id") REFERENCES "bills"("bill_id")
);

CREATE TABLE IF NOT EXISTS "agent_missions" (
  "mission_id" TEXT NOT NULL,
  "customer_id" TEXT,
  "mission_type" TEXT,
  "mission_status" TEXT,
  "created_at" TIMESTAMPTZ,
  "last_checkpoint_number" INTEGER,
  "total_steps" INTEGER,
  "idempotency_scope" TEXT,
  "resume_policy" TEXT,
  "approval_required" BOOLEAN,
  "simulated_external_actions" BOOLEAN,
  "data_class" TEXT,
  PRIMARY KEY ("mission_id"),
  FOREIGN KEY ("customer_id") REFERENCES "customers"("customer_id")
);

CREATE TABLE IF NOT EXISTS "agent_mission_steps" (
  "mission_step_id" TEXT NOT NULL,
  "mission_id" TEXT,
  "step_number" INTEGER,
  "step_key" TEXT,
  "step_status" TEXT,
  "idempotency_key" TEXT,
  "input_ref" TEXT,
  "output_ref" TEXT,
  "checkpoint_hash" TEXT,
  "external_side_effect_state" TEXT,
  "retry_count" INTEGER,
  "data_class" TEXT,
  PRIMARY KEY ("mission_step_id"),
  FOREIGN KEY ("mission_id") REFERENCES "agent_missions"("mission_id")
);

CREATE TABLE IF NOT EXISTS "value_events" (
  "value_event_id" TEXT NOT NULL,
  "customer_id" TEXT,
  "value_type" TEXT,
  "gross_value_inr" NUMERIC(20,2),
  "additional_cost_inr" NUMERIC(20,2),
  "net_value_inr" NUMERIC(20,2),
  "outcome_status" TEXT,
  "verification_level" TEXT,
  "evidence_ref" TEXT,
  "external_provider_confirmation" BOOLEAN,
  "deduplication_key" TEXT,
  "data_class" TEXT,
  PRIMARY KEY ("value_event_id"),
  FOREIGN KEY ("customer_id") REFERENCES "customers"("customer_id")
);

CREATE TABLE IF NOT EXISTS "budget_plans" (
  "budget_plan_id" TEXT NOT NULL,
  "customer_id" TEXT,
  "period_start" TEXT,
  "period_end" TEXT,
  "currency" TEXT,
  "income_reference_inr" NUMERIC(20,2),
  "planned_total_inr" NUMERIC(20,2),
  "plan_status" TEXT,
  "method" TEXT,
  "data_class" TEXT,
  PRIMARY KEY ("budget_plan_id"),
  FOREIGN KEY ("customer_id") REFERENCES "customers"("customer_id")
);

CREATE TABLE IF NOT EXISTS "budget_envelopes" (
  "budget_envelope_id" TEXT NOT NULL,
  "budget_plan_id" TEXT,
  "customer_id" TEXT,
  "envelope_type" TEXT,
  "planned_amount_inr" NUMERIC(20,2),
  "actual_spend_inr" NUMERIC(20,2),
  "remaining_amount_inr" NUMERIC(20,2),
  "overspent" TEXT,
  "allocation_ratio_percent" TEXT,
  "data_class" TEXT,
  PRIMARY KEY ("budget_envelope_id"),
  FOREIGN KEY ("budget_plan_id") REFERENCES "budget_plans"("budget_plan_id"),
  FOREIGN KEY ("customer_id") REFERENCES "customers"("customer_id")
);

CREATE TABLE IF NOT EXISTS "financial_goals" (
  "financial_goal_id" TEXT NOT NULL,
  "customer_id" TEXT,
  "goal_type" TEXT,
  "target_amount_inr" NUMERIC(20,2),
  "current_progress_inr" NUMERIC(20,2),
  "target_date" TEXT,
  "priority" TEXT,
  "goal_status" TEXT,
  "data_class" TEXT,
  PRIMARY KEY ("financial_goal_id"),
  FOREIGN KEY ("customer_id") REFERENCES "customers"("customer_id")
);

CREATE TABLE IF NOT EXISTS "tax_obligations" (
  "tax_obligation_id" TEXT NOT NULL,
  "customer_id" TEXT,
  "tax_period_label" TEXT,
  "tax_type" TEXT,
  "estimated_amount_inr" NUMERIC(20,2),
  "due_date" DATE,
  "estimate_source" TEXT,
  "tax_rule_engine" TEXT,
  "status" TEXT,
  "disclaimer" TEXT,
  "data_class" TEXT,
  PRIMARY KEY ("tax_obligation_id"),
  FOREIGN KEY ("customer_id") REFERENCES "customers"("customer_id")
);

CREATE TABLE IF NOT EXISTS "insurance_policies" (
  "insurance_policy_id" TEXT NOT NULL,
  "customer_id" TEXT,
  "policy_type" TEXT,
  "insurer_label" TEXT,
  "coverage_amount_inr" NUMERIC(20,2),
  "premium_amount_inr" NUMERIC(20,2),
  "premium_frequency" TEXT,
  "renewal_date" TEXT,
  "policy_status" TEXT,
  "policy_document_status" TEXT,
  "data_class" TEXT,
  PRIMARY KEY ("insurance_policy_id"),
  FOREIGN KEY ("customer_id") REFERENCES "customers"("customer_id")
);

CREATE TABLE IF NOT EXISTS "insurance_claims" (
  "insurance_claim_id" TEXT NOT NULL,
  "insurance_policy_id" TEXT,
  "customer_id" TEXT,
  "claim_type" TEXT,
  "claim_amount_inr" NUMERIC(20,2),
  "claim_status" TEXT,
  "submission_mode" TEXT,
  "evidence_status" TEXT,
  "data_class" TEXT,
  PRIMARY KEY ("insurance_claim_id"),
  FOREIGN KEY ("insurance_policy_id") REFERENCES "insurance_policies"("insurance_policy_id"),
  FOREIGN KEY ("customer_id") REFERENCES "customers"("customer_id")
);

CREATE TABLE IF NOT EXISTS "crisis_cases" (
  "crisis_case_id" TEXT NOT NULL,
  "customer_id" TEXT,
  "trigger_type" TEXT,
  "estimated_shortfall_inr" NUMERIC(20,2),
  "urgency" TEXT,
  "recommended_sequence_json" TEXT,
  "loan_first_strategy" TEXT,
  "case_status" TEXT,
  "external_aid_requested" TEXT,
  "data_class" TEXT,
  PRIMARY KEY ("crisis_case_id"),
  FOREIGN KEY ("customer_id") REFERENCES "customers"("customer_id")
);

CREATE TABLE IF NOT EXISTS "risk_signals" (
  "risk_signal_id" TEXT NOT NULL,
  "customer_id" TEXT,
  "source_type" TEXT,
  "signal_type" TEXT,
  "synthetic_message_or_evidence" TEXT,
  "risk_level" TEXT,
  "model_signal_confidence_fixture" TEXT,
  "deterministic_indicators_json" TEXT,
  "recommended_action" TEXT,
  "fraud_verdict" TEXT,
  "automated_payment_blocked" TEXT,
  "data_class" TEXT,
  PRIMARY KEY ("risk_signal_id"),
  FOREIGN KEY ("customer_id") REFERENCES "customers"("customer_id")
);

CREATE TABLE IF NOT EXISTS "micro_enterprises" (
  "enterprise_id" TEXT NOT NULL,
  "owner_customer_id" TEXT,
  "business_name" TEXT,
  "business_type" TEXT,
  "city" TEXT,
  "locality_cluster" TEXT,
  "monthly_revenue_estimate_inr" NUMERIC(20,2),
  "fixed_cost_estimate_inr" NUMERIC(20,2),
  "variable_cost_estimate_inr" NUMERIC(20,2),
  "estimated_contribution_margin_inr" NUMERIC(20,2),
  "capacity_per_week" TEXT,
  "enterprise_stage" TEXT,
  "external_business_registration" TEXT,
  "data_class" TEXT,
  PRIMARY KEY ("enterprise_id"),
  FOREIGN KEY ("owner_customer_id") REFERENCES "customers"("customer_id")
);

CREATE TABLE IF NOT EXISTS "enterprise_products" (
  "enterprise_product_id" TEXT NOT NULL,
  "enterprise_id" TEXT,
  "product_or_service_name" TEXT,
  "unit_price_inr" NUMERIC(20,2),
  "estimated_unit_cost_inr" NUMERIC(20,2),
  "estimated_unit_margin_inr" NUMERIC(20,2),
  "catalog_status" TEXT,
  "data_class" TEXT,
  PRIMARY KEY ("enterprise_product_id"),
  FOREIGN KEY ("enterprise_id") REFERENCES "micro_enterprises"("enterprise_id")
);

CREATE TABLE IF NOT EXISTS "enterprise_orders" (
  "enterprise_order_id" TEXT NOT NULL,
  "enterprise_id" TEXT,
  "enterprise_product_id" TEXT,
  "customer_order_label" TEXT,
  "order_date" TEXT,
  "quantity" INTEGER,
  "order_total_inr" NUMERIC(20,2),
  "order_status" TEXT,
  "payment_status" TEXT,
  "data_class" TEXT,
  PRIMARY KEY ("enterprise_order_id"),
  FOREIGN KEY ("enterprise_id") REFERENCES "micro_enterprises"("enterprise_id"),
  FOREIGN KEY ("enterprise_product_id") REFERENCES "enterprise_products"("enterprise_product_id")
);

CREATE TABLE IF NOT EXISTS "partner_settlements" (
  "settlement_id" TEXT NOT NULL,
  "provider_id" TEXT,
  "offer_id" TEXT,
  "gross_commission_inr" NUMERIC(20,2),
  "refunds_inr" NUMERIC(20,2),
  "taxes_inr" NUMERIC(20,2),
  "processing_costs_inr" NUMERIC(20,2),
  "eligible_net_revenue_inr" NUMERIC(20,2),
  "user_share_percent" NUMERIC(5,2),
  "user_share_inr" NUMERIC(20,2),
  "platform_share_inr" NUMERIC(20,2),
  "settlement_status" TEXT,
  "contract_approved" BOOLEAN,
  "payout_executed" BOOLEAN,
  "data_class" TEXT,
  PRIMARY KEY ("settlement_id"),
  FOREIGN KEY ("provider_id") REFERENCES "providers"("provider_id"),
  FOREIGN KEY ("offer_id") REFERENCES "offers"("offer_id")
);

CREATE TABLE IF NOT EXISTS "audit_events" (
  "audit_event_id" TEXT NOT NULL,
  "actor_customer_id" TEXT,
  "event_type" TEXT,
  "resource_type" TEXT,
  "resource_id" TEXT,
  "purpose" TEXT,
  "decision" TEXT,
  "occurred_at" TIMESTAMPTZ,
  "correlation_id" TEXT,
  "ip_address" TEXT,
  "data_class" TEXT,
  PRIMARY KEY ("audit_event_id"),
  FOREIGN KEY ("actor_customer_id") REFERENCES "customers"("customer_id")
);

COMMIT;
