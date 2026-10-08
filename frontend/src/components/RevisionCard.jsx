import { useState } from "react";
import Diff from "./Diff.jsx";
import { diff } from "../diff.js";

export default function RevisionCard({ rev, onDecide }) {
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState(rev.suggested);
  const { left, right } = diff(rev.original, rev.suggested);
  const cls = rev.status === "approved" || rev.status === "edited" ? "pass" : rev.status === "rejected" ? "fail" : "info";
  return (
    <div style={{ marginBottom: 12 }}>
      <b>{rev.field}</b> <span className={`b ${cls}`}>{rev.status}</span>
      <div className="cmp">
        <div><div className="mute">Original</div><div className="box"><Diff segs={left} /></div></div>
        <div><div className="mute">{rev.status === "edited" ? "Your edit" : "Revised"}</div>
          {editing ? <textarea value={text} onChange={(e) => setText(e.target.value)} />
            : <div className="box">{rev.status === "edited" ? rev.final : <Diff segs={right} />}</div>}</div>
      </div>
      <div className="row">
        {editing ? (<>
          <button className="ok" onClick={async () => { await onDecide(rev.id, "edit", text); setEditing(false); }}>Save edit</button>
          <button onClick={() => setEditing(false)}>Cancel</button></>) : (<>
          <button className="ok" onClick={() => onDecide(rev.id, "approve")}>Approve</button>
          <button onClick={() => { setText(rev.status === "edited" ? rev.final : rev.suggested); setEditing(true); }}>Edit</button>
          <button className="no" onClick={() => onDecide(rev.id, "reject")}>Reject</button>
          {rev.status !== "pending" && <button onClick={() => onDecide(rev.id, "reset")}>Reset</button>}</>)}
      </div>
    </div>
  );
}
