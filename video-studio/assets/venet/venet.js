// venet.js: canh "ve net" (whiteboard animation net that) cho HyperFrames.
// Moi canh la mot to giay: but ve tung net mot (duong thang, vong tron, tia sang, net gach cheo, chu viet ra),
// ban tay cam but chay theo dau net. Khong can anh: moi thu la net SVG do studio tu ve bang code,
// nen ap dung duoc cho moi chu de.
//
// Tat dinh: moi thu chi phu thuoc t; khong Math.random, khong Date.now (do nhieu dung hat giong).
// API (xem references/ve-net.md):
//   const V = VN.createStage(svg, { width, height, duration });
//   const S = V.scene("s01", { start: T.s01, space: V.pick([1000, 1000], [1600, 1000]) });
//   S.text("Vi sao co ngay dem?", 500, 80, { size: 64, anchor: "middle" });
//   S.sun(300, 320, 70, { color: "orange" });
//   ... trong render(t): V.render(t);
// Toa do trong canh la "khong gian thiet ke" (mac dinh 1000 x 1000), tu co vao vung an toan cua khung hinh.

const NS = "http://www.w3.org/2000/svg";

function el(tag, attrs, parent) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}

// So gia ngau nhien co hat giong (mulberry32): cung seed thi cung net ve moi lan render
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
const f1 = (v) => (Math.round(v * 10) / 10).toString();

// Bang mau but: ten ngan hoac ma CSS bat ky
export const COLORS = {
  ink: "#2a2320", red: "#c8432b", orange: "#e8912d", blue: "#2f6fa8",
  green: "#3f8f5a", yellow: "#f4c542", gray: "#8a847c", pink: "#d9667f", mark: "#ffe27a",
};
const col = (c) => COLORS[c] || c || COLORS.ink;

// ---------------------------------------------------------------- hinh phang cho net gach cheo
// Da giac loi (convex): hatch() chi dung duoc voi da giac loi.
export const poly = {
  // part: "bottom" | "top" | "left" | "right" de lay nua hinh tron
  circle(cx, cy, r, part) {
    const arc = { bottom: [0, Math.PI], top: [Math.PI, 2 * Math.PI], left: [Math.PI / 2, 1.5 * Math.PI], right: [-Math.PI / 2, Math.PI / 2] }[part];
    const full = !arc;
    const a0 = full ? 0 : arc[0], a1 = full ? 2 * Math.PI : arc[1];
    const steps = full ? 64 : 32;
    const pts = [];
    for (let i = 0; i < (full ? steps : steps + 1); i++) {
      const a = a0 + ((a1 - a0) * i) / steps;
      pts.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]);
    }
    return pts;
  },
  ellipse(cx, cy, rx, ry) {
    return Array.from({ length: 64 }, (_, i) => {
      const a = (i / 64) * 2 * Math.PI;
      return [cx + rx * Math.cos(a), cy + ry * Math.sin(a)];
    });
  },
  rect(x, y, w, h) { return [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]; },
};

// Net gach cheo phu da giac loi: cac net song song, ve lan luot (net le di len, net chan di xuong), hoi lech de giong tay ve
function hatchPath(pts, deg, gap, rand, inset) {
  const th = (deg * Math.PI) / 180;
  const d = [Math.cos(th), -Math.sin(th)];
  const n = [Math.sin(th), Math.cos(th)];
  const dot = (p, v) => p[0] * v[0] + p[1] * v[1];
  let smin = Infinity, smax = -Infinity;
  for (const p of pts) { const s = dot(p, n); smin = Math.min(smin, s); smax = Math.max(smax, s); }
  const segs = [];
  let flip = false;
  for (let s = smin + gap * 0.5; s < smax; s += gap) {
    const ts = [];
    for (let i = 0; i < pts.length; i++) {
      const a = pts[i], b = pts[(i + 1) % pts.length];
      const sa = dot(a, n) - s, sb = dot(b, n) - s;
      if ((sa < 0 && sb >= 0) || (sb < 0 && sa >= 0)) {
        const u = sa / (sa - sb);
        ts.push(dot([a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u], d));
      }
    }
    if (ts.length < 2) continue;
    const t0 = Math.min(...ts) + inset, t1 = Math.max(...ts) - inset;
    if (t1 <= t0) continue;
    const j = () => (rand() - 0.5) * gap * 0.16;
    const P = (t) => [n[0] * s + d[0] * t + j(), n[1] * s + d[1] * t + j()];
    const a = P(t0), b = P(t1);
    segs.push(flip ? [b, a] : [a, b]);
    flip = !flip;
  }
  return segs.map((sg) => `M${f1(sg[0][0])} ${f1(sg[0][1])} L${f1(sg[1][0])} ${f1(sg[1][1])}`).join(" ");
}

