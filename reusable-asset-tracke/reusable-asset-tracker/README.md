# Reusable Asset Return & Tracking System

A deterministic synthetic-data project for tracking reusable pallets, crates, and transport equipment across shipments, custody handoffs, returns, inspections, repairs, and deposit transactions.

## Requirements
- Python 3.10+ recommended
- No third-party dependencies required for the core generator

## Run a small starter dataset
From this directory:

```bash
python -m src.main --starter
```

## Run the requested full scale
```bash
python -m src.main
```

Default scale: 20,000 assets, 10,000 shipments, and 100,000 total custody-event rows, including return events and three custody-specific labelled anomaly events. The generator pads the valid baseline event stream before injecting the labelled custody anomalies.

## Customize scale and seed
```bash
python -m src.main --assets 1000 --shipments 500 --custody-events 5000 --seed 20261022
```

The seed is fixed by default (`20261022`). Run the same command twice to compare generated CSV checksums in `data/output/source_manifest.json`. The manifest includes hashes for the generated entity tables.

## Run tests
```bash
python -m unittest discover -s tests -v
```

## Outputs
- `data/output/*.csv`: master, transaction, event, ledger, and derived snapshot data
- `data/output/source_manifest.json`: seed, scale, row counts, SHA-256 checksums
- `data/output/validation_summary.json`: primary-key, foreign-key, and lifecycle checks
- `data/ground_truth/ground_truth.json`: separately stored known anomaly cases and expected decisions
- `docs/data_dictionary.md`: field definitions and relationships

## Business logic overview
- Unique IDs are generated using documented prefixes and zero padding.
- Asset lifecycle states and outstanding days are calculated from dates and return outcomes.
- Deposit balance is calculated by summing ledger charges and refunds; charges are positive and refunds negative.
- Damaged returns create repair records; aged non-returns can become LOST.
- Five required negative scenarios are added with `issue_type` labels and separate ground-truth labels.

## Validation and limitations
The validation report intentionally flags injected anomalies such as missing custody actors and repair closure without inspection. Those are expected negative cases, not evidence that the generator silently corrupted baseline records. Review the issue list and ground-truth file together. The current version is a challenge starter; it does not yet use a relational database or implement full event replay for all possible multi-shipment conflicts. See `docs/design_decisions.md` and `docs/schema.md`.

## AI use disclosure
AI tools may be used for this challenge, but the submission must remain your individual work. Record the actual prompts used in `prompts/prompt_history.md`, review and test all code yourself, and be prepared to explain design decisions and limitations. Never include secrets, credentials, personal data, or proprietary code in this public repository.

## Acceptance checks added

The acceptance tests also check uniqueness of the generated primary IDs, core asset/shipment references, presence of all five required anomaly labels in the separate ground-truth file, and the presence of a SHA-256 reproducibility hash in the source manifest:

```bash
python -m unittest discover -s tests -v
```

These tests are a useful baseline, not proof that every requirement is fully implemented. The validation report intentionally reports injected negative scenarios. Before submission, review those findings against `data/ground_truth/ground_truth.json`, verify full-scale counts, and inspect event replay and deposit reconciliation results.

## Improved business-rule outputs
- `src/business_rules.py` contains pure, testable functions for custody-event replay, outstanding-age calculation, and deposit reconciliation.
- `AssetSnapshot.csv` now takes its location from accepted custody history; events marked with injected issue types or missing actors are excluded from the operational projection but remain in the audit event table.
- `data/output/operational_metrics.json` summarizes row counts, rejected custody events, duplicate refund candidates, and net deposit balance.
- Duplicate refund detection is based on repeated refunds for the same asset and return authorization. Review flagged cases against the ground-truth file before treating them as confirmed fraud.

## Stronger verification
The test suite includes unit tests for outstanding age, duplicate-refund detection, and event replay when an event lacks an actor. These tests improve coverage but do not replace full acceptance validation. Before submission, run the generator twice at full scale with the same seed and compare the generated checksums.
