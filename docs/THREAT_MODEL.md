# Threat Model — Identity, Household and Consent Foundation

**Version:** 1.1
**Iterations:** 01 and 04
**Status:** Updated for the local Guardian evidence-review candidate; requires external security review before production.

## 1. Security objectives

Protect account control, personal financial information, household boundaries, user consent and the integrity of the audit trail. The system should fail closed when identity, authorization, consent or database state cannot be established.

## 2. Assets

- User credentials and password hashes.
- Bearer session tokens and their stored digests.
- Email verification tokens and household invitation tokens.
- User identity, email address and account state.
- Household membership and role relationships.
- Purpose/category/recipient-bound consent grants and revocation state.
- Future financial records, uploaded evidence files, structured invoice fields, document hashes/locators, skills, location signals and economic outcomes.
- Audit events documenting identity, membership and consent changes.
- Database connection strings, SMTP credentials and future model/provider API keys.

## 3. Actors and trust boundaries

- **Unauthenticated visitor:** may register, log in, verify an email challenge and read public consent terms.
- **Authenticated but unverified account:** may inspect its own account and request verification resend; must not create or inspect household/consent resources.
- **Verified user:** may perform operations on resources for which ownership/membership and role policies allow it.
- **Household owner:** may invite and revoke invitations; membership is not data access.
- **Household member:** sees limited membership metadata; sees another member's private/financial records only after that person grants an explicit matching consent and a data service enforces it.
- **Application operator:** can access runtime/database infrastructure; production access must be tightly scoped and logged.
- **External email provider:** receives only the recipient email and verification message/token; SMTP credentials are secret material.
- **Future model/provider:** receives only inputs permitted by the model-tier and user-consent policy; never gets unrestricted database access.

Trust boundaries exist at HTTP input/body streaming, bearer authentication, email control verification, MIME/signature validation, owner-level authorization, local/object storage, document scanning/extraction, consent enforcement, persistence, audit storage and external-provider adapters.

## 4. Implemented controls in Iteration 01

- Argon2 password hashing; password values are never written to audit events.
- Random 256-bit opaque session/verification/invitation tokens; only SHA-256 digests are persisted.
- Session expiry after 12 hours and immediate server-side revocation on logout.
- Generic login failure response and dummy password-hash verification when the account does not exist.
- Email verification challenges expire after 24 hours, are single-use and previous pending challenges are revoked when reissued.
- Verification resend has a 60-second per-account cooldown.
- Household/consent endpoints require a verified account.
- Household invitations expire after 72 hours, are single-use/revocable and match the invited email.
- Household membership response omits member email addresses.
- Only a household owner can invite or revoke an invitation in this iteration.
- Membership alone does not grant access to personal records.
- Consent grants bind subject, purpose, data categories, recipient type/id, terms version and expiry.
- Consent policy disallows raw transaction records for Commons aggregation and research participation.
- Revocation takes effect immediately in consent checks.
- Audit records are append-only at ORM and database-trigger levels for SQLite and PostgreSQL.
- Cross-user, unverified-user, invitation misuse, consent scope, expiry/revocation and audit immutability cases are covered by tests.

## 5. Iteration 04 Guardian evidence controls and residual risks

Implemented in the local candidate:

- Guardian routes require verified authentication; document and case queries are scoped to the authenticated owner. Case-to-document ownership is enforced by a composite database foreign key.
- Upload body is streamed with a 5 MiB ceiling; declared type must be PDF/PNG/JPEG and the magic signature must match. Filename is sanitized for display and never used as a storage path.
- SHA-256 and owner-scoped idempotency keys are persisted. Same-key/same-content retries replay; same-key/changed-content requests conflict.
- Local adapter uses generated UUID keys, mode `0700` directories, mode `0600` files, `fsync` and atomic rename. Evidence upload, case creation and downloads are audited without storing file contents in audit details.
- Original bytes are never parsed, executed or sent to a model in Iteration 04. Documents remain `STORED_UNSCANNED`. Review values and confidence are user-submitted structured fields; deterministic domain logic revalidates arithmetic.
- Draft approval is an internal workflow state only and does not send a message or perform a provider action.

Residual risks / controls not yet present:

- A MIME magic signature is not a safety scan. Malformed PDFs/images, parser exploits, embedded payloads and decompression bombs must be handled by a dedicated scanner/sandbox before any future parser or OCR worker opens content.
- The local filesystem adapter is not encrypted at rest and does not provide KMS, tenant-level envelope encryption, lifecycle retention, durable backup, object access policy or orphan reconciliation. It is not suitable for production financial documents.
- A crash between file write and DB commit may leave an orphan blob. Add an idempotent reconciliation job and durable object/DB state machine before production.
- Evidence locator and confidence values currently come from the caller. They are not verified against PDF text or rendered page regions; do not present them as model-verified/source-verified evidence.
- There is no malware scanner, OCR, Meta model gateway, prompt-injection filter, extraction schema/version trace or model evaluation. User-provided documents are untrusted; any future extraction worker must have no arbitrary tool/network access.
- Upload/download rate limits, quotas, retention/deletion controls, incident alerts, production TLS and independent penetration testing remain required.

