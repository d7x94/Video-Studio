// rig.ts: nhan vat chibi nhin chinh dien, dung kieu cut-out (cac manh SVG ve mot lan,
// moi khung chi doi transform va an hien hinh mat, hinh mieng).
// Dung chung Spec voi dan line-art (assets/lineart/src/cast/roster.ts) de cung mot nguoi
// giu nguyen trang phuc, mau, dao cu o ca hai kieu hinh.
//
// Khong gian hinh: chan o y = 0, truc giua x = 0, y am huong len. Nguoi lon cao khoang 300 don vi
// (tre em khoang 230). Tay "truoc" (tay ranh) la tay ben phai hinh (x duong); tay sau cam do.
// dir = -1 thi lat guong ca nhan vat (do cam tay chuyen sang ben kia).
import type { Spec, Gesture } from '../../lineart/src/cast/rig.ts';
import { el, g, fill, line, flat, f, shade, clamp, lerp, ease, hash, setUnder, under, OUT, W } from './svg.ts';
import { RAISE, drawQueArm, drawQueLegs, drawFlashlight, queArmPoints, drawQueArmAt, queLegPoints, drawQueLegAt, type QueArm, type QueLeg, type Vec } from './que.ts';
import { hasClip, clipLength, sampleClip } from './mocap.ts';

export type Expr = 'neutral' | 'happy' | 'wink' | 'deadpan' | 'surprised' | 'worried';
export type { Gesture };

export interface Look { skin: string; hair: string; blush?: number }
// Mau da va mau toc cho ban chibi (line-art khong to da). Toc bac lay tu hairColor cua Spec.
// Chi them o day, khong doi trang phuc, mau ao, dao cu da khoa trong roster.
export const LOOKS: Record<string, Look> = {
  'bac-si-minh': { skin: '#f3d3bb', hair: '#2b211e' },
  'dieu-duong-lan': { skin: '#f7dcc9', hair: '#2e211d' },
  'can-bo-thu': { skin: '#f7dcc9', hair: '#3a2420' },
  'co-giao-hoa': { skin: '#f8dfcd', hair: '#241a18' },
  'anh-duc': { skin: '#f1d0b6', hair: '#2b211e' },
  'anh-tuan': { skin: '#e2b896', hair: '#2b211e' },
  'chi-nam': { skin: '#e8be9c', hair: '#2b211e' },
  'anh-khoa': { skin: '#efcfb4', hair: '#2e2420' },
  'ong-bay': { skin: '#e9c4a6', hair: '#c9c4ba', blush: 0.45 },
  'ba-sau': { skin: '#efcdb2', hair: '#b8b2a6', blush: 0.5 },
  'be-an': { skin: '#f6d6bf', hair: '#2b211e' },
  'be-mai': { skin: '#f8dccb', hair: '#3a2621' },
};
const DEFAULT_LOOK: Look = { skin: '#f5d6c0', hair: '#352420' };

export type Move = Gesture | 'sweep';
export type Item = 'den-pin';
/** limbs: 'chibi' (tay ong, mac dinh) hoac 'que' (tay chan net que, dau mut cham tron). */
export interface ChibiOptions { x: number; y: number; scale?: number; dir?: 1 | -1; limbs?: 'chibi' | 'que';
  /** Skin theo vai (xem lineart/src/cast/skins.ts), vd 'sep', 'luat-su'. Khong ghi thi mac bo do khoa trong roster. */
  skin?: string;
  /** Khung hien (giay): chi hien khi from <= t < until; dung de doi skin theo canh (xem san khau). */
  from?: number; until?: number }
export interface Chibi {
  readonly spec: Spec;
  readonly root: SVGGElement;
  x: number; y: number; scale: number; dir: 1 | -1;
  /** Di toi hoanh do x (don vi san khau) roi dung; tu quay theo huong di. */
  walkTo(x: number): void;
  /** Chay toi x (nhanh gap khoang 2,3 lan di bo). */
  runTo(x: number): void;
  /** Ngoi xuong (ghe ve san bang C.bench) hoac dung len; doi tu the trong 0,35 giay. */
  sit(on: boolean): void;
  /** Cu chi trong `seconds` giay: wave, point, present, talk, bow, nod. */
  act(gesture: Move, seconds: number): void;
  /** Cam them do vat bang tay truoc (chi kieu que): 'den-pin' co luong sang; null de bo xuong. */
  hold(item: Item | null): void;
  /** Dien mot clip chuyen dong that (chi kieu que; ma clip xem references/nhan-vat-chibi.md muc Dong tac mocap).
   *  seconds: thoi gian dien (mac dinh: het clip; clip lap thi bat buoc). Tra ve so giay se dien. Dang di thi tam dung. */
  play(clip: string, seconds?: number): number;
  /** Quay ve phai (1) hoac trai (-1): lat guong nhanh. */
  face(dir: 1 | -1): void;
  /** Net mat; khong ghi giay thi giu den khi doi. */
  expr(name: Expr, seconds?: number): void;
  /** Nhep mieng theo loi doc trong `seconds` giay ke tu bay gio. */
  say(seconds: number): void;
  update(t: number, dt: number, speech: (t: number) => number | null): void;
}

const SUPPORTED: Record<string, string[]> = {
  top: ['shirt', 'coat', 'aodai', 'baba', 'dress', 'jacket', 'scrubs'],
  bottom: ['trousers', 'wide', 'shorts', 'plain'],
  hair: ['short', 'side', 'bun', 'long', 'ponytail', 'pigtails'],
  hat: ['none', 'nonla', 'cap', 'hardhat', 'officer', 'nurse'],
  extras: ['mask', 'glasses', 'stethoscope', 'redscarf', 'vest', 'lanyard', 'tie'],
  prop: ['none', 'clipboard', 'books', 'briefcase', 'basket', 'backpack', 'cane', 'ganh', 'suitcase'],
  build: ['adult', 'child', 'elder'],
};
function checkSpec(s: Spec) {
  const bad: string[] = [];
  const chk = (k: string, v: string) => { if (!SUPPORTED[k].includes(v)) bad.push(`${k}=${v}`); };
  chk('top', s.top); chk('bottom', s.bottom); chk('hair', s.hair); chk('hat', s.hat ?? 'none');
  chk('prop', s.prop ?? 'none'); chk('build', s.build);
  for (const e of s.extras ?? []) chk('extras', e);
  if (bad.length) throw new Error(`chibi: ${s.id} chua ve ban chibi (${bad.join(', ')})`);
}

// ---------------- hinh tinh ----------------
const SHOULDER_Y = -118, NECK_Y = -134;
const UPPER = 34, FORE = 32;
const BUILD = {
  adult: { body: 1, head: 1, speed: 120 },
  child: { body: 0.7, head: 0.86, speed: 105 },
  elder: { body: 0.97, head: 0.97, speed: 70 },
};

