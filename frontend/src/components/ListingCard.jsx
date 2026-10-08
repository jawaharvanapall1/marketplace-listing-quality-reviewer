import RevisionCard from "./RevisionCard.jsx";
import Diff from "./Diff.jsx";
import { diff } from "../diff.js";

export default function ListingCard({ l, busy, onReview, onDecide }) {
  const r = l.review;
  const byId = Object.fromEntries((r?.retrieved || []).map((c) => [c.id, c]));
  return (
    <div className="card">
      <div className="row" style={{ margin: 0 }}>
        <div><b>{l.title || "(no title)"}</b>
          <div className="mute">{l.seller || "no seller"} · {l.category || "no category"} · {l.price || "no price"}</div></div>
        <span className="sp" />
        <button className="p" disabled={busy} onClick={() => onReview(l.id)}>{busy ? "Reviewing…" : r ? "Re-review" : "Review"}</button>
      </div>
      {r && (<>
        <h3>Deterministic validation</h3>
        <div className="scroll">{r.validation.map((v) => (
          <div className="h" key={v.label}><span className={`b ${v.ok ? "pass" : "fail"}`}>{v.ok ? "pass" : "fail"}</span><b>{v.label}</b> — {v.msg}</div>))}</div>
        <h3>Findings ({r.findings.length}) <span className="mute">· {r.mode === "ai" ? "AI review grounded in retrieved sections (RAG)" : "offline pattern rules"}</span></h3>
        {r.note && <div className="mute">{r.note}</div>}
        {r.findings.length ? r.findings.map((f, i) => (
          <div className={`f ${f.severity}`} key={i}>
            <span className={`b ${f.severity}`}>{f.severity}</span><span className="b info">{f.kind}</span><span className="mute">{f.field}</span><br />
            <span className="t">{f.issue}</span>
            <div className="cite">Cited: {f.policy} — {byId[f.policy]?.title}: {byId[f.policy]?.text}</div>
            {f.assumption && <div className="cite">Assumption / unverifiable: {f.assumption}</div>}
          </div>)) : <div className="mute">No policy findings.</div>}
        {r.dropped > 0 && <div className="mute">{r.dropped} model finding(s) discarded for lacking a valid policy citation.</div>}
        <details><summary>Retrieved guidance ({r.retrieved.map((c) => c.id).join(", ")})</summary>
          {r.retrieved.map((c) => <div className="h" key={c.id}><b>{c.id} {c.title}</b> <span className="mute">({c.source})</span>: {c.text}</div>)}</details>
        <h3>Suggested revisions</h3>
        {l.revisions.length ? l.revisions.map((v) => <RevisionCard key={v.id + v.status + v.final} rev={v} onDecide={onDecide} />)
          : <div className="mute">No revisions suggested.</div>}
        {l.revisions.length > 0 && <details><summary>Original vs final version</summary>
          {l.revisions.map((v) => { const { left, right } = diff(v.original, v.final); return (
            <div className="cmp" style={{ margin: "6px 0" }} key={v.id}>
              <div><div className="mute">{v.field} · original</div><div className="box"><Diff segs={left} /></div></div>
              <div><div className="mute">{v.field} · final</div><div className="box"><Diff segs={right} /></div></div></div>); })}</details>}
      </>)}
    </div>
  );
}
