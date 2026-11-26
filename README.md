# Reusable Asset Return and Tracking System

A Python project for modelling the movement and return lifecycle of reusable logistics assets such as pallets, reusable crates and transport cages. It generates deterministic synthetic operational data, validates relationships and lifecycle records, and includes labelled edge cases for testing data-quality and business-rule handling.

The project focuses on a practical logistics question: **where is each reusable asset, who had custody of it, has it been returned, and do the related return and deposit records agree?**

## Project at a glance

- Generates synthetic master data and operational records.
- Models shipments, custody handoffs, return authorizations, inspections, repairs and deposit transactions.
- Creates an asset snapshot and operational metrics from generated records.
- Validates identifiers, selected relationships and lifecycle records.
- Keeps known anomaly examples in a separate ground-truth file.
- Uses a fixed random seed so the same configuration can be regenerated and compared.

## Repository layout

The runnable Python project is located in `reusable-asset-tracke/reusable-asset-tracker/`.

```text
.
├── README.md
└── reusable-asset-tracke/
    └── reusable-asset-tracker/
        ├── README.md
        ├── requirements.txt
        ├── src/
        │   ├── main.py
        │   ├── config.py
        │   ├── generator.py
        │   ├── validation.py
        │   └── business_rules.py
        ├── data/
        │   ├── ground_truth/
        │   └── output/
        ├── docs/
        ├── prompts/
        └── tests/
```

## Run the project

### Requirements

- Python 3.10 or later is recommended.
- The current `requirements.txt` specifies no third-party packages; the core generator uses the Python standard library.

### 1. Clone the repository

```bash
git clone https://github.com/Venkatakishore125/Reusable-Asset-Return-and-Tracking-System-.git
cd Reusable-Asset-Return-and-Tracking-System-
```

### 2. Open the runnable project folder

```bash
cd reusable-asset-tracke/reusable-asset-tracker
```

### 3. Create and activate a virtual environment (recommended)

**Windows PowerShell**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install declared dependencies

```bash
python -m pip install -r requirements.txt
```

There are currently no third-party runtime dependencies.

### 5. Generate a small starter dataset

```bash
python -m src.main --starter
```

### 6. Generate the default dataset

```bash
python -m src.main
```

The default configuration is set to generate 20,000 assets, 10,000 shipments and 100,000 custody-event rows. Start with the smaller starter run to check the setup before generating the full dataset.

### 7. Customize scale and seed

```bash
python -m src.main --assets 1000 --shipments 500 --custody-events 5000 --seed 20261022
```

The default seed is `20261022`. Keeping the seed and scale the same makes synthetic generation repeatable.

## Generated data

Generated CSV files are written under `data/output/`.

| Output | Purpose |
|---|---|
| `AssetType.csv` | Asset categories and deposit/return settings |
| `Owner.csv` | Supplier, pool-operator and customer participants |
| `Location.csv` | Logistics locations |
| `ReusableAsset.csv` | Asset master records |
| `Shipment.csv` | Dispatch and expected-return information |
| `CustodyEvent.csv` | Dispatch, transfer and return movement history |
| `ReturnAuthorization.csv` | Return request and receipt information |
| `Inspection.csv` | Condition checks after a return |
| `Repair.csv` | Repair work and associated costs |
| `DepositLedger.csv` | Deposit charges and refunds |
| `AssetSnapshot.csv` | Derived asset view |

Supporting JSON outputs include `source_manifest.json`, `operational_metrics.json`, `validation_summary.json`, and the separate `data/ground_truth/ground_truth.json` anomaly examples.

## Business rules and validation

The current code includes logic for outstanding-age calculation, custody-event replay, accepted-location reconstruction, deposit reconciliation, repeated-refund candidate detection, and selected primary-key/foreign-key checks.

The generator includes five labelled negative scenarios: simultaneous location conflict, return before dispatch, duplicate refund, repair closure without inspection, and missing custody actor. These are intentional test cases. Review validation findings together with the ground-truth file rather than treating every flagged row as an accidental data-generation failure.

## Run tests

From `reusable-asset-tracke/reusable-asset-tracker/`:

```bash
python -m unittest discover -s tests -v
```

The tests cover starter generation, expected output files, selected ID and reference checks, anomaly labels, manifest hashes and selected business rules. A passing test suite is a useful baseline, not proof that every possible lifecycle case is handled.

## Documentation

- [Project README and usage](reusable-asset-tracke/reusable-asset-tracker/README.md)
- [Data dictionary](reusable-asset-tracke/reusable-asset-tracker/docs/data_dictionary.md)
- [Schema and business rules](reusable-asset-tracke/reusable-asset-tracker/docs/schema.md)
- [Design decisions](reusable-asset-tracke/reusable-asset-tracker/docs/design_decisions.md)
- [Prompt history](reusable-asset-tracke/reusable-asset-tracker/prompts/prompt_history.md)
- [Project workflow](docs/PROJECT_WORKFLOW.md)
- [Validation guide](docs/VALIDATION_GUIDE.md)

## Scope and limitations

This is a synthetic-data and business-rule challenge project, not a deployed logistics application. It does not currently provide a web dashboard, live GPS tracking, barcode/RFID integration, a production relational database or live carrier integration. The existing design notes also describe limitations around multi-shipment event replay and complete lifecycle reconciliation.

## Author

**Venkat Kishore**  
GitHub: [@Venkatakishore125](https://github.com/Venkatakishore125)