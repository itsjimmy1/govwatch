// Minimal SVG chart helpers. No dependencies.
// ponytail: hand-rolled SVG beats a 90KB chart lib for two chart types.
const NS = 'http://www.w3.org/2000/svg';
const el = (n, a = {}) => {
  const e = document.createElementNS(NS, n);
  for (const [k, v] of Object.entries(a)) e.setAttribute(k, v);
  return e;
};
const fmt = n => n.toLocaleString('en-AU');

// Nice round upper bound so the y-axis reads cleanly.
function niceMax(v) {
  if (v <= 0) return 1;
  const mag = Math.pow(10, Math.floor(Math.log10(v)));
  for (const s of [1, 1.5, 2, 2.5, 3, 4, 5, 7.5, 10]) {
    if (v <= s * mag) return s * mag;
  }
  return 10 * mag;
}

/** Vertical bars. rows: [{x, y, fill?, title?}] */
export function bars(rows, { w = 1080, h = 300, pad = 40, ticks = 4, xEvery = 10 } = {}) {
  const svg = el('svg', { viewBox: `0 0 ${w} ${h}`, role: 'img' });
  const L = 52, B = 24, top = 10;
  const max = niceMax(Math.max(...rows.map(r => r.y)));
  const iw = w - L - 12, ih = h - B - top;
  const bw = iw / rows.length;

  for (let i = 0; i <= ticks; i++) {
    const v = (max / ticks) * i, y = top + ih - (v / max) * ih;
    svg.append(el('line', { class: 'grid', x1: L, x2: w - 12, y1: y, y2: y }));
    const t = el('text', { class: 'axis', x: L - 8, y: y + 4, 'text-anchor': 'end' });
    t.textContent = fmt(Math.round(v));
    svg.append(t);
  }
  rows.forEach((r, i) => {
    const bh = Math.max((r.y / max) * ih, r.y > 0 ? 1 : 0);
    const b = el('rect', {
      x: (L + i * bw + bw * 0.12).toFixed(1), y: (top + ih - bh).toFixed(1),
      width: Math.max(bw * 0.76, 0.8).toFixed(1), height: bh.toFixed(1),
      fill: r.fill || 'var(--accent)', rx: Math.min(1.5, bw / 4),
    });
    const ttl = el('title');
    ttl.textContent = r.title || `${r.x}: ${fmt(r.y)}`;
    b.append(ttl);
    svg.append(b);
    if (Number(r.x) % xEvery === 0) {
      const t = el('text', {
        class: 'axis', x: (L + i * bw + bw / 2).toFixed(1), y: h - 6,
        'text-anchor': 'middle',
      });
      t.textContent = r.label ?? r.x;
      svg.append(t);
    }
  });
  return svg;
}

/** Step line, for running counts. rows: [{x, y}] sorted by x. */
export function stepline(rows, { w = 1080, h = 260, ticks = 4, label = '' } = {}) {
  const svg = el('svg', { viewBox: `0 0 ${w} ${h}`, role: 'img' });
  const L = 52, B = 24, top = 10;
  const xs = rows.map(r => r.x), max = niceMax(Math.max(...rows.map(r => r.y)));
  const x0 = Math.min(...xs), x1 = Math.max(...xs);
  const iw = w - L - 12, ih = h - B - top;
  const px = x => L + ((x - x0) / (x1 - x0 || 1)) * iw;
  const py = y => top + ih - (y / max) * ih;

  for (let i = 0; i <= ticks; i++) {
    const v = (max / ticks) * i, y = py(v);
    svg.append(el('line', { class: 'grid', x1: L, x2: w - 12, y1: y, y2: y }));
    const t = el('text', { class: 'axis', x: L - 8, y: y + 4, 'text-anchor': 'end' });
    t.textContent = fmt(Math.round(v));
    svg.append(t);
  }
  let d = '';
  rows.forEach((r, i) => {
    d += i === 0 ? `M${px(r.x)},${py(r.y)}` : `L${px(r.x)},${py(rows[i - 1].y)}L${px(r.x)},${py(r.y)}`;
  });
  d += `L${px(x1)},${py(rows[rows.length - 1].y)}`;
  svg.append(el('path', { d, fill: 'none', stroke: 'var(--accent)', 'stroke-width': 2 }));

  for (let x = Math.ceil(x0 / 20) * 20; x <= x1; x += 20) {
    const t = el('text', { class: 'axis', x: px(x), y: h - 6, 'text-anchor': 'middle' });
    t.textContent = x;
    svg.append(t);
  }
  if (label) {
    const t = el('text', { class: 'axis-label', x: L + 6, y: top + 14 });
    t.textContent = label;
    svg.append(t);
  }
  return svg;
}

export { fmt };