function torsoPath(top: Spec['top']): string {
  switch (top) {
    case 'coat': return 'M-34 -124 Q-50 -120 -52 -100 L-58 -16 Q-30 -12 -3 -16 L3 -16 Q30 -12 58 -16 L52 -100 Q50 -120 34 -124 Z';
    case 'aodai': return 'M-30 -126 Q-48 -120 -50 -100 L-50 -62 Q-49 -54 -42 -50 L-34 -4 Q0 0 34 -4 L42 -50 Q49 -54 50 -62 L50 -100 Q48 -120 30 -126 Z';
    case 'baba': return 'M-34 -124 Q-52 -120 -54 -100 L-60 -40 Q0 -32 60 -40 L54 -100 Q52 -120 34 -124 Z';
    case 'dress': return 'M-30 -124 Q-46 -120 -48 -100 L-68 -30 Q0 -20 68 -30 L48 -100 Q46 -120 30 -124 Z';
    default: return 'M-34 -124 Q-50 -120 -52 -100 L-55 -46 Q0 -38 55 -46 L52 -100 Q50 -120 34 -124 Z';
  }
}

function drawLegs(parent: Element, s: Spec, look: Look) {
  const legs: SVGGElement[] = [];
  const shoe = s.shoeColor ?? '#3b302c';
  const bare = s.top === 'dress' || s.bottom === 'shorts';
  for (const side of [-1, 1]) {
    const lg = g(parent);
    const sd = side;
    if (s.bottom === 'wide') fill(lg, `M${sd * 4} -50 L${sd * 30} -50 L${sd * 34} -10 L${sd * 4} -10 Z`, s.bottomColor);
    else if (bare) {
      fill(lg, `M${sd * 8} -40 L${sd * 22} -40 L${sd * 21} -12 L${sd * 9} -12 Z`, look.skin);
      if (s.bottom === 'shorts') fill(lg, `M${sd * 3} -54 L${sd * 30} -54 L${sd * 28} -32 L${sd * 4} -32 Z`, s.bottomColor);
      fill(lg, `M${sd * 8} -18 L${sd * 22} -18 L${sd * 22} -10 L${sd * 8} -10 Z`, '#fdfdfc', W * 0.7);
    } else fill(lg, `M${sd * 5} -50 L${sd * 27} -50 L${sd * 25} -12 L${sd * 6} -12 Z`, s.bottomColor);
    fill(lg, `M${sd * 2} -2 Q${sd * 2} -16 ${sd * 16} -16 Q${sd * 32} -16 ${sd * 32} -4 Q${sd * 32} 2 ${sd * 16} 2 Q${sd * 2} 2 ${sd * 2} -2 Z`, shoe);
    legs.push(lg);
  }
  return legs;
}

function drawTorso(parent: Element, s: Spec, look: Look, id: string) {
  const t = g(parent);
  const d = torsoPath(s.top);
  const ex = s.extras ?? [];
  fill(t, d, s.topColor);
  if (!under()) {
    const clip = el('clipPath', { id: `${id}-torso` }, t);
    el('path', { d }, clip);
    el('rect', { x: 26, y: -130, width: 50, height: 130, fill: shade(s.topColor, 0.86), 'clip-path': `url(#${id}-torso)` }, t);
  }
  line(t, d, W);
  const thin = W * 0.55;
  switch (s.top) {
    case 'shirt':
      fill(t, 'M-20 -126 L-2 -104 L-6 -128 Z', s.topColor, W * 0.8);
      fill(t, 'M20 -126 L2 -104 L6 -128 Z', s.topColor, W * 0.8);
      line(t, 'M0 -104 L0 -46', thin);
      if (!under() && !ex.includes('tie')) for (const y of [-92, -74, -58]) el('circle', { cx: 0, cy: y, r: 2.6, fill: OUT }, t);
      break;
    case 'jacket':
      fill(t, 'M-24 -128 Q0 -116 24 -128 L22 -114 Q0 -104 -22 -114 Z', shade(s.topColor, 0.9), W * 0.8);
      line(t, 'M0 -110 L0 -46', W * 0.6);
      line(t, 'M-46 -54 Q0 -48 46 -54', W * 0.5);
      line(t, 'M-40 -80 L-24 -76 M40 -80 L24 -76', W * 0.5);
      break;
    case 'coat':
      fill(t, 'M-16 -126 L0 -96 L16 -126 Z', '#b9d3e6', W * 0.7);
      line(t, 'M-22 -126 L0 -86 L22 -126 M0 -86 L0 -16', thin);
      line(t, 'M-46 -52 L-26 -52 L-27 -36 L-45 -36 Z M26 -52 L46 -52 L45 -36 L27 -36 Z', thin);
      line(t, 'M24 -98 L40 -98', thin);
      el('path', { d: 'M28 -104 L28 -96 M33 -105 L33 -96', stroke: '#2d6fb0', 'stroke-width': under() ? 0 : 2.2 }, t);
      break;
    case 'scrubs':
      fill(t, 'M-18 -126 L0 -100 L18 -126 Z', look.skin, W * 0.7);
      line(t, 'M22 -96 L42 -96 L41 -80 L23 -80 Z', thin);
      break;
    case 'aodai':
      fill(t, 'M-14 -132 L14 -132 L14 -122 Q0 -118 -14 -122 Z', s.topColor, W * 0.7);
      line(t, 'M4 -122 Q24 -116 40 -104', thin);
      line(t, 'M-42 -50 L-50 -62 M42 -50 L50 -62', thin);
      break;
    case 'baba':
      line(t, 'M-18 -124 Q0 -110 18 -124', thin);
      line(t, 'M0 -114 L0 -36', thin);
      if (!under()) for (const y of [-100, -84, -68, -52]) el('circle', { cx: 0, cy: y, r: 2.4, fill: OUT }, t);
      line(t, 'M-48 -66 L-24 -66 L-25 -46 L-47 -46 Z M24 -66 L48 -66 L47 -46 L25 -46 Z', thin);
      break;
    case 'dress':
      fill(t, 'M-22 -126 Q-12 -110 0 -116 Q12 -110 22 -126 Q0 -118 -22 -126 Z', '#fdfdfc', W * 0.6);
      line(t, 'M-50 -84 Q0 -76 50 -84', thin);
      fill(t, 'M-6 -86 L6 -86 L6 -76 L-6 -76 Z', shade(s.topColor, 0.8), W * 0.5);
      break;
  }
  if (ex.includes('vest')) {
    const o = '#ef7d2a';
    fill(t, 'M-30 -126 Q-48 -120 -50 -100 L-52 -48 L-12 -46 L-10 -110 Z', o, W * 0.8);
    fill(t, 'M30 -126 Q48 -120 50 -100 L52 -48 L12 -46 L10 -110 Z', o, W * 0.8);
    for (const y of [-84, -64]) {
      fill(t, `M-50 ${y} L-11 ${y} L-11 ${y + 7} L-50 ${y + 7} Z`, '#dfe4e6', W * 0.5);
      fill(t, `M11 ${y} L50 ${y} L50 ${y + 7} L11 ${y + 7} Z`, '#dfe4e6', W * 0.5);
    }
  }
  if (ex.includes('tie')) {
    fill(t, 'M-6 -110 L6 -110 L4 -102 L-4 -102 Z', '#c0392b', W * 0.6);
    fill(t, 'M-4 -102 L4 -102 L9 -66 L0 -56 L-9 -66 Z', '#c0392b', W * 0.6);
  }
  if (ex.includes('redscarf')) {
    fill(t, 'M-24 -126 Q0 -112 24 -126 L6 -104 L-6 -104 Z', '#d6342c', W * 0.7);
    fill(t, 'M-6 -106 L-16 -80 L-4 -84 Z M6 -106 L16 -80 L4 -84 Z', '#d6342c', W * 0.6);
  }
  if (ex.includes('stethoscope')) {
    line(t, 'M-18 -126 Q-30 -104 -18 -86 Q-8 -76 2 -84 M18 -126 Q26 -108 22 -96', W * 0.8, '#3a3f45');
    fill(t, 'M-2 -90 a7 7 0 1 0 14 0 a7 7 0 1 0 -14 0', '#b8c0c6', W * 0.6);
  }
  if (ex.includes('lanyard')) {
    line(t, 'M-14 -126 L16 -88 M16 -126 L18 -88', W * 0.5, '#2d6fb0');
    fill(t, 'M7 -88 L29 -88 L29 -62 L7 -62 Z', '#fdfdfc', W * 0.7);
    flat(t, 'M9.5 -85.5 L26.5 -85.5 L26.5 -79 L9.5 -79 Z', '#2d6fb0');
    line(t, 'M12 -72 L24 -72 M12 -67 L20 -67', 1.6);
  }
  if ((s.prop ?? 'none') === 'backpack') line(t, 'M-30 -124 Q-36 -96 -40 -64 M30 -124 Q36 -96 40 -64', W * 1.6, shade(s.propColor ?? '#3f6ea8', 0.8));
  return t;
}

