// chibi.js: nhan vat chibi nhin chinh dien cho video-studio. Dan nhan vat dung chung roster voi line-art. Khong sua tay: sua nguon trong assets/chibi/src roi build lai.

// lineart/src/cast/roster.ts
var ROSTER = [
  {
    id: "bac-si-minh",
    name: "B\xE1c s\u0129 Minh",
    role: "B\xE1c s\u0129",
    build: "adult",
    sex: "nam",
    top: "coat",
    topColor: "#fdfdfc",
    sleeve: "long",
    bottom: "trousers",
    bottomColor: "#4a4f57",
    hair: "side",
    extras: ["stethoscope", "glasses"],
    prop: "none"
  },
  {
    id: "dieu-duong-lan",
    name: "\u0110i\u1EC1u d\u01B0\u1EE1ng Lan",
    role: "\u0110i\u1EC1u d\u01B0\u1EE1ng",
    build: "adult",
    sex: "nu",
    height: 0.95,
    top: "scrubs",
    topColor: "#7fb3c6",
    sleeve: "short",
    bottom: "trousers",
    bottomColor: "#7fb3c6",
    hair: "bun",
    hat: "nurse",
    hatColor: "#fdfdfc",
    extras: ["mask"],
    prop: "none",
    shoeColor: "#fdfdfc"
  },
  {
    id: "can-bo-thu",
    name: "Ch\u1ECB Thu",
    role: "C\xE1n b\u1ED9 ki\u1EC3m d\u1ECBch y t\u1EBF",
    build: "adult",
    sex: "nu",
    height: 0.95,
    top: "shirt",
    topColor: "#c3d6e8",
    sleeve: "long",
    bottom: "trousers",
    bottomColor: "#2c3b52",
    hair: "ponytail",
    hat: "officer",
    hatColor: "#2c3b52",
    extras: ["lanyard"],
    prop: "clipboard"
  },
  {
    id: "co-giao-hoa",
    name: "C\xF4 Hoa",
    role: "Gi\xE1o vi\xEAn",
    build: "adult",
    sex: "nu",
    height: 0.95,
    top: "aodai",
    topColor: "#7fa3c7",
    sleeve: "long",
    bottom: "plain",
    bottomColor: "#fdfdfc",
    hair: "long",
    prop: "books"
  },
  {
    id: "chi-nam",
    name: "Ch\u1ECB N\u0103m",
    role: "B\xE1n h\xE0ng rong",
    build: "adult",
    sex: "nu",
    height: 0.94,
    top: "baba",
    topColor: "#a9573f",
    sleeve: "long",
    bottom: "wide",
    bottomColor: "#2b2b2b",
    hair: "bun",
    hat: "nonla",
    hatColor: "#e9d7a3",
    prop: "ganh",
    gait: { stride: 20, period: 0.86 }
  },
  {
    id: "ba-sau",
    name: "B\xE0 S\xE1u",
    role: "Ng\u01B0\u1EDDi cao tu\u1ED5i",
    build: "elder",
    sex: "nu",
    height: 0.9,
    stoop: 6,
    top: "baba",
    topColor: "#6e5a86",
    sleeve: "long",
    bottom: "wide",
    bottomColor: "#2b2b2b",
    hair: "bun",
    hairColor: "#b8b2a6",
    prop: "basket"
  },
  {
    id: "anh-tuan",
    name: "Anh Tu\u1EA5n",
    role: "C\xF4ng nh\xE2n",
    build: "adult",
    sex: "nam",
    top: "shirt",
    topColor: "#5c7896",
    sleeve: "long",
    bottom: "trousers",
    bottomColor: "#39414d",
    hair: "short",
    hat: "hardhat",
    hatColor: "#e5b53a",
    extras: ["vest"],
    prop: "none"
  },
  {
    id: "anh-khoa",
    name: "Anh Khoa",
    role: "H\xE0nh kh\xE1ch",
    build: "adult",
    sex: "nam",
    top: "jacket",
    topColor: "#5f7a66",
    sleeve: "long",
    bottom: "trousers",
    bottomColor: "#3d4f6b",
    hair: "short",
    hat: "cap",
    hatColor: "#2b2b2b",
    extras: ["mask"],
    prop: "suitcase",
    propColor: "#2f5d6b"
  },
  {
    id: "anh-duc",
    name: "Anh \u0110\u1EE9c",
    role: "Nh\xE2n vi\xEAn v\u0103n ph\xF2ng",
    build: "adult",
    sex: "nam",
    top: "shirt",
    topColor: "#ece6d6",
    sleeve: "long",
    bottom: "trousers",
    bottomColor: "#2f3540",
    hair: "side",
    extras: ["tie"],
    prop: "briefcase"
  },
  {
    id: "ong-bay",
    name: "\xD4ng B\u1EA3y",
    role: "Ng\u01B0\u1EDDi cao tu\u1ED5i",
    build: "elder",
    sex: "nam",
    height: 0.97,
    stoop: 9,
    top: "shirt",
    topColor: "#d8cfb5",
    sleeve: "long",
    bottom: "trousers",
    bottomColor: "#6b6455",
    hair: "short",
    hairColor: "#c9c4ba",
    extras: ["glasses"],
    prop: "cane"
  },
  {
    id: "be-an",
    name: "B\xE9 An",
    role: "H\u1ECDc sinh",
    build: "child",
    sex: "nam",
    top: "shirt",
    topColor: "#fdfdfc",
    sleeve: "short",
    bottom: "shorts",
    bottomColor: "#2f4466",
    hair: "short",
    extras: ["redscarf"],
    prop: "backpack",
    propColor: "#3f6ea8"
  },
  {
    id: "be-mai",
    name: "B\xE9 Mai",
    role: "Em nh\u1ECF",
    build: "child",
    sex: "nu",
    top: "dress",
    topColor: "#d9826e",
    sleeve: "short",
    bottom: "plain",
    bottomColor: "#fdfdfc",
    hair: "pigtails",
    prop: "none",
    shoeColor: "#a33a2e"
  }
];
var byId = (id) => {
  const s = ROSTER.find((r) => r.id === id);
  if (!s) throw new Error(`unknown character ${id}`);
  return s;
};

// chibi/src/svg.ts
var NS = "http://www.w3.org/2000/svg";
var OUT = "#4a2c25";
var W = 5;
function el(tag, attrs = {}, parent) {
  const n = document.createElementNS(NS, tag);
  for (const k in attrs) n.setAttribute(k, String(attrs[k]));
  if (parent) parent.appendChild(n);
  return n;
}
var g = (parent, attrs = {}) => el("g", attrs, parent);
var UNDER = 0;
var setUnder = (r) => {
  UNDER = r;
};
var under = () => UNDER > 0;
var STICKER = "#ffffff";
var fill = (parent, d, colour, w = W) => el("path", { d, fill: UNDER ? STICKER : colour, stroke: UNDER ? STICKER : OUT, "stroke-width": w + 2 * UNDER, "stroke-linejoin": "round", "stroke-linecap": "round" }, parent);
var line = (parent, d, w = W * 0.7, colour = OUT) => el("path", { d, fill: "none", stroke: UNDER ? STICKER : colour, "stroke-width": w + 2 * UNDER, "stroke-linejoin": "round", "stroke-linecap": "round" }, parent);
var flat = (parent, d, colour, opacity = 1) => el("path", { d, fill: UNDER ? STICKER : colour, opacity: UNDER ? 1 : opacity }, parent);
var f = (n) => Math.abs(n) < 1e-4 ? "0" : n.toFixed(2);
function shade(hex, k = 0.82) {
  const h = hex.replace("#", "");
  const v = h.length === 3 ? h.split("").map((c) => parseInt(c + c, 16)) : [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16));
  return "#" + v.map((c) => Math.round(Math.max(0, Math.min(255, c * k))).toString(16).padStart(2, "0")).join("");
}
var clamp = (x, a = 0, b = 1) => x < a ? a : x > b ? b : x;
var lerp = (a, b, t) => a + (b - a) * t;
var ease = (x) => {
  x = clamp(x);
  return x * x * (3 - 2 * x);
};
function hash(s) {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return (h >>> 0) % 1e4 / 1e4;
}

