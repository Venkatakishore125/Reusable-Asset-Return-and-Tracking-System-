"""Deterministic synthetic data generator for reusable-asset lifecycle records."""
from __future__ import annotations
import argparse, csv, json, random, hashlib
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from .config import SEED, DEFAULT_SCALE, STARTER_SCALE, RETURN_WINDOW_DAYS, LOSS_AFTER_DAYS
from .business_rules import reconstruct_locations, reconcile_deposits, calculate_outstanding_days

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "output"
GT = ROOT / "data" / "ground_truth"
ASSET_TYPES = [
    {"asset_type_id":"TYPE-001","name":"Pallet","deposit_amount":25.0,"return_window_days":14,"repairable":True},
    {"asset_type_id":"TYPE-002","name":"Reusable Crate","deposit_amount":12.0,"return_window_days":10,"repairable":True},
    {"asset_type_id":"TYPE-003","name":"Transport Cage","deposit_amount":80.0,"return_window_days":21,"repairable":True},
]
OWNERS = [{"owner_id":"OWN-001","name":"Northstar Supply","owner_type":"Supplier"},{"owner_id":"OWN-002","name":"Loop Logistics","owner_type":"Pool Operator"},{"owner_id":"OWN-003","name":"Retail Partner","owner_type":"Customer"}]
LOCATIONS = [{"location_id":f"LOC-{i:03d}","name":name,"location_type":kind,"country":"IN"} for i,(name,kind) in enumerate([("Central Depot","Warehouse"),("Supplier Hub","Supplier"),("Retail DC","Warehouse"),("Repair Center","Repair Center"),("Transit Yard","Transit"),("Return Dock","Warehouse")],1)]

def iso(d): return d.isoformat()
def write_csv(path, rows):
    rows=list(rows)
    path.parent.mkdir(parents=True,exist_ok=True)
    if not rows: path.write_text("",encoding="utf-8"); return
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
def dump_json(path, obj): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(obj,indent=2,default=str),encoding="utf-8")