/** Do vat. where: 'back' sau than (ba lo, don ganh), 'ground' sau chan (vali, cap, gio, gay), 'body' truoc nguc (bia, sach). */
function drawProp(parent: Element, s: Spec, where: 'back' | 'ground' | 'body', que = false) {
  const p = s.prop ?? 'none';
  const col = s.propColor;
  if (where === 'body' && p === 'clipboard') {
    const c = g(parent, { transform: 'rotate(-8 -22 -74)' });
    fill(c, 'M-44 -102 L-2 -102 L-2 -46 L-44 -46 Z', '#b98a5a');
    fill(c, 'M-40 -96 L-6 -96 L-6 -50 L-40 -50 Z', '#fdfdfc', W * 0.6);
    fill(c, 'M-30 -106 L-16 -106 L-16 -98 L-30 -98 Z', '#9aa3ab', W * 0.6);
    line(c, 'M-34 -88 L-12 -88 M-34 -80 L-12 -80 M-34 -72 L-18 -72 M-34 -64 L-14 -64', 1.8, '#8c96a0');
  }
  if (where === 'body' && p === 'books') {
    const c = g(parent, { transform: 'rotate(-6 -22 -74)' });
    fill(c, 'M-46 -100 L-2 -100 L-2 -84 L-46 -84 Z', '#c0392b');
    fill(c, 'M-42 -84 L-4 -84 L-4 -66 L-42 -66 Z', '#e2b93b');
    fill(c, 'M-46 -66 L-2 -66 L-2 -48 L-46 -48 Z', '#3f7f5f');
    line(c, 'M-40 -92 L-10 -92 M-36 -75 L-12 -75 M-40 -57 L-10 -57', 1.8, '#fdfdfc');
  }
  if (where === 'ground' && p === 'suitcase') {
    const c = g(parent);
    const cc = col ?? '#2f5d6b';
    const body = 'M-100 -46 Q-100 -50 -96 -50 L-46 -50 Q-42 -50 -42 -46 L-42 -10 Q-42 -6 -46 -6 L-96 -6 Q-100 -6 -100 -10 Z';
    // tay que cao hon: keo dai can vali toi tay
    const gy = que ? -92 : -58;
    line(c, `M-80 -46 L-80 ${gy} M-62 -46 L-62 ${gy}`, W * 0.8, '#6b7178');
    fill(c, `M-86 ${gy - 4} L-58 ${gy - 4} L-58 ${gy + 4} L-86 ${gy + 4} Z`, '#3b302c', W * 0.7);
    fill(c, body, cc);
    if (!under()) el('rect', { x: -66, y: -48, width: 20, height: 40, fill: shade(cc, 0.82) }, c);
    line(c, body, W);
    line(c, 'M-86 -46 L-86 -10 M-56 -46 L-56 -10', W * 0.45);
    for (const x of [-90, -52]) fill(c, `M${x - 4} -2 a4 4 0 1 0 8 0 a4 4 0 1 0 -8 0`, '#3b302c', W * 0.5);
  }
  if (where === 'ground' && p === 'briefcase') {
    const c = g(parent, que ? { transform: 'translate(3 -32)' } : {});
    const cc = col ?? '#6b4428';
    line(c, 'M-70 -44 Q-70 -52 -62 -52 Q-54 -52 -54 -44', W * 0.9);
    fill(c, 'M-88 -42 L-36 -42 Q-32 -42 -32 -38 L-32 -10 Q-32 -6 -36 -6 L-88 -6 Q-92 -6 -92 -10 L-92 -38 Q-92 -42 -88 -42 Z', cc);
    line(c, 'M-92 -28 L-32 -28', W * 0.5);
    fill(c, 'M-66 -32 L-58 -32 L-58 -24 L-66 -24 Z', '#e2b93b', W * 0.5);
  }
  if (where === 'ground' && p === 'basket') {
    const c = g(parent, que ? { transform: 'translate(3 -28)' } : {});
    const cc = col ?? '#c9a165';
    line(c, 'M-86 -36 Q-62 -78 -38 -36', W * 1.1);
    fill(c, 'M-92 -36 L-32 -36 L-38 -6 Q-62 0 -86 -6 Z', cc);
    line(c, 'M-90 -26 L-34 -26 M-88 -16 L-36 -16 M-72 -36 L-70 -4 M-52 -36 L-52 -4', W * 0.4, shade(cc, 0.7));
    fill(c, 'M-80 -38 Q-70 -50 -58 -40 Q-50 -48 -42 -38 Z', '#5f9a4e', W * 0.6);
  }
  if (where === 'ground' && p === 'cane') {
    const c = g(parent);
    const d = que ? 'M-50 -80 Q-50 -94 -60 -94 Q-70 -94 -70 -82 L-74 0' : 'M-54 -50 Q-54 -60 -64 -60 Q-74 -60 -74 -50 L-76 0';
    line(c, d, W * 1.7, OUT);
    if (!under()) line(c, d, W * 0.8, '#9a6a3c');
  }
  if (where === 'back' && p === 'backpack') {
    const cc = col ?? '#3f6ea8';
    fill(parent, 'M-58 -118 Q-62 -128 -46 -130 L46 -130 Q62 -128 58 -118 L62 -56 Q0 -48 -62 -56 Z', cc);
    fill(parent, 'M-66 -92 L-56 -92 L-56 -64 L-66 -64 Z M56 -92 L66 -92 L66 -64 L56 -64 Z', shade(cc, 0.82), W * 0.7);
  }
  if (where === 'back' && p === 'ganh') {
    const cc = col ?? '#c9a165';
    line(parent, 'M-150 -132 L150 -132', W * 3.2, OUT);
    if (!under()) line(parent, 'M-150 -132 L150 -132', W * 1.8, '#b98a5a');
    for (const sd of [-1, 1]) {
      const x = sd * 130;
      line(parent, `M${x} -132 L${x - 24} -64 M${x} -132 L${x + 24} -64`, W * 0.5);
      fill(parent, `M${x - 34} -64 L${x + 34} -64 L${x + 26} -24 Q${x} -16 ${x - 26} -24 Z`, cc);
      line(parent, `M${x - 32} -52 L${x + 32} -52 M${x - 29} -38 L${x + 29} -38`, W * 0.4, shade(cc, 0.7));
      fill(parent, `M${x - 26} -66 Q${x - 14} -84 ${x} -68 Q${x + 12} -84 ${x + 26} -66 Z`, sd < 0 ? '#e0613f' : '#7cb34c', W * 0.6);
    }
  }
}

