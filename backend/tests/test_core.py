import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.validation import validate
from app.rag import PolicyIndex
from app.ai_review import run_review, offline

GOOD = dict(title="Sony WH-1000XM4 Wireless Headphones - Black", description="Used, very good condition. Includes case and cable. Battery about 30 hours.",
            category="Electronics", price="185.00", attributes="Brand: Sony", seller="AudioHub", tags="sony")
res = lambda d, o=(): {v["label"]: v["ok"] for v in validate(d, o)}
IDX = PolicyIndex(os.path.join(os.path.dirname(__file__), "..", "docs"))


class Validation(unittest.TestCase):
    def test_good(self): self.assertTrue(all(res(GOOD).values()))
    def test_price(self):
        for p in ["12,99", "$5", "0", "-3", "1.234", ""]: self.assertFalse(res({**GOOD, "price": p})["Price format"], p)
        self.assertTrue(res({**GOOD, "price": "7.5"})["Price format"])
    def test_required_category_length(self):
        r = res({**GOOD, "seller": "", "category": "Phones", "title": "Hi"})
        self.assertFalse(r["Required fields"]); self.assertFalse(r["Supported category"]); self.assertFalse(r["Title length"])
    def test_duplicates(self):
        o = [{"id": 1, **GOOD}]
        self.assertFalse(res(GOOD, o)["Duplicate check"])
        self.assertFalse(res({**GOOD, "title": GOOD["title"] + "!"}, o)["Duplicate check"])
        self.assertTrue(res({**GOOD, "seller": "Other"}, o)["Duplicate check"])


class Rag(unittest.TestCase):
    def test_chunks_loaded(self): self.assertGreaterEqual(len(IDX.chunks), 16)
    def test_health_query_retrieves_p5(self):
        ids = [c["id"] for c in IDX.retrieve({**GOOD, "description": "cures arthritis and is FDA approved"})]
        self.assertIn("P5", ids); self.assertIn("P1", ids)


class Review(unittest.TestCase):
    def test_citations_enforced(self):
        d = {**GOOD, "title": "BEST EVER CASE!!!", "description": "100% guaranteed. WhatsApp 9876543210"}
        r = run_review(d, IDX.retrieve(d))
        self.assertEqual(r["mode"], "offline"); self.assertTrue(r["findings"])
        allowed = {c["id"] for c in IDX.retrieve(d)}
        for f in r["findings"]: self.assertIn(f["policy"], allowed)
        self.assertIn("title", r["revisions"])
    def test_uncited_dropped(self):
        import app.ai_review as ai
        orig = ai.offline
        ai.offline = lambda d: {"findings": [{"field": "title", "severity": "major", "issue": "x", "policy": "ZZ9"}], "revisions": {}}
        try: r = run_review(GOOD, IDX.retrieve(GOOD))
        finally: ai.offline = orig
        self.assertEqual(r["dropped"], 1); self.assertEqual(r["findings"], [])


if __name__ == "__main__": unittest.main()
