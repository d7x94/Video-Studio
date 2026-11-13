// sim3d.js: thu vien dung canh 3D kieu "nha bup be" cho HyperFrames.
// Moi ham ve hinh chi phu thuoc thoi gian t (giay tinh tu dau video), khong dung
// Math.random, Date.now hay vong lap requestAnimationFrame: render tua tung khung
// hinh nen moi khung phai tinh lai duoc tu t.
//
// Quy uoc truc: Y huong len; nhan vat nhin theo +Z khi rotation.y = 0;
// goc nhin theo huong (dx, dz) la Math.atan2(dx, dz).
// Kiem chung voi bo Quaternius Ultimate Animated Character Pack (xuong 23 khop,
// ten xuong sau khi Three.js lam sach: UpperArmR, LowerArmR, UpperArmL, Head...).
import * as THREE from "three";
import { GLTFLoader } from "./jsm/loaders/GLTFLoader.js";

export { THREE };

// ---------- tien ich thoi gian ----------
export const clamp01 = x => (x < 0 ? 0 : x > 1 ? 1 : x);
export const ease = x => (1 - Math.cos(Math.PI * clamp01(x))) / 2;
export const smooth = x => { x = clamp01(x); return x * x * (3 - 2 * x); };
/** 0 ngoai [t0,t1], len 1 o giua theo hinh sin: dung cho dong tac mot lan (vay, chi). */
export const pulse = (t, t0, t1) => (t > t0 && t < t1 ? Math.sin(Math.PI * (t - t0) / (t1 - t0)) : 0);

// ---------- san khau ----------
export function createStage(canvas, { width, height, background = 0xf3e6d3, shadows = true } = {}) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(1);
  renderer.setSize(width, height, false);
  renderer.shadowMap.enabled = shadows;
  renderer.shadowMap.type = THREE.PCFShadowMap;
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(background);
  const camera = new THREE.PerspectiveCamera(width < height ? 32 : 28, width / height, 0.1, 100);
  scene.add(new THREE.HemisphereLight(0xfff4e0, 0x8a7a66, 1.8));
  const sun = new THREE.DirectionalLight(0xffffff, 2.0);
  sun.position.set(5, 9, 6);
  sun.castShadow = shadows;
  sun.shadow.mapSize.set(1024, 1024);
  Object.assign(sun.shadow.camera, { left: -6, right: 6, top: 6, bottom: -6 });
  scene.add(sun);
  const stage = { renderer, scene, camera, chars: [], render: () => renderer.render(scene, camera) };
  return stage;
}

const toon = c => new THREE.MeshToonMaterial({ color: c });
export function box(w, h, d, color) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), toon(color));
  m.castShadow = m.receiveShadow = true;
  return m;
}
export function cyl(rt, rb, h, color, seg = 10) {
  const m = new THREE.Mesh(new THREE.CylinderGeometry(rt, rb, h, seg), toon(color));
  m.castShadow = m.receiveShadow = true;
  return m;
}
const put = (scene, m, x, y, z) => { m.position.set(x, y, z); scene.add(m); return m; };

