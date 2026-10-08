import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import create_app


class Api(unittest.TestCase):
    def setUp(self):
        self.c = create_app({"DATABASE_URL": "sqlite:///:memory:", "ANTHROPIC_API_KEY": "", "TESTING": True}).test_client()

    def test_flow(self):
        sample = self.c.get("/api/sample").get_json()
        items = self.c.post("/api/listings", json={"listings": sample}).get_json()
        self.assertEqual(len(items), 5)
        bad = self.c.post(f"/api/listings/{items[1]['id']}/review").get_json()
        self.assertTrue(bad["review"]["findings"]); self.assertTrue(any(not v["ok"] for v in bad["review"]["validation"]))
        revs = {r["field"]: r for r in bad["revisions"]}
        v = self.c.post(f"/api/revisions/{revs['title']['id']}", json={"action": "approve"}).get_json()
        self.assertEqual({r["field"]: r for r in v["revisions"]}["title"]["status"], "approved")
        v = self.c.post(f"/api/revisions/{revs['title']['id']}", json={"action": "edit", "text": "Phone Case"}).get_json()
        t = {r["field"]: r for r in v["revisions"]}["title"]
        self.assertEqual((t["status"], t["final"]), ("edited", "Phone Case"))
        self.c.post(f"/api/revisions/{revs['description']['id']}", json={"action": "reject"})
        acts = [h["action"] for h in self.c.get(f"/api/history?listing_id={items[1]['id']}").get_json()]
        for a in ("added", "approved", "edited", "rejected"): self.assertIn(a, acts)
        dup = self.c.post(f"/api/listings/{items[3]['id']}/review").get_json()
        self.assertFalse(next(x for x in dup["review"]["validation"] if x["label"] == "Duplicate check")["ok"])

    def test_bad_input(self):
        self.assertEqual(self.c.post("/api/listings", json={"listings": []}).status_code, 400)
        self.assertEqual(self.c.post("/api/revisions/999", json={"action": "approve"}).status_code, 404)


if __name__ == "__main__": unittest.main()