// chibi/src/que.ts
var RAISE = 46;
var ARM_A = 40;
var ARM_B = 40;
var STICK = 7.5;
var SLEEVE = 22;
var RAD = Math.PI / 180;
var dirOf = (r) => [-Math.sin(r * RAD), Math.cos(r * RAD)];
var P = (p) => `${f(p[0])} ${f(p[1])}`;
function drawQueArm(parent, s, side) {
  const sleeveCol = s.topColor;
  const stick = line(parent, "M0 0", STICK, OUT);
  const hand = g(parent);
  fill(hand, "M-8 0 a8 8 0 1 0 16 0 a8 8 0 1 0 -16 0", "#2a211e", W * 0.5);
  const sleeveO = line(parent, "M0 0", SLEEVE + W * 1.6, OUT);
  const sleeveI = line(parent, "M0 0", SLEEVE, sleeveCol);
  return { side, sleeveO, sleeveI, stick, hand };
}
function poseQueArm(a, u1, u2) {
  const S = [a.side * 40, -116];
  const r1 = -a.side * u1, r2 = r1 - a.side * u2;
  const v1 = dirOf(r1), v2 = dirOf(r2);
  const E = [S[0] + ARM_A * v1[0], S[1] + ARM_A * v1[1]];
  const H = [E[0] + ARM_B * v2[0], E[1] + ARM_B * v2[1]];
  const C = [2 * E[0] - (S[0] + H[0]) / 2, 2 * E[1] - (S[1] + H[1]) / 2];
  a.stick.setAttribute("d", `M${P(S)} Q${P(C)} ${P(H)}`);
  const sl = [S[0] + 16 * v1[0], S[1] + 16 * v1[1]];
  const d = `M${P([S[0] + 2 * v1[0], S[1] + 2 * v1[1]])} L${P(sl)}`;
  a.sleeveO.setAttribute("d", d);
  a.sleeveI.setAttribute("d", d);
  a.hand.setAttribute("transform", `translate(${P(H)})`);
  return { hand: H, angle: r2 };
}
function drawQueLegs(parent, s, look) {
  const legs = [];
  const bare = s.top === "dress" || s.bottom === "shorts";
  const stubCol = bare ? s.bottomColor : s.bottomColor;
  for (const side of [-1, 1]) {
    const stick = line(parent, "M0 0", STICK, OUT);
    const foot = g(parent);
    fill(foot, `M${-side * 4} -1 Q${-side * 4} -11 ${side * 8} -11 Q${side * 20} -11 ${side * 20} -3 Q${side * 20} 2 ${side * 8} 2 Q${-side * 4} 2 ${-side * 4} -1 Z`, s.shoeColor ?? "#2a211e", W * 0.6);
    const stubO = line(parent, "M0 0", 26 + W * 1.6, OUT);
    const stubI = line(parent, "M0 0", 26, stubCol);
    legs.push({ side, stubO, stubI, stick, foot });
    void look;
  }
  return legs;
}
function poseQueLegs(legs, hipY, phase, walking, stubLen, sit = 0, running = false) {
  const stride = running ? 34 : 24, liftH = running ? 24 : 14;
  for (const L of legs) {
    const ph = phase + (L.side > 0 ? Math.PI : 0);
    const Hp = [L.side * 15, hipY];
    let F = [L.side * 17, -6];
    let bx = 3;
    if (walking) {
      const lift = Math.max(0, Math.cos(ph));
      F = [L.side * 15 + stride * Math.sin(ph), -6 - lift * liftH];
      bx = 4 + lift * 14;
    }
    if (sit > 0) {
      F = [F[0] + (L.side * 26 - F[0]) * sit, F[1] + (-6 - F[1]) * sit];
      bx = bx + (L.side * 20 - bx) * sit;
    }
    const M = [(Hp[0] + F[0]) / 2 + bx, (Hp[1] + F[1]) / 2];
    L.stick.setAttribute("d", `M${P(Hp)} Q${P(M)} ${P(F)}`);
    L.foot.setAttribute("transform", `translate(${P([F[0], F[1] + 6])})`);
    const d = `M${P([Hp[0], Hp[1] - 4])} L${P([Hp[0], Hp[1] + stubLen])}`;
    L.stubO.setAttribute("d", d);
    L.stubI.setAttribute("d", d);
  }
}
function drawFlashlight(parent, uid, withBeam) {
  const root = g(parent);
  if (withBeam) {
    const defs = el("defs", {}, root);
    const lg = el("linearGradient", { id: `${uid}-beam`, x1: 0, y1: 0, x2: 0, y2: 1 }, defs);
    el("stop", { offset: 0, "stop-color": "#fff6cf", "stop-opacity": 0.55 }, lg);
    el("stop", { offset: 0.55, "stop-color": "#ffe9a6", "stop-opacity": 0.18 }, lg);
    el("stop", { offset: 1, "stop-color": "#ffe9a6", "stop-opacity": 0 }, lg);
    el("path", { d: "M-9 34 L-260 900 L260 900 L9 34 Z", fill: `url(#${uid}-beam)` }, root);
  }
  fill(root, "M-6 -6 L6 -6 L7 22 L-7 22 Z", "#3a3f45", W * 0.6);
  fill(root, "M-10 22 L10 22 L9 34 L-9 34 Z", shade("#3a3f45", 1.4), W * 0.6);
  return { g: root };
}