// ---------- phong mau (7 x 7, tuong sau o z = -3.5, tuong trai o x = -3.5) ----------
function shell(scene, { floor, plank, back, left }) {
  put(scene, box(7, 0.2, 7, floor), 0, -0.1, 0);
  if (plank) for (let i = 0; i < 7; i++) put(scene, box(0.02, 0.201, 7, plank), -3.5 + i, -0.1, 0);
  put(scene, box(7, 3.2, 0.2, back), 0, 1.6, -3.5);
  put(scene, box(0.2, 3.2, 7, left), -3.5, 1.6, 0);
}
export const ROOMS = {
  /** Phong khach gia dinh: sofa, cua so, chau cay, xo nuoc dong. */
  nha(scene) {
    shell(scene, { floor: 0xd9b38c, plank: 0xc49a6c, back: 0x9ed2c6, left: 0x7fb7be });
    put(scene, box(1.8, 1.2, 0.05, 0xdff6ff), 1.2, 1.9, -3.38);
    const sofa = new THREE.Group();
    sofa.add(box(2.4, 0.5, 0.9, 0xe76f51));
    const b = box(2.4, 0.8, 0.25, 0xe76f51); b.position.set(0, 0.55, -0.35); sofa.add(b);
    put(scene, sofa, -1.6, 0.25, -2.6);
    put(scene, cyl(0.25, 0.2, 0.45, 0xb5651d, 8), 2.8, 0.22, -2.8);
    const bush = new THREE.Mesh(new THREE.IcosahedronGeometry(0.5, 0), toon(0x2a9d8f)); bush.castShadow = true;
    put(scene, bush, 2.8, 0.85, -2.8);
    const bucket = put(scene, cyl(0.35, 0.3, 0.4, 0x457b9d), 2.0, 0.2, 1.2);
    const water = new THREE.Mesh(new THREE.CircleGeometry(0.32, 10), toon(0x8ecae6));
    water.rotation.x = -Math.PI / 2; put(scene, water, 2.0, 0.41, 1.2);
    return { bucket, water, sofa };
  },
  /** Phong kham: ban kham, ghe, giuong benh, tu thuoc co chu thap. */
  "phong-kham"(scene) {
    shell(scene, { floor: 0xdfe7ea, plank: null, back: 0xf4f7f6, left: 0xcfe8e4 });
    const desk = new THREE.Group();
    desk.add(box(1.6, 0.08, 0.8, 0xc8a27a));
    for (const [x, z] of [[-0.72, -0.32], [0.72, -0.32], [-0.72, 0.32], [0.72, 0.32]]) { const l = box(0.06, 0.72, 0.06, 0x8d6e52); l.position.set(x, -0.4, z); desk.add(l); }
    put(scene, desk, 1.3, 0.76, -1.6);
    put(scene, box(0.5, 0.45, 0.5, 0x3d5a80), 1.3, 0.225, -0.9);   // ghe don
    const bed = new THREE.Group();
    bed.add(box(2.0, 0.5, 0.9, 0xffffff));
    const pil = box(0.5, 0.12, 0.7, 0xa8dadc); pil.position.set(-0.7, 0.31, 0); bed.add(pil);
    put(scene, bed, -2.2, 0.3, -2.7);
    const cab = put(scene, box(1.0, 1.8, 0.45, 0xffffff), 2.6, 0.9, -3.15);
    put(scene, box(0.36, 0.1, 0.02, 0xe63946), 2.6, 1.45, -2.91);
    put(scene, box(0.1, 0.36, 0.02, 0xe63946), 2.6, 1.45, -2.91);
    put(scene, box(1.4, 1.0, 0.04, 0xa8dadc), -0.4, 2.0, -3.38);
    return { desk, bed, cabinet: cab };
  },
  /** Khu kiem dich cua khau: quay kiem tra co vach kinh, cot day chan, bang chi dan. */
  "cua-khau"(scene) {
    shell(scene, { floor: 0xbfc5c9, plank: 0xadb4b8, back: 0xe9eef0, left: 0xd6dde0 });
    const counter = new THREE.Group();
    counter.add(box(2.6, 1.05, 0.7, 0x1d3557));
    const top = box(2.7, 0.06, 0.8, 0xf1faee); top.position.y = 0.55; counter.add(top);
    const glass = new THREE.Mesh(new THREE.BoxGeometry(2.6, 0.7, 0.03), new THREE.MeshStandardMaterial({ color: 0xbde0fe, transparent: true, opacity: 0.35 }));
    glass.position.set(0, 0.95, 0.1); counter.add(glass);
    put(scene, counter, 0.9, 0.52, -2.2);
    for (const x of [-2.4, -1.2, 0.0]) {
      put(scene, cyl(0.05, 0.05, 0.95, 0x6c757d, 8), x, 0.47, 0.6);
      put(scene, cyl(0.18, 0.18, 0.05, 0x6c757d, 12), x, 0.02, 0.6);
    }
    const belt1 = put(scene, box(1.15, 0.06, 0.02, 0xe63946), -1.8, 0.85, 0.6);
    const belt2 = put(scene, box(1.15, 0.06, 0.02, 0xe63946), -0.6, 0.85, 0.6);
    const sign = put(scene, box(2.2, 0.6, 0.05, 0x2a9d8f), 0.9, 2.5, -3.36);
    return { counter, sign, belts: [belt1, belt2] };
  },
};
export function buildRoom(stage, name) {
  const fn = ROOMS[name];
  if (!fn) throw new Error(`Khong co phong "${name}". Co: ${Object.keys(ROOMS).join(", ")}`);
  stage.props = fn(stage.scene);
  return stage.props;
}

// ---------- nhan vat ----------
export const SKIN = { sang: 0xf1c27d, vua: 0xe0ac69, ngam: 0xc68642, nau: 0x8d5524 };
const loader = new GLTFLoader();

