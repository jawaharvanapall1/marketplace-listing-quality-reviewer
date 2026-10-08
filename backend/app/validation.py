"""Deterministic validation. No AI involved; every rule is reproducible."""
import re
from .config import CATEGORIES

PRICE = re.compile(r"^\d{1,7}(\.\d{1,2})?$")
tok = lambda s: re.findall(r"[a-z0-9]+", str(s or "").lower())


def find_duplicate(d, others):
    seller, title = " ".join(tok(d.get("seller"))), tok(d.get("title"))
    tset = set(title)
    for o in others:
        if " ".join(tok(o.get("seller"))) != seller:
            continue
        ot = tok(o.get("title"))
        if ot == title:
            return o
        u = set(ot)
        union = tset | u
        if union and len(tset & u) / len(union) >= 0.8:
            return o
    return None


def validate(d, others=()):
    out = []
    add = lambda ok, label, msg: out.append({"ok": bool(ok), "label": label, "msg": msg})
    miss = [k for k in ("title", "description", "category", "price", "seller") if not str(d.get(k) or "").strip()]
    add(not miss, "Required fields", "Missing: " + ", ".join(miss) if miss else "All present")
    p = str(d.get("price") or "").strip()
    p_ok = bool(PRICE.match(p)) and float(p) > 0
    add(p_ok, "Price format", p if p_ok else f'Need a positive number, max 2 decimals, no symbols or commas (got "{p}")')
    tl = len(str(d.get("title") or "").strip())
    add(10 <= tl <= 80, "Title length", f"{tl} chars (allowed 10-80)")
    dl = len(str(d.get("description") or "").strip())
    add(50 <= dl <= 1000, "Description length", f"{dl} chars (allowed 50-1000)")
    c = d.get("category")
    add(c in CATEGORIES, "Supported category", c if c in CATEGORIES else f'"{c or ""}" is not supported')
    pairs = [x for x in re.split(r"\n|;", str(d.get("attributes") or "")) if re.search(r"\S+\s*:\s*\S+", x)]
    add(pairs, "Attributes", f"{len(pairs)} key: value pair(s)")
    tags = [t for t in str(d.get("tags") or "").split(",") if t.strip()]
    add(len(tags) <= 10, "Tag count", f"{len(tags)} (max 10)")
    dup = find_duplicate(d, others)
    add(not dup, "Duplicate check", f'Similar to "{dup["title"]}" (listing #{dup["id"]})' if dup else "No duplicates found")
    return out