interface Arm { root: SVGGElement; elbow: SVGGElement; side: 1 | -1 }
function drawArm(parent: Element, s: Spec, look: Look, side: 1 | -1): Arm {
  const root = g(parent);
  const longSleeve = s.sleeve === 'long';
  const sleeve = s.topColor;
  if (longSleeve) fill(root, `M-12 -6 Q0 -12 12 -6 L11 ${UPPER + 2} L-11 ${UPPER + 2} Z`, sleeve);
  else {
    fill(root, `M-9 6 L9 6 L9 ${UPPER + 2} L-9 ${UPPER + 2} Z`, look.skin);
    fill(root, 'M-12 -6 Q0 -12 12 -6 L12 16 L-12 16 Z', sleeve);
  }
  if ((s.extras ?? []).includes('vest')) fill(root, 'M-12 -6 Q0 -12 12 -6 L12 6 L-12 6 Z', '#ef7d2a', W * 0.7);
  const elbow = g(root);
  if (longSleeve) {
    fill(elbow, `M-11 -4 L11 -4 L10 ${FORE - 4} L-10 ${FORE - 4} Z`, sleeve);
    line(elbow, `M-10 ${FORE - 8} L10 ${FORE - 8}`, W * 0.45);
  } else fill(elbow, `M-8 -4 L8 -4 L8 ${FORE - 4} L-8 ${FORE - 4} Z`, look.skin);
  // ban tay: hinh gang tay tron, ngon cai ve phia trong
  fill(elbow, `M-11 ${FORE + 4} Q-12 ${FORE - 8} 0 ${FORE - 8} Q12 ${FORE - 8} 11 ${FORE + 4} Q10 ${FORE + 16} 0 ${FORE + 16} Q-10 ${FORE + 16} -11 ${FORE + 4} Z`, look.skin);
  line(elbow, `M${-side * 8} ${FORE + 2} Q${-side * 15} ${FORE} ${-side * 12} ${FORE - 6}`, W * 0.6);
  return { root, elbow, side };
}

interface Face {
  root: SVGGElement;
  eyes: Record<string, SVGGElement>;
  mouths: SVGGElement[];
  brows: Record<string, SVGGElement>;
  mask?: SVGGElement;
}

/** Toc phia sau vai (toc dai): nam sau than, theo chuyen dong cua dau. */
function drawHairBack(parent: Element, s: Spec, hair: string) {
  if (s.hair === 'long') {
    fill(parent, 'M-80 -96 C-92 -36 -90 24 -78 62 Q-60 74 -40 62 Q0 70 40 62 Q60 74 78 62 C90 24 92 -36 80 -96 Z', hair);
    line(parent, 'M-62 0 Q-64 30 -60 58 M62 0 Q64 30 60 58', W * 0.45, shade(hair, 0.7));
  }
}

