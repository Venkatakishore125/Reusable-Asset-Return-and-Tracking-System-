# Schema and business rules

The CSV files mirror relational entities and use primary/foreign-key fields documented in `data_dictionary.md`. Master data is generated before dependent records. The generator uses seed `20261022` by default.

Rules:
1. Asset IDs and transaction IDs are deterministic, zero-padded, and immutable.
2. A return authorization is OPEN until receipt is recorded; received returns have an inspection.
3. Damaged returns create a repair record and do not receive an automatic deposit refund in the baseline.
4. An asset is LOST when it has not returned and the dispatch age exceeds 30 days; otherwise it can be OVERDUE after its due date or IN_CIRCULATION.
5. Ledger charges are positive and refunds negative. The net balance is calculated by summing source ledger entries.
6. Ground-truth anomalies are injected after valid baseline records and stored separately under `data/ground_truth/`.
7. The asset snapshot reports a derived status, outstanding age, and ledger balance. For event-history reconstruction, use ordered CustodyEvent rows and flag conflicting active locations for review.

## Known limitations to discuss
This is a synthetic challenge implementation, not a production logistics platform. The starter generator is designed for local execution; event identity and lifecycle reconciliation can be improved further for multi-shipment-per-asset cases. `AssetSnapshot.current_location_id` currently follows generated state, while conflict events are surfaced as labelled anomalies for validation rather than silently overwriting history. A production version should derive the location exclusively by replaying valid custody events, use database constraints/transactions, and implement idempotent event ingestion.
