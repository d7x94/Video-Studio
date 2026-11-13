// svg.ts: cong cu ve chung cho nhan vat chibi (net nau dam, to mau phang, vien sticker trang).
export const NS = 'http://www.w3.org/2000/svg';
export const OUT = '#4a2c25';
export const W = 5;
export type Attrs = Record<string, string | number>;

export function el<K extends keyof SVGElementTagNameMap>(tag: K, attrs: Attrs = {}, parent?: Element | null): SVGElementTagNameMap[K] {
  const n = document.createElementNS(NS, tag);
  for (const k in attrs) n.setAttribute(k, String(attrs[k]));
  if (parent) parent.appendChild(n);
  return n;
}
export const g = (parent: Element, attrs: Attrs = {}) => el('g', attrs, parent);

// Vien sticker: nhan vat duoc dung hai lan. Lan dau (UNDER > 0) moi hinh thanh mang trang
// net day them 2 x UNDER phia sau; lan sau la hinh that. Re hon nhieu so voi bo loc feMorphology.
let UNDER = 0;
export const setUnder = (r: number) => { UNDER = r; };
export const under = () => UNDER > 0;
const STICKER = '#ffffff';

/** Mang to mau phang co vien nau. */
export const fill = (parent: Element, d: string, colour: string, w = W) =>
  el('path', { d, fill: UNDER ? STICKER : colour, stroke: UNDER ? STICKER : OUT, 'stroke-width': w + 2 * UNDER, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' }, parent);
/** Net vien khong to. */
export const line = (parent: Element, d: string, w = W * 0.7, colour = OUT) =>
  el('path', { d, fill: 'none', stroke: UNDER ? STICKER : colour, 'stroke-width': w + 2 * UNDER, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' }, parent);
/** Mang to khong vien (bong, ma hong). */
export const flat = (parent: Element, d: string, colour: string, opacity = 1) =>
  el('path', { d, fill: UNDER ? STICKER : colour, opacity: UNDER ? 1 : opacity }, parent);

export const f = (n: number) => (Math.abs(n) < 1e-4 ? '0' : n.toFixed(2));

/** Lam toi mot mau hex theo he so k (0..1). */
export function shade(hex: string, k = 0.82): string {
  const h = hex.replace('#', '');
  const v = h.length === 3 ? h.split('').map((c) => parseInt(c + c, 16)) : [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16));
  return '#' + v.map((c) => Math.round(Math.max(0, Math.min(255, c * k))).toString(16).padStart(2, '0')).join('');
}

export const clamp = (x: number, a = 0, b = 1) => (x < a ? a : x > b ? b : x);
export const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
export const ease = (x: number) => { x = clamp(x); return x * x * (3 - 2 * x); };

/** So gia ngau nhien tat dinh tu mot chuoi (dung cho nhip chop mat). */
export function hash(s: string): number {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
  return ((h >>> 0) % 10000) / 10000;
}
