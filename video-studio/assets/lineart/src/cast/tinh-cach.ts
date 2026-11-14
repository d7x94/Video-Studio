// tinh-cach.ts: lop tinh cach (cach dien) cua vai, dung chung cho line-art va chibi.
// Nhan vat (mat, dang, giong) co dinh; skin la trang phuc; tinh cach la cach dien: ten cu chi theo
// tinh huong -> cu chi co san, ten bieu cam theo tinh huong -> net mat co san (chibi), va hai thao tac
// chung noi(giay) / nghe(giay) cho moi nhan vat.
//
// Du lieu tinh cach la JSON (thu vien SKILL/tinh-cach/ va PROJECT/tinh-cach/), inject.py gom lai
// thanh tinh-cach.js dat window.TINH_CACH = { <id>: {...} } truoc khi nap thu vien.
//   L.add('anh-duc', { x, y, skin: 'sep', tinhCach: 'nghiem-khac' })
//   hung.act('ra-lenh', 2)   // -> cu chi co san theo tinh cach
//   hung.noi(2.4)            // chibi: nhep mieng + cu chi 'khi-noi'; line-art: cu chi 'khi-noi' (mac dinh talk)
//   hung.nghe(2)             // chibi: bieu cam 'nghe'; ca hai: cu chi 'khi-nghe' neu co
export const GESTURES = ['wave', 'point', 'present', 'talk', 'bow', 'nod'] as const;
export type Gesture = typeof GESTURES[number];
export const EXPRS = ['neutral', 'happy', 'wink', 'deadpan', 'surprised', 'worried'] as const;
export type Expr = typeof EXPRS[number];

export interface TinhCach {
  id: string; ten: string; mo_ta?: string;
  /** Ten cu chi theo tinh huong -> cu chi co san. Khoa dac biet: 'khi-noi', 'khi-nghe'. */
  cu_chi?: Record<string, Gesture>;
  /** Ten bieu cam theo tinh huong -> net mat co san (chi chibi). Khoa dac biet: 'binh-thuong' (net mat mac dinh), 'nghe'. */
  bieu_cam?: Record<string, Expr>;
}

export function tinhCachById(id: string): TinhCach {
  const all = (globalThis as unknown as { TINH_CACH?: Record<string, TinhCach> }).TINH_CACH ?? {};
  const tc = all[id];
  if (!tc) throw new Error(`khong co tinh cach ${id} (tinh-cach.js co: ${Object.keys(all).join(', ') || 'khong co'}; chay lai inject.py)`);
  return tc;
}

export interface Dien { noi(seconds: number): void; nghe(seconds: number): void }

type Actor = { act: (name: any, seconds: any) => void; expr?: (name: any, seconds?: number) => void;
  say?: (seconds: number) => void; exprBase?: (name: any) => void };

/** Gan tinh cach vao nhan vat: doi ten cu chi, ten bieu cam, va them noi()/nghe(). Khong co tinh cach van co noi()/nghe() mac dinh. */
export function applyTinhCach<T extends Actor>(c: T, id?: string): T & Dien {
  const tc = id ? tinhCachById(id) : undefined;
  const cc = tc?.cu_chi ?? {}, bc = tc?.bieu_cam ?? {};
  const act = c.act.bind(c);
  (c as Actor).act = (name: string, seconds: number) => act(cc[name] ?? name, seconds);
  if (c.expr) {
    const expr = c.expr.bind(c);
    (c as Actor).expr = (name: string, seconds?: number) => expr(bc[name] ?? name, seconds);
    if (bc['binh-thuong'] && c.exprBase) c.exprBase(bc['binh-thuong']);
  }
  const d = c as T & Dien;
  d.noi = (s) => {
    if (c.say) { c.say(s); if (cc['khi-noi']) act(cc['khi-noi'], s); }
    else act(cc['khi-noi'] ?? 'talk', s);
  };
  d.nghe = (s) => {
    if (bc['nghe'] && c.expr) (c as Actor).expr!(bc['nghe'], s);
    if (cc['khi-nghe']) act(cc['khi-nghe'], Math.min(s, 1.6));
  };
  return d;
}
