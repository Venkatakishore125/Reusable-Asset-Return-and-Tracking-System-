# Validation and Testing Guide

## Run the checks

Open a terminal in reusable-asset-tracke/reusable-asset-tracker/.

Run the complete test suite:

```bash
python -m unittest discover -s tests -v
```

The test suite invokes the generator at starter scale before it checks the output. Existing generated starter data under data/output/ may therefore be replaced.

To run a starter generation and validation:

```bash
python -m src.main --starter
```

To run the validator directly and write the validation summary:

```bash
python -m src.validation
```

## What is checked

The current validation and tests cover selected conditions, including:

- Uniqueness of key asset, shipment, custody, return, inspection, repair and ledger identifiers.
- Core asset, shipment, location and owner references.
- Presence of required anomaly labels in the ground-truth file.
- Reproducibility metadata and SHA-256 hashes in the source manifest.
- Outstanding-day calculation.
- Deposit reconciliation and repeated refund candidate identification.
- Rejection of custody events with a missing actor in the tested replay scenario.
- Creation of expected starter output tables.

## Understanding validation findings

Some validation issues are intentionally generated. In particular, the project includes negative examples for simultaneous location conflicts, a return before dispatch, duplicate refunds, repair closure without inspection, and missing custody actor.

Use both of these files when reviewing results:

- data/output/validation_summary.json
- data/ground_truth/ground_truth.json

A flagged row should be compared with its ground-truth label and expected handling. Do not remove negative examples simply to obtain a clean validation status; they are present to test the validation process.

## Reproducibility check

The default seed is 20261022. To compare output between runs:

1. Run the same generator command twice with the same scale and seed.
2. Compare the hashes recorded in data/output/source_manifest.json.
3. Investigate differences if the same inputs do not produce the same generated table checksums.

The manifest also records the seed and scale used for the run.

## Interpreting anomaly outputs

- A duplicate refund candidate is a record requiring review; it is not, by itself, proof of fraud.
- An event rejected from the operational location projection remains part of the source event history for audit and analysis.
- A validation issue may be expected when the generator deliberately creates a negative test case.
- The generated values are synthetic and should not be represented as production measurements.

## Current test coverage limits

The tests are a useful baseline, not a complete verification of all business scenarios. In particular, the project documentation identifies multi-shipment event replay and complete lifecycle reconciliation as areas for further work. Add tests when these rules are extended.