export default function History({ events }) {
  return (
    <div className="card">
      <div className="row" style={{ margin: 0 }}><h2 style={{ margin: 0 }}>Review + approval history</h2><span className="sp" />
        <a href="/api/history" target="_blank" rel="noreferrer">Raw JSON</a></div>
      {events.length ? events.slice(0, 200).map((e) => (
        <div className="h" key={e.id}>
          <span className="mute">{new Date(e.created_at).toLocaleString()}</span> · <b>{e.title}</b> · {e.field_name || "-"} · {e.action}
          {e.after_text && <div className="mute">→ {e.after_text.slice(0, 140)}</div>}
        </div>)) : <div className="mute">No activity yet.</div>}
    </div>
  );
}
