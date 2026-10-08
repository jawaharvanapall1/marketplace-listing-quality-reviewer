import { useState } from "react";

const EMPTY = { title: "", description: "", category: "", price: "", seller: "", attributes: "", tags: "" };

export default function ListingForm({ categories, onAdd, onSample, onBatch }) {
  const [f, setF] = useState({ ...EMPTY, category: "" });
  const [batch, setBatch] = useState("");
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  const submit = async () => {
    if (!f.title.trim() && !f.description.trim()) return;
    await onAdd([{ ...f, category: f.category || categories[0] }]);
    setF({ ...EMPTY });
  };
  return (
    <div className="card">
      <h2>Add listing</h2>
      <div className="g">
        <div><label>Title</label><input value={f.title} onChange={set("title")} /></div>
        <div><label>Category</label>
          <select value={f.category || categories[0] || ""} onChange={set("category")}>{categories.map((c) => <option key={c}>{c}</option>)}</select></div>
        <div><label>Price</label><input value={f.price} onChange={set("price")} placeholder="19.99" /></div>
        <div><label>Seller</label><input value={f.seller} onChange={set("seller")} /></div>
      </div>
      <label>Description</label><textarea value={f.description} onChange={set("description")} />
      <div className="g">
        <div><label>Attributes (Key: Value per line)</label><textarea value={f.attributes} onChange={set("attributes")} /></div>
        <div><label>Tags (comma separated, optional)</label><input value={f.tags} onChange={set("tags")} /></div>
      </div>
      <div className="row"><button className="p" onClick={submit}>Add to queue</button><button onClick={onSample}>Load sample batch</button></div>
      <details><summary>Paste a batch (JSON array)</summary>
        <textarea value={batch} onChange={(e) => setBatch(e.target.value)} placeholder='[{"title":"...","description":"...","category":"...","price":"9.99","attributes":"Brand: X","seller":"...","tags":""}]' />
        <div className="row"><button onClick={async () => { if (await onBatch(batch)) setBatch(""); }}>Import batch</button></div>
      </details>
    </div>
  );
}
