# MAKOS Web Workspace — Design and Interaction Contract

## Product surface

The first web release is an operational workspace for AwnNORA Personal Mode. It is not a marketing site or static dashboard. It has a live/synthetic environment distinction, an API readiness indicator, a private-account connection flow, CSV statement ingestion, cashflow and obligation summaries, Guardian case visibility, and a consent-gated Meta explanation surface.

## Visual direction

Use an editorial, restrained and trustworthy visual language:

- Warm paper surfaces, ink-toned text and a restrained forest-green action colour.
- Georgia for display headings, system typography for controls and data.
- Clear label hierarchy, generous whitespace, careful tables, compact metrics and legible source/status metadata.
- Subtle borders and low-intensity hover states; animation must never carry meaning.
- Responsive desktop-first workspace with a narrow-screen stacked layout.

Avoid random rainbow colour, decorative motion, sparkle/orb/dot-grid effects, purple/black novelty styling, terminal windows, glass effects, emoji, icon packs, generic feature-card rows or template-looking bento layouts. The interface uses small CSS-drawn navigation marks and semantic text labels.

## Trust states

Every data surface must distinguish:

1. `SYNTHETIC DEMO`: fictional fixtures only.
2. `PRIVATE ACCOUNT`: authenticated user's private scope. This label alone does not prove the data are real.
3. `SYNTHETIC FIXTURE DATA`: the account is authenticated but seeded from a fictional test persona; the UI explicitly repeats that no real bank history or VIVC is represented.
4. `MIXED DATA`: at least one synthetic fixture account and at least one other account are present.
5. `SANDBOX`: future integration environment; never equate with live provider settlement.
6. `LIVE`: only after a real provider response is independently verified and reconciled.

The Guardian screen explicitly says uploaded documents remain `STORED_UNSCANNED`. The interface must not offer OCR/model extraction until a scanner, quarantine lifecycle and parser isolation are actually active.

## First-user path

1. Register a dedicated account and verify inbox control.
2. Create an INR account from the web workspace.
3. Upload a UTF-8 CSV statement to that account.
4. The API runs bounded parsing, exact decimal-to-minor-unit conversion, idempotency, duplicate handling and audit.
5. The Personal Power Report is refreshed from persisted rows.
6. A separate optional consent is shown before sending aggregate financial and essential-obligation summaries to Meta.

The CSV importer accepts a UTF-8 CSV up to 2 MiB and 10,000 data rows. It requires `date`, `amount` and `direction`. Supply `cashflow_treatment` explicitly as `INCOME`, `EXPENSE`, `REFUND`, `TRANSFER` or `IGNORE`; a missing treatment defaults to `IGNORE`. The interface deliberately does not provide a synthetic CSV file for import into a live account, because the API would classify those uploaded rows as `CSV_IMPORT`, not `SYNTHETIC_FIXTURE`.

## Current page status

- Your position: live backend Personal Power Report + CSV import; synthetic demo values are fixture-backed.
- Protection: live Guardian case list; evidence is unscanned; no extraction or provider delivery.
- Opportunity, Entitlements, Enterprise and Commons: interactive demonstration/preview surfaces; no live source or settlement engine yet.
- AI intelligence: Muse Spark explanation endpoint is live only when server configuration and the separate AI consent are present. Other listed Meta models are roadmap targets, not connected runtimes.
