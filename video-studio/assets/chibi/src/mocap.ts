// mocap.ts: phat clip chuyen dong that (CMU mocap, xem tools/mocap) tren tay chan que.
// Moi clip la day khung 20 so (xem tools/mocap/bvh2que.py): tay sau, tay truoc (khuyu, ban tay tinh tu vai),
// chan trai, chan phai (goi, ban chan tinh tu hong), dx dy cua hong, nghieng than x10, cui ve truoc.
// Tu the la ham thuan cua thoi gian tinh tu luc bat dau clip (noi suy tuyen tinh giua hai khung).
import { MOCAP, MOCAP_STRIDE } from './mocap-clips.ts';

export const MOCAP_IDS = Object.keys(MOCAP);

/** Do dai clip (giay). Clip khong co thi tra ve 0. */
export function clipLength(id: string): number {
  const c = MOCAP[id];
  return c ? (c.n - 1) / c.fps : 0;
}

export function hasClip(id: string): boolean { return id in MOCAP; }

const cache: Record<string, number[]> = {};
const data = (id: string) => cache[id] ??= MOCAP[id].d.split(',').map(Number);

/** Lay mau clip tai giay k tinh tu dau clip. Clip lap thi quay vong, khong lap thi giu khung cuoi. */
export function sampleClip(id: string, k: number, out: number[]): number[] {
  const c = MOCAP[id], d = data(id);
  const S = MOCAP_STRIDE;
  let u = Math.max(0, k) * c.fps;
  if (c.loop) u = u % (c.n - 1);
  else u = Math.min(u, c.n - 1);
  const i = Math.floor(u), j = Math.min(i + 1, c.n - 1), a = u - i;
  for (let q = 0; q < S; q++) out[q] = d[i * S + q] * (1 - a) + d[j * S + q] * a;
  return out;
}