## 6. Important residual risks / production blockers

- Email inbox-control verification is implemented and the end-to-end challenge flow was exercised with synthetic accounts using the development mail adapter. The SMTP adapter is implemented, but it must be configured and tested with a real provider before deployment. The development log backend exposes the token in local logs and is forbidden when `APP_ENV=production`.
- The SMTP integration has not been exercised against a real SMTP service; no claim of production email delivery is made.
- Login and verification endpoints still need IP/device-aware abuse controls and distributed rate limiting; only verification resend has an account-level cooldown.
- No password reset, MFA/passkeys, account recovery or account deletion/export workflow.
- No household leave/remove-member, ownership transfer, household deletion lifecycle or fine-grained admin policy.
- No personal-data read service exists yet. Future data services must call `require_active_consent` inside the same transaction as the protected data access; the public consent-check endpoint is informational only.
- No encryption-at-rest/KMS deployment configuration, TLS enforcement, secure cookie/session rotation, request-size limits, structured security monitoring or independent penetration test.
- Audit rows are immutable, but a production database superuser can still alter schema or disable triggers. Separate audit replication/WORM storage is a future control.
- SMTP delivery failure occurs after account/session/challenge persistence; the API returns 503 and the authenticated account can request a resend after the cooldown. This recovery path is tested only at service/API level, not against a live provider.
- Account identity is not proof of legal identity. Email verification proves control of an email inbox only.

## 7. High-level threat register

| Threat | Impact | Implemented mitigation | Residual work |
|---|---|---|---|
| Password database disclosure | Account takeover | Argon2id hash; unique salts via library | Password reset, credential stuffing defense, MFA |
| Bearer token theft | Session hijack | High-entropy token, hash at rest, 12-hour expiry, logout revoke | Rotation, device/session management, TLS, alerts |
| Email spoofing during invite | Unauthorized household joining | Single-use email challenge, verified-account gate and invited-email match | Real SMTP provider test, link handling UX |
| Invitation replay | Unauthorized repeated membership action | Token digest, accepted/revoked state, expiry | Concurrency test against live PostgreSQL |
| Cross-user IDOR | Private data exposure | Owner-scoped document/case queries, composite owner/evidence FK, opaque not-found response | Apply authorization to each future data resource |
| Malicious or oversized evidence upload | Storage exhaustion or parser exploit | 5 MiB streaming cap, PDF/PNG/JPEG signature check, no parsing/execution, unscanned state | Malware scanning/sandbox, per-user quotas/rate limits, content parsing hardening |
| Filename/path traversal | Cross-owner overwrite or disclosure | Sanitized display name; generated UUID storage key | Object-store IAM, key rotation, path fuzz testing |
| False evidence locator/confidence | Incorrect dispute or user harm | Findings are explicitly advisory; values are marked user-submitted; no external send | OCR/model extraction with verified page/region spans, confidence calibration, human verification |
| Orphaned document blob | Untracked sensitive file | Atomic local write and best-effort delete on DB failure | Crash reconciliation, lifecycle job, deletion/retention workflows |
| Evidence download cache/leak | Private invoice disclosure | Owner-only route, private no-store cache, nosniff, download audit | TLS, access alerting, stronger encryption and production object policies |
| Consent scope inflation | Excessive sharing | Purpose/category matrix, recipient binding, version and expiry | Policy review, data access enforcement integration tests |
| Revoked consent still used | Unwanted processing | Immediate status update and `require_active_consent` helper | Make all future readers enforce within same transaction |
| Household membership implies sharing | Privacy breach | Membership and consent stored separately | Data-sharing UI must display individual consent controls |
| Raw data leaks into Commons/research | Re-identification/privacy harm | Category allowlist excludes raw transaction/contact/evidence data | Aggregate thresholds, suppression, anti-inference tests, privacy review |
| Audit tampering | Loss of accountability | ORM hook plus SQLite/PostgreSQL trigger | External immutable audit sink and key/role separation |
| SMTP token/log leakage | Account takeover | Development-only log mode; SMTP config from env | Secrets manager, redacted logs, provider integration test |
| Model prompt injection / data exfiltration | Unauthorized action/data disclosure | No model integration in this iteration | Threat model each model tool, typed capabilities and allowlists |

## 8. Required controls before real personal financial data

1. Configure and verify a real SMTP provider and domain authentication (SPF/DKIM/DMARC).
2. Implement password reset, MFA/passkeys, login throttling and suspicious-session handling.
3. Add PostgreSQL integration and concurrency tests on a real PostgreSQL service.
4. Add encryption/key-management, encrypted document storage, malware scanning/quarantine, orphan reconciliation, backups/restore drills, TLS/headers, secrets manager and environment separation.
5. Implement account data export/deletion and retention schedule, including legal holds and audit minimization.
6. Implement data access services that enforce purpose/category/recipient consent in the same transaction.
7. Complete privacy review, legal review and independent penetration testing.
8. Keep demo/hackathon accounts synthetic until all required controls are satisfied.
