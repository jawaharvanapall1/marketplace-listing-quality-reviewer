async function call(method, url, body) {
  const r = await fetch(url, { method, headers: { "content-type": "application/json" }, body: body ? JSON.stringify(body) : undefined });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error || r.statusText);
  return j;
}
export const api = {
  meta: () => call("GET", "/api/meta"),
  sample: () => call("GET", "/api/sample"),
  listings: () => call("GET", "/api/listings"),
  history: () => call("GET", "/api/history"),
  add: (listings) => call("POST", "/api/listings", { listings }),
  review: (id) => call("POST", `/api/listings/${id}/review`),
  decide: (revId, action, text) => call("POST", `/api/revisions/${revId}`, { action, text }),
};
