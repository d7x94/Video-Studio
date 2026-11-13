// vetay.js: canh "ve tay" (whiteboard animation) cho HyperFrames.
// Moi canh la mot buc tranh (anh nguoi dung tao, da chuan bi bang scripts/ve_tay_anh.py)
// hien dan theo vet co, co ban tay cam but chay theo dau vet. Hai luot: phac chi (anh -sketch)
// roi to mau (anh mau). Do hoa ban tay, giay va vet co deu do studio tu ve bang code.
//
// Tat dinh: moi thu chi phu thuoc t; khong Math.random, khong Date.now.
// API:
//   const V = VT.createStage(svg, { width, height });
//   V.scene("s01", { start: T.s01, color: "img/s01.jpg", sketch: "img/s01-sketch.jpg" });
//   ... trong render(t): V.render(t);

const NS = "http://www.w3.org/2000/svg";

function el(tag, attrs, parent) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}

// So gia ngau nhien co hat giong (mulberry32): cung seed thi cung vet co moi lan render
function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const ease = (p) => (p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2);

// Vet co zig-zag phu kin hop [x, y, w, h]: cac hang ngang di qua lai, co gon song,
// dau hang lech ngau nhien de mep tranh khong thang.
export function scribble(box, rows, seed, jitter = 0.35) {
  const [x, y, w, h] = box;
  const r = rng(seed);
  const rh = h / rows;
  const pts = [];
  const step = 36;
  for (let i = 0; i < rows; i++) {
    const cy = y + rh * (i + 0.5);
    const ltr = i % 2 === 0;
    const x0 = x - rh * 0.2 + r() * rh * 0.5;
    const x1 = x + w + rh * 0.2 - r() * rh * 0.5;
    const n = Math.max(2, Math.round((x1 - x0) / step));
    const ph = r() * Math.PI * 2;
    const amp = rh * jitter;
    const freq = 1.5 + r() * 2;
    for (let k = 0; k <= n; k++) {
      const u = ltr ? k / n : 1 - k / n;
      const px = x0 + (x1 - x0) * u;
      const py = cy + amp * Math.sin(ph + u * Math.PI * 2 * freq) + (r() - 0.5) * rh * 0.12;
      pts.push([px, py]);
    }
  }
  return "M" + pts.map((p) => p[0].toFixed(1) + " " + p[1].toFixed(1)).join(" L");
}

// Ban tay phai cam but, ve bang SVG. Goc toa do = dau ngoi but; tay nam phia duoi ben phai.
// Ngon tay ve bang "khuc xuc xich": net vien dam roi net mau da mong hon chong len.
const SKIN = "#f1c7a1", SKIN_D = "#d9a27c", INK = "#3b2620";
function finger(g, pts, w) {
  const d = "M" + pts.map((q) => q.join(" ")).join(" L");
  el("path", { d, fill: "none", stroke: INK, "stroke-width": w + 9, "stroke-linecap": "round", "stroke-linejoin": "round" }, g);
  el("path", { d, fill: "none", stroke: SKIN, "stroke-width": w, "stroke-linecap": "round", "stroke-linejoin": "round" }, g);
}
function drawHand(g) {
  const o = { stroke: INK, "stroke-width": 4.5, "stroke-linejoin": "round" };
  // Ong tay ao va co tay ao
  el("path", Object.assign({ d: "M212 300 L560 560 L660 430 L282 222 Z", fill: "#fbfaf6" }, o), g);
  el("path", Object.assign({ d: "M206 296 L278 216 L312 236 L238 322 Z", fill: "#e6e1d4" }, o), g);
  // Ngon cai (phia duoi but)
  finger(g, [[150, 178], [98, 150], [44, 94]], 30);
  // Long ban tay
  el("path", Object.assign({ d: "M114 116 C150 94 214 110 252 160 C282 202 272 262 232 292 C192 320 140 302 120 262 C100 222 94 152 114 116 Z", fill: SKIN }, o), g);
  // Ngon giua, ap ut cuon vao long tay
  finger(g, [[208, 272], [180, 274]], 24);
  finger(g, [[188, 248], [152, 242]], 28);
  finger(g, [[168, 220], [124, 202]], 30);
  // But: dau ngoi, than but
  el("path", Object.assign({ d: "M0 0 L21.5 17.2 L6.3 26.8 Z", fill: "#e8dcc4" }, o), g);
  el("path", { d: "M0 0 L7 5.6 L2 8.8 Z", fill: INK }, g);
  el("path", Object.assign({ d: "M21.5 17.2 L138.4 202.2 L123.2 211.8 L6.3 26.8 Z", fill: "#4f6d8f" }, o), g);
  el("path", { d: "M17 22 L131 205", stroke: "#86a3c2", "stroke-width": 4, "stroke-linecap": "round" }, g);
  // Ngon tro nam doc tren than but
  finger(g, [[170, 140], [116, 124], [44, 46]], 30);
  el("ellipse", { cx: 46, cy: 44, rx: 9, ry: 6, transform: "rotate(57 46 44)", fill: "#f7dcc4", stroke: SKIN_D, "stroke-width": 2.5 }, g);
  // Nep gap khop tay
  el("path", { d: "M84 98 C90 92 98 92 102 98", fill: "none", stroke: SKIN_D, "stroke-width": 3.5, "stroke-linecap": "round" }, g);
  el("path", { d: "M196 170 C214 182 230 184 244 178", fill: "none", stroke: SKIN_D, "stroke-width": 4, "stroke-linecap": "round" }, g);
}

