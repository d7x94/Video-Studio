// stage.ts: san khau chibi cho HyperFrames. Giong stage line-art: mo phong tien tung buoc 1/60 giay,
// tua lui thi dung lai tu dau, nen moi khung la ham thuan cua t.
//
//   const C = createChibiStage(svg, { width: 1080, height: 1920 });
//   C.setup((C) => {
//     const thu = C.add("can-bo-thu", { x: 330, y: 1700, scale: 2.6 });
//     C.at(T.s01, () => thu.say(2.4));
//   });
//   function render(t) { C.render(t); }
import type { Spec } from '../../lineart/src/cast/rig.ts';
import { byId } from '../../lineart/src/cast/roster.ts';
import { createChibi, type Chibi, type ChibiOptions } from './rig.ts';
import { el } from './svg.ts';

export interface ChibiStage {
  svg: SVGSVGElement;
  back: SVGGElement; people: SVGGElement; front: SVGGElement;
  width: number; height: number;
  setup(fn: (C: ChibiStage) => void): void;
  add(who: string | Spec, opt: ChibiOptions): Chibi;
  at(t: number, fn: () => void): void;
  render(t: number): void;
  readonly time: number;
}

const STEP = 1 / 60;

/** Am luong loi doc (0..1) tu speech.js do inject.py sinh; null neu khong co. */
export function speechAt(t: number): number | null {
  const S = (window as unknown as { SPEECH?: { fps: number; env: number[] } }).SPEECH;
  if (!S) return null;
  const i = Math.floor(t * S.fps);
  return i >= 0 && i < S.env.length ? S.env[i] : 0;
}

export function createChibiStage(svg: SVGSVGElement, opt: { width: number; height: number; sticker?: number }): ChibiStage {
  const { width, height } = opt;
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  const sticker = opt.sticker ?? 7;
  const back = el('g', {}, svg), people = el('g', {}, svg), front = el('g', {}, svg);
  let setupFn: ((C: ChibiStage) => void) | null = null;
  let cast: Chibi[] = [];
  let cues: Array<{ t: number; fn: () => void; done: boolean }> = [];
  let simT = 0, built = false, n = 0;

  const C: ChibiStage = {
    svg, back, people, front, width, height,
    get time() { return simT; },
    setup(fn) { setupFn = fn; built = false; },
    add(who, o) {
      const spec = typeof who === 'string' ? byId(who) : who;
      const c = createChibi(people, spec, o, `ch${n++}`, sticker);
      cast.push(c);
      return c;
    },
    at(t, fn) { cues.push({ t, fn, done: false }); },
    render(t) {
      if (!built || t < simT - 1e-6) rebuild();
      fire(simT);
      while (simT < t - 1e-9) {
        const dt = Math.min(STEP, t - simT);
        simT += dt;
        fire(simT);
        for (const c of cast) c.update(simT, dt, speechAt);
      }
    },
  };
  function fire(now: number) { for (const q of cues) if (!q.done && q.t <= now + 1e-9) { q.done = true; q.fn(); } }
  function rebuild() {
    for (const layer of [back, people, front]) while (layer.firstChild) layer.removeChild(layer.firstChild);
    cast = []; cues = []; simT = 0; n = 0;
    setupFn?.(C);
    for (const c of cast) c.update(0, 0, speechAt);
    built = true;
  }
  return C;
}
