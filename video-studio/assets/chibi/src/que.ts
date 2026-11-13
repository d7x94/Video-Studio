// que.ts: tay chan kieu que (rubber hose) cho nhan vat chibi.
// Moi tay, chan la mot net cong tu vai (hong) toi ban tay (ban chan), dau mut la cham tron.
// Hinh duoc tinh lai moi khung tu goc vai, goc khuyu (tay) hoac pha buoc chan (chan).
import { el, g, line, fill, f, shade, OUT, W } from './svg.ts';
import type { Spec } from '../../lineart/src/cast/rig.ts';

export const RAISE = 46;          // than nang len de chan que dai hon
export const ARM_A = 40, ARM_B = 40;
const STICK = 7.5;                // do day net tay chan
const SLEEVE = 22;                // do day ong tay ao ngan

export type Vec = [number, number];
const RAD = Math.PI / 180;
/** Vector don vi huong xuong (0,1) quay theo chieu kim dong ho r do. */
const dirOf = (r: number): Vec => [-Math.sin(r * RAD), Math.cos(r * RAD)];
const P = (p: Vec) => `${f(p[0])} ${f(p[1])}`;

export interface QueArm { side: 1 | -1; sleeveO: SVGPathElement; sleeveI: SVGPathElement; stick: SVGPathElement; hand: SVGGElement }
export function drawQueArm(parent: Element, s: Spec, side: 1 | -1): QueArm {
  const sleeveCol = s.topColor;
  const stick = line(parent, 'M0 0', STICK, OUT);
  const hand = g(parent);
  fill(hand, 'M-8 0 a8 8 0 1 0 16 0 a8 8 0 1 0 -16 0', '#2a211e', W * 0.5);
  const sleeveO = line(parent, 'M0 0', SLEEVE + W * 1.6, OUT);
  const sleeveI = line(parent, 'M0 0', SLEEVE, sleeveCol);
  return { side, sleeveO, sleeveI, stick, hand };
}

/** Diem vai, khuyu, ban tay cua tay que theo goc. u1: mo vai ra ngoai (do), u2: gap khuyu (do). */
export function queArmPoints(side: 1 | -1, u1: number, u2: number): { S: Vec; E: Vec; H: Vec; r2: number } {
  const S: Vec = [side * 40, -116];
  const r1 = -side * u1, r2 = r1 - side * u2;
  const v1 = dirOf(r1), v2 = dirOf(r2);
  const E: Vec = [S[0] + ARM_A * v1[0], S[1] + ARM_A * v1[1]];
  const H: Vec = [E[0] + ARM_B * v2[0], E[1] + ARM_B * v2[1]];
  return { S, E, H, r2 };
}

/** Ve tay que qua diem khuyu E toi ban tay H (tinh tu goc toa do than). Tra ve vi tri ban tay va huong cang tay. */
export function drawQueArmAt(a: QueArm, E: Vec, H: Vec): { hand: Vec; angle: number } {
  const S: Vec = [a.side * 40, -116];
  const C: Vec = [2 * E[0] - (S[0] + H[0]) / 2, 2 * E[1] - (S[1] + H[1]) / 2];
  a.stick.setAttribute('d', `M${P(S)} Q${P(C)} ${P(H)}`);
  const l1 = Math.hypot(E[0] - S[0], E[1] - S[1]) || 1;
  const v1: Vec = [(E[0] - S[0]) / l1, (E[1] - S[1]) / l1];
  const sl: Vec = [S[0] + 16 * v1[0], S[1] + 16 * v1[1]];
  const d = `M${P([S[0] + 2 * v1[0], S[1] + 2 * v1[1]])} L${P(sl)}`;
  a.sleeveO.setAttribute('d', d); a.sleeveI.setAttribute('d', d);
  a.hand.setAttribute('transform', `translate(${P(H)})`);
  // huong cang tay (do, 0 = huong xuong, quay theo chieu kim dong ho nhu dirOf)
  const angle = Math.atan2(-(H[0] - E[0]), H[1] - E[1]) / RAD;
  return { hand: H, angle };
}

/** Dat tu the tay que. u1: mo vai ra ngoai (do), u2: gap khuyu (do). Tra ve vi tri ban tay va huong cang tay. */
export function poseQueArm(a: QueArm, u1: number, u2: number): { hand: Vec; angle: number } {
  const p = queArmPoints(a.side, u1, u2);
  drawQueArmAt(a, p.E, p.H);
  return { hand: p.H, angle: p.r2 };
}

