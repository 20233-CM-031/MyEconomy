# AwnNORA — Meta AI Integration and Hackathon Demonstration Strategy

## Product thesis

AwnNORA is a system-level demonstration of Human Economic Intelligence: it connects multimodal understanding, structured reasoning, deterministic economic services, controlled tools, durable workflows and user-facing approvals. The Meta model is a specialist cognitive layer inside the system, not the system itself.

## Use Meta models where the capability matters

| Meta capability | AwnNORA job | Data boundary | Evaluation |
|---|---|---|---|
| Muse Spark 1.3 (`muse-spark-1.3`) | Interpret a minimized Personal Power Report now; later multimodal invoice/contract reasoning; propose schema-constrained mission plans | Standard mode only for personal context; no direct identifiers, raw statements or Guardian evidence before quarantine and scan gates | answer usefulness, finding-reference validity, schema validity, hallucination/abstention, latency, tokens and cost |
| Muse Wonder 1.0 (`muse-wonder-1.0`) | Future complex GENIEA missions with long-horizon planning, delegation and recovery | Standard mode only for private context; use only after durable mission, least-privilege tools, checkpoint and reconciliation are implemented | end-to-end task completion, recovery, delegation precision, tool safety, latency and total cost |
| Muse Voice Transcribe 1.0 | Convert spoken user intake/clarification into a transcript and structured draft | Explicit microphone permission; disclose realtime/file route; transcript is user-editable before persistence | transcript correction rate, slot accuracy, turn attribution and latency; the model returns turn-level, not word-level timestamps |
| SAM 3.1 (`sam-3.1`) | Segment visible physical assets/resources, such as equipment, produce crates or inventory items | Only the selected image/video and coarse task context; never use segmentation as an ownership, safety, identity or capacity verifier | mask/box quality, count precision, tracking continuity and human correction rate |
| Muse Glimmer (30B open weight) | Benchmark local multimodal processing for privacy-sensitive/edge deployments and offline fallback | Local deployment only; no remote personal-data transfer in this path | quality vs Spark, memory, VRAM/RAM, throughput, cost, robustness and abstention |
| Muse Spark Open (816B MoE; 42B active) | Optional large open-weight agent/reasoning experiment when dedicated hardware or a suitable hosted runtime exists | Separate hosting, license, infra and data-governance review; do not assume consumer-GPU self-hosting is practical | throughput, serving cost, memory, quality and safe orchestration |
| Muse Image 1.0 | Potential one-person enterprise catalogue/product artwork from user-approved assets | Use only user-authorized assets and require human approval before publishing | product fidelity, brand consistency and human approval rate |

## Implemented in this package

- `muse-spark-1.3` Standard-mode model adapter for a private Personal Power Report explanation.
- Explicit `store: false`, no external model tools and strict JSON Schema output.
- A separate `AI_ASSISTANCE` consent, restricted to `financial_summary` plus `household_obligations` and the recipient `meta-model-api`.
- A privacy minimizer that sends only aggregate totals, deterministic finding IDs/codes/text and the user's question. It omits names, account IDs, transaction rows, counterparty/payee information and evidence documents.
- Server-side validation rejects unknown finding IDs. The API never accepts model-generated money, eligibility, consent, settlement or mutation instructions.
- Audit records record model/mode/scope/action counts, not prompt content or personal financial data.

## Important Meta data-use distinction

Meta documents `muse-spark-1.3` as Standard mode and `muse-spark-1.3-contributor` as Contributor mode. The adapter pins the Standard model ID and has no setting to select Contributor. Meta states Standard-mode content is not used to train Meta models; Contributor-mode content may be used for training. The system still requires AwnNORA's own informed, purpose-specific consent and data minimization. Verify current terms and availability again before submission. Sources: official Meta Model API model documentation and structured-output documentation.

## Demo sequence mapped to judging criteria

1. **Impact (30%)** — first user gets a private, actionable Personal Power Report without bank-linking or Commons scale. Show missing-data warnings and why possible duplicate findings are not counted as savings.
2. **Meta AI tooling (25%)** — grant separate AI assistance consent and ask Muse Spark to explain a report finding. Show the request boundary, Standard model ID, structured JSON output, finding-ID validation and the deterministic-vs-model split.
3. **Technical depth (20%)** — inspect exact-money logic, consent enforcement, audit, source references, scenario tests, negative offer rejection, Commons suppression and mission-recovery invariants.
4. **Demo (25%)** — move from personal report to Guardian review, opportunity/benefit preview and opt-in Commons simulation; label each simulated integration; return to a live local API mode for the actually implemented slices.

## Truthful feature claims