function drawHead(parent: Element, s: Spec, look: Look, hair: string): { face: Face; tail?: SVGGElement } {
  const head = g(parent);
  const hairDark = shade(hair, 0.72);
  const hat = s.hat ?? 'none';
  let tail: SVGGElement | undefined;
  // toc sau dau
  if (s.hair === 'ponytail') {
    tail = g(head);
    fill(tail, 'M40 -118 C100 -112 112 -46 86 -6 C80 -30 66 -46 52 -64 Z', hair);
    line(tail, 'M70 -90 C82 -70 86 -50 84 -30', W * 0.45, hairDark);
    fill(head, 'M40 -122 Q50 -128 56 -116 Q50 -108 42 -112 Z', '#d0464b', W * 0.7);
  }
  if (s.hair === 'bun' && hat !== 'nonla') {
    fill(head, 'M-26 -150 a26 22 0 1 0 52 0 a26 22 0 1 0 -52 0', hair);
    line(head, 'M-14 -156 Q0 -164 14 -156', W * 0.45, hairDark);
  }
  if (s.hair === 'pigtails') {
    for (const sd of [-1, 1]) {
      fill(head, `M${sd * 66} -96 Q${sd * 118} -100 ${sd * 112} -44 Q${sd * 104} -22 ${sd * 92} -30 Q${sd * 96} -60 ${sd * 66} -70 Z`, hair);
      fill(head, `M${sd * 62} -98 a8 8 0 1 0 ${sd * 16} 0 a8 8 0 1 0 ${-sd * 16} 0`, '#e0613f', W * 0.6);
    }
  }
  fill(head, 'M-80 -62 C-82 -124 -44 -150 0 -150 C44 -150 82 -124 80 -62 C80 -40 72 -30 66 -26 L-66 -26 C-72 -30 -80 -40 -80 -62 Z', hair);
  // tai
  for (const sd of [-1, 1]) fill(head, `M${sd * 70} -70 Q${sd * 86} -72 ${sd * 84} -54 Q${sd * 82} -40 ${sd * 68} -42`, look.skin);
  fill(head, 'M-74 -62 C-74 -116 -42 -140 0 -140 C42 -140 74 -116 74 -62 C74 -22 42 0 0 0 C-42 0 -74 -22 -74 -62 Z', look.skin);
  flat(head, 'M-40 -6 Q0 8 40 -6 Q20 0 0 0 Q-20 0 -40 -6 Z', shade(look.skin, 0.9));
  // mat (ban bong trang khong can net mat)
  const face = g(head);
  let faceOut: Face = { root: face, eyes: {}, mouths: [], brows: {} };
  if (!under()) faceOut = drawFace(face, s, look);
  // toc truoc (mai)
  const fringe: Record<string, string> = {
    ponytail: 'M-76 -60 C-82 -116 -44 -146 0 -146 C44 -146 82 -116 76 -60 L68 -78 Q58 -96 42 -98 Q32 -82 12 -80 Q8 -96 0 -100 Q-14 -84 -34 -82 Q-46 -96 -58 -92 Q-68 -82 -76 -60 Z',
    short: 'M-76 -64 C-82 -118 -44 -146 0 -146 C44 -146 82 -118 76 -64 L70 -80 L60 -90 L52 -84 L40 -96 L30 -86 L16 -98 L4 -88 L-10 -98 L-22 -86 L-36 -96 L-48 -84 L-60 -92 L-70 -80 Z',
    side: 'M-76 -64 C-82 -118 -44 -148 0 -148 C44 -148 82 -118 76 -64 L72 -84 Q62 -102 30 -104 Q-6 -104 -28 -88 Q-34 -98 -46 -94 Q-64 -86 -76 -64 Z',
    bun: 'M-76 -62 C-82 -116 -44 -146 0 -146 C44 -146 82 -116 76 -62 Q66 -96 34 -106 Q12 -110 0 -98 Q-12 -110 -34 -106 Q-66 -96 -76 -62 Z',
    long: 'M-78 -40 C-84 -116 -44 -148 0 -148 C44 -148 84 -116 78 -40 Q72 -90 40 -104 Q14 -110 0 -98 Q-14 -110 -40 -104 Q-72 -90 -78 -40 Z',
    pigtails: 'M-76 -62 C-82 -116 -44 -146 0 -146 C44 -146 82 -116 76 -62 L66 -80 Q50 -94 30 -92 Q24 -82 12 -82 Q4 -96 -8 -90 Q-20 -80 -34 -84 Q-54 -96 -66 -80 Z',
  };
  fill(head, fringe[s.hair], hair);
  if (s.hair === 'side') line(head, 'M-28 -88 Q-10 -110 20 -114', W * 0.45, hairDark);
  if (s.hair === 'bun' || s.hair === 'long') line(head, 'M0 -98 L0 -130', W * 0.45, hairDark);
  // mu
  if (hat === 'officer') {
    const c = s.hatColor ?? '#2c3b52';
    fill(head, 'M-66 -112 C-78 -132 -82 -150 -62 -158 C-22 -170 22 -170 62 -158 C82 -150 78 -132 66 -112 Z', c);
    fill(head, 'M-64 -116 L64 -116 L62 -98 L-62 -98 Z', shade(c, 0.85));
    line(head, 'M-60 -108 L60 -108', W * 0.5, '#d9b44a');
    fill(head, 'M-62 -100 Q0 -88 62 -100 Q0 -82 -62 -100 Z', '#1e1e22', W * 0.6);
    fill(head, 'M-11 -136 a11 11 0 1 0 22 0 a11 11 0 1 0 -22 0', '#e2b93b', W * 0.6);
    if (!under()) el('path', { d: 'M0 -142 L3 -136 L0 -130 L-3 -136 Z', fill: '#c0392b' }, head);
  } else if (hat === 'cap') {
    const c = s.hatColor ?? '#2b2b2b';
    fill(head, 'M-72 -96 C-78 -136 -40 -158 0 -158 C40 -158 78 -136 72 -96 Z', c);
    line(head, 'M0 -158 L0 -100 M-36 -150 Q-44 -124 -40 -100 M36 -150 Q44 -124 40 -100', W * 0.45, shade(c, 1.6));
    fill(head, 'M-6 -160 a6 4 0 1 0 12 0 a6 4 0 1 0 -12 0', c, W * 0.6);
    fill(head, 'M-78 -98 Q0 -116 78 -98 Q88 -88 72 -84 Q0 -98 -72 -84 Q-88 -88 -78 -98 Z', shade(c, 1.35));
  } else if (hat === 'hardhat') {
    const c = s.hatColor ?? '#e5b53a';
    fill(head, 'M-74 -100 C-78 -142 -40 -164 0 -164 C40 -164 78 -142 74 -100 Z', c);
    if (!under()) el('path', { d: 'M20 -156 Q56 -146 66 -104 L48 -104 Q44 -136 20 -150 Z', fill: shade(c, 0.86) }, head);
    line(head, 'M-74 -100 C-78 -142 -40 -164 0 -164 C40 -164 78 -142 74 -100', W);
    fill(head, 'M-12 -166 L12 -166 L10 -104 L-10 -104 Z', shade(c, 1.08), W * 0.7);
    fill(head, 'M-88 -104 Q0 -116 88 -104 L86 -94 Q0 -104 -86 -94 Z', c);
  } else if (hat === 'nurse') {
    const c = s.hatColor ?? '#fdfdfc';
    fill(head, 'M-42 -130 Q0 -152 42 -130 L48 -110 Q0 -124 -48 -110 Z', c);
    if (!under()) el('path', { d: 'M-3 -140 L3 -140 L3 -134 L9 -134 L9 -128 L3 -128 L3 -122 L-3 -122 L-3 -128 L-9 -128 L-9 -134 L-3 -134 Z', fill: '#d6342c' }, head);
  } else if (hat === 'nonla') {
    const c = s.hatColor ?? '#e9d7a3';
    if (!under()) line(head, 'M-60 -92 Q-60 -40 -30 -6 M60 -92 Q60 -40 30 -6', W * 0.4, '#7a5a3a');
    fill(head, 'M-128 -98 L0 -206 L128 -98 Q0 -78 -128 -98 Z', c);
    line(head, 'M0 -206 L-70 -88 M0 -206 L-24 -82 M0 -206 L24 -82 M0 -206 L70 -88', W * 0.4, shade(c, 0.72));
    line(head, 'M-104 -118 Q0 -104 104 -118 M-74 -144 Q0 -134 74 -144', W * 0.4, shade(c, 0.72));
  }
  return { face: faceOut, tail };
}

