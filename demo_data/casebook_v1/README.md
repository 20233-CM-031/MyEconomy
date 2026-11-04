# Synthetic Casebook Lifecycle v1

This extension adds a reproducible lifecycle corpus for the AwnNORA casebook. It contains 72 synthetic cases, 198 ordered lifecycle events and 72 scenario assertions generated from seed `20261104`.

- `cases.jsonl`: user-private style case records with synthetic owner references.
- `events.jsonl`: append-only event sequences, fixed timestamps and replay keys.
- `scenarios.json`: cross-engine demo and acceptance scenarios.
- `manifest.json`: counts, coverage boundary and safety rules.
- `generate_casebook_dataset.py`: deterministic generator.
- `validate_casebook_dataset.py`: consistency and safety validation.

Only the `PERSONAL` engine uses the Iteration 06 casebook API. Guardian, Opportunity, Entitlement, Crisis, Enterprise and Commons-labelled entries are scenario fixtures for integrated product storytelling; they are **not** persisted engine implementations. Nothing in this dataset belongs to a real person or bank account. Synthetic rows must not be seeded into an account and then described as live impact.

Every record is `SYNTHETIC`, external actions are false, and verified value is zero. A case marked `RESOLVED` means a synthetic workflow state only; it does not represent a verified refund, saving, award, salary or settlement.

Run:

```bash
python generate_casebook_dataset.py
python validate_casebook_dataset.py
```
