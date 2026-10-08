// Word-level LCS diff -> two segment lists: left (original, with deletions) and right (revised, with insertions).
export function diff(a = "", b = "") {
  const x = a.split(/(\s+)/), y = b.split(/(\s+)/), n = x.length, m = y.length;
  const L = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0));
  for (let i = n - 1; i >= 0; i--) for (let j = m - 1; j >= 0; j--)
    L[i][j] = x[i] === y[j] ? L[i + 1][j + 1] + 1 : Math.max(L[i + 1][j], L[i][j + 1]);
  const left = [], right = [];
  let i = 0, j = 0;
  while (i < n && j < m) {
    if (x[i] === y[j]) { left.push({ t: "same", s: x[i] }); right.push({ t: "same", s: y[j] }); i++; j++; }
    else if (L[i + 1][j] >= L[i][j + 1]) left.push({ t: "del", s: x[i++] });
    else right.push({ t: "ins", s: y[j++] });
  }
  while (i < n) left.push({ t: "del", s: x[i++] });
  while (j < m) right.push({ t: "ins", s: y[j++] });
  return { left, right };
}