// ---------------------------------------------------------------- ban tay cam but
// Goc toa do = dau ngoi but; tay nam phia duoi ben phai. (Cung hinh ban tay voi vetay.js)
const SKIN = "#f1c7a1", SKIN_D = "#d9a27c", INK = "#3b2620";
function finger(g, pts, w) {
  const d = "M" + pts.map((q) => q.join(" ")).join(" L");
  el("path", { d, fill: "none", stroke: INK, "stroke-width": w + 9, "stroke-linecap": "round", "stroke-linejoin": "round" }, g);
  el("path", { d, fill: "none", stroke: SKIN, "stroke-width": w, "stroke-linecap": "round", "stroke-linejoin": "round" }, g);
}
function drawHand(g) {
  const o = { stroke: INK, "stroke-width": 4.5, "stroke-linejoin": "round" };
  el("path", Object.assign({ d: "M212 300 L560 560 L660 430 L282 222 Z", fill: "#fbfaf6" }, o), g);
  el("path", Object.assign({ d: "M206 296 L278 216 L312 236 L238 322 Z", fill: "#e6e1d4" }, o), g);
  finger(g, [[150, 178], [98, 150], [44, 94]], 30);
  el("path", Object.assign({ d: "M114 116 C150 94 214 110 252 160 C282 202 272 262 232 292 C192 320 140 302 120 262 C100 222 94 152 114 116 Z", fill: SKIN }, o), g);
  finger(g, [[208, 272], [180, 274]], 24);
  finger(g, [[188, 248], [152, 242]], 28);
  finger(g, [[168, 220], [124, 202]], 30);
  el("path", Object.assign({ d: "M0 0 L21.5 17.2 L6.3 26.8 Z", fill: "#e8dcc4" }, o), g);
  el("path", { d: "M0 0 L7 5.6 L2 8.8 Z", fill: INK }, g);
  el("path", Object.assign({ d: "M21.5 17.2 L138.4 202.2 L123.2 211.8 L6.3 26.8 Z", fill: "#4f6d8f" }, o), g);
  el("path", { d: "M17 22 L131 205", stroke: "#86a3c2", "stroke-width": 4, "stroke-linecap": "round" }, g);
  finger(g, [[170, 140], [116, 124], [44, 46]], 30);
  el("ellipse", { cx: 46, cy: 44, rx: 9, ry: 6, transform: "rotate(57 46 44)", fill: "#f7dcc4", stroke: SKIN_D, "stroke-width": 2.5 }, g);
  el("path", { d: "M84 98 C90 92 98 92 102 98", fill: "none", stroke: SKIN_D, "stroke-width": 3.5, "stroke-linecap": "round" }, g);
  el("path", { d: "M196 170 C214 182 230 184 244 178", fill: "none", stroke: SKIN_D, "stroke-width": 4, "stroke-linecap": "round" }, g);
}

// ---------------------------------------------------------------- san khau
const SPEED = 900;        // toc do but tu nhien: don vi thiet ke tren giay
const T_IN = 0.5;         // thoi gian ban tay tu ngoai khung vao net dau
const T_MOVE = 0.14;      // thoi gian nhac but di chuyen giua hai net
const T_OUT = 0.5;        // thoi gian ban tay roi khung sau net cuoi

