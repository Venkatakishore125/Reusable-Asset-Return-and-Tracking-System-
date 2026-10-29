import csv, subprocess, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class ProjectSmokeTests(unittest.TestCase):
    def test_starter_generates_expected_core_tables(self):
        subprocess.run([sys.executable,'-m','src.main','--starter'],cwd=ROOT,check=True,capture_output=True,text=True)
        out=ROOT/'data'/'output'
        for name in ['AssetType.csv','ReusableAsset.csv','Shipment.csv','CustodyEvent.csv','ReturnAuthorization.csv','Inspection.csv','Repair.csv','DepositLedger.csv','AssetSnapshot.csv']:
            self.assertTrue((out/name).exists(),name)
        with (out/'ReusableAsset.csv').open(newline='',encoding='utf-8') as f: self.assertEqual(len(list(csv.DictReader(f))),100)
        with (out/'Shipment.csv').open(newline='',encoding='utf-8') as f: self.assertEqual(len(list(csv.DictReader(f))),50)
    def test_ground_truth_is_separate(self):
        subprocess.run([sys.executable,'-m','src.main','--starter'],cwd=ROOT,check=True,capture_output=True,text=True)
        self.assertTrue((ROOT/'data'/'ground_truth'/'ground_truth.json').exists())
if __name__=='__main__': unittest.main()
