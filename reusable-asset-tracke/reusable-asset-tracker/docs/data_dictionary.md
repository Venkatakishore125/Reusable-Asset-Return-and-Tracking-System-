# Data dictionary (starter version)

Types: `string` unless stated; dates use ISO-8601 `YYYY-MM-DD`; money is decimal currency units (synthetic INR-like values). `PK` = primary key, `FK` = foreign key. IDs are immutable and unique.

| Entity | Field | Type | Required | Validation / allowed values |
|---|---|---|---|---|
| AssetType | asset_type_id | string, PK | Yes | `TYPE-NNN`, unique |
| AssetType | name | string | Yes | Pallet, Reusable Crate, Transport Cage |
| AssetType | deposit_amount | decimal | Yes | >= 0 |
| AssetType | return_window_days | integer | Yes | > 0; days |
| AssetType | repairable | boolean | Yes | true/false |
| ReusableAsset | asset_id | string, PK | Yes | `ASSET-0000001` pattern, unique |
| ReusableAsset | asset_type_id | string, FK | Yes | Must exist in AssetType |
| ReusableAsset | owner_id | string, FK | Yes | Must exist in Owner |
| ReusableAsset | serial_number | string | Yes | Unique synthetic serial |
| ReusableAsset | created_date | date | Yes | Valid ISO date |
| ReusableAsset | lifecycle_state | enum | Yes | AVAILABLE, UNDER_REPAIR, LOST, OVERDUE, IN_CIRCULATION |
| ReusableAsset | current_location_id | string, FK | Yes | Must exist in Location; snapshot is reconstructible from events in a production version |
| Owner | owner_id | string, PK | Yes | Unique owner ID |
| Owner | name | string | Yes | Non-empty |
| Owner | owner_type | enum | Yes | Supplier, Pool Operator, Customer |
| Location | location_id | string, PK | Yes | Unique location ID |
| Location | name | string | Yes | Non-empty |
| Location | location_type | enum | Yes | Warehouse, Supplier, Repair Center, Transit |
| Location | country | string | Yes | ISO-like country code; `IN` in synthetic data |
| Shipment | shipment_id | string, PK | Yes | `SHP-2026-000001`, unique |
| Shipment | origin_location_id / destination_location_id | string, FK | Yes | Must exist in Location |
| Shipment | carrier_owner_id | string, FK | Yes | Must exist in Owner |
| Shipment | dispatch_date / expected_return_date | date | Yes | Expected return must be on/after dispatch |
| Shipment | shipment_status | enum | Yes | DISPATCHED in generated baseline |
| CustodyEvent | custody_event_id | string, PK | Yes | `CUST-<asset-id>-NNNNNN`, unique |
| CustodyEvent | asset_id / shipment_id | string, FK | Yes | Must exist in parent tables |
| CustodyEvent | event_type | enum-like string | Yes | DISPATCH, TRANSFER, RETURN_RECEIVED, LOCATION_CONFLICT |
| CustodyEvent | event_date | date | Yes | ISO date; compare to dispatch/previous events |
| CustodyEvent | from_location_id / to_location_id | string, FK | Yes | Must exist in Location |
| CustodyEvent | actor_owner_id | string, optional for anomaly | Usually | Must exist in Owner unless deliberately blank and labelled MISSING_ACTOR |
| CustodyEvent | issue_type | enum-like string | Yes | NONE or documented anomaly label |
| ReturnAuthorization | rma_id | string, PK | Yes | `RMA-2026-000001`, unique |
| ReturnAuthorization | asset_id / shipment_id | string, FK | Yes | Must exist in parent tables |
| ReturnAuthorization | created_date | date | Yes | ISO date |
| ReturnAuthorization | status | enum | Yes | OPEN, RECEIVED |
| ReturnAuthorization | received_date | date, optional | No | Required when status=RECEIVED; blank while OPEN |
| Inspection | inspection_id | string, PK | Yes | Unique `INSP-NNNNNN` |
| Inspection | asset_id / rma_id | string, FK | Yes | Must exist in parent tables |
| Inspection | inspection_date | date | Yes | On/after receipt date in valid baseline |
| Inspection | condition | enum | Yes | GOOD, DAMAGED |
| Inspection | notes | string | No | Free text; synthetic only |
| Repair | repair_id | string, PK | Yes | `REP-2026-000001`, unique |
| Repair | asset_id | string, FK | Yes | Must exist in ReusableAsset |
| Repair | inspection_id | string, optional FK | No | Must reference Inspection; intentionally blank only for labelled anomaly |
| Repair | opened_date / closed_date | date | Yes/optional | Closed date on/after open date; CLOSED requires inspection except labelled anomaly |
| Repair | repair_status | enum | Yes | OPEN, CLOSED |
| Repair | cost_amount | decimal | Yes | >= 0 |
| DepositLedger | ledger_entry_id | string, PK | Yes | Unique ledger ID |
| DepositLedger | asset_id / rma_id | string, FK-like | Yes/optional | Asset must exist; RMA may be blank only if documented |
| DepositLedger | entry_type | enum | Yes | DEPOSIT_CHARGE, DEPOSIT_REFUND |
| DepositLedger | amount | decimal | Yes | Charges positive, refunds negative |
| DepositLedger | entry_date | date | Yes | ISO date |
| DepositLedger | reference_id | string | Yes | Shipment/RMA reference for traceability |

## Relationships and cardinality
- AssetType 1:N ReusableAsset; Owner 1:N ReusableAsset and Shipment.
- Location 1:N Shipment origin/destination and CustodyEvent from/to location.
- ReusableAsset 1:N CustodyEvent, ReturnAuthorization, Inspection, Repair, and DepositLedger.
- Shipment 1:N CustodyEvent and ReturnAuthorization in this simplified model.
- ReturnAuthorization 1:N Inspection and DepositLedger; Inspection 1:N Repair (nullable inspection FK is allowed only for a labelled negative test).
- Owner-to-Location access or asset-to-shipment assignment can become N:M in a production model; represent those with bridge tables rather than duplicated columns.
- Events are append-only. Current state is a derived snapshot, not a replacement for event history.