/**
 * Nap nhan vat, doi mau theo ten vat lieu, chuan hoa chieu cao.
 * colors: { TenVatLieu: 0xRRGGBB } (vd { Shirt: 0x2a9d8f }); "Skin" va "Face" (mat) co tham so rieng.
 */
export async function loadChar(stage, file, { height = 1.65, skin = SKIN.sang, eyes = 0x2b1d14, colors = {} } = {}) {
  const g = await loader.loadAsync("assets/" + file);
  const root = g.scene;
  const materials = new Set();
  root.traverse(o => {
    if (!o.isMesh) return;
    o.castShadow = true;
    (Array.isArray(o.material) ? o.material : [o.material]).forEach(m => {
      materials.add(m.name);
      m.metalness = 0; m.roughness = 0.85;
      if (m.name === "Skin") m.color.setHex(skin);
      if (m.name === "Face") m.color.setHex(eyes);
      if (colors[m.name] !== undefined) m.color.setHex(colors[m.name]);
    });
  });
  const bb = new THREE.Box3().setFromObject(root);
  root.scale.setScalar(height / (bb.max.y - bb.min.y));
  const mixer = new THREE.AnimationMixer(root);
  const act = {};
  for (const c of g.animations) { const a = mixer.clipAction(c); a.play(); a.setEffectiveWeight(0); act[c.name] = a; }
  const bone = n => root.getObjectByName(n);
  stage.scene.add(root);
  const ch = { root, mixer, act, materials: [...materials], clips: Object.keys(act),
    head: bone("Head"), armR: bone("UpperArmR"), foreR: bone("LowerArmR"), armL: bone("UpperArmL"), foreL: bone("LowerArmL"), torso: bone("Torso") };
  stage.chars.push(ch);
  return ch;
}

/** Dat vi tri va huong (goc, radian) cho nhan vat. */
export function place(ch, x, z, angle = 0) { ch.root.position.set(x, 0, z); ch.root.rotation.y = angle; }
/** Goc de nhan vat o (x,z) nhin ve diem (tx,tz). */
export const angleTo = (x, z, tx, tz) => Math.atan2(tx - x, tz - z);

const LOOPING = new Set(["Idle", "Walk", "Run", "Walk_Carry", "Run_Carry"]);

/**
 * Tron hoat anh co san theo ke hoach [[ten clip, bat dau, ket thuc], ...], chuyen tiep 0,3 s.
 * Clip hay dung: Idle, Walk, Run, SitDown, StandUp, PickUp, Victory, Walk_Carry, Jump.
 */
export function animate(ch, plan, t, { blend = 0.3 } = {}) {
  const w = {}, tm = {};
  for (const [n, a, b] of plan) {
    if (!ch.act[n]) throw new Error(`Nhan vat khong co clip "${n}". Co: ${ch.clips.join(", ")}`);
    if (t < a - blend || t > b + blend) continue;
    const k = smooth((t - a + blend) / blend) * smooth((b + blend - t) / blend);
    if (k > (w[n] || 0)) { w[n] = k; tm[n] = Math.max(0, t - a); }
  }
  for (const n in ch.act) {
    const a = ch.act[n], d = a.getClip().duration, local = tm[n] || 0;
    a.setEffectiveWeight(w[n] || 0);
    // Clip lap (dung, di, chay) quay vong; clip mot lan (ngoi xuong, nhat do...) dung o khung cuoi
    a.time = LOOPING.has(n) ? local % d : Math.min(local, d - 1e-3);
  }
  ch.mixer.update(0);
}

/** Thoi gian quay nguoi sau khi di xong. Dong tac huong ve khan gia (vay, chi, noi)
 *  nen bat dau tu t1 + TURN tro di, neu khong nhan vat se lam dong tac khi dang quay lung. */
export const TURN = 0.6;

/**
 * Di chuyen tu `from` den `to` ([x, z]) trong [t0, t1], quay mat theo huong di;
 * sau khi den noi quay dan sang goc `endAngle` (mac dinh giu huong di).
 * Tra ve true khi dang di (dung de chon clip Walk).
 *
 * MOI NHAN VAT CHI GOI walk MOT LAN moi khung hinh: ham dat vi tri o moi thoi diem t
 * (truoc t0 thi dung o `from`), nen lan goi sau se ghi de lan goi truoc. Nhan vat di
 * nhieu chang thi truyen MANG cac chang theo thu tu thoi gian:
 *   S.walk(doc, [{ from, to, t0, t1, endAngle }, { from, to, t0, t1, endAngle }], t)
 * Truoc chang dau nhan vat dung o `from` cua chang dau; giua hai chang thi dung o `to`
 * cua chang truoc. `from` cua chang sau nen trung `to` cua chang truoc.
 */
