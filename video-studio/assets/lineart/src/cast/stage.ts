// stage.ts — line-art stage for HyperFrames (and any player that seeks by time).
// The figures are physical (springs, gait phase), so state comes from simulating
// forward in fixed 1/60 s steps. render(t) steps forward from the last time; a seek
// backwards rebuilds the scene from the setup function and replays from 0. Every
// frame is therefore a pure function of t, as frame-by-frame rendering requires.
//
//   const L = createLineStage(svg, { width: 1920, height: 1080 });
//   L.setup((L) => {
//     L.ground(900);
//     const lan = L.add('dieu-duong-lan', { x: 300, y: 900, scale: 3.2 });
//     L.at(0, () => lan.walkTo(800));
//     L.at(T.s02 + 0.4, () => lan.act('talk', 4));
//   });
//   function render(t) { L.render(t); }
import { el, pen, inkDefs, f } from '../lib/ink.ts';
import { createCharacter, type Character, type Spec } from './rig.ts';
import { byId } from './roster.ts';
import { withSkin } from './skins.ts';
import { applyTinhCach, type Dien } from './tinh-cach.ts';

export interface StageOptions { width: number; height: number; paper?: string; ink?: string }
export interface AddOptions { x: number; y: number; scale?: number; dir?: 1 | -1; phase?: number;
  /** Skin theo vai (xem cast/skins.ts), vd 'sep', 'luat-su'. Khong ghi thi mac bo do khoa trong roster. */
  skin?: string;
  /** Tinh cach (cach dien) cua vai, ma trong tinh-cach.js (vd 'nghiem-khac'): doi ten cu chi, them noi()/nghe(). */
  tinhCach?: string;
  /** Khung hien (giay): nhan vat chi hien khi from <= t < until. Dung de doi skin theo canh:
   *  them cung nhan vat nhieu lan, moi ban mot skin, khung hien noi tiep nhau o ranh gioi canh.
   *  Hai ban cua cung mot nhan vat khong duoc trung khung hien. */
  from?: number; until?: number }
export interface LineStage {
  svg: SVGSVGElement;
  /** Layers inside the ink filter, back to front: back (props, set), people, front. */
  back: SVGGElement; people: SVGGElement; front: SVGGElement;
  width: number; height: number;
  setup(fn: (L: LineStage) => void): void;
  add(who: string | Spec, opt: AddOptions): Character & Dien;
  at(t: number, fn: () => void): void;
  ground(y: number, x0?: number, x1?: number, weight?: number): SVGPathElement;
  render(t: number): void;
  /** Current simulated time. */
  readonly time: number;
}

const STEP = 1 / 60;
export const windAt = (t: number): number => 0.18 + 0.25 * Math.sin(t * 0.21) + 0.15 * Math.sin(t * 0.67);

export function createLineStage(svg: SVGSVGElement, opt: StageOptions): LineStage {
  const { width, height } = opt;
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  svg.style.color = opt.ink ?? '#1c1c1c';
  svg.style.setProperty('--paper', opt.paper ?? '#fdfcf8');
  const { filter } = inkDefs(svg, 'ls');
  const bg = el('rect', { width, height, fill: opt.paper ?? '#fdfcf8' }, svg);
  bg.setAttribute('data-bg', '1');
  const scene = el('g', { filter }, svg);
  const back = el('g', {}, scene), people = el('g', {}, scene), front = el('g', {}, scene);

  let setupFn: ((L: LineStage) => void) | null = null;
  let cast: Character[] = [];
  let cues: Array<{ t: number; fn: () => void; done: boolean }> = [];
  let simT = 0, built = false;
  const shadows: Array<[Character, SVGEllipseElement]> = [];
  const windows: Array<[Character, SVGEllipseElement, number, number]> = [];

  const L: LineStage = {
    svg, back, people, front, width, height,
    get time() { return simT; },
    setup(fn) { setupFn = fn; built = false; },
    add(who, o) {
      const spec = withSkin(typeof who === 'string' ? byId(who) : who, o.skin);
      const w0 = o.from ?? -Infinity, w1 = o.until ?? Infinity;
      checkWindow(spec.id, w0, w1, o.from !== undefined || o.until !== undefined);
      const sh = el('ellipse', { rx: 9 * (o.scale ?? 1), ry: 1.4 * (o.scale ?? 1), fill: '#1c1c1c', opacity: 0.07, cy: o.y + 1 }, people);
      const c = applyTinhCach(createCharacter(people, spec, o), o.tinhCach);
      cast.push(c); shadows.push([c, sh]);
      if (o.from !== undefined || o.until !== undefined) windows.push([c, sh, w0, w1]);
      return c;
    },
    at(t, fn) { cues.push({ t, fn, done: false }); },
    ground(y, x0 = 0, x1 = width, weight = 0.9) {
      const p = pen(back, weight);
      p.setAttribute('d', `M${f(x0)} ${f(y + 1)} L${f(x1)} ${f(y + 1)}`);
      return p;
    },
    render(t) {
      if (!built || t < simT - 1e-6) rebuild();
      // fire cues due at the very start before the first step
      fire(simT);
      while (simT < t - 1e-9) {
        const dt = Math.min(STEP, t - simT);
        simT += dt;
        fire(simT);
        const w = windAt(simT);
        for (const c of cast) c.update(simT, dt, w);
      }
      for (const [c, sh] of shadows) sh.setAttribute('cx', f(c.x));
      for (const [c, sh, w0, w1] of windows) {
        const d = simT >= w0 - 1e-9 && simT < w1 - 1e-9 ? '' : 'none';
        c.g.style.display = d; sh.style.display = d;
      }
    },
  };

  function fire(now: number) {
    for (const q of cues) if (!q.done && q.t <= now + 1e-9) { q.done = true; q.fn(); }
  }
  const spans: Record<string, Array<[number, number, boolean]>> = {};
  function checkWindow(id: string, w0: number, w1: number, windowed: boolean) {
    if (!(w0 < w1)) throw new Error(`${id}: from (${w0}) phai nho hon until (${w1})`);
    const list = (spans[id] ??= []);
    // Chi kiem khi co ban dung from/until (video cu dat cung nhan vat hai lan khong khung hien van chay nhu truoc).
    for (const [a, b, wd] of list) if ((windowed || wd) && w0 < b - 1e-9 && a < w1 - 1e-9)
      throw new Error(`${id} da co tren san khau trong khoang ${a}..${b}: mot nhan vat chi hien mot ban cung luc (doi skin thi dat from/until noi tiep)`);
    list.push([w0, w1, windowed]);
  }
  function rebuild() {
    for (const layer of [back, people, front]) while (layer.firstChild) layer.removeChild(layer.firstChild);
    cast = []; cues = []; shadows.length = 0; windows.length = 0; simT = 0;
    for (const k of Object.keys(spans)) delete spans[k];
    setupFn?.(L);
    for (const c of cast) c.update(0, 0, windAt(0));
    built = true;
  }
  return L;
}
