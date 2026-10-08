"""AI policy review: LLM sees the listing + ONLY retrieved sections; uncited findings are discarded."""
import json, re
import requests
from .config import REVISABLE, SEVERITIES

KINDS = "unclear|misleading|prohibited|incomplete|unverifiable"


def build_prompt(listing, chunks):
    pol = "\n".join(f"{c['id']} | {c['title']}: {c['text']}" for c in chunks)
    return f"""You review marketplace listings against policy. Use ONLY these policy sections as citations:
{pol}

LISTING (JSON):
{json.dumps(listing, ensure_ascii=False)}

Find unclear, misleading, prohibited, incomplete or unverifiable content. Every finding MUST cite one policy id from the list above.
severity: {'|'.join(SEVERITIES)}. kind: {KINDS}. field: title|description|category|price|attributes|seller|tags.
Put assumptions you had to make, or claims that cannot be verified from the listing, in "assumption".
Give improved wording only for fields that need it; preserve facts and never invent specs, prices or brands.
Respond with ONLY JSON: {{"findings":[{{"field":"","severity":"","kind":"","issue":"","policy":"","assumption":""}}],"revisions":{{"title":"","description":"","attributes":"","tags":""}}}}"""


def call_llm(listing, chunks, api_key, model):
    r = requests.post("https://api.anthropic.com/v1/messages", timeout=60,
                      headers={
                          "x-api-key": api_key,
                          "anthropic-version": "2023-06-01",
                          "content-type": "application/json"},
                      json={"model": model, "max_tokens": 2000, "messages": [{"role": "user", "content": build_prompt(listing, chunks)}]})
    r.raise_for_status()
    text = "".join(b.get("text", "") for b in r.json()["content"] if b.get("type") == "text")
    return json.loads(re.sub(r"```json|```", "", text).strip())


PAT = [
    (r"\b(best|#1|number one|guaranteed|100%|cheapest|perfect|miracle|amazing)\b", "P3", "major", "unverifiable", "Absolute or superlative claim that cannot be verified."),
    (r"\b(cures?|treats?|heals?|anti-?cancer|fda approved|arthritis)\b", "P5", "critical", "prohibited", "Health claim without documentation."),
    (r"\b(replica|counterfeit|fake|firearm|ammo|vape)\b", "P4", "critical", "prohibited", "Possibly prohibited item."),
    (r"(\b\d{10}\b|\+?\d[\d\s-]{9,}|@\w+\.\w+|whatsapp)", "P7", "major", "prohibited", "Off-platform contact details."),
    (r"\b(act now|limited time|hurry|last chance)\b", "B4", "minor", "misleading", "Pressure language."),
]


def _caps(s):
    letters = re.sub(r"[^A-Za-z]", "", str(s or ""))
    return len(letters) > 5 and sum(c.isupper() for c in letters) / len(letters) > 0.6


def _clean(s):
    s = re.sub(r"\b(act now|limited time( offer)?|hurry|last chance|100% guaranteed|guaranteed|best ever|cheapest|miracle)\b[!.,\s-]*", "", str(s or ""), flags=re.I)
    s = re.sub(r"\s{2,}", " ", re.sub(r"!+", ".", s)).strip()
    return s.lower().capitalize() if _caps(s) else s


def offline(d):
    findings = []
    for field in ("title", "description"):
        for pat, pid, sev, kind, msg in PAT:
            m = re.search(pat, str(d.get(field) or ""), re.I)
            if m:
                findings.append({"field": field, "severity": sev, "kind": kind, "policy": pid, "issue": f'{msg} ("{m.group(0)}")'})
    if _caps(d.get("title")):
        findings.append({"field": "title", "severity": "minor", "kind": "unclear", "policy": "P2", "issue": "Title is mostly capitals."})
    if "!!" in str(d.get("title") or ""):
        findings.append({"field": "title", "severity": "minor", "kind": "unclear", "policy": "P2", "issue": "Repeated punctuation in title."})
    if not re.search(r"\b(new|used|refurbished)\b", str(d.get("description") or ""), re.I) and d.get("category") not in ("Home Services", "Professional Services"):
        findings.append({"field": "description", "severity": "minor", "kind": "incomplete", "policy": "P8", "issue": "Condition (new/used/refurbished) not stated."})
    revs = {}
    for f in ("title", "description"):
        c = _clean(d.get(f))
        if c and c != d.get(f):
            revs[f] = c
    return {"findings": findings, "revisions": revs}


def run_review(listing, chunks, api_key="", model=""):
    raw, mode, note = None, "ai", ""
    if api_key:
        try:
            raw = call_llm(listing, chunks, api_key, model)
        except Exception as e:  # network, auth, bad JSON -> degrade gracefully
            note = f"LLM call failed ({type(e).__name__}: {e}); used offline rules."
    else:
        note = "No ANTHROPIC_API_KEY set; used offline rules."
    if raw is None:
        raw, mode = offline(listing), "offline"
    allowed, dropped, findings = {c["id"] for c in chunks}, 0, []
    for f in raw.get("findings") or []:
        if isinstance(f, dict) and f.get("issue") and f.get("policy") in allowed:   # citation enforcement
            f["severity"] = f.get("severity") if f.get("severity") in SEVERITIES else "info"
            findings.append(f)
        else:
            dropped += 1
    findings.sort(key=lambda f: SEVERITIES.index(f["severity"]))
    revisions = {}
    for f in REVISABLE:
        t = str((raw.get("revisions") or {}).get(f) or "").strip()
        if t and t != str(listing.get(f) or "").strip():
            revisions[f] = t
    return {"mode": mode, "note": note, "dropped": dropped, "findings": findings, "revisions": revisions}