export function walk(ch, spec, t) {
  let leg = spec;
  if (Array.isArray(spec)) {
    if (!spec.length) throw new Error("walk: mang chang rong");
    leg = spec[0];
    for (const l of spec) if (t >= l.t0) leg = l;
  }
  const { from, to, t0, t1, endAngle } = leg;
  const k = ease((t - t0) / (t1 - t0));
  const x = from[0] + (to[0] - from[0]) * k, z = from[1] + (to[1] - from[1]) * k;
  const heading = angleTo(from[0], from[1], to[0], to[1]);
  ch.root.position.set(x, 0, z);
  if (t < t1) { ch.root.rotation.y = heading; return t >= t0; }
  const turn = ease((t - t1) / TURN);
  const target = endAngle === undefined ? heading : endAngle;
  let d = target - heading; while (d > Math.PI) d -= 2 * Math.PI; while (d < -Math.PI) d += 2 * Math.PI;
  ch.root.rotation.y = heading + d * turn;
  return false;
}

// ---------- dong tac them bang code (goi SAU animate) ----------
const qq = new THREE.Quaternion();
const AX = { X: new THREE.Vector3(1, 0, 0), Y: new THREE.Vector3(0, 1, 0), Z: new THREE.Vector3(0, 0, 1) };
export const addRot = (b, axis, ang) => { if (b && ang) b.quaternion.multiply(qq.setFromAxisAngle(AX[axis], ang)); };

/** Vay tay phai trong [t0, t1]. */
export function wave(ch, t, t0, t1) {
  const w = pulse(t, t0, t1);
  addRot(ch.armR, "X", w * 2.2); addRot(ch.armR, "Z", -w * 0.9);
  addRot(ch.foreR, "X", w * (0.6 + Math.sin(t * 14) * 0.45));
}
/** Dua tay phai ra ngang chi ve mot ben trong [t0, t1]. */
export function point(ch, t, t0, t1) {
  const w = smooth((t - t0) / 0.35) * smooth((t1 - t) / 0.35);
  addRot(ch.armR, "X", w * 1.35); addRot(ch.foreR, "X", w * 0.15);
}
/** Noi: gat dau theo am luong loi doc, tay trai dien ta nhe; chi trong [t0, t1]. */
export function talk(ch, t, t0, t1, speech = speechAt) {
  if (t < t0 || t > t1) return;
  const e = speech(t);
  addRot(ch.head, "X", e * 0.18);
  addRot(ch.armL, "X", Math.max(0, Math.sin((t - t0) * 1.3)) * 0.4);
}
/** Lang nghe: gat gu nhe. */
export function listen(ch, t, t0 = 0, t1 = 1e9, phase = 0) {
  if (t < t0 || t > t1) return;
  addRot(ch.head, "X", Math.max(0, Math.sin(t * 2.2 + phase)) * 0.12);
}

// ---------- loi doc ----------
/** Am luong loi doc (0..1) tai thoi diem t, tu speech.js do inject.py sinh. */
export function speechAt(t) {
  const S = window.SPEECH;
  if (!S) return 0;
  const f = Math.floor(t * S.fps);
  return f >= 0 && f < S.env.length ? S.env[f] : 0;
}

// ---------- camera ----------
/**
 * Camera di qua cac "canh may": [{ t, pos: [x,y,z], look: [x,y,z] }, ...] (t tang dan).
 * Giua hai canh may thi noi suy mem; truoc canh dau va sau canh cuoi thi dung yen.
 */
export function cameraPath(camera, shots, t) {
  let a = shots[0], b = shots[shots.length - 1];
  for (let i = 0; i < shots.length - 1; i++) if (t >= shots[i].t && t <= shots[i + 1].t) { a = shots[i]; b = shots[i + 1]; break; }
  if (t <= shots[0].t) b = a = shots[0];
  if (t >= shots[shots.length - 1].t) a = b = shots[shots.length - 1];
  const k = a === b ? 0 : ease((t - a.t) / (b.t - a.t));
  const L = (u, v) => u.map((x, i) => x + (v[i] - x) * k);
  camera.position.set(...L(a.pos, b.pos));
  camera.lookAt(...L(a.look, b.look));
}
