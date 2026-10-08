"""RAG over the Policy/Guide Documents: markdown files chunked by '## <ID> <Title>' headings, ranked with BM25."""
import glob, math, os, re
from collections import Counter

tok = lambda s: re.findall(r"[a-z0-9]+", str(s or "").lower())
ALWAYS = ("P1", "P3", "B1")   # core sections always supplied to the reviewer


class PolicyIndex:
    def __init__(self, docs_dir):
        self.chunks = []
        for path in sorted(glob.glob(os.path.join(docs_dir, "*.md"))):
            src = os.path.basename(path)
            with open(path, encoding="utf8") as fh:
                body = fh.read()
            for m in re.finditer(r"^##\s+(\S+)\s+(.+?)\n(.*?)(?=^##\s|\Z)", body, re.S | re.M):
                self.chunks.append({"id": m.group(1), "title": m.group(2).strip(), "text": m.group(3).strip(), "source": src})
        self._tf = [Counter(tok(c["title"] + " " + c["text"])) for c in self.chunks]
        self._len = [sum(t.values()) for t in self._tf]
        self._avg = (sum(self._len) / len(self._len)) if self._len else 1
        df = Counter(w for t in self._tf for w in t)
        n = len(self.chunks)
        self._idf = {w: math.log(1 + (n - f + 0.5) / (f + 0.5)) for w, f in df.items()}

    def by_id(self, cid):
        return next((c for c in self.chunks if c["id"] == cid), None)

    def retrieve(self, listing, k=6, k1=1.5, b=0.75):
        q = tok(" ".join(str(listing.get(f) or "") for f in ("title", "description", "category", "attributes", "tags")))
        scores = []
        for i, tf in enumerate(self._tf):
            s = sum(self._idf.get(w, 0) * tf[w] * (k1 + 1) / (tf[w] + k1 * (1 - b + b * self._len[i] / self._avg)) for w in set(q) if w in tf)
            scores.append((s, i))
        top = [self.chunks[i] for s, i in sorted(scores, reverse=True)[:k] if s > 0]
        for cid in ALWAYS:
            c = self.by_id(cid)
            if c and c not in top:
                top.append(c)
        return top