- Muse Spark assistance is a real API call only when `MODEL_API_KEY` is configured, the user has an active `AI_ASSISTANCE` consent, and the backend responds successfully.
- Without credentials, the UI must say the model is not connected. Never substitute a scripted explanation and call it Muse output.
- Voice, SAM 3.1, Glimmer and Muse Image are architectural integration targets in this package, not functioning live integrations.
- Guardian's existing files remain `STORED_UNSCANNED`; the new model assistance endpoint is text-only and does not accept invoice files.
- This package does not submit a hackathon entry or verify eligibility for any bonus prize.


## Data boundary details

The `AI_ASSISTANCE` grant requires both `financial_summary` and `household_obligations`, because the report may include essential-obligation totals. The API requires both grants for every request. Payee names in recurring-obligation findings are replaced with generic wording before model submission. The user-facing model request is selected from a fixed intent enum; arbitrary free text is not forwarded. The lookback window is capped at 365 days. The API commits the report-read/request-audit transaction before waiting on the model network call, so a slow provider does not hold a database connection open.


## Model and deadline facts checked for this transfer

- Meta's current Model API documentation lists `muse-spark-1.3` and supports chat completions at `https://api.meta.ai/v1`. The adapter in this package pins that model ID and requests Standard mode by not using Contributor. Availability and terms should be rechecked at submission and deployment time.
- Meta documentation describes Standard mode as not using requests and responses for model training, while Contributor may use content for training. This package therefore uses Standard mode only for personal context.
- Muse Glimmer is an open-weight local model candidate, not an API integration in this package. Benchmark it only after obtaining and validating the current release/weights.
- The Meta AI Global Hackathon page lists a 9:00 PM ET deadline on 4 November 2026. For India (UTC+5:30), this is 7:30 AM IST on 5 November 2026. The four judging weights used in the team's plan (Impact 30%, Meta AI 25%, Technical 20%, Demo 25%) are the team's supplied rubric; do not cite them as published weights unless the organizer's current rules confirm them.

Official references: https://www.meta.ai/docs/muse-model-api/models/ ; https://www.meta.ai/docs/muse-model-api/quickstart/ ; https://ai.meta.com/blog/muse-spark-glimmer/ ; https://www.meta.com/ai-global-hackathon/


## Official capability reference

The current Meta Model API catalog lists Muse Spark 1.3 (`muse-spark-1.3`) as Standard mode, Muse Wonder 1.0 as a long-horizon model, Muse Voice Transcribe 1.0 for live/file speech-to-text, and SAM 3.1 for image/video segmentation. Muse Glimmer is a 30B open-weight text+image model with Apache 2.0 weights. Muse Spark Open is an 816B mixture-of-experts release with 42B active parameters and requires its own serving runtime; it is not a hosted Model API call. Recheck availability, regional access, prices, quotas and licenses before use.

References: https://dev.meta.ai/docs/models ; https://dev.meta.ai/docs/muse-glimmer ; https://dev.meta.ai/docs/speech-to-text ; https://dev.meta.ai/docs/sam/overview

## Bonus-prize engineering targets supplied by the team

These are team targets, not a claim that every prize category or amount has been independently verified in the current official rules.

1. **Best Agentic Use-Case:** prioritize one real GENIEA mission end-to-end: a user-authorized economic investigation that decomposes work, calls typed read-only services, checkpoints progress, resumes after interruption, requests approval for any consequential action, reconciles tool state before retry and records a confirmed outcome. A free-running chatbot or multi-agent diagram is not sufficient.
2. **Best Meta Open Weight Model Build:** use Muse Glimmer as the practical local benchmark candidate because it is the 30B open-weight multimodal model designed for local runtime. Keep the same contract/evaluation set as the Spark API path, and compare quality, abstention, memory, throughput and operating cost. Muse Spark Open is a separate much larger deployment option, not the default single-workstation route.
3. **Most Viral Project / Community Vote:** show one coherent 2–4 minute user story, make a clear public project page/gallery entry, publish a truthful screen-recording and explain the user's real problem. Only publish after the submitted build works; clearly label synthetic data and simulated partners.
4. **Best Creative Build:** optional Muse Image extension for One-Person Enterprise: generate a product catalogue visual from user-approved product facts and a rights-cleared reference image, then require the seller to verify the output before publishing. Do not divert time from the real user journey to add decorative image generation.

The user's supplied scoring weights remain the operational planning rubric: Impact 30%, Meta AI 25%, Technical 20%, Demo 25%. The official event page currently describes the Indie track in terms of creativity, technical ambition and whether it works, and the Startup track in terms of technical execution and production durability; verify the current judging rules/bonus eligibility in the participant portal before submission.