function drawFace(face: SVGGElement, s: Spec, look: Look): Face {
  const ex = s.extras ?? [];
  const blush = look.blush ?? 0.75;
  for (const sd of [-1, 1]) el('ellipse', { cx: sd * 46, cy: -36, rx: 13, ry: 7, fill: '#f09a90', opacity: blush }, face);
  line(face, 'M-2 -44 Q4 -40 -1 -36', W * 0.55);
  if (s.build === 'elder') line(face, 'M-52 -46 Q-46 -42 -42 -46 M52 -46 Q46 -42 42 -46', W * 0.4);
  const eyes: Record<string, SVGGElement> = {};
  const eyeOpen = (gg: SVGGElement, sd: number) => {
    el('ellipse', { cx: sd * 28, cy: -54, rx: 8, ry: 11, fill: OUT }, gg);
    el('circle', { cx: sd * 28 + 2.5, cy: -58, r: 3.2, fill: '#fff' }, gg);
  };
  const shut = (gg: SVGGElement, sd: number, kind: 'down' | 'up' | 'wink') => {
    const x = sd * 28;
    if (kind === 'down') line(gg, `M${x - 10} -54 Q${x} -46 ${x + 10} -54`, W * 0.8);
    else if (kind === 'up') line(gg, `M${x - 10} -50 Q${x} -62 ${x + 10} -50`, W * 0.8);
    else line(gg, `M${x + sd * 9} -61 L${x - sd * 9} -54 L${x + sd * 9} -47`, W * 0.8);
  };
  const mk = (name: string, fn: (gg: SVGGElement) => void) => { const gg = g(face, { display: 'none' }); fn(gg); eyes[name] = gg; };
  mk('open', (gg) => { eyeOpen(gg, -1); eyeOpen(gg, 1); });
  mk('closed', (gg) => { shut(gg, -1, 'down'); shut(gg, 1, 'down'); });
  mk('happy', (gg) => { shut(gg, -1, 'up'); shut(gg, 1, 'up'); });
  mk('wink', (gg) => { eyeOpen(gg, -1); shut(gg, 1, 'wink'); });
  mk('deadpan', (gg) => {
    for (const sd of [-1, 1]) {
      const x = sd * 28;
      el('path', { d: `M${x - 13} -56 L${x + 13} -56 L${x + 12} -50 Q${x} -42 ${x - 12} -50 Z`, fill: '#fff', stroke: OUT, 'stroke-width': W * 0.7, 'stroke-linejoin': 'round' }, gg);
      el('circle', { cx: x, cy: -51, r: 4.5, fill: OUT }, gg);
    }
  });
  mk('surprised', (gg) => {
    for (const sd of [-1, 1]) {
      el('circle', { cx: sd * 28, cy: -54, r: 12, fill: '#fff', stroke: OUT, 'stroke-width': W * 0.7 }, gg);
      el('circle', { cx: sd * 28, cy: -54, r: 4.5, fill: OUT }, gg);
    }
  });
  const brows: Record<string, SVGGElement> = {};
  const browCol = s.hairColor ?? OUT;
  const mb = (name: string, l: string, r: string) => {
    const gg = g(face, { display: 'none' });
    line(gg, l, W * 0.75, browCol); line(gg, r, W * 0.75, browCol); brows[name] = gg;
  };
  mb('normal', 'M-40 -76 Q-29 -81 -18 -77', 'M18 -77 Q29 -81 40 -76');
  mb('up', 'M-40 -82 Q-29 -90 -18 -84', 'M18 -84 Q29 -90 40 -82');
  mb('worried', 'M-40 -76 Q-30 -78 -18 -84', 'M18 -84 Q30 -78 40 -76');
  mb('flat', 'M-40 -74 L-18 -74', 'M18 -74 L40 -74');
  if (ex.includes('glasses')) {
    const gl = g(face);
    for (const sd of [-1, 1]) el('rect', { x: sd * 28 - 16, y: -68, width: 32, height: 27, rx: 9, fill: '#ffffff', 'fill-opacity': 0.18, stroke: OUT, 'stroke-width': W * 0.65 }, gl);
    line(gl, 'M-12 -56 Q0 -61 12 -56 M-44 -58 L-64 -62 M44 -58 L64 -62', W * 0.6);
  }
  // mieng: 0 khep, 1 nho, 2 mo, 3 mo rong
  const mouths: SVGGElement[] = [];
  const mm = (fn: (gg: SVGGElement) => void) => { const gg = g(face, { display: 'none' }); fn(gg); mouths.push(gg); };
  mm((gg) => line(gg, 'M-8 -24 Q0 -19 8 -24', W * 0.7));
  mm((gg) => { el('ellipse', { cx: 0, cy: -22, rx: 5, ry: 5.5, fill: OUT }, gg); });
  mm((gg) => {
    fill(gg, 'M-10 -26 Q0 -28 10 -26 Q10 -12 0 -12 Q-10 -12 -10 -26 Z', '#7a2e2a', W * 0.6);
    flat(gg, 'M-6 -15 Q0 -20 6 -15 Q0 -12.5 -6 -15 Z', '#e07a74');
  });
  mm((gg) => {
    fill(gg, 'M-14 -28 Q0 -31 14 -28 Q13 -8 0 -8 Q-13 -8 -14 -28 Z', '#7a2e2a', W * 0.6);
    flat(gg, 'M-9 -12 Q0 -19 9 -12 Q0 -8.5 -9 -12 Z', '#e07a74');
  });
  let mask: SVGGElement | undefined;
  if (ex.includes('mask')) {
    for (const sd of [-1, 1]) line(face, `M${sd * 40} -38 Q${sd * 62} -46 ${sd * 72} -58`, W * 0.5, '#b8c4cc');
    mask = g(face);
    fill(mask, 'M-42 -42 Q0 -48 42 -42 L38 -12 Q0 2 -38 -12 Z', '#e8f0f4');
    line(mask, 'M-36 -32 Q0 -36 36 -32 M-34 -22 Q0 -26 34 -22', W * 0.4, '#a9b6bf');
  }
  return { root: face, eyes, mouths, brows, mask };
}

// ---------------- tu the ----------------
const mix = (a: Vec, b: Vec, k: number): Vec => [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k];
interface Pose { u1: number; u2: number }
const REST: Pose = { u1: 10, u2: 6 };
// tay sau khi cam do (u1: mo vai ra ngoai, u2: gap khuyu; do)
const HOLD: Record<string, Pose> = {
  clipboard: { u1: 10, u2: -100 }, books: { u1: 10, u2: -100 },
  suitcase: { u1: 28, u2: 0 }, briefcase: { u1: 14, u2: 0 }, basket: { u1: 14, u2: 0 }, cane: { u1: 14, u2: 0 },
  ganh: { u1: 60, u2: 105 },
};
function gesturePose(gest: Move, k: number): Pose {
  switch (gest) {
    case 'wave': return { u1: 125, u2: 35 + 25 * Math.sin(k * 11) };
    case 'point': return { u1: 86, u2: 2 };
    case 'present': return { u1: 52, u2: 34 + 4 * Math.sin(k * 3) };
    case 'talk': return { u1: 18, u2: -112 + 12 * Math.sin(k * 7) };
    case 'sweep': return { u1: 52 + 26 * Math.sin(k * 2.2), u2: 22 };
    default: return REST;
  }
}