export interface QueLeg { side: 1 | -1; stubO: SVGPathElement; stubI: SVGPathElement; stick: SVGPathElement; foot: SVGGElement }
export function drawQueLegs(parent: Element, s: Spec, look: { skin: string }): QueLeg[] {
  const legs: QueLeg[] = [];
  const bare = s.top === 'dress' || s.bottom === 'shorts';
  const stubCol = bare ? s.bottomColor : s.bottomColor;
  for (const side of [-1, 1] as const) {
    const stick = line(parent, 'M0 0', STICK, OUT);
    const foot = g(parent);
    fill(foot, `M${-side * 4} -1 Q${-side * 4} -11 ${side * 8} -11 Q${side * 20} -11 ${side * 20} -3 Q${side * 20} 2 ${side * 8} 2 Q${-side * 4} 2 ${-side * 4} -1 Z`, s.shoeColor ?? '#2a211e', W * 0.6);
    const stubO = line(parent, 'M0 0', 26 + W * 1.6, OUT);
    const stubI = line(parent, 'M0 0', 26, stubCol);
    legs.push({ side, stubO, stubI, stick, foot });
    void look;
  }
  return legs;
}

/** Diem hong, giua (diem dieu khien) va ban chan cua chan que theo nhip buoc. */
export function queLegPoints(side: 1 | -1, hipY: number, phase: number, walking: boolean, sit = 0, running = false): { Hp: Vec; M: Vec; F: Vec } {
  const stride = running ? 34 : 24, liftH = running ? 24 : 14;
  const ph = phase + (side > 0 ? Math.PI : 0);
  const Hp: Vec = [side * 15, hipY];
  let F: Vec = [side * 17, -6];
  let bx = 3;
  if (walking) {
    const lift = Math.max(0, Math.cos(ph));
    F = [side * 15 + stride * Math.sin(ph), -6 - lift * liftH];
    bx = 4 + lift * 14;
  }
  if (sit > 0) {
    F = [F[0] + (side * 26 - F[0]) * sit, F[1] + (-6 - F[1]) * sit];
    bx = bx + (side * 20 - bx) * sit;
  }
  const M: Vec = [(Hp[0] + F[0]) / 2 + bx, (Hp[1] + F[1]) / 2];
  return { Hp, M, F };
}

/** Ve chan que: duong cong tu hong Hp qua diem dieu khien M toi ban chan F. */
export function drawQueLegAt(L: QueLeg, Hp: Vec, M: Vec, F: Vec, stubLen: number) {
  L.stick.setAttribute('d', `M${P(Hp)} Q${P(M)} ${P(F)}`);
  L.foot.setAttribute('transform', `translate(${P([F[0], F[1] + 6])})`);
  const d = `M${P([Hp[0], Hp[1] - 4])} L${P([Hp[0], Hp[1] + stubLen])}`;
  L.stubO.setAttribute('d', d); L.stubI.setAttribute('d', d);
}

/** Dat chan que. hipY: do cao hong (khong gian than), phase: pha buoc (rad), walking: dang di,
 *  sit: 0..1 muc ngoi (dau goi mo ra hai ben), running: buoc dai va nhac chan cao hon. */
export function poseQueLegs(legs: QueLeg[], hipY: number, phase: number, walking: boolean, stubLen: number, sit = 0, running = false) {
  for (const L of legs) {
    const p = queLegPoints(L.side, hipY, phase, walking, sit, running);
    drawQueLegAt(L, p.Hp, p.M, p.F, stubLen);
  }
}

/** Den pin cam tay: than den doc theo cang tay, luong sang hinh non phia truoc. */
export function drawFlashlight(parent: Element, uid: string, withBeam: boolean): { g: SVGGElement } {
  const root = g(parent);
  if (withBeam) {
    const defs = el('defs', {}, root);
    const lg = el('linearGradient', { id: `${uid}-beam`, x1: 0, y1: 0, x2: 0, y2: 1 }, defs);
    el('stop', { offset: 0, 'stop-color': '#fff6cf', 'stop-opacity': 0.55 }, lg);
    el('stop', { offset: 0.55, 'stop-color': '#ffe9a6', 'stop-opacity': 0.18 }, lg);
    el('stop', { offset: 1, 'stop-color': '#ffe9a6', 'stop-opacity': 0 }, lg);
    el('path', { d: 'M-9 34 L-260 900 L260 900 L9 34 Z', fill: `url(#${uid}-beam)` }, root);
  }
  fill(root, 'M-6 -6 L6 -6 L7 22 L-7 22 Z', '#3a3f45', W * 0.6);
  fill(root, 'M-10 22 L10 22 L9 34 L-9 34 Z', shade('#3a3f45', 1.4), W * 0.6);
  return { g: root };
}
