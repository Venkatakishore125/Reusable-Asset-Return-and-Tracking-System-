"""Acceptance checks for core challenge requirements (starter-scale data)."""
import csv, json, subprocess, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data' / 'output'
GT = ROOT / 'data' / 'ground_truth' / 'ground_truth.json'

def rows(name):
    with (OUT / f'{name}.csv').open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

class AcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, '-m', 'src.main', '--starter', '--seed', '20261022'], cwd=ROOT, check=True, capture_output=True, text=True)

    def test_deterministic_primary_ids(self):
        for table, key in [('ReusableAsset','asset_id'), ('Shipment','shipment_id'), ('CustodyEvent','custody_event_id'), ('ReturnAuthorization','rma_id'), ('Inspection','inspection_id'), ('Repair','repair_id'), ('DepositLedger','ledger_entry_id')]:
            values = [r[key] for r in rows(table)]
            self.assertEqual(len(values), len(set(values)), f'duplicate IDs in {table}')
        self.assertTrue(all(r['asset_id'].startswith('ASSET-') for r in rows('ReusableAsset')))
        self.assertTrue(all(r['shipment_id'].startswith('SHP-2026-') for r in rows('Shipment')))

    def test_foreign_keys_for_core_event_tables(self):
        asset_ids = {r['asset_id'] for r in rows('ReusableAsset')}
        ship_ids = {r['shipment_id'] for r in rows('Shipment')}
        for r in rows('CustodyEvent'):
            self.assertIn(r['asset_id'], asset_ids)
            self.assertIn(r['shipment_id'], ship_ids)
        for r in rows('ReturnAuthorization'):
            self.assertIn(r['asset_id'], asset_ids)
            self.assertIn(r['shipment_id'], ship_ids)

    def test_all_required_anomaly_labels_are_separate(self):
        labels = {r['issue_type'] for r in json.loads(GT.read_text(encoding='utf-8'))}
        required = {'SIMULTANEOUS_LOCATION', 'RETURN_BEFORE_DISPATCH', 'DUPLICATE_REFUND', 'REPAIR_WITHOUT_INSPECTION', 'MISSING_ACTOR'}
        self.assertTrue(required.issubset(labels), f'missing labels: {required-labels}')

    def test_manifest_has_reproducibility_hashes(self):
        manifest = json.loads((OUT / 'source_manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['seed'], 20261022)
        self.assertIn('ReusableAsset', manifest['tables'])
        self.assertEqual(len(manifest['tables']['ReusableAsset']['sha256']), 64)

if __name__ == '__main__':
    unittest.main()

class BusinessRuleUnitTests(unittest.TestCase):
    def test_outstanding_days_and_closed_return(self):
        from src.business_rules import calculate_outstanding_days
        self.assertEqual(calculate_outstanding_days('2026-10-01', '', '2026-10-11'), 10)
        self.assertEqual(calculate_outstanding_days('2026-10-01', '2026-10-05', '2026-10-11'), 0)

    def test_deposit_reconciliation_flags_duplicate_refund(self):
        from src.business_rules import reconcile_deposits
        rows = [
            {'asset_id':'ASSET-1','rma_id':'RMA-1','entry_type':'DEPOSIT_CHARGE','amount':'25','ledger_entry_id':'L1'},
            {'asset_id':'ASSET-1','rma_id':'RMA-1','entry_type':'DEPOSIT_REFUND','amount':'-25','ledger_entry_id':'L2'},
            {'asset_id':'ASSET-1','rma_id':'RMA-1','entry_type':'DEPOSIT_REFUND','amount':'-25','ledger_entry_id':'L3'},
        ]
        result = reconcile_deposits(rows)
        self.assertEqual(result['net_balance_by_asset']['ASSET-1'], -25.0)
        self.assertEqual(result['duplicate_refund_entry_ids'], ['L3'])

    def test_replay_rejects_missing_actor_and_keeps_history(self):
        from src.business_rules import reconstruct_locations
        assets = [{'asset_id':'ASSET-1','current_location_id':'LOC-001'}]
        shipments = [{'shipment_id':'SHP-1','origin_location_id':'LOC-001','destination_location_id':'LOC-002','dispatch_date':'2026-10-01'}]
        events = [
            {'custody_event_id':'C1','asset_id':'ASSET-1','shipment_id':'SHP-1','event_type':'DISPATCH','event_date':'2026-10-01','from_location_id':'LOC-001','to_location_id':'LOC-002','actor_owner_id':'OWN-1','issue_type':'NONE'},
            {'custody_event_id':'C2','asset_id':'ASSET-1','shipment_id':'SHP-1','event_type':'TRANSFER','event_date':'2026-10-02','from_location_id':'LOC-002','to_location_id':'LOC-003','actor_owner_id':'','issue_type':'MISSING_ACTOR'},
        ]
        result = reconstruct_locations(assets, events, shipments)
        self.assertEqual(result['locations']['ASSET-1'], 'LOC-002')
        self.assertIn('C2', result['rejected_event_ids'])
