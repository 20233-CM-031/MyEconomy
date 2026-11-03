# Regulatory-aware data and workflow rules (India-oriented)

**Research snapshot: 2026-11-03, Asia/Kolkata.** This is an engineering design note, not legal advice, a compliance opinion or a certification. Applicability depends on our actual role, data processing, user types, vendors, regulated partners and later commencement/amendment notifications. Have Indian privacy/financial-services counsel review before production.

## 1. Digital Personal Data Protection Act, 2023 and Rules, 2025

The DPDP Act commencement notification G.S.R. 843(E), dated 13 November 2025, uses staged commencement. As of 3 November 2026, only the provisions identified as immediately effective in that notification have commenced; selected provisions commence one year after publication (13 November 2026), and a larger set of substantive provisions is scheduled for 13 May 2027 (18 months after publication). Do not represent every substantive obligation as already operative on 3 November 2026. Re-check the official schedule and later notifications before each release.

The DPDP Rules, 2025 were notified as G.S.R. 846(E) on 13 November 2025 and also use staged commencement. The production implementation should be designed for clear notice, specified purposes, valid consent/withdrawal, data-principal rights, security safeguards, retention/deletion and processor governance, while legal counsel confirms which provisions apply on the launch date.

**Engineering controls used in this fixture:** purpose-specific consent records, recipient and category scopes, expiry/revocation timestamps, event-time consent checks, audit receipts, data minimisation and a separate research/Commons purpose. These fixture columns demonstrate design intent; they do not certify legal compliance.

## 2. RBI Account Aggregator framework

RBI's NBFC Account Aggregator Directions require explicit customer consent for retrieval/sharing/transmission and describe a standardised consent artefact containing the customer, information type, purpose, recipient, notification address, creation/expiry and AA identity/signature. The directions include revocation, logging/auditability, identity verification, security and prohibit an AA from supporting customer transactions. The Department of Financial Services describes the AA framework as a voluntary, consent-based transfer between financial institutions, with FIPs and FIUs in the regulated ecosystem.

**Architecture implication:** do not scrape bank credentials or claim MyEconomy is an Account Aggregator. A live bank-data flow must use authorised AA/FIU roles and partnerships, valid consent artefacts and the correct technical ecosystem. AA data-sharing must not be confused with payment initiation.

## 3. RBI Digital Lending Guidelines (conditional)

The RBI's 2 September 2022 Digital Lending Guidelines require regulated entities to ensure need-based data collection by digital lending apps with prior explicit borrower consent and audit trail, borrower discretion over categories/third-party disclosure/retention/revocation, and explicit consent before sharing personal information with third parties (subject to statutory/regulatory exceptions). MyEconomy is not a lender in this current scope. If we later facilitate/arrange digital lending, identify the actual regulated-entity/LSP/DLA role and have counsel and the regulated entity map all current rules before implementation. The synthetic loan schedule is not a credit offer, underwriting model or sanction.

## 4. KYC, payments and regulated activity

No Aadhaar, PAN, card PAN, UPI PIN, bank password, real account number or actual payment credential is generated. A fictional KYC status field is not KYC verification. KYC, payments, payout, insurance distribution, tax filing, credit decisions and regulated benefit applications require their own eligible entity, provider controls and legal review.

## 5. Dataset safety rules

- Each row is labelled `SYNTHETIC_FIXTURE` or an equivalent synthetic flag.
- Customer emails use `example.invalid`; phone strings use deliberate `+91-00000-xxxxx` placeholders.
- Provider, scheme, partner and offer labels are fictional `DEMO-*` or `SYNTH-*` records.
- Locations are broad city/locality clusters, not home addresses.
- No individual income, transactions or identifiers go into Commons demand signals.
- Consent is checked at event time. A later revocation stops future use; historical event validity is evaluated against timestamps and audit evidence.
- Offers are evaluated with full incremental costs and recurring commitments. Negative or zero net benefit is rejected.
- Benefit eligibility matches are potential assessments, not official determinations or awards.
- Claims, applications, orders, settlements and value events are simulated, not transmitted or paid.
- Never send fixture data to a bank, insurer, government body, provider, sponsor or real payment service.

## 6. Official references

1. MeitY, DPDP Act commencement notification G.S.R. 843(E), 13 Nov 2025: https://www.meity.gov.in/static/uploads/2025/11/c56ceae6c383460ca69577428d36828b.pdf
2. MeitY, DPDP Rules, 2025 notification G.S.R. 846(E), 13 Nov 2025: https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf
3. MeitY DPDP Rules and enforcement timeline portal: https://www.meity.gov.in/documents/act-and-policies/digital-personal-data-protection-rules-2025-gDOxUjMtQWa?pageTitle=Digital-Personal-Data-Protection-Rules-2025%3B
4. Department of Financial Services, Account Aggregator Framework: https://www.financialservices.gov.in/account-aggregator-framework
5. RBI Master Direction - NBFC Account Aggregator Directions, 2016 (updated 6 Sep 2024): https://systemhealth.rbi.org.in/Scripts/BS_ViewMasDirections.aspx_id%3D10598%281%29.html
6. RBI Guidelines on Digital Lending, 2 Sep 2022: https://systemhealth.rbi.org.in/Scripts/NotificationUser.aspx_Id%3D12382%26Mode%3D0.html
7. RBI Master Direction - KYC Direction, 2016 (check current updated version at integration time): https://www.rbi.org.in/
