export default function Diff({ segs }) {
  return segs.map((g, i) => g.t === "del" ? <del key={i}>{g.s}</del> : g.t === "ins" ? <ins key={i}>{g.s}</ins> : <span key={i}>{g.s}</span>);
}
