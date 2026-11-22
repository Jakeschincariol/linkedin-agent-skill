import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from growth_agent import app

class GrowthAgentTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.db=Path(self.tmp.name)/"test.db"
        self.patch=patch.object(app,"DB",self.db); self.patch.start()
        app.connect().close()
    def tearDown(self):
        self.patch.stop(); self.tmp.cleanup()
    def test_draft_requires_explicit_approval(self):
        draft_id=app.add_draft("Title","Body")
        with app.connect() as c:
            self.assertEqual(c.execute("SELECT status FROM drafts WHERE id=?",(draft_id,)).fetchone()[0],"draft")
        app.approve_draft(draft_id)
        with app.connect() as c:
            self.assertEqual(c.execute("SELECT status FROM drafts WHERE id=?",(draft_id,)).fetchone()[0],"approved")
    def test_contact_and_touchpoint(self):
        cid=app.add_contact("A Recruiter",category="recruiter")
        app.log_touch(cid,"linkedin","Reviewed public profile")
        with app.connect() as c:
            self.assertEqual(c.execute("SELECT COUNT(*) FROM touchpoints").fetchone()[0],1)
    def test_metrics_csv_upsert(self):
        path=Path(self.tmp.name)/"metrics.csv"
        with path.open("w",newline="") as f:
            w=csv.writer(f); w.writerow(["post_ref","captured_at","impressions","reactions","comments","reposts","clicks"])
            w.writerow(["p1","2026-11-24T12:00:00+05:30",100,5,2,1,3])
        self.assertEqual(app.import_metrics(path),1)
        self.assertEqual(app.report()["metrics"]["impressions"],100)
    def test_negative_metrics_rejected(self):
        path=Path(self.tmp.name)/"bad.csv"
        with path.open("w",newline="") as f:
            w=csv.writer(f); w.writerow(["post_ref","captured_at","impressions","reactions","comments","reposts","clicks"])
            w.writerow(["p1","now",-1,0,0,0,0])
        with self.assertRaises(ValueError): app.import_metrics(path)

if __name__=="__main__": unittest.main()