export function createChibi(layer: Element, spec: Spec, opt: ChibiOptions, uid: string, sticker = 7): Chibi {
  checkSpec(spec);
  const look = LOOKS[spec.id] ?? DEFAULT_LOOK;
  const hair = spec.hairColor ?? look.hair;
  const B = BUILD[spec.build];
  const h = spec.height ?? 1;
  const bodyK = B.body * h, headK = B.head * h;
  const stoop = (spec.stoop ?? 0) * 0.9;
  const holds = spec.prop ?? 'none';
  const que = opt.limbs === 'que';
  const root = g(layer);
  const flip = g(root);
  const build = (r: number, id: string) => {
    setUnder(r);
    const body = g(flip, { transform: `scale(${f(bodyK)})` });
    drawProp(g(body), spec, 'ground', que);
    const qLegs: QueLeg[] = que ? drawQueLegs(body, spec, look) : [];
    const legs = que ? [g(body), g(body)] : drawLegs(body, spec, look);
    const upper = g(body);
    const hairBack = g(upper);
    drawHairBack(hairBack, spec, hair);
    drawProp(upper, spec, 'back');
    const qBack: QueArm | null = que ? drawQueArm(upper, spec, -1) : null;
    const armBack = que ? { root: g(upper), elbow: g(upper), side: -1 as const } : drawArm(upper, spec, look, -1);
    drawTorso(upper, spec, look, id);
    fill(upper, 'M-13 -142 L13 -142 L13 -122 L-13 -122 Z', shade(look.skin, 0.88), W * 0.8);
    const headWrap = g(upper);
    const { face, tail } = drawHead(headWrap, spec, look, hair);
    drawProp(upper, spec, 'body');
    const qFront: QueArm | null = que ? drawQueArm(upper, spec, 1) : null;
    const armFront = que ? { root: g(upper), elbow: g(upper), side: 1 as const } : drawArm(upper, spec, look, 1);
    const itemG = g(upper, { display: 'none' });
    if (que) drawFlashlight(itemG, id + 'den', r === 0);
    // tay om do truoc nguc hoac gac don ganh: ve len tren cung
    if (holds === 'clipboard' || holds === 'books' || holds === 'ganh') {
      upper.appendChild(armBack.root);
      if (qBack) for (const n of [qBack.stick, qBack.hand, qBack.sleeveO, qBack.sleeveI]) upper.appendChild(n);
    }
    setUnder(0);
    return { legs, upper, hairBack, headWrap, armBack, armFront, face, tail, qLegs, qBack, qFront, itemG };
  };
  // ban bong trang (vien sticker) o duoi, hinh that o tren
  const parts = sticker > 0 ? [build(sticker / bodyK, uid + 'u'), build(0, uid)] : [build(0, uid)];
  const face = parts[parts.length - 1].face;

  const blinkSeed = hash(spec.id);
  let x = opt.x, y = opt.y, scale = opt.scale ?? 1, dir: 1 | -1 = opt.dir ?? 1;
  let flipFrom: 1 | -1 = dir, flipAt = -10;
  let target: number | null = null, walkPhase = 0, walking = false, running = false;
  let sitting = false, sitAt = -10;
  let gest: { name: Move; t0: number; t1: number } | null = null;
  let item: Item | null = null;
  let mo: { id: string; t0: number; t1: number } | null = null;
  let moPrev: { id: string; t0: number; t1: number } | null = null;   // clip dang tron ra khi clip moi bat dau
  const mv: number[] = new Array(20).fill(0), mvPrev: number[] = new Array(20).fill(0);
  let exprState: { name: Expr; t1: number } = { name: 'neutral', t1: Infinity };
  let speakUntil = -1, speakFrom = -1;
  let now = 0;
  const headScale = headK / bodyK;

  const setPose = (a: Arm, p: Pose, swing = 0) => {
    const u1 = p.u1 + swing;
    a.root.setAttribute('transform', `translate(${a.side * 44} ${SHOULDER_Y + 6}) rotate(${f(-a.side * u1)})`);
    a.elbow.setAttribute('transform', `translate(0 ${UPPER}) rotate(${f(-a.side * p.u2)})`);
  };
  const show = (rec: Record<string, SVGGElement>, key: string | number) => {
    for (const k in rec) rec[k].setAttribute('display', k === String(key) ? 'inline' : 'none');
  };

  const c: Chibi = {
    spec, root,
    get x() { return x; }, set x(v) { x = v; },
    get y() { return y; }, set y(v) { y = v; },
    get scale() { return scale; }, set scale(v) { scale = v; },
    get dir() { return dir; }, set dir(v) { dir = v; },
    walkTo(tx) { target = tx; running = false; if (sitting) c.sit(false); if (Math.abs(tx - x) > 1) c.face(tx > x ? 1 : -1); },
    runTo(tx) { c.walkTo(tx); running = true; },
    sit(on) { if (on !== sitting) { sitting = on; sitAt = now; } },
    act(name, seconds) { gest = { name, t0: now, t1: now + Math.max(0.6, seconds) }; },
    hold(it) { item = que ? it : null; },
    play(id, seconds) {
      if (!que) { console.warn(`[chibi] play('${id}') chi dung voi limbs: 'que'`); return 0; }
      if (!hasClip(id)) throw new Error(`[chibi] khong co clip mocap '${id}'`);
      const len = seconds ?? clipLength(id);
      moPrev = mo && now < mo.t1 + 0.3 ? { ...mo, t1: Math.min(mo.t1, now) } : null;
      mo = { id, t0: now, t1: now + Math.max(0.6, len) };
      return len;
    },
    face(d) { if (d !== dir) { flipFrom = dir; dir = d; flipAt = now; } },
    expr(name, seconds) { exprState = { name, t1: seconds ? now + seconds : Infinity }; },
    say(seconds) { speakFrom = now; speakUntil = now + seconds; },
    update(t, dt, speech) {
      now = t;
      walking = false;
      if (target !== null) {
        const sitK0 = clamp((t - sitAt) / 0.35);
        const ready = sitting ? false : sitK0 >= 1;
        const d = target - x, step = B.speed * scale * dt * (running ? 2.3 : 1);
        if (!ready) { /* cho dung han roi moi di */ }
        else if (Math.abs(d) <= step) { x = target; target = null; running = false; }
        else { x += Math.sign(d) * step; walking = true; walkPhase += dt * (spec.build === 'elder' ? 6 : 9) * (running ? 1.6 : 1); }
      }
      // lat guong khi doi huong: co nhanh qua 0 trong 0,16 giay
      const fk = clamp((t - flipAt) / 0.16);
      const sx = fk >= 1 ? dir : lerp(flipFrom, dir, ease(fk));
      root.setAttribute('transform', `translate(${f(x)} ${f(y)}) scale(${f(scale)})`);
      flip.setAttribute('transform', `scale(${f(Math.abs(sx) < 0.04 ? 0.04 * Math.sign(sx || 1) : sx)} 1)`);
      // than: tho, nhun khi di
      const bob = walking ? -Math.abs(Math.sin(walkPhase)) * (running ? 16 : 10) : Math.sin(t * 2.1 + blinkSeed * 6) * 1.2;
      const sk = ease(clamp((t - sitAt) / 0.35));
      const sitK = sitting ? sk : 1 - sk;
      const lsy = f(1 - 0.4 * sitK);
      const l0 = `translate(0 ${f(walking ? Math.min(0, Math.sin(walkPhase) * 8) : 0)}) scale(1 ${lsy})`;
      const l1 = `translate(0 ${f(walking ? Math.min(0, -Math.sin(walkPhase) * 8) : 0)}) scale(1 ${lsy})`;
      // cu chi
      let w = 0, k = 0, gname: Move | null = null;
      if (gest && t < gest.t1 + 0.3) {
        gname = gest.name; k = t - gest.t0;
        w = walking ? 0 : ease(Math.min((t - gest.t0) / 0.25, (gest.t1 + 0.3 - t) / 0.3));
      } else gest = null;
      const sw = walking ? Math.sin(walkPhase) * (running ? 30 : 16) : 0;
      const armGest = gname ? gesturePose(gname, k) : REST;
      // cam den pin: tu the nghi la roi den xuong dat phia truoc
      const base: Pose = item ? { u1: 40, u2: 26 } : REST;
      const fp = { u1: lerp(base.u1, armGest.u1, w), u2: lerp(base.u2, armGest.u2, w) };
      // dau: gat, cui, nghieng theo loi noi
      let hy = stoop, hr = 0, by = 0;
      if (gname === 'nod') hy += w * Math.max(0, Math.sin(k * 7)) * 6;
      if (gname === 'bow') { hy += w * 12; by = w * 6; }
      const talking = t >= speakFrom && t < speakUntil;
      hr += talking ? Math.sin(t * 4.3) * 2.2 : Math.sin(t * 0.9 + blinkSeed * 9) * 1.2;
      const tr = `rotate(${f(walking ? Math.sin(walkPhase * 2) * 5 : Math.sin(t * 1.7) * 2)} 46 -116)`;
      // ngoi: que ha hong tu -92 xuong -60; chibi ha than 16 va ep chan
      const raise = que ? lerp(-RAISE, -14, sitK) : 16 * sitK;
      // clip mocap: tron vao 0,3 giay dau, tron ra 0,3 giay cuoi; dang di thi tat
      const weightOf = (m: { t0: number; t1: number }) => ease(clamp(Math.min((t - m.t0) / 0.3, (m.t1 + 0.3 - t) / 0.3)));
      let wm = 0;
      if (mo && t < mo.t1 + 0.3) {
        wm = walking ? 0 : weightOf(mo);
        sampleClip(mo.id, Math.min(t, mo.t1) - mo.t0, mv);
      } else mo = null;
      // clip truoc chua tron ra het: tron cheo sang clip moi thay vi giat ve tu the nghi
      if (moPrev && t < moPrev.t1 + 0.3 && !walking) {
        const wp = weightOf(moPrev);
        sampleClip(moPrev.id, Math.min(t, moPrev.t1) - moPrev.t0, mvPrev);
        const a = wp * (1 - wm), W = a + wm;
        if (W > 0) for (let q = 0; q < 20; q++) mv[q] = (mvPrev[q] * a + (mo ? mv[q] * wm : 0)) / W;
        wm = W;
      } else moPrev = null;
      const mdx = mv[16] * wm, mdy = mv[17] * wm, mtilt = mv[18] / 10 * wm;
      if (wm > 0) hy += clamp(mv[19] / 60) * 14 * wm;
      const ht = `translate(0 ${f(NECK_Y + hy)}) rotate(${f(hr)}) scale(${f(headScale)})`;
      const ut = `translate(${f(mdx)} ${f(bob + by + raise + mdy)})` + (wm > 0 ? ` rotate(${f(mtilt)} 0 -46)` : '');
      for (const p of parts) {
        p.upper.setAttribute('transform', wm > 0 || que ? ut : `translate(0 ${f(bob + by + raise)})`);
        p.legs[0].setAttribute('transform', l0); p.legs[1].setAttribute('transform', l1);
        setPose(p.armFront, fp, sw);
        setPose(p.armBack, HOLD[holds] ?? REST, HOLD[holds] ? 0 : -sw);
        if (que) {
          const stub = spec.top === 'coat' || spec.top === 'aodai' || spec.top === 'dress' ? 0 : 12;
          for (const L of p.qLegs) {
            const q = queLegPoints(L.side, -46 + bob + by + raise, walkPhase, walking, sitK, running);
            q.Hp[0] += mdx; q.Hp[1] += mdy; q.M[0] += mdx; q.F[0] += mdx;
            if (wm > 0) {
              const o = L.side > 0 ? 12 : 8;
              const K: Vec = [q.Hp[0] + mv[o], q.Hp[1] + mv[o + 1]], F: Vec = [q.Hp[0] + mv[o + 2], q.Hp[1] + mv[o + 3]];
              const M: Vec = [2 * K[0] - (q.Hp[0] + F[0]) / 2, 2 * K[1] - (q.Hp[1] + F[1]) / 2];
              q.M = mix(q.M, M, wm); q.F = mix(q.F, F, wm);
            }
            drawQueLegAt(L, q.Hp, q.M, q.F, stub);
          }
          const hb = HOLD[holds] ?? REST;
          const armAt = (a: QueArm, u1: number, u2: number, o: number) => {
            const q = queArmPoints(a.side, u1, u2);
            if (wm > 0) {
              q.E = mix(q.E, [q.S[0] + mv[o], q.S[1] + mv[o + 1]], wm);
              q.H = mix(q.H, [q.S[0] + mv[o + 2], q.S[1] + mv[o + 3]], wm);
            }
            return drawQueArmAt(a, q.E, q.H);
          };
          const hf = armAt(p.qFront!, fp.u1 + (item ? sw * 0.3 : sw), fp.u2, 4);
          armAt(p.qBack!, hb.u1 + (HOLD[holds] ? 0 : -sw), hb.u2, 0);
          p.itemG.setAttribute('display', item ? 'inline' : 'none');
          if (item) p.itemG.setAttribute('transform', `translate(${f(hf.hand[0])} ${f(hf.hand[1])}) rotate(${f(hf.angle)})`);
        }
        p.headWrap.setAttribute('transform', ht);
        p.hairBack.setAttribute('transform', ht);
        p.tail?.setAttribute('transform', tr);
      }
      face.root.setAttribute('transform', 'translate(6 0)');
      // net mat
      if (exprState.t1 <= t) exprState = { name: 'neutral', t1: Infinity };
      const ex = exprState.name;
      const period = 3.1 + blinkSeed * 1.6;
      const ph = (t + blinkSeed * period) % period;
      const blink = ph < 0.13 && (ex === 'neutral' || ex === 'surprised' || ex === 'worried');
      show(face.eyes, blink ? 'closed' : ex === 'neutral' || ex === 'worried' ? 'open' : ex);
      show(face.brows, ex === 'surprised' || ex === 'happy' ? 'up' : ex === 'worried' ? 'worried' : ex === 'deadpan' ? 'flat' : 'normal');
      // mieng theo loi doc (speech.js); khong co thi mo phong nhip noi
      let m = 0;
      if (talking) {
        const s = speech(t);
        const lvl = s === null ? Math.max(0, Math.sin(t * 13) * 0.6 + Math.sin(t * 7.1) * 0.4) : s;
        m = lvl < 0.12 ? 0 : lvl < 0.4 ? 1 : lvl < 0.72 ? 2 : 3;
      } else if (ex === 'surprised') m = 1;
      else if (ex === 'happy') m = 2;
      show(face.mouths as unknown as Record<string, SVGGElement>, m);
      if (face.mask) face.mask.setAttribute('transform', `translate(0 -26) scale(1 ${f(1 + m * 0.05)}) translate(0 26)`);
    },
  };
  c.update(0, 0, () => null);
  return c;
}
