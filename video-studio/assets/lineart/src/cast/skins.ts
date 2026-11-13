// skins.ts: skin theo vai. Nhan vat (khuon mat, dang, mau da, toc, kinh, giong) co dinh trong roster;
// skin la bo do theo vai: trang phuc, mau, mu, do deo, dao cu, kem ten cu chi rieng cua vai.
// Dung chung cho line-art va chibi:  L.add('bac-si-minh', { ..., skin: 'sep' })
//
// Quy tac:
//  - Khong co `skin` thi nhan vat mac bo do khoa trong roster (nhu truoc day).
//  - Skin chi duoc dung cac mau ve da co trong ca hai rig (xem SUPPORTED trong chibi/src/rig.ts).
//    Mau do moi (vest, ao khoac dai...) phai ve them vao ca hai rig truoc, roi moi them skin.
//  - Kinh ('glasses') la dac diem khuon mat nen di theo nhan vat, khong theo skin.
//  - `gestures` dat ten cu chi theo vai, tro ve cu chi co san cua thu vien (wave, point, present, talk, bow, nod).
import type { Spec, Gesture } from './rig.ts';
import { byId } from './roster.ts';

type Outfit = Pick<Spec, 'top' | 'topColor' | 'sleeve' | 'bottom' | 'bottomColor' | 'hat' | 'hatColor' | 'extras' | 'prop' | 'propColor' | 'shoeColor'>;

export interface Skin {
  id: string;
  label: string;
  outfit: Outfit;
  /** Ten cu chi rieng cua vai -> cu chi co san. VD luat-su: 'trinh-ho-so' -> 'present'. */
  gestures?: Record<string, Gesture>;
}

const fromRoster = (id: string, label: string, gestures?: Record<string, Gesture>): Skin => {
  const s = byId(id);
  return {
    id: label, label: s.role,
    outfit: {
      top: s.top, topColor: s.topColor, sleeve: s.sleeve, bottom: s.bottom, bottomColor: s.bottomColor,
      hat: s.hat, hatColor: s.hatColor, extras: (s.extras ?? []).filter((e) => e !== 'glasses'), prop: s.prop, propColor: s.propColor, shoeColor: s.shoeColor,
    },
    gestures,
  };
};

const LIST: Skin[] = [
  // Bo do rieng cho cac vai ngoai dan
  {
    id: 'sep', label: 'Sep / giam doc',
    outfit: { top: 'jacket', topColor: '#2f3441', sleeve: 'long', bottom: 'trousers', bottomColor: '#1f232b', extras: ['tie'], prop: 'none', shoeColor: '#1b1b1b' },
    gestures: { 'ra-lenh': 'point', 'thuyet-phuc': 'present', 'tra-loi': 'talk' },
  },
  {
    id: 'luat-su', label: 'Luat su',
    outfit: { top: 'jacket', topColor: '#3b3f4a', sleeve: 'long', bottom: 'trousers', bottomColor: '#2b2d34', extras: [], prop: 'books', propColor: '#6b4f3a', shoeColor: '#1b1b1b' },
    gestures: { 'trinh-ho-so': 'present', 'phan-tich': 'talk', 'chi-dieu-khoan': 'point' },
  },
  {
    id: 'nhan-vien-van-phong', label: 'Nhan vien van phong',
    outfit: { top: 'shirt', topColor: '#ece6d6', sleeve: 'long', bottom: 'trousers', bottomColor: '#2f3540', extras: ['tie'], prop: 'briefcase' },
  },
  // Bo do theo nghe da co trong dan: ai cung mac duoc
  fromRoster('bac-si-minh', 'bac-si', { 'kham': 'point', 'giai-thich': 'present' }),
  fromRoster('dieu-duong-lan', 'dieu-duong', { 'huong-dan': 'present' }),
  fromRoster('can-bo-thu', 'can-bo-kiem-dich', { 'kiem-tra': 'point', 'huong-dan': 'present' }),
  fromRoster('anh-tuan', 'cong-nhan'),
  fromRoster('anh-khoa', 'hanh-khach'),
];

export const SKINS: Record<string, Skin> = Object.fromEntries(LIST.map((s) => [s.id, s]));

export const skinById = (id: string): Skin => {
  const s = SKINS[id];
  if (!s) throw new Error(`unknown skin ${id} (co: ${Object.keys(SKINS).join(', ')})`);
  return s;
};

/** Tra ve Spec cua nhan vat mac skin: giu nguyen than the, toc, kinh, dang di; thay toan bo bo do. */
export function withSkin(spec: Spec, skinId?: string): Spec {
  if (!skinId) return spec;
  const sk = skinById(skinId);
  const glasses = (spec.extras ?? []).includes('glasses');
  const extras = [...(sk.outfit.extras ?? [])];
  if (glasses && !extras.includes('glasses')) extras.push('glasses');
  return { ...spec, ...sk.outfit, extras };
}

/** Boc act() de goi duoc ten cu chi theo vai. Ten khong co trong skin thi chuyen thang cho thu vien. */
export function applyGestureAliases<T extends { act: (name: any, seconds: any) => void }>(c: T, skinId?: string): T {
  const map = skinId ? skinById(skinId).gestures : undefined;
  if (!map) return c;
  const base = c.act.bind(c);
  (c as { act: (name: string, seconds: number) => void }).act = (name, seconds) => base(map[name] ?? name, seconds);
  return c;
}