// chibi/src/rig.ts
var LOOKS = {
  "bac-si-minh": { skin: "#f3d3bb", hair: "#2b211e" },
  "dieu-duong-lan": { skin: "#f7dcc9", hair: "#2e211d" },
  "can-bo-thu": { skin: "#f7dcc9", hair: "#3a2420" },
  "co-giao-hoa": { skin: "#f8dfcd", hair: "#241a18" },
  "anh-duc": { skin: "#f1d0b6", hair: "#2b211e" },
  "anh-tuan": { skin: "#e2b896", hair: "#2b211e" },
  "chi-nam": { skin: "#e8be9c", hair: "#2b211e" },
  "anh-khoa": { skin: "#efcfb4", hair: "#2e2420" },
  "ong-bay": { skin: "#e9c4a6", hair: "#c9c4ba", blush: 0.45 },
  "ba-sau": { skin: "#efcdb2", hair: "#b8b2a6", blush: 0.5 },
  "be-an": { skin: "#f6d6bf", hair: "#2b211e" },
  "be-mai": { skin: "#f8dccb", hair: "#3a2621" }
};
var DEFAULT_LOOK = { skin: "#f5d6c0", hair: "#352420" };
var SUPPORTED = {
  top: ["shirt", "coat", "aodai", "baba", "dress", "jacket", "scrubs"],
  bottom: ["trousers", "wide", "shorts", "plain"],
  hair: ["short", "side", "bun", "long", "ponytail", "pigtails"],
  hat: ["none", "nonla", "cap", "hardhat", "officer", "nurse"],
  extras: ["mask", "glasses", "stethoscope", "redscarf", "vest", "lanyard", "tie"],
  prop: ["none", "clipboard", "books", "briefcase", "basket", "backpack", "cane", "ganh", "suitcase"],
  build: ["adult", "child", "elder"]
};
function checkSpec(s) {
  const bad = [];
  const chk = (k, v) => {
    if (!SUPPORTED[k].includes(v)) bad.push(`${k}=${v}`);
  };
  chk("top", s.top);
  chk("bottom", s.bottom);
  chk("hair", s.hair);
  chk("hat", s.hat ?? "none");
  chk("prop", s.prop ?? "none");
  chk("build", s.build);
  for (const e of s.extras ?? []) chk("extras", e);
  if (bad.length) throw new Error(`chibi: ${s.id} chua ve ban chibi (${bad.join(", ")})`);
}
var SHOULDER_Y = -118;
var NECK_Y = -134;
var UPPER = 34;
var FORE = 32;
var BUILD = {
  adult: { body: 1, head: 1, speed: 120 },
  child: { body: 0.7, head: 0.86, speed: 105 },
  elder: { body: 0.97, head: 0.97, speed: 70 }
};
function torsoPath(top) {
  switch (top) {
    case "coat":
      return "M-34 -124 Q-50 -120 -52 -100 L-58 -16 Q-30 -12 -3 -16 L3 -16 Q30 -12 58 -16 L52 -100 Q50 -120 34 -124 Z";
    case "aodai":
      return "M-30 -126 Q-48 -120 -50 -100 L-50 -62 Q-49 -54 -42 -50 L-34 -4 Q0 0 34 -4 L42 -50 Q49 -54 50 -62 L50 -100 Q48 -120 30 -126 Z";
    case "baba":
      return "M-34 -124 Q-52 -120 -54 -100 L-60 -40 Q0 -32 60 -40 L54 -100 Q52 -120 34 -124 Z";
    case "dress":
      return "M-30 -124 Q-46 -120 -48 -100 L-68 -30 Q0 -20 68 -30 L48 -100 Q46 -120 30 -124 Z";
    default:
      return "M-34 -124 Q-50 -120 -52 -100 L-55 -46 Q0 -38 55 -46 L52 -100 Q50 -120 34 -124 Z";
  }
}
function drawLegs(parent, s, look) {
  const legs = [];
  const shoe = s.shoeColor ?? "#3b302c";
  const bare = s.top === "dress" || s.bottom === "shorts";
  for (const side of [-1, 1]) {
    const lg = g(parent);
    const sd = side;
    if (s.bottom === "wide") fill(lg, `M${sd * 4} -50 L${sd * 30} -50 L${sd * 34} -10 L${sd * 4} -10 Z`, s.bottomColor);
    else if (bare) {
      fill(lg, `M${sd * 8} -40 L${sd * 22} -40 L${sd * 21} -12 L${sd * 9} -12 Z`, look.skin);
      if (s.bottom === "shorts") fill(lg, `M${sd * 3} -54 L${sd * 30} -54 L${sd * 28} -32 L${sd * 4} -32 Z`, s.bottomColor);
      fill(lg, `M${sd * 8} -18 L${sd * 22} -18 L${sd * 22} -10 L${sd * 8} -10 Z`, "#fdfdfc", W * 0.7);
    } else fill(lg, `M${sd * 5} -50 L${sd * 27} -50 L${sd * 25} -12 L${sd * 6} -12 Z`, s.bottomColor);
    fill(lg, `M${sd * 2} -2 Q${sd * 2} -16 ${sd * 16} -16 Q${sd * 32} -16 ${sd * 32} -4 Q${sd * 32} 2 ${sd * 16} 2 Q${sd * 2} 2 ${sd * 2} -2 Z`, shoe);
    legs.push(lg);
  }
  return legs;
}
function drawTorso(parent, s, look, id) {
  const t = g(parent);
  const d = torsoPath(s.top);
  const ex = s.extras ?? [];
  fill(t, d, s.topColor);
  if (!under()) {
    const clip = el("clipPath", { id: `${id}-torso` }, t);
    el("path", { d }, clip);
    el("rect", { x: 26, y: -130, width: 50, height: 130, fill: shade(s.topColor, 0.86), "clip-path": `url(#${id}-torso)` }, t);
  }
  line(t, d, W);
  const thin = W * 0.55;
  switch (s.top) {
    case "shirt":
      fill(t, "M-20 -126 L-2 -104 L-6 -128 Z", s.topColor, W * 0.8);
      fill(t, "M20 -126 L2 -104 L6 -128 Z", s.topColor, W * 0.8);
      line(t, "M0 -104 L0 -46", thin);
      if (!under() && !ex.includes("tie")) for (const y of [-92, -74, -58]) el("circle", { cx: 0, cy: y, r: 2.6, fill: OUT }, t);
      break;
    case "jacket":
      fill(t, "M-24 -128 Q0 -116 24 -128 L22 -114 Q0 -104 -22 -114 Z", shade(s.topColor, 0.9), W * 0.8);
      line(t, "M0 -110 L0 -46", W * 0.6);
      line(t, "M-46 -54 Q0 -48 46 -54", W * 0.5);
      line(t, "M-40 -80 L-24 -76 M40 -80 L24 -76", W * 0.5);
      break;
    case "coat":
      fill(t, "M-16 -126 L0 -96 L16 -126 Z", "#b9d3e6", W * 0.7);
      line(t, "M-22 -126 L0 -86 L22 -126 M0 -86 L0 -16", thin);
      line(t, "M-46 -52 L-26 -52 L-27 -36 L-45 -36 Z M26 -52 L46 -52 L45 -36 L27 -36 Z", thin);
      line(t, "M24 -98 L40 -98", thin);
      el("path", { d: "M28 -104 L28 -96 M33 -105 L33 -96", stroke: "#2d6fb0", "stroke-width": under() ? 0 : 2.2 }, t);
      break;
    case "scrubs":
      fill(t, "M-18 -126 L0 -100 L18 -126 Z", look.skin, W * 0.7);
      line(t, "M22 -96 L42 -96 L41 -80 L23 -80 Z", thin);
      break;
    case "aodai":
      fill(t, "M-14 -132 L14 -132 L14 -122 Q0 -118 -14 -122 Z", s.topColor, W * 0.7);
      line(t, "M4 -122 Q24 -116 40 -104", thin);
      line(t, "M-42 -50 L-50 -62 M42 -50 L50 -62", thin);
      break;
    case "baba":
      line(t, "M-18 -124 Q0 -110 18 -124", thin);
      line(t, "M0 -114 L0 -36", thin);
      if (!under()) for (const y of [-100, -84, -68, -52]) el("circle", { cx: 0, cy: y, r: 2.4, fill: OUT }, t);
      line(t, "M-48 -66 L-24 -66 L-25 -46 L-47 -46 Z M24 -66 L48 -66 L47 -46 L25 -46 Z", thin);
      break;
    case "dress":
      fill(t, "M-22 -126 Q-12 -110 0 -116 Q12 -110 22 -126 Q0 -118 -22 -126 Z", "#fdfdfc", W * 0.6);
      line(t, "M-50 -84 Q0 -76 50 -84", thin);
      fill(t, "M-6 -86 L6 -86 L6 -76 L-6 -76 Z", shade(s.topColor, 0.8), W * 0.5);
      break;
  }
  if (ex.includes("vest")) {
    const o = "#ef7d2a";
    fill(t, "M-30 -126 Q-48 -120 -50 -100 L-52 -48 L-12 -46 L-10 -110 Z", o, W * 0.8);
    fill(t, "M30 -126 Q48 -120 50 -100 L52 -48 L12 -46 L10 -110 Z", o, W * 0.8);
    for (const y of [-84, -64]) {
      fill(t, `M-50 ${y} L-11 ${y} L-11 ${y + 7} L-50 ${y + 7} Z`, "#dfe4e6", W * 0.5);
      fill(t, `M11 ${y} L50 ${y} L50 ${y + 7} L11 ${y + 7} Z`, "#dfe4e6", W * 0.5);
    }
  }
  if (ex.includes("tie")) {
    fill(t, "M-6 -110 L6 -110 L4 -102 L-4 -102 Z", "#c0392b", W * 0.6);
    fill(t, "M-4 -102 L4 -102 L9 -66 L0 -56 L-9 -66 Z", "#c0392b", W * 0.6);
  }
  if (ex.includes("redscarf")) {
    fill(t, "M-24 -126 Q0 -112 24 -126 L6 -104 L-6 -104 Z", "#d6342c", W * 0.7);
    fill(t, "M-6 -106 L-16 -80 L-4 -84 Z M6 -106 L16 -80 L4 -84 Z", "#d6342c", W * 0.6);
  }
  if (ex.includes("stethoscope")) {
    line(t, "M-18 -126 Q-30 -104 -18 -86 Q-8 -76 2 -84 M18 -126 Q26 -108 22 -96", W * 0.8, "#3a3f45");
    fill(t, "M-2 -90 a7 7 0 1 0 14 0 a7 7 0 1 0 -14 0", "#b8c0c6", W * 0.6);
  }
  if (ex.includes("lanyard")) {
    line(t, "M-14 -126 L16 -88 M16 -126 L18 -88", W * 0.5, "#2d6fb0");
    fill(t, "M7 -88 L29 -88 L29 -62 L7 -62 Z", "#fdfdfc", W * 0.7);
    flat(t, "M9.5 -85.5 L26.5 -85.5 L26.5 -79 L9.5 -79 Z", "#2d6fb0");
    line(t, "M12 -72 L24 -72 M12 -67 L20 -67", 1.6);
  }
  if ((s.prop ?? "none") === "backpack") line(t, "M-30 -124 Q-36 -96 -40 -64 M30 -124 Q36 -96 40 -64", W * 1.6, shade(s.propColor ?? "#3f6ea8", 0.8));
  return t;
}
function drawProp(parent, s, where, que = false) {
  const p = s.prop ?? "none";
  const col = s.propColor;
  if (where === "body" && p === "clipboard") {
    const c = g(parent, { transform: "rotate(-8 -22 -74)" });
    fill(c, "M-44 -102 L-2 -102 L-2 -46 L-44 -46 Z", "#b98a5a");
    fill(c, "M-40 -96 L-6 -96 L-6 -50 L-40 -50 Z", "#fdfdfc", W * 0.6);
    fill(c, "M-30 -106 L-16 -106 L-16 -98 L-30 -98 Z", "#9aa3ab", W * 0.6);
    line(c, "M-34 -88 L-12 -88 M-34 -80 L-12 -80 M-34 -72 L-18 -72 M-34 -64 L-14 -64", 1.8, "#8c96a0");
  }
  if (where === "body" && p === "books") {
    const c = g(parent, { transform: "rotate(-6 -22 -74)" });
    fill(c, "M-46 -100 L-2 -100 L-2 -84 L-46 -84 Z", "#c0392b");
    fill(c, "M-42 -84 L-4 -84 L-4 -66 L-42 -66 Z", "#e2b93b");
    fill(c, "M-46 -66 L-2 -66 L-2 -48 L-46 -48 Z", "#3f7f5f");
    line(c, "M-40 -92 L-10 -92 M-36 -75 L-12 -75 M-40 -57 L-10 -57", 1.8, "#fdfdfc");
  }
  if (where === "ground" && p === "suitcase") {
    const c = g(parent);
    const cc = col ?? "#2f5d6b";
    const body = "M-100 -46 Q-100 -50 -96 -50 L-46 -50 Q-42 -50 -42 -46 L-42 -10 Q-42 -6 -46 -6 L-96 -6 Q-100 -6 -100 -10 Z";
    const gy = que ? -92 : -58;
    line(c, `M-80 -46 L-80 ${gy} M-62 -46 L-62 ${gy}`, W * 0.8, "#6b7178");
    fill(c, `M-86 ${gy - 4} L-58 ${gy - 4} L-58 ${gy + 4} L-86 ${gy + 4} Z`, "#3b302c", W * 0.7);
    fill(c, body, cc);
    if (!under()) el("rect", { x: -66, y: -48, width: 20, height: 40, fill: shade(cc, 0.82) }, c);
    line(c, body, W);
    line(c, "M-86 -46 L-86 -10 M-56 -46 L-56 -10", W * 0.45);
    for (const x of [-90, -52]) fill(c, `M${x - 4} -2 a4 4 0 1 0 8 0 a4 4 0 1 0 -8 0`, "#3b302c", W * 0.5);
  }
  if (where === "ground" && p === "briefcase") {
    const c = g(parent, que ? { transform: "translate(3 -32)" } : {});
    const cc = col ?? "#6b4428";
    line(c, "M-70 -44 Q-70 -52 -62 -52 Q-54 -52 -54 -44", W * 0.9);
    fill(c, "M-88 -42 L-36 -42 Q-32 -42 -32 -38 L-32 -10 Q-32 -6 -36 -6 L-88 -6 Q-92 -6 -92 -10 L-92 -38 Q-92 -42 -88 -42 Z", cc);
    line(c, "M-92 -28 L-32 -28", W * 0.5);
    fill(c, "M-66 -32 L-58 -32 L-58 -24 L-66 -24 Z", "#e2b93b", W * 0.5);
  }
  if (where === "ground" && p === "basket") {
    const c = g(parent, que ? { transform: "translate(3 -28)" } : {});
    const cc = col ?? "#c9a165";
    line(c, "M-86 -36 Q-62 -78 -38 -36", W * 1.1);
    fill(c, "M-92 -36 L-32 -36 L-38 -6 Q-62 0 -86 -6 Z", cc);
    line(c, "M-90 -26 L-34 -26 M-88 -16 L-36 -16 M-72 -36 L-70 -4 M-52 -36 L-52 -4", W * 0.4, shade(cc, 0.7));
    fill(c, "M-80 -38 Q-70 -50 -58 -40 Q-50 -48 -42 -38 Z", "#5f9a4e", W * 0.6);
  }
  if (where === "ground" && p === "cane") {
    const c = g(parent);
    const d = que ? "M-50 -80 Q-50 -94 -60 -94 Q-70 -94 -70 -82 L-74 0" : "M-54 -50 Q-54 -60 -64 -60 Q-74 -60 -74 -50 L-76 0";
    line(c, d, W * 1.7, OUT);
    if (!under()) line(c, d, W * 0.8, "#9a6a3c");
  }
  if (where === "back" && p === "backpack") {
    const cc = col ?? "#3f6ea8";
    fill(parent, "M-58 -118 Q-62 -128 -46 -130 L46 -130 Q62 -128 58 -118 L62 -56 Q0 -48 -62 -56 Z", cc);
    fill(parent, "M-66 -92 L-56 -92 L-56 -64 L-66 -64 Z M56 -92 L66 -92 L66 -64 L56 -64 Z", shade(cc, 0.82), W * 0.7);
  }
  if (where === "back" && p === "ganh") {
    const cc = col ?? "#c9a165";
    line(parent, "M-150 -132 L150 -132", W * 3.2, OUT);
    if (!under()) line(parent, "M-150 -132 L150 -132", W * 1.8, "#b98a5a");
    for (const sd of [-1, 1]) {
      const x = sd * 130;
      line(parent, `M${x} -132 L${x - 24} -64 M${x} -132 L${x + 24} -64`, W * 0.5);
      fill(parent, `M${x - 34} -64 L${x + 34} -64 L${x + 26} -24 Q${x} -16 ${x - 26} -24 Z`, cc);
      line(parent, `M${x - 32} -52 L${x + 32} -52 M${x - 29} -38 L${x + 29} -38`, W * 0.4, shade(cc, 0.7));
      fill(parent, `M${x - 26} -66 Q${x - 14} -84 ${x} -68 Q${x + 12} -84 ${x + 26} -66 Z`, sd < 0 ? "#e0613f" : "#7cb34c", W * 0.6);
    }
  }
}
function drawArm(parent, s, look, side) {
  const root = g(parent);
  const longSleeve = s.sleeve === "long";
  const sleeve = s.topColor;
  if (longSleeve) fill(root, `M-12 -6 Q0 -12 12 -6 L11 ${UPPER + 2} L-11 ${UPPER + 2} Z`, sleeve);
  else {
    fill(root, `M-9 6 L9 6 L9 ${UPPER + 2} L-9 ${UPPER + 2} Z`, look.skin);
    fill(root, "M-12 -6 Q0 -12 12 -6 L12 16 L-12 16 Z", sleeve);
  }
  if ((s.extras ?? []).includes("vest")) fill(root, "M-12 -6 Q0 -12 12 -6 L12 6 L-12 6 Z", "#ef7d2a", W * 0.7);
  const elbow = g(root);
  if (longSleeve) {
    fill(elbow, `M-11 -4 L11 -4 L10 ${FORE - 4} L-10 ${FORE - 4} Z`, sleeve);
    line(elbow, `M-10 ${FORE - 8} L10 ${FORE - 8}`, W * 0.45);
  } else fill(elbow, `M-8 -4 L8 -4 L8 ${FORE - 4} L-8 ${FORE - 4} Z`, look.skin);
  fill(elbow, `M-11 ${FORE + 4} Q-12 ${FORE - 8} 0 ${FORE - 8} Q12 ${FORE - 8} 11 ${FORE + 4} Q10 ${FORE + 16} 0 ${FORE + 16} Q-10 ${FORE + 16} -11 ${FORE + 4} Z`, look.skin);
  line(elbow, `M${-side * 8} ${FORE + 2} Q${-side * 15} ${FORE} ${-side * 12} ${FORE - 6}`, W * 0.6);
  return { root, elbow, side };
}
function drawHairBack(parent, s, hair) {
  if (s.hair === "long") {
    fill(parent, "M-80 -96 C-92 -36 -90 24 -78 62 Q-60 74 -40 62 Q0 70 40 62 Q60 74 78 62 C90 24 92 -36 80 -96 Z", hair);
    line(parent, "M-62 0 Q-64 30 -60 58 M62 0 Q64 30 60 58", W * 0.45, shade(hair, 0.7));
  }
}
function drawHead(parent, s, look, hair) {
  const head = g(parent);
  const hairDark = shade(hair, 0.72);
  const hat = s.hat ?? "none";
  let tail;
  if (s.hair === "ponytail") {
    tail = g(head);
    fill(tail, "M40 -118 C100 -112 112 -46 86 -6 C80 -30 66 -46 52 -64 Z", hair);
    line(tail, "M70 -90 C82 -70 86 -50 84 -30", W * 0.45, hairDark);
    fill(head, "M40 -122 Q50 -128 56 -116 Q50 -108 42 -112 Z", "#d0464b", W * 0.7);
  }
  if (s.hair === "bun" && hat !== "nonla") {
    fill(head, "M-26 -150 a26 22 0 1 0 52 0 a26 22 0 1 0 -52 0", hair);
    line(head, "M-14 -156 Q0 -164 14 -156", W * 0.45, hairDark);
  }
  if (s.hair === "pigtails") {
    for (const sd of [-1, 1]) {
      fill(head, `M${sd * 66} -96 Q${sd * 118} -100 ${sd * 112} -44 Q${sd * 104} -22 ${sd * 92} -30 Q${sd * 96} -60 ${sd * 66} -70 Z`, hair);
      fill(head, `M${sd * 62} -98 a8 8 0 1 0 ${sd * 16} 0 a8 8 0 1 0 ${-sd * 16} 0`, "#e0613f", W * 0.6);
    }
  }
  fill(head, "M-80 -62 C-82 -124 -44 -150 0 -150 C44 -150 82 -124 80 -62 C80 -40 72 -30 66 -26 L-66 -26 C-72 -30 -80 -40 -80 -62 Z", hair);
  for (const sd of [-1, 1]) fill(head, `M${sd * 70} -70 Q${sd * 86} -72 ${sd * 84} -54 Q${sd * 82} -40 ${sd * 68} -42`, look.skin);
  fill(head, "M-74 -62 C-74 -116 -42 -140 0 -140 C42 -140 74 -116 74 -62 C74 -22 42 0 0 0 C-42 0 -74 -22 -74 -62 Z", look.skin);
  flat(head, "M-40 -6 Q0 8 40 -6 Q20 0 0 0 Q-20 0 -40 -6 Z", shade(look.skin, 0.9));
  const face = g(head);
  let faceOut = { root: face, eyes: {}, mouths: [], brows: {} };
  if (!under()) faceOut = drawFace(face, s, look);
  const fringe = {
    ponytail: "M-76 -60 C-82 -116 -44 -146 0 -146 C44 -146 82 -116 76 -60 L68 -78 Q58 -96 42 -98 Q32 -82 12 -80 Q8 -96 0 -100 Q-14 -84 -34 -82 Q-46 -96 -58 -92 Q-68 -82 -76 -60 Z",
    short: "M-76 -64 C-82 -118 -44 -146 0 -146 C44 -146 82 -118 76 -64 L70 -80 L60 -90 L52 -84 L40 -96 L30 -86 L16 -98 L4 -88 L-10 -98 L-22 -86 L-36 -96 L-48 -84 L-60 -92 L-70 -80 Z",
    side: "M-76 -64 C-82 -118 -44 -148 0 -148 C44 -148 82 -118 76 -64 L72 -84 Q62 -102 30 -104 Q-6 -104 -28 -88 Q-34 -98 -46 -94 Q-64 -86 -76 -64 Z",
    bun: "M-76 -62 C-82 -116 -44 -146 0 -146 C44 -146 82 -116 76 -62 Q66 -96 34 -106 Q12 -110 0 -98 Q-12 -110 -34 -106 Q-66 -96 -76 -62 Z",
    long: "M-78 -40 C-84 -116 -44 -148 0 -148 C44 -148 84 -116 78 -40 Q72 -90 40 -104 Q14 -110 0 -98 Q-14 -110 -40 -104 Q-72 -90 -78 -40 Z",
    pigtails: "M-76 -62 C-82 -116 -44 -146 0 -146 C44 -146 82 -116 76 -62 L66 -80 Q50 -94 30 -92 Q24 -82 12 -82 Q4 -96 -8 -90 Q-20 -80 -34 -84 Q-54 -96 -66 -80 Z"
  };
  fill(head, fringe[s.hair], hair);
  if (s.hair === "side") line(head, "M-28 -88 Q-10 -110 20 -114", W * 0.45, hairDark);
  if (s.hair === "bun" || s.hair === "long") line(head, "M0 -98 L0 -130", W * 0.45, hairDark);
  if (hat === "officer") {
    const c = s.hatColor ?? "#2c3b52";
    fill(head, "M-66 -112 C-78 -132 -82 -150 -62 -158 C-22 -170 22 -170 62 -158 C82 -150 78 -132 66 -112 Z", c);
    fill(head, "M-64 -116 L64 -116 L62 -98 L-62 -98 Z", shade(c, 0.85));
    line(head, "M-60 -108 L60 -108", W * 0.5, "#d9b44a");
    fill(head, "M-62 -100 Q0 -88 62 -100 Q0 -82 -62 -100 Z", "#1e1e22", W * 0.6);
    fill(head, "M-11 -136 a11 11 0 1 0 22 0 a11 11 0 1 0 -22 0", "#e2b93b", W * 0.6);
    if (!under()) el("path", { d: "M0 -142 L3 -136 L0 -130 L-3 -136 Z", fill: "#c0392b" }, head);
  } else if (hat === "cap") {
    const c = s.hatColor ?? "#2b2b2b";
    fill(head, "M-72 -96 C-78 -136 -40 -158 0 -158 C40 -158 78 -136 72 -96 Z", c);
    line(head, "M0 -158 L0 -100 M-36 -150 Q-44 -124 -40 -100 M36 -150 Q44 -124 40 -100", W * 0.45, shade(c, 1.6));
    fill(head, "M-6 -160 a6 4 0 1 0 12 0 a6 4 0 1 0 -12 0", c, W * 0.6);
    fill(head, "M-78 -98 Q0 -116 78 -98 Q88 -88 72 -84 Q0 -98 -72 -84 Q-88 -88 -78 -98 Z", shade(c, 1.35));
  } else if (hat === "hardhat") {
    const c = s.hatColor ?? "#e5b53a";
    fill(head, "M-74 -100 C-78 -142 -40 -164 0 -164 C40 -164 78 -142 74 -100 Z", c);
    if (!under()) el("path", { d: "M20 -156 Q56 -146 66 -104 L48 -104 Q44 -136 20 -150 Z", fill: shade(c, 0.86) }, head);
    line(head, "M-74 -100 C-78 -142 -40 -164 0 -164 C40 -164 78 -142 74 -100", W);
    fill(head, "M-12 -166 L12 -166 L10 -104 L-10 -104 Z", shade(c, 1.08), W * 0.7);
    fill(head, "M-88 -104 Q0 -116 88 -104 L86 -94 Q0 -104 -86 -94 Z", c);
  } else if (hat === "nurse") {
    const c = s.hatColor ?? "#fdfdfc";
    fill(head, "M-42 -130 Q0 -152 42 -130 L48 -110 Q0 -124 -48 -110 Z", c);
    if (!under()) el("path", { d: "M-3 -140 L3 -140 L3 -134 L9 -134 L9 -128 L3 -128 L3 -122 L-3 -122 L-3 -128 L-9 -128 L-9 -134 L-3 -134 Z", fill: "#d6342c" }, head);
  } else if (hat === "nonla") {
    const c = s.hatColor ?? "#e9d7a3";
    if (!under()) line(head, "M-60 -92 Q-60 -40 -30 -6 M60 -92 Q60 -40 30 -6", W * 0.4, "#7a5a3a");
    fill(head, "M-128 -98 L0 -206 L128 -98 Q0 -78 -128 -98 Z", c);
    line(head, "M0 -206 L-70 -88 M0 -206 L-24 -82 M0 -206 L24 -82 M0 -206 L70 -88", W * 0.4, shade(c, 0.72));
    line(head, "M-104 -118 Q0 -104 104 -118 M-74 -144 Q0 -134 74 -144", W * 0.4, shade(c, 0.72));
  }
  return { face: faceOut, tail };
}
function drawFace(face, s, look) {
  const ex = s.extras ?? [];
  const blush = look.blush ?? 0.75;
  for (const sd of [-1, 1]) el("ellipse", { cx: sd * 46, cy: -36, rx: 13, ry: 7, fill: "#f09a90", opacity: blush }, face);
  line(face, "M-2 -44 Q4 -40 -1 -36", W * 0.55);
  if (s.build === "elder") line(face, "M-52 -46 Q-46 -42 -42 -46 M52 -46 Q46 -42 42 -46", W * 0.4);
  const eyes = {};
  const eyeOpen = (gg, sd) => {
    el("ellipse", { cx: sd * 28, cy: -54, rx: 8, ry: 11, fill: OUT }, gg);
    el("circle", { cx: sd * 28 + 2.5, cy: -58, r: 3.2, fill: "#fff" }, gg);
  };
  const shut = (gg, sd, kind) => {
    const x = sd * 28;
    if (kind === "down") line(gg, `M${x - 10} -54 Q${x} -46 ${x + 10} -54`, W * 0.8);
    else if (kind === "up") line(gg, `M${x - 10} -50 Q${x} -62 ${x + 10} -50`, W * 0.8);
    else line(gg, `M${x + sd * 9} -61 L${x - sd * 9} -54 L${x + sd * 9} -47`, W * 0.8);
  };
  const mk = (name, fn) => {
    const gg = g(face, { display: "none" });
    fn(gg);
    eyes[name] = gg;
  };
  mk("open", (gg) => {
    eyeOpen(gg, -1);
    eyeOpen(gg, 1);
  });
  mk("closed", (gg) => {
    shut(gg, -1, "down");
    shut(gg, 1, "down");
  });
  mk("happy", (gg) => {
    shut(gg, -1, "up");
    shut(gg, 1, "up");
  });
  mk("wink", (gg) => {
    eyeOpen(gg, -1);
    shut(gg, 1, "wink");
  });
  mk("deadpan", (gg) => {
    for (const sd of [-1, 1]) {
      const x = sd * 28;
      el("path", { d: `M${x - 13} -56 L${x + 13} -56 L${x + 12} -50 Q${x} -42 ${x - 12} -50 Z`, fill: "#fff", stroke: OUT, "stroke-width": W * 0.7, "stroke-linejoin": "round" }, gg);
      el("circle", { cx: x, cy: -51, r: 4.5, fill: OUT }, gg);
    }
  });
  mk("surprised", (gg) => {
    for (const sd of [-1, 1]) {
      el("circle", { cx: sd * 28, cy: -54, r: 12, fill: "#fff", stroke: OUT, "stroke-width": W * 0.7 }, gg);
      el("circle", { cx: sd * 28, cy: -54, r: 4.5, fill: OUT }, gg);
    }
  });
  const brows = {};
  const browCol = s.hairColor ?? OUT;
  const mb = (name, l, r) => {
    const gg = g(face, { display: "none" });
    line(gg, l, W * 0.75, browCol);
    line(gg, r, W * 0.75, browCol);
    brows[name] = gg;
  };
  mb("normal", "M-40 -76 Q-29 -81 -18 -77", "M18 -77 Q29 -81 40 -76");
  mb("up", "M-40 -82 Q-29 -90 -18 -84", "M18 -84 Q29 -90 40 -82");
  mb("worried", "M-40 -76 Q-30 -78 -18 -84", "M18 -84 Q30 -78 40 -76");
  mb("flat", "M-40 -74 L-18 -74", "M18 -74 L40 -74");
  if (ex.includes("glasses")) {
    const gl = g(face);
    for (const sd of [-1, 1]) el("rect", { x: sd * 28 - 16, y: -68, width: 32, height: 27, rx: 9, fill: "#ffffff", "fill-opacity": 0.18, stroke: OUT, "stroke-width": W * 0.65 }, gl);
    line(gl, "M-12 -56 Q0 -61 12 -56 M-44 -58 L-64 -62 M44 -58 L64 -62", W * 0.6);
  }
  const mouths = [];
  const mm = (fn) => {
    const gg = g(face, { display: "none" });
    fn(gg);
    mouths.push(gg);
  };
  mm((gg) => line(gg, "M-8 -24 Q0 -19 8 -24", W * 0.7));
  mm((gg) => {
    el("ellipse", { cx: 0, cy: -22, rx: 5, ry: 5.5, fill: OUT }, gg);
  });
  mm((gg) => {
    fill(gg, "M-10 -26 Q0 -28 10 -26 Q10 -12 0 -12 Q-10 -12 -10 -26 Z", "#7a2e2a", W * 0.6);
    flat(gg, "M-6 -15 Q0 -20 6 -15 Q0 -12.5 -6 -15 Z", "#e07a74");
  });
  mm((gg) => {
    fill(gg, "M-14 -28 Q0 -31 14 -28 Q13 -8 0 -8 Q-13 -8 -14 -28 Z", "#7a2e2a", W * 0.6);
    flat(gg, "M-9 -12 Q0 -19 9 -12 Q0 -8.5 -9 -12 Z", "#e07a74");
  });
  let mask;
  if (ex.includes("mask")) {
    for (const sd of [-1, 1]) line(face, `M${sd * 40} -38 Q${sd * 62} -46 ${sd * 72} -58`, W * 0.5, "#b8c4cc");
    mask = g(face);
    fill(mask, "M-42 -42 Q0 -48 42 -42 L38 -12 Q0 2 -38 -12 Z", "#e8f0f4");
    line(mask, "M-36 -32 Q0 -36 36 -32 M-34 -22 Q0 -26 34 -22", W * 0.4, "#a9b6bf");
  }
  return { root: face, eyes, mouths, brows, mask };
}
var REST = { u1: 10, u2: 6 };
var HOLD = {
  clipboard: { u1: 10, u2: -100 },
  books: { u1: 10, u2: -100 },
  suitcase: { u1: 28, u2: 0 },
  briefcase: { u1: 14, u2: 0 },
  basket: { u1: 14, u2: 0 },
  cane: { u1: 14, u2: 0 },
  ganh: { u1: 60, u2: 105 }
};
function gesturePose(gest, k) {
  switch (gest) {
    case "wave":
      return { u1: 125, u2: 35 + 25 * Math.sin(k * 11) };
    case "point":
      return { u1: 86, u2: 2 };
    case "present":
      return { u1: 52, u2: 34 + 4 * Math.sin(k * 3) };
    case "talk":
      return { u1: 18, u2: -112 + 12 * Math.sin(k * 7) };
    case "sweep":
      return { u1: 52 + 26 * Math.sin(k * 2.2), u2: 22 };
    default:
      return REST;
  }
}
function createChibi(layer, spec, opt, uid, sticker = 7) {
  checkSpec(spec);
  const look = LOOKS[spec.id] ?? DEFAULT_LOOK;
  const hair = spec.hairColor ?? look.hair;
  const B = BUILD[spec.build];
  const h = spec.height ?? 1;
  const bodyK = B.body * h, headK = B.head * h;
  const stoop = (spec.stoop ?? 0) * 0.9;
  const holds = spec.prop ?? "none";
  const que = opt.limbs === "que";
  const root = g(layer);
  const flip = g(root);
  const build = (r, id) => {
    setUnder(r);
    const body = g(flip, { transform: `scale(${f(bodyK)})` });
    drawProp(g(body), spec, "ground", que);
    const qLegs = que ? drawQueLegs(body, spec, look) : [];
    const legs = que ? [g(body), g(body)] : drawLegs(body, spec, look);
    const upper = g(body);
    const hairBack = g(upper);
    drawHairBack(hairBack, spec, hair);
    drawProp(upper, spec, "back");
    const qBack = que ? drawQueArm(upper, spec, -1) : null;
    const armBack = que ? { root: g(upper), elbow: g(upper), side: -1 } : drawArm(upper, spec, look, -1);
    drawTorso(upper, spec, look, id);
    fill(upper, "M-13 -142 L13 -142 L13 -122 L-13 -122 Z", shade(look.skin, 0.88), W * 0.8);
    const headWrap = g(upper);
    const { face: face2, tail } = drawHead(headWrap, spec, look, hair);
    drawProp(upper, spec, "body");
    const qFront = que ? drawQueArm(upper, spec, 1) : null;
    const armFront = que ? { root: g(upper), elbow: g(upper), side: 1 } : drawArm(upper, spec, look, 1);
    const itemG = g(upper, { display: "none" });
    if (que) drawFlashlight(itemG, id + "den", r === 0);
    if (holds === "clipboard" || holds === "books" || holds === "ganh") {
      upper.appendChild(armBack.root);
      if (qBack) for (const n of [qBack.stick, qBack.hand, qBack.sleeveO, qBack.sleeveI]) upper.appendChild(n);
    }
    setUnder(0);
    return { legs, upper, hairBack, headWrap, armBack, armFront, face: face2, tail, qLegs, qBack, qFront, itemG };
  };
  const parts = sticker > 0 ? [build(sticker / bodyK, uid + "u"), build(0, uid)] : [build(0, uid)];
  const face = parts[parts.length - 1].face;
  const blinkSeed = hash(spec.id);
  let x = opt.x, y = opt.y, scale = opt.scale ?? 1, dir = opt.dir ?? 1;
  let flipFrom = dir, flipAt = -10;
  let target = null, walkPhase = 0, walking = false, running = false;
  let sitting = false, sitAt = -10;
  let gest = null;
  let item = null;
  let exprState = { name: "neutral", t1: Infinity };
  let speakUntil = -1, speakFrom = -1;
  let now = 0;
  const headScale = headK / bodyK;
  const setPose = (a, p, swing = 0) => {
    const u1 = p.u1 + swing;
    a.root.setAttribute("transform", `translate(${a.side * 44} ${SHOULDER_Y + 6}) rotate(${f(-a.side * u1)})`);
    a.elbow.setAttribute("transform", `translate(0 ${UPPER}) rotate(${f(-a.side * p.u2)})`);
  };
  const show = (rec, key) => {
    for (const k in rec) rec[k].setAttribute("display", k === String(key) ? "inline" : "none");
  };
  const c = {
    spec,
    root,
    get x() {
      return x;
    },
    set x(v) {
      x = v;
    },
    get y() {
      return y;
    },
    set y(v) {
      y = v;
    },
    get scale() {
      return scale;
    },
    set scale(v) {
      scale = v;
    },
    get dir() {
      return dir;
    },
    set dir(v) {
      dir = v;
    },
    walkTo(tx) {
      target = tx;
      running = false;
      if (sitting) c.sit(false);
      if (Math.abs(tx - x) > 1) c.face(tx > x ? 1 : -1);
    },
    runTo(tx) {
      c.walkTo(tx);
      running = true;
    },
    sit(on) {
      if (on !== sitting) {
        sitting = on;
        sitAt = now;
      }
    },
    act(name, seconds) {
      gest = { name, t0: now, t1: now + Math.max(0.6, seconds) };
    },
    hold(it) {
      item = que ? it : null;
    },
    face(d) {
      if (d !== dir) {
        flipFrom = dir;
        dir = d;
        flipAt = now;
      }
    },
    expr(name, seconds) {
      exprState = { name, t1: seconds ? now + seconds : Infinity };
    },
    say(seconds) {
      speakFrom = now;
      speakUntil = now + seconds;
    },
    update(t, dt, speech) {
      now = t;
      walking = false;
      if (target !== null) {
        const sitK0 = clamp((t - sitAt) / 0.35);
        const ready = sitting ? false : sitK0 >= 1;
        const d = target - x, step = B.speed * scale * dt * (running ? 2.3 : 1);
        if (!ready) {
        } else if (Math.abs(d) <= step) {
          x = target;
          target = null;
          running = false;
        } else {
          x += Math.sign(d) * step;
          walking = true;
          walkPhase += dt * (spec.build === "elder" ? 6 : 9) * (running ? 1.6 : 1);
        }
      }
      const fk = clamp((t - flipAt) / 0.16);
      const sx = fk >= 1 ? dir : lerp(flipFrom, dir, ease(fk));
      root.setAttribute("transform", `translate(${f(x)} ${f(y)}) scale(${f(scale)})`);
      flip.setAttribute("transform", `scale(${f(Math.abs(sx) < 0.04 ? 0.04 * Math.sign(sx || 1) : sx)} 1)`);
      const bob = walking ? -Math.abs(Math.sin(walkPhase)) * (running ? 16 : 10) : Math.sin(t * 2.1 + blinkSeed * 6) * 1.2;
      const sk = ease(clamp((t - sitAt) / 0.35));
      const sitK = sitting ? sk : 1 - sk;
      const lsy = f(1 - 0.4 * sitK);
      const l0 = `translate(0 ${f(walking ? Math.min(0, Math.sin(walkPhase) * 8) : 0)}) scale(1 ${lsy})`;
      const l1 = `translate(0 ${f(walking ? Math.min(0, -Math.sin(walkPhase) * 8) : 0)}) scale(1 ${lsy})`;
      let w = 0, k = 0, gname = null;
      if (gest && t < gest.t1 + 0.3) {
        gname = gest.name;
        k = t - gest.t0;
        w = walking ? 0 : ease(Math.min((t - gest.t0) / 0.25, (gest.t1 + 0.3 - t) / 0.3));
      } else gest = null;
      const sw = walking ? Math.sin(walkPhase) * (running ? 30 : 16) : 0;
      const armGest = gname ? gesturePose(gname, k) : REST;
      const base = item ? { u1: 40, u2: 26 } : REST;
      const fp = { u1: lerp(base.u1, armGest.u1, w), u2: lerp(base.u2, armGest.u2, w) };
      let hy = stoop, hr = 0, by = 0;
      if (gname === "nod") hy += w * Math.max(0, Math.sin(k * 7)) * 6;
      if (gname === "bow") {
        hy += w * 12;
        by = w * 6;
      }
      const talking = t >= speakFrom && t < speakUntil;
      hr += talking ? Math.sin(t * 4.3) * 2.2 : Math.sin(t * 0.9 + blinkSeed * 9) * 1.2;
      const ht = `translate(0 ${f(NECK_Y + hy)}) rotate(${f(hr)}) scale(${f(headScale)})`;
      const tr = `rotate(${f(walking ? Math.sin(walkPhase * 2) * 5 : Math.sin(t * 1.7) * 2)} 46 -116)`;
      const raise = que ? lerp(-RAISE, -14, sitK) : 16 * sitK;
      for (const p of parts) {
        p.upper.setAttribute("transform", `translate(0 ${f(bob + by + raise)})`);
        p.legs[0].setAttribute("transform", l0);
        p.legs[1].setAttribute("transform", l1);
        setPose(p.armFront, fp, sw);
        setPose(p.armBack, HOLD[holds] ?? REST, HOLD[holds] ? 0 : -sw);
        if (que) {
          poseQueLegs(p.qLegs, -46 + bob + by + raise, walkPhase, walking, spec.top === "coat" || spec.top === "aodai" || spec.top === "dress" ? 0 : 12, sitK, running);
          const hf = poseQueArm(p.qFront, fp.u1 + (item ? sw * 0.3 : sw), fp.u2);
          const hb = HOLD[holds] ?? REST;
          poseQueArm(p.qBack, hb.u1 + (HOLD[holds] ? 0 : -sw), hb.u2);
          p.itemG.setAttribute("display", item ? "inline" : "none");
          if (item) p.itemG.setAttribute("transform", `translate(${f(hf.hand[0])} ${f(hf.hand[1])}) rotate(${f(hf.angle)})`);
        }
        p.headWrap.setAttribute("transform", ht);
        p.hairBack.setAttribute("transform", ht);
        p.tail?.setAttribute("transform", tr);
      }
      face.root.setAttribute("transform", "translate(6 0)");
      if (exprState.t1 <= t) exprState = { name: "neutral", t1: Infinity };
      const ex = exprState.name;
      const period = 3.1 + blinkSeed * 1.6;
      const ph = (t + blinkSeed * period) % period;
      const blink = ph < 0.13 && (ex === "neutral" || ex === "surprised" || ex === "worried");
      show(face.eyes, blink ? "closed" : ex === "neutral" || ex === "worried" ? "open" : ex);
      show(face.brows, ex === "surprised" || ex === "happy" ? "up" : ex === "worried" ? "worried" : ex === "deadpan" ? "flat" : "normal");
      let m = 0;
      if (talking) {
        const s = speech(t);
        const lvl = s === null ? Math.max(0, Math.sin(t * 13) * 0.6 + Math.sin(t * 7.1) * 0.4) : s;
        m = lvl < 0.12 ? 0 : lvl < 0.4 ? 1 : lvl < 0.72 ? 2 : 3;
      } else if (ex === "surprised") m = 1;
      else if (ex === "happy") m = 2;
      show(face.mouths, m);
      if (face.mask) face.mask.setAttribute("transform", `translate(0 -26) scale(1 ${f(1 + m * 0.05)}) translate(0 26)`);
    }
  };
  c.update(0, 0, () => null);
  return c;
}