def generate(scale=DEFAULT_SCALE, seed=SEED):
    rng=random.Random(seed); OUT.mkdir(parents=True,exist_ok=True); GT.mkdir(parents=True,exist_ok=True)
    today=date(2026,10,27); start=today-timedelta(days=180)
    assets=[]; shipments=[]; custody=[]; rmas=[]; inspections=[]; repairs=[]; ledger=[]; truth=[]
    for i in range(1,scale['assets']+1):
        typ=ASSET_TYPES[(i-1)%len(ASSET_TYPES)]
        assets.append({"asset_id":f"ASSET-{i:07d}","asset_type_id":typ['asset_type_id'],"owner_id":OWNERS[(i-1)%len(OWNERS)]['owner_id'],"serial_number":f"SN-{i:08d}","created_date":iso(start+timedelta(days=rng.randint(0,150))),"lifecycle_state":"AVAILABLE","current_location_id":"LOC-001"})
    # Create shipments and valid dispatch/transfer event chains first.
    asset_shipments=defaultdict(list)
    for i in range(1,scale['shipments']+1):
        a=assets[(i-1)%len(assets)]; dispatch=start+timedelta(days=rng.randint(0,150)); src="LOC-001"; dst=rng.choice(["LOC-002","LOC-003","LOC-005"])
        shipments.append({"shipment_id":f"SHP-2026-{i:06d}","origin_location_id":src,"destination_location_id":dst,"carrier_owner_id":"OWN-002","dispatch_date":iso(dispatch),"expected_return_date":iso(dispatch+timedelta(days=ASSET_TYPES[(i-1)%3]['return_window_days'])) ,"shipment_status":"DISPATCHED"})
        asset_shipments[a['asset_id']].append(shipments[-1])
        custody.append({"custody_event_id":f"CUST-{a['asset_id']}-{i:06d}","asset_id":a['asset_id'],"shipment_id":shipments[-1]['shipment_id'],"event_type":"DISPATCH","event_date":iso(dispatch),"from_location_id":src,"to_location_id":dst,"actor_owner_id":"OWN-002","issue_type":"NONE"})
        # Some assets get a transfer event; use unique per-asset event counters.
        if rng.random()<0.65:
            transfer=dispatch+timedelta(days=rng.randint(1,4)); nextloc=rng.choice(["LOC-003","LOC-005","LOC-006"])
            custody.append({"custody_event_id":f"CUST-{a['asset_id']}-{i+scale['shipments']:06d}","asset_id":a['asset_id'],"shipment_id":shipments[-1]['shipment_id'],"event_type":"TRANSFER","event_date":iso(transfer),"from_location_id":dst,"to_location_id":nextloc,"actor_owner_id":rng.choice(["OWN-001","OWN-002","OWN-003"]),"issue_type":"NONE"})
    # Generate return authorizations, inspection, repair and deposit entries from rules.
    for i, a in enumerate(assets,1):
        linked=asset_shipments.get(a['asset_id'],[])
        if not linked: continue
        sh=linked[0]; dispatch=date.fromisoformat(sh['dispatch_date']); due=date.fromisoformat(sh['expected_return_date']); typ=ASSET_TYPES[(i-1)%3]
        status_roll=rng.random(); returned = status_roll < 0.72
        damaged = returned and rng.random()<0.12
        lost = (not returned) and (today-dispatch).days>LOSS_AFTER_DAYS
        rma_id=f"RMA-2026-{len(rmas)+1:06d}"
        if returned:
            ret_date=min(today, due+timedelta(days=rng.randint(-3,18)))
            rmas.append({"rma_id":rma_id,"asset_id":a['asset_id'],"shipment_id":sh['shipment_id'],"created_date":iso(max(dispatch,ret_date-timedelta(days=rng.randint(1,5)))),"status":"RECEIVED","received_date":iso(ret_date)})
            event_num=sum(1 for e in custody if e['asset_id']==a['asset_id'])+1
            custody.append({"custody_event_id":f"CUST-{a['asset_id']}-800001","asset_id":a['asset_id'],"shipment_id":sh['shipment_id'],"event_type":"RETURN_RECEIVED","event_date":iso(ret_date),"from_location_id":sh['destination_location_id'],"to_location_id":"LOC-006","actor_owner_id":"OWN-002","issue_type":"NONE"})
            condition="DAMAGED" if damaged else "GOOD"
            inspections.append({"inspection_id":f"INSP-{len(inspections)+1:06d}","asset_id":a['asset_id'],"rma_id":rma_id,"inspection_date":iso(ret_date+timedelta(days=1) if ret_date<today else ret_date),"condition":condition,"notes":"Synthetic inspection"})
            if damaged:
                rep_id=f"REP-2026-{len(repairs)+1:06d}"
                repairs.append({"repair_id":rep_id,"asset_id":a['asset_id'],"inspection_id":inspections[-1]['inspection_id'],"opened_date":inspections[-1]['inspection_date'],"closed_date":iso(min(today,date.fromisoformat(inspections[-1]['inspection_date'])+timedelta(days=3))),"repair_status":"CLOSED","cost_amount":round(rng.uniform(5,40),2)})
            ledger.append({"ledger_entry_id":f"LED-{len(ledger)+1:07d}","asset_id":a['asset_id'],"rma_id":rma_id,"entry_type":"DEPOSIT_CHARGE","amount":typ['deposit_amount'],"entry_date":sh['dispatch_date'],"reference_id":sh['shipment_id']})
            if not damaged:
                ledger.append({"ledger_entry_id":f"LED-{len(ledger)+1:07d}","asset_id":a['asset_id'],"rma_id":rma_id,"entry_type":"DEPOSIT_REFUND","amount":-typ['deposit_amount'],"entry_date":iso(ret_date),"reference_id":rma_id})
            a['lifecycle_state']='UNDER_REPAIR' if damaged else 'AVAILABLE'; a['current_location_id']='LOC-004' if damaged else 'LOC-006'
        else:
            rmas.append({"rma_id":rma_id,"asset_id":a['asset_id'],"shipment_id":sh['shipment_id'],"created_date":iso(max(dispatch,due-timedelta(days=2))),"status":"OPEN","received_date":""})
            ledger.append({"ledger_entry_id":f"LED-{len(ledger)+1:07d}","asset_id":a['asset_id'],"rma_id":rma_id,"entry_type":"DEPOSIT_CHARGE","amount":typ['deposit_amount'],"entry_date":sh['dispatch_date'],"reference_id":sh['shipment_id']})
            a['lifecycle_state']='LOST' if lost else ('OVERDUE' if today>due else 'IN_CIRCULATION')
            a['current_location_id']=sh['destination_location_id']
    # Pad the valid baseline event stream to the requested event volume before injecting five known anomalies.
    # This keeps the configured custody-event count reproducible and includes dispatch, transfer, and return events.
    target_baseline_events=max(0, scale["custody_events"]-3)
    filler_index=1
    while len(custody) < target_baseline_events and assets:
        a=assets[(filler_index-1) % len(assets)]
        linked=asset_shipments.get(a["asset_id"], [])
        if linked:
            sh=linked[(filler_index-1) % len(linked)]
            base_date=date.fromisoformat(sh["dispatch_date"])
            event_date=min(today, base_date+timedelta(days=1+(filler_index % 25)))
            from_loc=sh["destination_location_id"]
            to_loc=rng.choice(["LOC-002","LOC-003","LOC-005","LOC-006"])
            custody.append({"custody_event_id":f"CUST-{a['asset_id']}-700000{filler_index:06d}","asset_id":a["asset_id"],"shipment_id":sh["shipment_id"],"event_type":"TRANSFER","event_date":iso(event_date),"from_location_id":from_loc,"to_location_id":to_loc,"actor_owner_id":rng.choice(["OWN-001","OWN-002","OWN-003"]),"issue_type":"NONE"})
        filler_index += 1
        if filler_index > target_baseline_events*3 + 10 and len(custody) < target_baseline_events:
            raise RuntimeError("Could not fill custody-event target: no assets have linked shipments")
    # Add clearly labelled, isolated negative scenarios; labels are never included in ordinary input exports.
    def mark(issue, entity, record_id, expected): truth.append({"issue_type":issue,"entity_name":entity,"record_id":record_id,"expected_decision":expected,"rule":"Injected exception for validation; not a naturally inferred label."})
    if assets:
        a=assets[0]; sh=shipments[0]
        custody.append({"custody_event_id":f"CUST-{a['asset_id']}-900001","asset_id":a['asset_id'],"shipment_id":sh['shipment_id'],"event_type":"LOCATION_CONFLICT","event_date":iso(today),"from_location_id":"LOC-002","to_location_id":"LOC-003","actor_owner_id":"OWN-002","issue_type":"SIMULTANEOUS_LOCATION"}); mark("SIMULTANEOUS_LOCATION","ReusableAsset",a['asset_id'],"Flag conflicting active locations for manual review")
        custody.append({"custody_event_id":f"CUST-{a['asset_id']}-900002","asset_id":a['asset_id'],"shipment_id":sh['shipment_id'],"event_type":"RETURN_RECEIVED","event_date":iso(date.fromisoformat(sh['dispatch_date'])-timedelta(days=1)),"from_location_id":"LOC-002","to_location_id":"LOC-006","actor_owner_id":"OWN-002","issue_type":"RETURN_BEFORE_DISPATCH"}); mark("RETURN_BEFORE_DISPATCH","CustodyEvent",f"CUST-{a['asset_id']}-900002","Reject or quarantine return event dated before dispatch")
        ledger.append({"ledger_entry_id":"LED-ANOMALY-REFUND-2","asset_id":a['asset_id'],"rma_id":rmas[0]['rma_id'] if rmas else "","entry_type":"DEPOSIT_REFUND","amount":-25.0,"entry_date":iso(today),"reference_id":"ANOMALY-DUPLICATE-REFUND"}); mark("DUPLICATE_REFUND","DepositLedger","LED-ANOMALY-REFUND-2","Flag duplicate refund; reconcile by asset and deposit")
        repairs.append({"repair_id":"REP-2026-900001","asset_id":a['asset_id'],"inspection_id":"","opened_date":iso(today-timedelta(days=2)),"closed_date":iso(today),"repair_status":"CLOSED","cost_amount":10.0}); mark("REPAIR_WITHOUT_INSPECTION","Repair","REP-2026-900001","Do not accept closure without a valid inspection")
        custody.append({"custody_event_id":f"CUST-{a['asset_id']}-900003","asset_id":a['asset_id'],"shipment_id":sh['shipment_id'],"event_type":"TRANSFER","event_date":iso(today),"from_location_id":"LOC-002","to_location_id":"LOC-003","actor_owner_id":"","issue_type":"MISSING_ACTOR"}); mark("MISSING_ACTOR","CustodyEvent",f"CUST-{a['asset_id']}-900003","Require actor; flag event for correction")
    # Master data and dependent tables exported separately.
    tables={"AssetType":ASSET_TYPES,"Owner":OWNERS,"Location":LOCATIONS,"ReusableAsset":assets,"Shipment":shipments,"CustodyEvent":custody,"ReturnAuthorization":rmas,"Inspection":inspections,"Repair":repairs,"DepositLedger":ledger}
    for name, rows in tables.items(): write_csv(OUT/f"{name}.csv",rows)
    # Derived snapshot is calculated from source records, not independently randomized.
    ledger_by_asset=defaultdict(float)
    for row in ledger: ledger_by_asset[row['asset_id']]+=float(row['amount'])
    custody_by_asset=defaultdict(list)
    for row in custody: custody_by_asset[row['asset_id']].append(row)
    replay = reconstruct_locations(assets, custody, shipments)
    deposit_reconciliation = reconcile_deposits(ledger)
    snapshot=[]
    for a in assets:
        evs=sorted(custody_by_asset[a['asset_id']],key=lambda e:e['event_date'])
        latest=evs[-1] if evs else None
        linked=asset_shipments.get(a['asset_id'],[]); dispatch=date.fromisoformat(linked[0]['dispatch_date']) if linked else None
        snapshot.append({"asset_id":a['asset_id'],"lifecycle_state":a['lifecycle_state'],"current_location_id":replay["locations"].get(a['asset_id'], a['current_location_id']),"days_outstanding":calculate_outstanding_days(iso(dispatch) if dispatch else "", "" if a['lifecycle_state'] in ("IN_CIRCULATION","OVERDUE","LOST") else iso(today), iso(today)),"loss_status":"LOST" if a['lifecycle_state']=="LOST" else "NOT_LOST","deposit_net_balance":round(ledger_by_asset[a['asset_id']],2),"latest_event_type":latest['event_type'] if latest else "NONE"})
    write_csv(OUT/"AssetSnapshot.csv",snapshot); dump_json(GT/"ground_truth.json",truth)
    dump_json(OUT/"operational_metrics.json", {"as_of_date": iso(today), "assets": len(assets), "shipments": len(shipments), "custody_events": len(custody), "rejected_custody_event_count": len(replay["rejected_event_ids"]), "rejected_custody_event_ids_sample": replay["rejected_event_ids"][:100], "duplicate_refund_entry_ids": deposit_reconciliation["duplicate_refund_entry_ids"], "net_deposit_balance_total": round(sum(deposit_reconciliation["net_balance_by_asset"].values()), 2), "ground_truth_cases": len(truth)})
    manifest={"seed":seed,"scale":scale,"generated_at":"fixed-by-design: 2026-10-27","tables":{name:{"rows":len(rows),"sha256":hashlib.sha256((OUT/f"{name}.csv").read_bytes()).hexdigest()} for name,rows in tables.items()},"snapshot":{"rows":len(snapshot),"sha256":hashlib.sha256((OUT/"AssetSnapshot.csv").read_bytes()).hexdigest()},"ground_truth_rows":len(truth)}
    dump_json(OUT/"source_manifest.json",manifest)
    return tables, snapshot, truth

if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('--starter',action='store_true'); p.add_argument('--seed',type=int,default=SEED); p.add_argument('--assets',type=int); p.add_argument('--shipments',type=int); p.add_argument('--custody-events',type=int)
    args=p.parse_args(); scale=STARTER_SCALE.copy() if args.starter else DEFAULT_SCALE.copy()
    for key,val in [('assets',args.assets),('shipments',args.shipments),('custody_events',args.custody_events)]:
        if val is not None: scale[key]=val
    generate(scale,args.seed); print(f"Generated data in {OUT}; seed={args.seed}; scale={scale}")