export function createStage(svg, opts = {}) {
  const W = opts.width || 1920, H = opts.height || 1080;
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  const defs = el("defs", {}, svg);
  const layer = el("g", {}, svg);
  const handG = el("g", { opacity: 0 }, svg);
  const handScale = opts.handScale || (Math.min(W, H) / 1080) * 1.2;
  const hand = el("g", {}, handG);
  drawHand(hand);
  const scenes = [];
  let uid = 0;

  function scene(id, o) {
    const s = Object.assign({
      start: 0, end: null, delay: 0.25, draw: null, sketchShare: 0.42,
      margin: 0.045, rows: null, seed: 7 + uid * 13, zoom: 0.035, fadeOut: 0.45,
      hand: true,
    }, o, { id });
    const m = s.margin;
    s.box = s.box || [W * m, H * m, W * (1 - 2 * m), H * (1 - 2 * m)];
    const rowsA = s.rows || Math.max(4, Math.round(s.box[3] / (H > W ? 210 : 170)));
    const rowsB = rowsA + 1;
    const g = el("g", { opacity: 0 }, layer);
    const mk = (rows, seed) => {
      const mid = `vt-m${uid++}`;
      const mask = el("mask", { id: mid, maskUnits: "userSpaceOnUse", x: 0, y: 0, width: W, height: H }, defs);
      const p = el("path", {
        d: scribble(s.box, rows, seed), fill: "none", stroke: "#fff",
        "stroke-width": ((s.box[3] / rows) * 1.6).toFixed(1), "stroke-linecap": "round", "stroke-linejoin": "round",
      }, mask);
      const len = p.getTotalLength();
      p.setAttribute("stroke-dasharray", `${len} ${len}`);
      p.setAttribute("stroke-dashoffset", len);
      return { mid, p, len };
    };
    s.A = s.sketch ? mk(rowsA, s.seed) : null;
    s.B = mk(rowsB, s.seed + 101);
    if (s.sketch) s.imA = el("image", { href: s.sketch, x: 0, y: 0, width: W, height: H, preserveAspectRatio: "xMidYMid slice", mask: `url(#${s.A.mid})` }, g);
    s.imB = el("image", { href: s.color, x: 0, y: 0, width: W, height: H, preserveAspectRatio: "xMidYMid slice", mask: `url(#${s.B.mid})` }, g);
    s.g = g;
    scenes.push(s);
    return s;
  }

  // Thoi diem: mac dinh moi canh ket thuc khi canh sau bat dau
  function finalize() {
    scenes.sort((a, b) => a.start - b.start);
    scenes.forEach((s, i) => {
      if (s.end == null) s.end = i + 1 < scenes.length ? scenes[i + 1].start : (opts.duration || s.start + 8);
      const life = s.end - s.start;
      if (s.draw == null) s.draw = clamp(life * 0.62, 2.2, 5.5);
    });
    finalize.done = true;
  }

  // Vi tri diem tren vet co, doi qua phong to cua canh
  function at(s, pass, p, z) {
    const pt = pass.p.getPointAtLength(pass.len * p);
    return [W / 2 + (pt.x - W / 2) * z, H / 2 + (pt.y - H / 2) * z];
  }

  function render(t) {
    if (!finalize.done) finalize();
    let handPos = null, handAlpha = 0;
    for (const s of scenes) {
      const vis = t >= s.start - 0.001 && t < s.end + s.fadeOut;
      if (!vis) { s.g.setAttribute("opacity", 0); continue; }
      const out = t > s.end ? 1 - (t - s.end) / s.fadeOut : 1;
      s.g.setAttribute("opacity", clamp(out, 0, 1).toFixed(3));
      const life = s.end - s.start;
      const z = 1 + s.zoom * ease(clamp((t - s.start) / Math.max(life, 0.1), 0, 1));
      s.g.setAttribute("transform", `translate(${(W / 2) * (1 - z)} ${(H / 2) * (1 - z)}) scale(${z})`);
      const p = clamp((t - s.start - s.delay) / s.draw, 0, 1);
      const share = s.A ? s.sketchShare : 0;
      const pa = share ? clamp(p / share, 0, 1) : 1;
      const pb = clamp((p - share) / (1 - share), 0, 1);
      if (s.A) {
        s.A.p.setAttribute("stroke-dashoffset", (s.A.len * (1 - pa)).toFixed(1));
        s.imA.setAttribute("opacity", pb >= 1 || pa <= 0 ? 0 : 1);
      }
      s.B.p.setAttribute("stroke-dashoffset", (s.B.len * (1 - pb)).toFixed(1));
      s.imB.setAttribute("opacity", pb <= 0 ? 0 : 1);   // tien do 0: dau net tron van ve mot cham
      if (!s.hand || t > s.end) continue;
      // Ban tay: hien khi bat dau ve, roi khung sau khi ve xong
      const t0 = s.start + s.delay, t1 = t0 + s.draw;
      if (t < t0 - 0.2) continue;
      if (t <= t1) {
        const pos = s.A && pa < 1 ? at(s, s.A, Math.max(pa, 0.0005), z) : at(s, s.B, Math.max(pb, 0.0005), z);
        handPos = pos;
        handAlpha = clamp((t - (t0 - 0.2)) / 0.2, 0, 1);
      } else if (t <= t1 + 0.6) {
        const e = ease((t - t1) / 0.6);
        const end = at(s, s.B, 1, z);
        handPos = [end[0] + (W * 1.05 - end[0]) * e, end[1] + (H * 1.15 - end[1]) * e];
        handAlpha = 1;
      }
    }
    if (handPos) {
      handG.setAttribute("opacity", handAlpha.toFixed(3));
      hand.setAttribute("transform", `translate(${handPos[0].toFixed(1)} ${handPos[1].toFixed(1)}) scale(${handScale.toFixed(3)})`);
    } else {
      handG.setAttribute("opacity", 0);
    }
  }

  return { scene, render, W, H };
}