// chibi/src/stage.ts
var STEP = 1 / 60;
function speechAt(t) {
  const S = window.SPEECH;
  if (!S) return null;
  const i = Math.floor(t * S.fps);
  return i >= 0 && i < S.env.length ? S.env[i] : 0;
}
function createChibiStage(svg, opt) {
  const { width, height } = opt;
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  const sticker = opt.sticker ?? 7;
  const back = el("g", {}, svg), people = el("g", {}, svg), front = el("g", {}, svg);
  let setupFn = null;
  let cast = [];
  let cues = [];
  let simT = 0, built = false, n = 0;
  const C = {
    svg,
    back,
    people,
    front,
    width,
    height,
    get time() {
      return simT;
    },
    setup(fn) {
      setupFn = fn;
      built = false;
    },
    add(who, o) {
      const spec = typeof who === "string" ? byId(who) : who;
      const c = createChibi(people, spec, o, `ch${n++}`, sticker);
      cast.push(c);
      return c;
    },
    at(t, fn) {
      cues.push({ t, fn, done: false });
    },
    shade(opacity = 0.4, colour = "#0a0c14") {
      const defs = el("defs", {}, back);
      const rg = el("radialGradient", { id: "cb-vig", cx: 0.5, cy: 0.55, r: 0.75 }, defs);
      el("stop", { offset: 0.35, "stop-color": "#000", "stop-opacity": 0 }, rg);
      el("stop", { offset: 1, "stop-color": "#000", "stop-opacity": Math.min(0.85, opacity * 1.9) }, rg);
      el("rect", { width, height, fill: colour, opacity }, back);
      el("rect", { width, height, fill: "url(#cb-vig)" }, back);
    },
    bench(x, y, scale, w = 170, seat = 60) {
      const b = el("g", { transform: `translate(${f(x)} ${f(y)}) scale(${f(scale)})` }, back);
      const top = -seat;
      for (const sd of [-1, 1]) line(b, `M${sd * (w / 2 - 14)} ${top} L${sd * (w / 2 - 14)} 0`, W * 1.4, OUT);
      fill(b, `M${-w / 2} ${top - 12} L${w / 2} ${top - 12} L${w / 2} ${top + 4} L${-w / 2} ${top + 4} Z`, "#8a6a4a");
      line(b, `M${-w / 2 + 6} ${top - 4} L${w / 2 - 6} ${top - 4}`, W * 0.4, "#5e4630");
    },
    render(t) {
      if (!built || t < simT - 1e-6) rebuild();
      fire(simT);
      while (simT < t - 1e-9) {
        const dt = Math.min(STEP, t - simT);
        simT += dt;
        fire(simT);
        for (const c of cast) c.update(simT, dt, speechAt);
      }
    }
  };
  function fire(now) {
    for (const q of cues) if (!q.done && q.t <= now + 1e-9) {
      q.done = true;
      q.fn();
    }
  }
  function rebuild() {
    for (const layer of [back, people, front]) while (layer.firstChild) layer.removeChild(layer.firstChild);
    cast = [];
    cues = [];
    simT = 0;
    n = 0;
    setupFn?.(C);
    for (const c of cast) c.update(0, 0, speechAt);
    built = true;
  }
  return C;
}
export {
  LOOKS,
  OUT,
  ROSTER,
  W,
  byId,
  createChibi,
  createChibiStage,
  el,
  fill,
  flat,
  g,
  line,
  shade,
  speechAt
};
