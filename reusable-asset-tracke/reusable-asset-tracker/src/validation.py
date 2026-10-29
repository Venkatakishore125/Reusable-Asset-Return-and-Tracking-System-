"""Basic relational, uniqueness, lifecycle, and reconciliation checks."""
import csv
from collections import Counter, defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'/'output'
def read(name):
    with (DATA/f'{name}.csv').open(newline='',encoding='utf-8') as f: return list(csv.DictReader(f))
def validate():
    issues=[]
    assets=read('ReusableAsset'); types=read('AssetType'); owners=read('Owner'); locations=read('Location'); shipments=read('Shipment'); events=read('CustodyEvent'); rmas=read('ReturnAuthorization'); inspections=read('Inspection'); repairs=read('Repair'); ledger=read('DepositLedger')
    checks=[('ReusableAsset','asset_id',assets),('Shipment','shipment_id',shipments),('CustodyEvent','custody_event_id',events),('ReturnAuthorization','rma_id',rmas),('Inspection','inspection_id',inspections),('Repair','repair_id',repairs),('DepositLedger','ledger_entry_id',ledger)]
    for table,key,rows in checks:
        ids=[r[key] for r in rows]
        if len(ids)!=len(set(ids)): issues.append(f'{table}: duplicate primary key in {key}')
    asset_ids={r['asset_id'] for r in assets}; type_ids={r['asset_type_id'] for r in types}; owner_ids={r['owner_id'] for r in owners}; loc_ids={r['location_id'] for r in locations}; ship_ids={r['shipment_id'] for r in shipments}; rma_ids={r['rma_id'] for r in rmas}; insp_ids={r['inspection_id'] for r in inspections}
    for r in assets:
        if r['asset_type_id'] not in type_ids: issues.append(f"Asset {r['asset_id']}: invalid asset_type_id")
        if r['owner_id'] not in owner_ids: issues.append(f"Asset {r['asset_id']}: invalid owner_id")
        if r['current_location_id'] not in loc_ids: issues.append(f"Asset {r['asset_id']}: invalid location")
    for r in shipments:
        if r['origin_location_id'] not in loc_ids or r['destination_location_id'] not in loc_ids: issues.append(f"Shipment {r['shipment_id']}: invalid location FK")
        if r['carrier_owner_id'] not in owner_ids: issues.append(f"Shipment {r['shipment_id']}: invalid owner FK")
    for r in events:
        if r['asset_id'] not in asset_ids: issues.append(f"Event {r['custody_event_id']}: invalid asset FK")
        if r['shipment_id'] not in ship_ids: issues.append(f"Event {r['custody_event_id']}: invalid shipment FK")
        if r['from_location_id'] not in loc_ids or r['to_location_id'] not in loc_ids: issues.append(f"Event {r['custody_event_id']}: invalid location FK")
        if not r['actor_owner_id']: issues.append(f"Event {r['custody_event_id']}: missing actor")
    for r in rmas:
        if r['asset_id'] not in asset_ids or r['shipment_id'] not in ship_ids: issues.append(f"RMA {r['rma_id']}: invalid FK")
    for r in inspections:
        if r['asset_id'] not in asset_ids or r['rma_id'] not in rma_ids: issues.append(f"Inspection {r['inspection_id']}: invalid FK")
    for r in repairs:
        if r['asset_id'] not in asset_ids: issues.append(f"Repair {r['repair_id']}: invalid asset FK")
        if r['inspection_id'] and r['inspection_id'] not in insp_ids: issues.append(f"Repair {r['repair_id']}: invalid inspection FK")
        if r['repair_status']=='CLOSED' and not r['inspection_id']: issues.append(f"Repair {r['repair_id']}: closed without inspection")
    # Deposit entries must be numeric; negative values represent refunds.
    for r in ledger:
        try: float(r['amount'])
        except ValueError: issues.append(f"Ledger {r['ledger_entry_id']}: nonnumeric amount")
        if r['asset_id'] not in asset_ids: issues.append(f"Ledger {r['ledger_entry_id']}: invalid asset FK")
    # Ground truth intentionally injected anomalies should be surfaced, not silently removed.
    return {"status":"PASS" if not issues else "ISSUES_FOUND","issue_count":len(issues),"issues":issues,"row_counts":{"assets":len(assets),"shipments":len(shipments),"custody_events":len(events),"rmas":len(rmas),"inspections":len(inspections),"repairs":len(repairs),"ledger_entries":len(ledger)}}
if __name__=='__main__':
    import json
    result=validate(); print(json.dumps(result,indent=2)); (ROOT/'data'/'output'/'validation_summary.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
