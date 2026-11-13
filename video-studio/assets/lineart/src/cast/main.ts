// Cast line-up: everyone walks in, stops on a mark, greets in turn; name cards fade in.
//   ?debug           deterministic stepping for capture
//   ?v               9:16 layout (3 columns × 4 rows) instead of 16:9 (6 × 2)
import { el, pen, inkDefs, run, f } from '../lib/ink.ts';
import { pointerWind, ease, clamp } from '../lib/motion.ts';
import { createCharacter, type Gesture } from './rig.ts';
import { ROSTER } from './roster.ts';

const q = new URLSearchParams(location.search);
const vertical = q.has('v');
const W = vertical ? 1080 : 1920, H = vertical ? 1920 : 1080;
const COLS = vertical ? 3 : 6;
const ROWS = Math.ceil(ROSTER.length / COLS);
const SCALE = vertical ? 2.3 : 2.85;
const rowH = (H - 40) / ROWS;

const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': 'Dàn nhân vật nét mực' });
svg.style.setProperty('--paper', '#fdfcf8');
document.querySelector('#stage')!.appendChild(svg);
const { filter } = inkDefs(svg, 'c');
const scene = el('g', { filter }, svg);
const labels = el('g', {}, svg);

const ORDER = ['bac-si-minh', 'dieu-duong-lan', 'can-bo-thu', 'co-giao-hoa', 'anh-duc', 'anh-tuan',
  'chi-nam', 'anh-khoa', 'ong-bay', 'ba-sau', 'be-an', 'be-mai'];
const GESTURE: Record<string, Gesture> = {
  'bac-si-minh': 'present', 'dieu-duong-lan': 'nod', 'can-bo-thu': 'point', 'co-giao-hoa': 'bow',
  'anh-duc': 'nod', 'anh-tuan': 'wave', 'chi-nam': 'wave', 'anh-khoa': 'wave',
  'ong-bay': 'nod', 'ba-sau': 'bow', 'be-an': 'wave', 'be-mai': 'wave',
};

const cast = ORDER.map((id, i) => {
  const spec = ROSTER.find((r) => r.id === id)!;
  const col = i % COLS, row = Math.floor(i / COLS);
  const slotX = (W / COLS) * (col + 0.5) - 10;
  const ground = 40 + rowH * (row + 1) - (vertical ? 110 : 125);
  // ground line and a soft shadow under the feet
  pen(scene, 0.9).setAttribute('d', `M${f(slotX - W / COLS / 2 + 30)} ${f(ground + 1)} L${f(slotX + W / COLS / 2 - 30)} ${f(ground + 1)}`);
  const shadow = el('ellipse', { rx: 26, ry: 4, fill: '#1c1c1c', opacity: 0.07, cy: ground + 2 }, scene);
  const dist = spec.build === 'elder' ? 120 : spec.build === 'child' ? 230 : 260;
  const c = createCharacter(scene, spec, { x: slotX - dist, y: ground, scale: SCALE, phase: i * 0.37 });
  c.walkTo(slotX);
  const lab = el('g', { opacity: 0 }, labels);
  const name = el('text', { x: slotX, y: ground + 46, 'text-anchor': 'middle', 'font-size': vertical ? 30 : 30, 'font-weight': 600 }, lab);
  name.textContent = spec.name;
  const role = el('text', { x: slotX, y: ground + 80, 'text-anchor': 'middle', 'font-size': vertical ? 23 : 22, opacity: 0.7 }, lab);
  role.textContent = spec.role;
  return { c, shadow, lab, i, slotX };
});

const wind = pointerWind(svg, 0.15);
run((t, dt) => {
  const wv = wind.step(t);
  for (const k of cast) {
    k.c.update(t, dt, wv);
    k.shadow.setAttribute('cx', f(k.c.x));
    const due = 4.6 + k.i * 0.55;
    if (t >= due && t - dt < due) k.c.act(GESTURE[k.c.spec.id], k.c.spec.build === 'elder' ? 3 : 2.6);
    k.lab.setAttribute('opacity', f(ease(clamp((t - 3.6 - k.i * 0.12) / 0.8, 0, 1))));
  }
});
