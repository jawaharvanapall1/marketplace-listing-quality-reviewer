import json, os
from flask import Blueprint, current_app, jsonify, request
from .ai_review import run_review
from .config import CATEGORIES, REVISABLE
from .db import now, dumps, loads
from .validation import validate

api = Blueprint("api", __name__)
FIELDS = ("title", "description", "category", "price", "attributes", "seller", "tags")
db = lambda: current_app.extensions["db"]
policy = lambda: current_app.extensions["policy"]


def clean(d):
    out = {k: ("\n".join(d[k]) if k == "attributes" and isinstance(d.get(k), list) else ", ".join(d[k]) if k == "tags" and isinstance(d.get(k), list) else str(d.get(k) or "")) for k in FIELDS}
    return out


def log(listing_id, action, field=None, before="", after="", review_id=None):
    db().execute("INSERT INTO history_events(listing_id,review_id,field_name,action,before_text,after_text,created_at) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                 (listing_id, review_id, field, action, before or "", after or "", now()))


def view(row):
    """Listing + its latest review + that review's revisions."""
    v = {k: row[k] for k in ("id", *FIELDS)}
    r = db().one("SELECT * FROM reviews WHERE listing_id=%s ORDER BY id DESC LIMIT 1", (row["id"],))
    v["review"], v["revisions"] = None, []
    if r:
        v["review"] = {"id": r["id"], "mode": r["mode"], "note": r["note"], "dropped": r["dropped"], "created_at": r["created_at"],
                       "validation": loads(r["validation"]), "findings": loads(r["findings"]),
                       "retrieved": [c for c in (policy().by_id(i) for i in loads(r["retrieved"])) if c]}
        v["revisions"] = [{"id": x["id"], "field": x["field_name"], "original": x["original"], "suggested": x["suggested"],
                           "final": x["final_text"], "status": x["status"]}
                          for x in db().query("SELECT * FROM revisions WHERE review_id=%s ORDER BY id", (r["id"],))]
    return v


@api.get("/meta")
def meta():
    return jsonify(categories=CATEGORIES, sections=[{k: c[k] for k in ("id", "title", "source")} for c in policy().chunks])


@api.get("/sample")
def sample():
    with open(os.path.join(os.path.dirname(__file__), "..", "data", "sample.json"), encoding="utf8") as f:
        return jsonify(json.load(f))


@api.get("/listings")
def list_listings():
    return jsonify([view(r) for r in db().query("SELECT * FROM listings ORDER BY id")])


@api.post("/listings")
def add_listings():
    items = (request.get_json(silent=True) or {}).get("listings")
    if not isinstance(items, list) or not 1 <= len(items) <= 50:
        return jsonify(error="Provide 1-50 listings in 'listings'"), 400
    out = []
    for d in items:
        c = clean(d if isinstance(d, dict) else {})
        lid = db().execute("INSERT INTO listings(title,description,category,price,attributes,seller,tags,created_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                           (*[c[k] for k in FIELDS], now()))
        log(lid, "added", after="listing added to queue")
        out.append(view(db().one("SELECT * FROM listings WHERE id=%s", (lid,))))
    return jsonify(out), 201


@api.post("/listings/<int:lid>/review")
def review(lid):
    row = db().one("SELECT * FROM listings WHERE id=%s", (lid,))
    if not row:
        return jsonify(error="Not found"), 404
    others = db().query("SELECT id,title,seller FROM listings WHERE id<>%s", (lid,))
    chunks = policy().retrieve(row)
    res = run_review({k: row[k] for k in FIELDS}, chunks, current_app.config["ANTHROPIC_API_KEY"], current_app.config["ANTHROPIC_MODEL"])
    rid = db().execute("INSERT INTO reviews(listing_id,mode,note,dropped,validation,findings,retrieved,created_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                       (lid, res["mode"], res["note"], res["dropped"], dumps(validate(row, others)), dumps(res["findings"]),
                        dumps([c["id"] for c in chunks]), now()))
    for f in REVISABLE:
        if f in res["revisions"]:
            db().execute("INSERT INTO revisions(review_id,listing_id,field_name,original,suggested,final_text,status,updated_at) VALUES(%s,%s,%s,%s,%s,%s,'pending',%s)",
                         (rid, lid, f, row[f] or "", res["revisions"][f], row[f] or "", now()))
    log(lid, f"reviewed ({res['mode']})", after=f"{len(res['findings'])} findings, {len(res['revisions'])} suggested revisions", review_id=rid)
    return jsonify(view(row))


@api.post("/revisions/<int:rid>")
def decide(rid):
    rev = db().one("SELECT * FROM revisions WHERE id=%s", (rid,))
    if not rev:
        return jsonify(error="Not found"), 404
    body = request.get_json(silent=True) or {}
    a, status, final, after = body.get("action"), None, rev["final_text"], rev["suggested"]
    if a == "approve":
        status, final = "approved", rev["suggested"]
    elif a == "reject":
        status, final = "rejected", rev["original"]
    elif a == "reset":
        status, final = "pending", rev["original"]
    elif a == "edit":
        text = str(body.get("text") or "").strip()
        if not text:
            return jsonify(error="Empty text"), 400
        status, final, after = "edited", text, text
    else:
        return jsonify(error="Unknown action"), 400
    db().execute("UPDATE revisions SET status=%s, final_text=%s, updated_at=%s WHERE id=%s", (status, final, now(), rid))
    log(rev["listing_id"], {"approve": "approved", "reject": "rejected", "reset": "reset to pending", "edit": "edited"}[a],
        rev["field_name"], rev["original"] if a != "edit" else rev["final_text"], after, rev["review_id"])
    return jsonify(view(db().one("SELECT * FROM listings WHERE id=%s", (rev["listing_id"],))))


@api.get("/history")
def history():
    lid = request.args.get("listing_id", type=int)
    sql = "SELECT h.*, l.title FROM history_events h JOIN listings l ON l.id=h.listing_id" + (" WHERE h.listing_id=%s" if lid else "") + " ORDER BY h.id DESC"
    return jsonify(db().query(sql, (lid,) if lid else ()))
