# Reusable Asset Return & Tracking System

This project explores how reusable logistics assets can be followed through their day-to-day movement. Examples include pallets, reusable crates and transport cages that move between suppliers, warehouses, carriers and customers before being returned, inspected and put back into circulation.

The goal is to keep a useful record of each asset's identity, shipment history, custody changes, return status and deposit activity. The current repository implements a deterministic synthetic-data generator and validation/business-rule checks that can be run locally.

## What is included

- Master data for asset types, owners and locations.
- Reusable asset and shipment records.
- Custody-event history for dispatches, transfers and returns.
- Return authorization, inspection and repair records.
- Deposit charge and refund ledger entries.
- Derived asset snapshots and operational metrics.
- Separate ground-truth examples for deliberately injected data-quality scenarios.
- Validation checks and unit/acceptance tests.

## Business workflow represented

1. **Register an asset:** assign an asset ID, type, owner and initial location.
2. **Dispatch it:** connect the asset to a shipment and record dispatch.
3. **Track custody:** record transfers between locations and responsible parties.
4. **Process a return:** create a return authorization and record receipt.
5. **Inspect the asset:** capture its condition after return.
6. **Repair when needed:** create a repair record for damaged items.
7. **Reconcile deposits:** record charges and refunds and calculate the net balance.
8. **Review data quality:** validate references and identify selected inconsistent records.

This workflow describes the generated records. It is not a live application where users submit transactions through a user interface.

## Technology

- Python 3.10+ recommended
- Python standard library (the current requirements file has no third-party dependencies)
- CSV for generated tables
- JSON for manifests, metrics, validation summaries and ground-truth examples
- `unittest` for automated tests

## Setup

Create a virtual environment from this directory:

```bash
python -m venv .venv
```

Activate it using the command for your operating system:

```powershell
.\.venv\Scripts\Activate.ps1
```

```bash
source .venv/bin/activate
```

Install declared dependencies:

```bash
python -m pip install -r requirements.txt
```

The current implementation uses the standard library, so no extra package installation is required.

## Run

Generate a small starter dataset:

```bash
python -m src.main --starter
```

Generate the default dataset:

```bash
python -m src.main
```

Override data volume and seed:

```bash
python -m src.main --assets 1000 --shipments 500 --custody-events 5000 --seed 20261022
```

The default scale is configured in `src/config.py`: 20,000 assets, 10,000 shipments and 100,000 custody-event rows. The default seed is `20261022`.

## Generated files

All generated tables are written to `data/output/`: `AssetType.csv`, `Owner.csv`, `Location.csv`, `ReusableAsset.csv`, `Shipment.csv`, `CustodyEvent.csv`, `ReturnAuthorization.csv`, `Inspection.csv`, `Repair.csv`, `DepositLedger.csv`, and `AssetSnapshot.csv`.

JSON outputs include `source_manifest.json` (seed, scale, row counts and hashes), `operational_metrics.json` (selected operational and reconciliation counts), `validation_summary.json` (validation results when run directly), and `data/ground_truth/ground_truth.json` (labelled anomaly examples).

## Business rules in the current code

The `src/business_rules.py` module contains functions for replaying custody events to reconstruct accepted locations, calculating outstanding days for an unreturned asset, reconciling deposit ledger balances, and identifying repeated refund candidates for the same asset and return authorization.

The generator deliberately adds five negative scenarios: `SIMULTANEOUS_LOCATION`, `RETURN_BEFORE_DISPATCH`, `DUPLICATE_REFUND`, `REPAIR_WITHOUT_INSPECTION`, and `MISSING_ACTOR`. These are test cases, not ordinary business transactions.

## Run tests

```bash
python -m unittest discover -s tests -v
```

The tests generate starter data before checking it. Generated files under `data/output/` may be replaced when the test suite runs.

## Project structure

```text
reusable-asset-tracker/
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

## Design notes and limitations

- The records are synthetic and do not represent a real company's logistics data.
- CSV files are easy to inspect, but a production system would normally use a database with constraints and transactions.
- The project is not yet a live tracking product and does not integrate with GPS, RFID, barcode scanners or carrier APIs.
- Multi-shipment event replay and lifecycle reconciliation have known limitations; see `docs/design_decisions.md` and `docs/schema.md`.
- Duplicate refund candidates need review; a repeated refund record is not, by itself, proof of fraud.

## Further improvements

- Add a relational persistence layer and transactional updates.
- Improve lifecycle replay for assets used across multiple shipments.
- Add APIs or a user interface for asset registration and custody handoffs.
- Add barcode/RFID scanning or carrier status ingestion.
- Add role-based access, audit controls and operational reporting.
- Expand edge-case and reconciliation tests.

## Author

**Venkat Kishore**  
GitHub: [@Venkatakishore125](https://github.com/Venkatakishore125)