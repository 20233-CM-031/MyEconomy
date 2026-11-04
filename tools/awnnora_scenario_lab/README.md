# AwnNORA Scenario Lab

Generate deterministic synthetic runs for all major AwnNORA capability families. See `docs/transfer/SCENARIO_LAB.md` after applying the overlay.

```bash
python tools/awnnora_scenario_lab/generate.py --out demo_data/scenario_lab_v1 --replicas 25 --seed 20261104
python tools/awnnora_scenario_lab/validate.py demo_data/scenario_lab_v1
```

Default output: 46 templates × 25 replicas = 1,150 scenario runs. Use `--replicas 1000` for a 46,000-run local stress dataset. Every record remains `SYNTHETIC_FIXTURE`; these are not real execution traces and must never count as VIVC or trigger provider calls.
