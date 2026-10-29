"""Pure business rules for replaying custody history and reconciling deposits.

Ground-truth anomalies are deliberately excluded from the operational view. This
keeps bad events visible in the audit dataset without letting them silently
rewrite an asset's accepted location.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import date

INVALID_ISSUES = {"SIMULTANEOUS_LOCATION", "RETURN_BEFORE_DISPATCH", "MISSING_ACTOR"}


def reconstruct_locations(assets, events, shipments):
    """Return accepted current locations and rejected event IDs.

    Events are replayed in date/ID order. Events with a known injected issue,
    missing actor, unknown asset/shipment, or a return before dispatch are
    rejected from the operational projection but remain in source history.
    A transfer is accepted only if its from-location matches the last accepted
    location; dispatch starts from the shipment origin.
    """
    asset_ids = {a["asset_id"] for a in assets}
    ship_by_id = {s["shipment_id"]: s for s in shipments}
    location = {a["asset_id"]: a.get("current_location_id", "") for a in assets}
    rejected = []
    events_by_asset = defaultdict(list)
    for event in events:
        events_by_asset[event.get("asset_id", "")].append(event)
    for asset_id, rows in events_by_asset.items():
        if asset_id not in asset_ids:
            rejected.extend(e.get("custody_event_id", "") for e in rows)
            continue
        rows.sort(key=lambda e: (e.get("event_date", ""), e.get("custody_event_id", "")))
        current = "LOC-001"
        dispatched_at = {}
        for e in rows:
            eid = e.get("custody_event_id", "")
            issue = e.get("issue_type", "NONE")
            shipment = ship_by_id.get(e.get("shipment_id", ""))
            if issue in INVALID_ISSUES or not e.get("actor_owner_id") or shipment is None:
                rejected.append(eid); continue
            event_date = e.get("event_date", "")
            if e.get("event_type") == "DISPATCH":
                if e.get("from_location_id") != shipment.get("origin_location_id"):
                    rejected.append(eid); continue
                current = e.get("to_location_id", current)
                dispatched_at[e.get("shipment_id", "")] = event_date
            elif e.get("event_type") == "RETURN_RECEIVED":
                dispatch_date = dispatched_at.get(e.get("shipment_id", ""), shipment.get("dispatch_date", ""))
                if not dispatch_date or event_date < dispatch_date:
                    rejected.append(eid); continue
                current = e.get("to_location_id", current)
            elif e.get("event_type") == "TRANSFER":
                if e.get("from_location_id") != current:
                    rejected.append(eid); continue
                current = e.get("to_location_id", current)
            else:
                rejected.append(eid)
        location[asset_id] = current
    return {"locations": location, "rejected_event_ids": sorted(set(rejected))}


def calculate_outstanding_days(dispatch_date, return_date, as_of):
    """Days outstanding for an open asset; zero after a completed return."""
    if not dispatch_date or return_date:
        return 0
    return max(0, (date.fromisoformat(as_of) - date.fromisoformat(dispatch_date)).days)


def reconcile_deposits(ledger):
    """Summarize net balance and identify likely duplicate refunds per asset/RMA."""
    net = defaultdict(float)
    refund_seen = set()
    duplicate_ids = []
    for row in ledger:
        asset_id, rma_id = row.get("asset_id", ""), row.get("rma_id", "")
        amount = float(row.get("amount", 0) or 0)
        net[asset_id] += amount
        if row.get("entry_type") == "DEPOSIT_REFUND":
            key = (asset_id, rma_id)
            if key in refund_seen:
                duplicate_ids.append(row.get("ledger_entry_id", ""))
            refund_seen.add(key)
    return {"net_balance_by_asset": {k: round(v, 2) for k, v in net.items()},
            "duplicate_refund_entry_ids": sorted(duplicate_ids)}
