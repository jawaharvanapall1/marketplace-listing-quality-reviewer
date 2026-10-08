import { useCallback, useEffect, useState } from "react";
import { api } from "./api.js";
import ListingForm from "./components/ListingForm.jsx";
import ListingCard from "./components/ListingCard.jsx";
import History from "./components/History.jsx";

export default function App() {
  const [meta, setMeta] = useState({ categories: [] });
  const [listings, setListings] = useState([]);
  const [events, setEvents] = useState([]);
  const [busy, setBusy] = useState(new Set());
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    const [l, h] = await Promise.all([api.listings(), api.history()]);
    setListings(l); setEvents(h);
  }, []);
  const guard = (fn) => async (...a) => { try { setError(""); return await fn(...a); } catch (e) { setError(e.message); return false; } };

  useEffect(() => { guard(async () => { setMeta(await api.meta()); await refresh(); })(); }, [refresh]);

  const add = guard(async (items) => { await api.add(items); await refresh(); return true; });
  const sample = guard(async () => { await api.add(await api.sample()); await refresh(); });
  const batch = guard(async (text) => { await api.add(JSON.parse(text)); await refresh(); return true; });
  const review = guard(async (id) => {
    setBusy((s) => new Set(s).add(id));
    try { await api.review(id); } finally { setBusy((s) => { const n = new Set(s); n.delete(id); return n; }); }
    await refresh();
  });
  const reviewAll = guard(async () => { for (const l of listings) await review(l.id); });
  const decide = guard(async (revId, action, text) => { await api.decide(revId, action, text); await refresh(); });

  return (
    <>
      <h1>Marketplace Listing Quality Reviewer</h1>
      <p className="sub">React → Flask REST API → deterministic validation + AI policy review (RAG) → MySQL. Every decision is logged.</p>
      {error && <div className="card fail">{error}</div>}
      <ListingForm categories={meta.categories} onAdd={add} onSample={sample} onBatch={batch} />
      <div className="row" style={{ margin: "0 0 10px" }}><h2 style={{ margin: 0 }}>Queue</h2><span className="sp" /><button className="p" onClick={reviewAll}>Review all</button></div>
      {listings.length ? listings.map((l) => <ListingCard key={l.id} l={l} busy={busy.has(l.id)} onReview={review} onDecide={decide} />)
        : <div className="card mute">Queue is empty. Add a listing or load the sample batch.</div>}
      <History events={events} />
    </>
  );
}
