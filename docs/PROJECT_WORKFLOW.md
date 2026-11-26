# Project Workflow

## Why this project matters

Reusable logistics items such as pallets, crates and transport cages are used repeatedly across suppliers, warehouses, carriers and customers. When records are spread across different handoffs, it becomes difficult to confirm where an asset is, whether it has returned, and whether the deposit record matches the movement history.

This project models that workflow with generated data so the records and business rules can be inspected and tested without using real company or customer information.

## Main participants

| Participant | Typical responsibility |
|---|---|
| Supplier | Provides reusable assets and may receive returned items |
| Planner | Plans asset availability and shipment movements |
| Carrier / warehouse operator | Handles shipment and custody handoffs |
| Logistics analyst | Reviews movements, overdue assets and data quality |
| Operations manager | Uses asset and return information to make operational decisions |

These are the business roles represented by the project context. The current code generates synthetic owner records; it does not implement separate user accounts or role-based login.

## End-to-end lifecycle

1. **Asset registration** — assign an immutable asset ID, asset type, owner and starting location.
2. **Shipment planning and dispatch** — create a shipment with origin, destination, dispatch date and expected return date.
3. **Custody recording** — record who handled the asset and where it moved.
4. **Return authorization** — create a return record for an asset expected to come back.
5. **Return receipt** — record that the asset arrived back at a receiving location.
6. **Inspection** — capture whether the returned asset is in good or damaged condition.
7. **Repair** — create a repair record when an asset needs attention before reuse.
8. **Deposit reconciliation** — record deposit charges and refunds and calculate the resulting balance.
9. **Operational review** — inspect the derived asset snapshot, metrics, validation findings and labelled anomaly cases.

## Entity relationships

- An asset type can describe many reusable assets.
- An owner can own or handle many assets and shipments.
- A location can be referenced as the origin, destination, or from/to location of events.
- An asset can have many shipment, custody, return, inspection, repair and ledger records over time.
- A shipment can have multiple custody events and return authorizations in this simplified data model.
- The asset snapshot is a derived view; custody events remain the historical record.

For field-level definitions and keys, see the data dictionary and schema notes in reusable-asset-tracke/reusable-asset-tracker/docs/.

## Known exception scenarios

The generator includes labelled negative cases for:

- SIMULTANEOUS_LOCATION — conflicting location information.
- RETURN_BEFORE_DISPATCH — a return event dated before dispatch.
- DUPLICATE_REFUND — a repeated refund candidate for an asset and return authorization.
- REPAIR_WITHOUT_INSPECTION — a repair record closed without a linked inspection.
- MISSING_ACTOR — a custody event without an actor.

These records are intentionally included for validation and review. The ground-truth labels are stored separately from operational CSV tables.

## What a production version would still need

- A relational database with constraints and transactional updates.
- Authenticated users and role-based permissions.
- An API or user interface for registering assets and recording handoffs.
- Idempotent ingestion to handle duplicate messages or events safely.
- Complete event replay and lifecycle reconciliation across repeated shipments.
- Integration with barcode/RFID readers, GPS or carrier systems where appropriate.
- Monitoring, audit retention, backups and operational security controls.