export function createStage(svg, opts = {}) {
  const W = opts.width || 1920, H = opts.height || 1080;
  const portrait = H > W;
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  const defs = el("defs", {}, svg);
  const layer = el("g", {}, svg);
  const handG = el("g", { opacity: 0 }, svg);
  const handScale = opts.handScale || (Math.min(W, H) / 1080) * 1.2;
  const hand = el("g", {}, handG);
  drawHand(hand);
  // Vung an toan de ve: tranh nhan tren (.tag) va phu de duoi (xem template)
  const area = opts.area || (portrait ? { x: 40, y: 370, w: W - 80, h: 1000 } : { x: 80, y: 140, w: W - 160, h: 800 });
  const scenes = [];
  const warnings = [];
  let uid = 0;
  let finalized = false;

  function scene(id, o) {
    const s = Object.assign({
      start: 0, end: null, delay: 0.2, draw: null, fadeOut: 0.35, space: [1000, 1000], hand: true,
      seed: 11 + uid * 17,
    }, o, { id, items: [] });
    uid++;
    const rand = rng(s.seed);
    const k = Math.min(area.w / s.space[0], area.h / s.space[1]);
    s.k = k;
    s.ox = area.x + (area.w - k * s.space[0]) / 2;
    s.oy = area.y + (area.h - k * s.space[1]) / 2;
    s.g = el("g", { opacity: 0 }, layer);
    const c = el("g", { transform: `translate(${f1(s.ox)} ${f1(s.oy)}) scale(${k.toFixed(4)})` }, s.g);
    s.c = c;
    scenes.push(s);

    const add = (it) => { s.items.push(it); return it; };
    const bow = (len, m) => (rand() - 0.5) * 2 * Math.min(len * 0.025, m);
    const jt = (m) => (rand() - 0.5) * 2 * m;

    // ---- net co ban: mot duong SVG ve dan bang stroke-dashoffset
    function strokeItem(d, o2 = {}) {
      const attrs = {
        d, fill: "none", stroke: col(o2.color), "stroke-width": o2.w || 6,
        "stroke-linecap": "round", "stroke-linejoin": "round", opacity: 0,
      };
      if (o2.alpha != null) attrs["stroke-opacity"] = o2.alpha;
      const p = el("path", attrs, c);
      const it = { kind: "stroke", el: p, len: 0, at: o2.at, dur: o2.dur, last: -1 };
      const remeasure = () => { it.len = p.getTotalLength(); it.nat = Math.max(0.18, Math.min(1.8, it.len / SPEED)); };
      remeasure();
      it.remeasure = remeasure;
      it.pt = (u) => { const q = p.getPointAtLength(it.len * clamp(u, 0, 1)); return [q.x, q.y]; };
      it.set = (u) => {
        if (u === it.last) return;
        it.last = u;
        if (u <= 0) { p.setAttribute("opacity", 0); return; }
        p.setAttribute("opacity", 1);
        if (u >= 1) p.removeAttribute("stroke-dasharray");
        else {
          p.setAttribute("stroke-dasharray", `${it.len.toFixed(1)} ${it.len.toFixed(1)}`);
          p.setAttribute("stroke-dashoffset", (it.len * (1 - u)).toFixed(1));
        }
      };
      return add(it);
    }

    // ---- hop cat quet chu/vet to: hien dan tu trai sang phai
    function wipeItem(node, measure, o2, nat, tipY) {
      const cid = `vn-c${uid}-${s.items.length}`;
      const cp = el("clipPath", { id: cid, clipPathUnits: "userSpaceOnUse" }, defs);
      const r = el("rect", { x: 0, y: 0, width: 0, height: 0 }, cp);
      node.setAttribute("clip-path", `url(#${cid})`);
      node.setAttribute("opacity", 0);
      const it = { kind: "wipe", el: node, at: o2.at, dur: o2.dur, nat, bb: { x: 0, y: 0, width: 1, height: 1 }, last: -1 };
      it.measure = () => { it.bb = measure(); };
      it.pt = (u) => {
        const b = it.bb;
        return [b.x + b.width * clamp(u, 0, 1), b.y + b.height * tipY + Math.sin(u * 46) * b.height * 0.1];
      };
      it.set = (u) => {
        const b = it.bb;
        r.setAttribute("x", f1(b.x - 6)); r.setAttribute("y", f1(b.y - 6));
        r.setAttribute("height", f1(b.height + 12));
        r.setAttribute("width", f1((b.width + 12) * (u >= 1 ? 1.2 : u)));
        node.setAttribute("opacity", u <= 0 ? 0 : 1);
      };
      return add(it);
    }

    const api = {
      id, k: s.k, space: s.space,
      // Tuy chon chung cho moi ham: color, w (do day net), at (giay tu dau canh, de khop loi doc), dur (giay)

      path(d, o2) { return strokeItem(d, o2); },

      polyline(pts, o2) {
        const d = pts.map((p, i) => `${i ? "L" : "M"}${f1(p[0] + jt(1.2))} ${f1(p[1] + jt(1.2))}`).join(" ");
        return strokeItem(d, o2);
      },

      line(x1, y1, x2, y2, o2 = {}) {
        const len = Math.hypot(x2 - x1, y2 - y1);
        const nx = -(y2 - y1) / (len || 1), ny = (x2 - x1) / (len || 1);
        const b = bow(len, 6);
        const cx = (x1 + x2) / 2 + nx * b, cy = (y1 + y2) / 2 + ny * b;
        return strokeItem(`M${f1(x1)} ${f1(y1)} Q${f1(cx)} ${f1(cy)} ${f1(x2)} ${f1(y2)}`, o2);
      },

      // Mui ten: than cong nhe (o.bend) + hai net dau mui
      arrow(x1, y1, x2, y2, o2 = {}) {
        const len = Math.hypot(x2 - x1, y2 - y1) || 1;
        const ux = (x2 - x1) / len, uy = (y2 - y1) / len;
        const nx = -uy, ny = ux;
        const b = (o2.bend || 0) * len + bow(len, 6);
        const cx = (x1 + x2) / 2 + nx * b, cy = (y1 + y2) / 2 + ny * b;
        // Huong dau mui: tiep tuyen cuoi duong cong
        let tx = x2 - cx, ty = y2 - cy;
        const tl = Math.hypot(tx, ty) || 1; tx /= tl; ty /= tl;
        const hs = o2.head || Math.min(34, len * 0.3);
        const a1 = [x2 - tx * hs + ty * hs * 0.55, y2 - ty * hs - tx * hs * 0.55];
        const a2 = [x2 - tx * hs - ty * hs * 0.55, y2 - ty * hs + tx * hs * 0.55];
        return strokeItem(`M${f1(x1)} ${f1(y1)} Q${f1(cx)} ${f1(cy)} ${f1(x2)} ${f1(y2)} M${f1(a1[0])} ${f1(a1[1])} L${f1(x2)} ${f1(y2)} L${f1(a2[0])} ${f1(a2[1])}`, o2);
      },

      rect(x, y, w, h, o2 = {}) {
        const r = Math.min(o2.r || 0, w / 2, h / 2);
        const q = () => jt(1.5);
        const X = x + q(), Y = y + q(), X2 = x + w + q(), Y2 = y + h + q();
        const d = r > 0
          ? `M${f1(X + r)} ${f1(Y)} L${f1(X2 - r)} ${f1(Y)} Q${f1(X2)} ${f1(Y)} ${f1(X2)} ${f1(Y + r)} L${f1(X2)} ${f1(Y2 - r)} Q${f1(X2)} ${f1(Y2)} ${f1(X2 - r)} ${f1(Y2)} L${f1(X + r)} ${f1(Y2)} Q${f1(X)} ${f1(Y2)} ${f1(X)} ${f1(Y2 - r)} L${f1(X)} ${f1(Y + r)} Q${f1(X)} ${f1(Y)} ${f1(X + r + 12)} ${f1(Y)}`
          : `M${f1(X)} ${f1(Y)} L${f1(X2)} ${f1(Y)} L${f1(X2)} ${f1(Y2)} L${f1(X)} ${f1(Y2)} L${f1(X)} ${f1(Y - 4)}`;
        return strokeItem(d, o2);
      },

      // Vong tron/elip ve mot nhat, hoi qua diem dau (qua 4%) va ban kinh troi nhe
      ellipse(cx, cy, rx, ry, o2 = {}) {
        const a0 = rand() * Math.PI * 2, ph = rand() * 6.28;
        const n = 72, turn = 1.04;
        const rot = ((o2.rot || 0) * Math.PI) / 180;
        const pts = [];
        for (let i = 0; i <= n; i++) {
          const t = i / n;
          const a = a0 + t * turn * 2 * Math.PI;
          const g = 1 + 0.012 * Math.sin(2 * a + ph) + 0.03 * t - 0.015;
          const x = rx * g * Math.cos(a), y = ry * g * Math.sin(a);
          pts.push([cx + x * Math.cos(rot) - y * Math.sin(rot), cy + x * Math.sin(rot) + y * Math.cos(rot)]);
        }
        return strokeItem("M" + pts.map((p) => `${f1(p[0])} ${f1(p[1])}`).join(" L"), o2);
      },
      circle(cx, cy, r, o2) { return api.ellipse(cx, cy, r, r, o2); },

      // Net gach cheo ziczac phu mot da giac loi (xem poly.circle, poly.rect, poly.ellipse)
      // o: angle (do, mac dinh 45), gap (khoang cach net, mac dinh 16), w (do day net)
      hatch(pts, o2 = {}) {
        const d = hatchPath(pts, o2.angle == null ? 45 : o2.angle, o2.gap || 16, rand, o2.inset == null ? 3 : o2.inset);
        return strokeItem(d, Object.assign({ w: 3.5 }, o2));
      },
      // To mau bang net to, gap day (nhu bay mau): hatch voi net day va doi mau nhe
      shade(pts, o2 = {}) {
        const gap = o2.gap || 18;
        return api.hatch(pts, Object.assign({ w: gap * 1.15, alpha: 0.5, angle: 25 }, o2, { gap }));
      },

      // Gach chan uon song duoi mot doan
      underline(x1, x2, y, o2 = {}) {
        const n = Math.max(4, Math.round((x2 - x1) / 40));
        const pts = [];
        for (let i = 0; i <= n; i++) pts.push([x1 + ((x2 - x1) * i) / n, y + (i % 2 ? 4 : -2) + jt(1.5)]);
        const d = "M" + pts.map((p) => `${f1(p[0])} ${f1(p[1])}`).join(" L");
        return strokeItem(d, Object.assign({ w: 5 }, o2));
      },

      // ---- hinh ghep san (mot nhat cac net co ban o tren)
      sun(cx, cy, r, o2 = {}) {
        const color = o2.color || "orange";
        api.circle(cx, cy, r, { color, w: o2.w });
        const n = o2.rays || 8, ph = rand() * 0.2;
        for (let i = 0; i < n; i++) {
          const a = ph + (i * 2 * Math.PI) / n;
          api.line(cx + Math.cos(a) * r * 1.4, cy + Math.sin(a) * r * 1.4, cx + Math.cos(a) * r * 1.85, cy + Math.sin(a) * r * 1.85, { color, w: o2.w, dur: 0.12 });
        }
      },
      moon(cx, cy, r, o2 = {}) {
        const a1 = (-75 * Math.PI) / 180, a2 = (95 * Math.PI) / 180;
        const P1 = [cx + r * Math.cos(a1), cy + r * Math.sin(a1)], P2 = [cx + r * Math.cos(a2), cy + r * Math.sin(a2)];
        const ri = r * 0.78;
        return strokeItem(`M${f1(P1[0])} ${f1(P1[1])} A${r} ${r} 0 1 0 ${f1(P2[0])} ${f1(P2[1])} A${f1(ri)} ${f1(ri)} 0 0 1 ${f1(P1[0])} ${f1(P1[1])}`, Object.assign({ color: "blue" }, o2));
      },
      check(x, y, s2, o2 = {}) {
        return api.polyline([[x - s2 * 0.5, y], [x - s2 * 0.12, y + s2 * 0.4], [x + s2 * 0.55, y - s2 * 0.45]], Object.assign({ color: "green", w: 9 }, o2));
      },
      cross(x, y, s2, o2 = {}) {
        const c2 = Object.assign({ color: "red", w: 9 }, o2);
        api.line(x - s2 * 0.45, y - s2 * 0.45, x + s2 * 0.45, y + s2 * 0.45, c2);
        api.line(x + s2 * 0.45, y - s2 * 0.45, x - s2 * 0.45, y + s2 * 0.45, c2);
      },
      heart(cx, cy, s2, o2 = {}) {
        const d = `M${f1(cx)} ${f1(cy + s2 * 0.95)} C${f1(cx - s2 * 1.5)} ${f1(cy + s2 * 0.0)} ${f1(cx - s2 * 1.15)} ${f1(cy - s2 * 1.15)} ${f1(cx)} ${f1(cy - s2 * 0.4)} C${f1(cx + s2 * 1.15)} ${f1(cy - s2 * 1.15)} ${f1(cx + s2 * 1.5)} ${f1(cy + s2 * 0.0)} ${f1(cx)} ${f1(cy + s2 * 0.95)}`;
        return strokeItem(d, Object.assign({ color: "red" }, o2));
      },
      star(cx, cy, r, o2 = {}) {
        const pts = [0, 2, 4, 1, 3, 0].map((i) => {
          const a = ((-90 + i * 72) * Math.PI) / 180;
          return [cx + r * Math.cos(a), cy + r * Math.sin(a)];
        });
        return api.polyline(pts, Object.assign({ color: "yellow", w: 7 }, o2));
      },
      bulb(cx, cy, s2, o2 = {}) {
        const c2 = Object.assign({ color: "orange" }, o2);
        const R = s2 * 0.78, nk = s2 * 0.3;
        const yb = cy + s2 * 0.5;
        strokeItem(`M${f1(cx - nk)} ${f1(yb)} A${f1(R)} ${f1(R)} 0 1 1 ${f1(cx + nk)} ${f1(yb)}`, c2);
        api.line(cx - nk, yb + s2 * 0.2, cx + nk, yb + s2 * 0.2, c2);
        api.line(cx - nk * 0.7, yb + s2 * 0.4, cx + nk * 0.7, yb + s2 * 0.4, c2);
        api.polyline([[cx - nk * 0.5, yb], [cx - nk * 0.25, yb - s2 * 0.3], [cx + nk * 0.25, yb - s2 * 0.3], [cx + nk * 0.5, yb]], Object.assign({}, c2, { w: 4 }));
      },
      person(cx, cy, s2, o2 = {}) {
        const c2 = Object.assign({ color: "ink" }, o2);
        api.circle(cx, cy - s2 * 0.72, s2 * 0.22, c2);
        api.line(cx, cy - s2 * 0.48, cx, cy + s2 * 0.2, c2);
        api.polyline([[cx - s2 * 0.42, cy - s2 * 0.02], [cx, cy - s2 * 0.34], [cx + s2 * 0.42, cy - s2 * 0.02]], c2);
        api.polyline([[cx - s2 * 0.3, cy + s2 * 0.85], [cx, cy + s2 * 0.2], [cx + s2 * 0.3, cy + s2 * 0.85]], c2);
      },
      doc(x, y, w, h, o2 = {}) {
        const c2 = Object.assign({ color: "ink" }, o2);
        const f = w * 0.26;
        strokeItem(`M${f1(x)} ${f1(y)} L${f1(x + w - f)} ${f1(y)} L${f1(x + w)} ${f1(y + f)} L${f1(x + w)} ${f1(y + h)} L${f1(x)} ${f1(y + h)} Z`, c2);
        api.polyline([[x + w - f, y], [x + w - f, y + f], [x + w, y + f]], Object.assign({}, c2, { w: 4 }));
        [0.42, 0.57, 0.72].forEach((u, i) => api.line(x + w * 0.16, y + h * u, x + w * (i == 2 ? 0.55 : 0.84), y + h * u, Object.assign({}, c2, { w: 4 })));
      },
      clock(cx, cy, r, o2 = {}) {
        const c2 = Object.assign({ color: "ink" }, o2);
        api.circle(cx, cy, r, c2);
        api.line(cx, cy, cx, cy - r * 0.62, c2);
        api.line(cx, cy, cx + r * 0.45, cy + r * 0.15, c2);
        [[0, -1], [1, 0], [0, 1], [-1, 0]].forEach(([dx, dy]) => api.line(cx + dx * r * 0.82, cy + dy * r * 0.82, cx + dx * r * 0.95, cy + dy * r * 0.95, Object.assign({}, c2, { w: 4, dur: 0.1 })));
      },
      magnifier(cx, cy, r, o2 = {}) {
        const c2 = Object.assign({ color: "blue" }, o2);
        api.circle(cx, cy, r, c2);
        api.line(cx + r * 0.72, cy + r * 0.72, cx + r * 1.7, cy + r * 1.7, Object.assign({}, c2, { w: 11 }));
      },
      house(cx, cy, s2, o2 = {}) {
        const c2 = Object.assign({ color: "ink" }, o2);
        api.rect(cx - s2 * 0.7, cy - s2 * 0.1, s2 * 1.4, s2 * 0.9, c2);
        api.polyline([[cx - s2 * 0.85, cy - s2 * 0.05], [cx, cy - s2 * 0.85], [cx + s2 * 0.85, cy - s2 * 0.05]], c2);
        api.rect(cx - s2 * 0.15, cy + s2 * 0.3, s2 * 0.3, s2 * 0.5, Object.assign({}, c2, { color: "orange" }));
      },
      tree(cx, cy, s2, o2 = {}) {
        const c2 = Object.assign({ color: "green" }, o2);
        api.circle(cx, cy - s2 * 0.35, s2 * 0.55, c2);
        api.line(cx, cy + s2 * 0.2, cx, cy + s2 * 0.9, Object.assign({}, c2, { color: "ink", w: 9 }));
      },

      // ---- chu viet ra: cat quet tu trai sang phai, but chay theo mep cat
      // o: size (56), weight (700), anchor (start|middle|end), color, lh (gian dong 1.25),
      //    mark (mau to vet: "mark" hoac ma mau), under (mau gach chan), font
      // Nhieu dong: xuong dong bang \n, moi dong viet tiep nhau.
      text(str, x, y, o2 = {}) {
        const size = o2.size || 56;
        const lines = String(str).split("\n");
        const out = [];
        lines.forEach((ln, i) => {
          const ty = y + i * size * (o2.lh || 1.25);
          const t = el("text", {
            x, y: ty, "font-size": size, "font-weight": o2.weight || 700, "text-anchor": o2.anchor || "start",
            fill: col(o2.color), style: `font-family:${o2.font || '"Be Vietnam Pro", sans-serif'}`,
          }, c);
          t.textContent = ln;
          const nat = clamp(ln.length * 0.07, 0.3, 2.2);
          if (o2.mark) {
            const mk = el("rect", { fill: col(o2.mark === true ? "mark" : o2.mark) }, c);
            c.insertBefore(mk, t);
            const m = wipeItem(mk, () => {
              const b = t.getBBox();
              return { x: b.x - 8, y: b.y + b.height * 0.32, width: b.width + 16, height: b.height * 0.62 };
            }, { at: i === 0 ? o2.at : undefined }, clamp(nat * 0.6, 0.25, 1.2), 0.5);
            const setM = m.set;
            m.set = (u) => {
              const b = m.bb;
              mk.setAttribute("x", f1(b.x)); mk.setAttribute("y", f1(b.y));
              mk.setAttribute("width", f1(b.width)); mk.setAttribute("height", f1(b.height));
              setM(u);
            };
          }
          const it = wipeItem(t, () => t.getBBox(), { at: !o2.mark && i === 0 ? o2.at : undefined, dur: o2.dur }, nat, 0.62);
          out.push(it);
          if (o2.under) {
            const u = strokeItem("M0 0", { color: o2.under, w: 5 });
            u.lazy = true;
            let lastW = -1;
            u.measure = () => {
              const b = t.getBBox();
              if (Math.abs(b.width - lastW) < 0.5) return;
              lastW = b.width;
              const n = Math.max(4, Math.round(b.width / 40)), yy = b.y + b.height * 0.98;
              const pts = [];
              for (let q = 0; q <= n; q++) pts.push(`${f1(b.x + (b.width * q) / n)} ${f1(yy + (q % 2 ? 3 : -2))}`);
              u.el.setAttribute("d", "M" + pts.join(" L"));
              u.last = -1;
              u.remeasure();
            };
          }
        });
        return out[0];
      },

      // Dung but nghi (ban tay giu nguyen) mot luc, de khop nhip loi doc
      wait(sec) { return add({ kind: "wait", dur: sec, nat: sec, explicit: true, set() {}, pt: null }); },
    };
    return api;
  }

  // ---------------------------------------------------------------- thoi gian
  function resolve(s) {
    s.items.forEach((it) => { if (it.measure) it.measure(); if (it.dur != null) it.explicit = true; });
    const life = s.end - s.start;
    const last = scenes[scenes.length - 1] === s;
    const real = s.items.filter((it) => it.kind !== "wait");
    const tail = (last ? 0 : s.fadeOut) + 0.3;
    if (s.draw == null) s.draw = Math.max(1.2, life - s.delay - tail - T_OUT);
    const hasAt = s.items.some((it) => it.at != null);
    const travel = real.length ? T_IN + (real.length - 1) * T_MOVE : 0;
    const fixed = s.items.reduce((a, it) => a + (it.explicit ? it.dur : 0), 0);
    const flow = s.items.reduce((a, it) => a + (it.explicit ? 0 : it.nat), 0);
    const f = hasAt || flow === 0 ? 1 : clamp((s.draw - travel - fixed) / flow, 0.35, 2.0);
    let cur = s.delay, first = true;
    for (const it of s.items) {
      if (it.kind === "wait") { it.start = cur; cur += it.dur; continue; }
      it.tr = first ? T_IN : T_MOVE;
      first = false;
      it.start = cur + it.tr;
      if (it.at != null) it.start = Math.max(it.start, it.at);
      if (!it.explicit) it.dur = it.nat * f;
      cur = it.start + it.dur;
    }
    s.drawEnd = cur;
    if (cur + T_OUT > life + 0.05 && real.length) {
      const msg = `canh ${s.id}: ve xong luc ${cur.toFixed(2)}s nhung canh chi dai ${life.toFixed(2)}s (them bot net hoac keo dai canh)`;
      warnings.push(msg);
      if (typeof console !== "undefined") console.warn("[venet] " + msg);
    }
  }

  function finalize() {
    scenes.sort((a, b) => a.start - b.start);
    scenes.forEach((s, i) => {
      s.last = i + 1 === scenes.length;
      if (s.end == null) s.end = !s.last ? scenes[i + 1].start : (opts.duration || s.start + 8);
    });
    scenes.forEach(resolve);
    finalized = true;
    // Bao cao thoi gian de scripts/ve_net_kiem_tra.sh doc ra (khong anh huong hinh)
    svg.setAttribute("data-venet-report", JSON.stringify({ scenes: report(), warnings }));
  }

  const toScreen = (s, p) => [s.ox + p[0] * s.k, s.oy + p[1] * s.k];

  function handAt(s, lt) {
    const out = [W * 1.08, H * 1.12];
    const real = s.items.filter((it) => it.kind !== "wait");
    if (!s.hand || !real.length) return null;
    let prev = out;
    for (let i = 0; i < real.length; i++) {
      const it = real[i];
      const a = toScreen(s, it.pt(0));
      const t0 = it.start - it.tr;
      if (lt < t0) return i === 0 ? null : prev;
      if (lt < it.start) { const e = ease((lt - t0) / it.tr); return [prev[0] + (a[0] - prev[0]) * e, prev[1] + (a[1] - prev[1]) * e]; }
      if (lt <= it.start + it.dur) return toScreen(s, it.pt((lt - it.start) / it.dur));
      prev = toScreen(s, it.pt(1));
    }
    // Sau net cuoi: ban tay roi khung
    const t1 = real[real.length - 1].start + real[real.length - 1].dur;
    if (lt > t1 + T_OUT) return null;
    const e = ease((lt - t1) / T_OUT);
    return [prev[0] + (out[0] - prev[0]) * e, prev[1] + (out[1] - prev[1]) * e];
  }

  function render(t) {
    if (!finalized) finalize();
    let cur = null;
    for (const s of scenes) {
      const vis = t >= s.start - 0.001 && t < s.end;
      if (!vis) { s.g.setAttribute("opacity", 0); continue; }
      const toEnd = s.end - t;
      const o = !s.last && toEnd < s.fadeOut ? toEnd / s.fadeOut : 1;
      s.g.setAttribute("opacity", clamp(o, 0, 1).toFixed(3));
      const lt = t - s.start;
      for (const it of s.items) {
        if (it.kind === "wait") continue;
        if (it.measure) it.measure();
        it.set(clamp((lt - it.start) / it.dur, 0, 1));
      }
      cur = s;
    }
    const pos = cur ? handAt(cur, t - cur.start) : null;
    if (pos) {
      handG.setAttribute("opacity", 1);
      hand.setAttribute("transform", `translate(${pos[0].toFixed(1)} ${pos[1].toFixed(1)}) scale(${handScale.toFixed(3)})`);
    } else {
      handG.setAttribute("opacity", 0);
    }
  }

  // Bao cao thoi gian tung canh: de agent kiem tra ve co kip khong
  function report() {
    if (!finalized) finalize();
    return scenes.map((s) => ({ id: s.id, start: s.start, end: s.end, drawEnd: +(s.start + s.drawEnd).toFixed(2), items: s.items.length }));
  }

  // Font tai xong thi do lai chu va ve lai khung hien tai
  let lastT = 0;
  const baseRender = render;
  const stage = {
    scene, W, H, portrait, area, warnings, report,
    render(t) { lastT = t; baseRender(t); },
    pick: (p, l) => (portrait ? p : l),
  };
  if (typeof document !== "undefined" && document.fonts && document.fonts.ready) {
    document.fonts.ready.then(() => { if (finalized) stage.render(lastT); });
  }
  return stage;
}
