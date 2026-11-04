# ADR-0003: Owner-scoped financial data plane and strict CSV ingestion

- **Status:** Accepted for Iteration 02 v1
- **Date:** 2026-11-04
- **Owners:** MyEconomy engineering team
- **Supersedes:** No prior ADR

## Context

Iteration 00 computed cashflow from caller-provided JSON without persistence. Iteration 01 added verified identity, user/household boundaries, consent and audit. The system now needs durable personal financial records to support Day-One analysis, Guardian and future personal agents. The synthetic dataset already contains linked statement rows, accounts and recurring obligations; we need a controlled way to load realistic data through real application logic.

Financial data is high-impact. Incorrect currency arithmetic, repeated imports, double-counted transfers, refunds misclassified as income, cross-user access or partial imports can produce harmful advice. A broad “upload file and let the model figure it out” endpoint is unacceptable.

## Decisions

1. **Start with a modular monolith and PostgreSQL-oriented relational schema.** Four tables (`financial_accounts`, `transaction_import_batches`, `financial_transactions`, `recurring_obligations`) are added under the existing SQLAlchemy/Alembic structure. No premature service extraction.
2. **Persist money as integer minor units and currency code.** Decimal is used at the boundary; no binary floats. Amount/direction/treatment are separate; no implicit FX.
3. **Enforce owner/account/currency scope in the database.** Composite unique keys and foreign keys prevent transactions/imports/obligations from being attached to an account owned by another user or using the wrong account currency. API queries additionally filter by authenticated owner and return 404 for non-owner resources.
4. **Make CSV import bounded and deterministic.** Stream the HTTP body with a 2 MiB guard. The pure domain parser enforces UTF-8, 10,000 row and 32 column caps, exact dates, Decimal precision, currency match and treatment/status invariants.
5. **Use an idempotent batch envelope.** Store original byte SHA-256, safe filename, user-scoped idempotency key, counts, validation errors and completion status. Never retain raw CSV bytes.
6. **Reject invalid input atomically.** Any malformed row or conflicting reused provider reference rejects the batch and inserts no transaction rows.
7. **Separate provider identity from heuristic similarity.** Exact external references are unique within owner/account; same reference/different content rejects. Similar rows without provider ID are preserved and linked as possible duplicates, not silently dropped.
8. **Make treatment semantics explicit and conservative.** Only POSTED rows affect cashflow. Refund credits offset expenses but do not become income. Transfers and ignored movements do not change income/expense. If a CSV omits treatment, store `IGNORE`; direction alone cannot prove that a credit is salary or a debit is consumption. Pending, reversed and void records remain visible but excluded.
9. **Reconcile provider lifecycle monotonically.** Same external reference + same financial fingerprint may update `PENDING -> POSTED|REVERSED|VOID` or `POSTED -> REVERSED|VOID`. `REVERSED` and `VOID` are terminal. Count and audit lifecycle updates separately from inserts and duplicates; database triggers reinforce application validation.
10. **Keep recurring obligations distinct from actual transactions.** A schedule is not proof of payment or a debit mandate. `autopay_enabled` is descriptive only.
11. **Load synthetic data into an existing verified local user.** The seed script refuses production, verifies all selected rows are synthetic, uses stable IDs and creates no fake login identity.
12. **Keep cross-person sharing out of this iteration.** Household membership never grants access. Future cross-user reads must enforce purpose-specific consent in the same database transaction as the data access.

## Alternatives considered

- **Float/NUMERIC amount with arbitrary currency conversions:** rejected because float introduces precision risk and cross-currency arithmetic needs explicit provenance. Decimal is accepted only at API/import boundaries.
- **Automatic duplicate suppression by fingerprint:** rejected because two legitimate same-value purchases may occur at the same time/category. Fingerprint only flags a candidate.
- **Store original CSV files in the financial database:** rejected for data minimization and retention reasons. Store hash + sanitized filename + counts/errors; raw source bytes stay in request memory and are discarded.
- **Build a bank connector first:** rejected because credentials, provider contracts, regulatory role/consent and recovery semantics are not established. CSV is the first user-controlled ingestion path.
- **Use an LLM to interpret transactions or compute money:** rejected. A model may later suggest categories or explain evidence, but deterministic application/domain rules remain authoritative for arithmetic, authorization, state and ledger integrity.

## Consequences

Positive:
- Reproducible imports, clear provenance and idempotent retries.
- Exact monetary arithmetic and database-enforced scope constraints.
- A single synthetic persona can exercise actual persistence/API code.
- Strong foundation for Personal Power, Guardian and Opportunity workflows.

Costs/limitations:
- CSV adapters must be added for individual bank/export formats.
- The currency registry is still curated and requires authoritative review.
- No live PostgreSQL validation of this new migration until its CI run.
- Duplicate similarity is only a review signal; it can produce false positives.
- Full real-time bank ingestion, user-driven transaction reclassification, retention, encryption/KMS and financial-sharing consent enforcement remain later work.
