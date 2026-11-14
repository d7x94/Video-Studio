// lineart.js: dan nhan vat net muc cho video-studio. Build tu lib/ cua JDhruv14/line-art-animation (MIT, xem LICENSE-line-art-animation.txt) va cast/ (rig, roster, stage). Khong sua tay: sua nguon roi build lai.

// lib/ink.ts
var NS = "http://www.w3.org/2000/svg";
var INK = "currentColor";
var PAPER = "#fdfdfc";
var INK_DAY = "#1c1c1c";
var PEN = 1.35;
function el(tag, attrs = {}, parent) {
  const n = document.createElementNS(NS, tag);
  for (const k in attrs) n.setAttribute(k, String(attrs[k]));
  if (attrs.fill === PAPER) n.classList.add("pp");
  if (parent) parent.appendChild(n);
  return n;
}
var f = (n) => n.toFixed(2);
var pt = (p) => `${f(p[0])} ${f(p[1])}`;
var pen = (parent, w = PEN) => el("path", { fill: "none", stroke: INK, "stroke-width": w, "stroke-linecap": "round", "stroke-linejoin": "round" }, parent);
var shape = (parent, w = PEN) => el("path", { fill: PAPER, stroke: INK, "stroke-width": w, "stroke-linejoin": "round", "stroke-linecap": "round" }, parent);
var blot = (parent) => el("path", { fill: INK }, parent);
var paint = (parent, colour, w = PEN) => el("path", { fill: colour, stroke: INK, "stroke-width": w, "stroke-linejoin": "round", "stroke-linecap": "round" }, parent);
function limb(parent, width, w = PEN) {
  const g = el("g", {}, parent);
  const fill = el("path", { fill: PAPER }, g);
  const a = pen(g, w), b = pen(g, w);
  const half = (width - w) / 2;
  return {
    g,
    draw(joints, endGap = [0.4, 0.9]) {
      const s = joints[0], e = joints[joints.length - 1];
      let c = [(s[0] + e[0]) / 2, (s[1] + e[1]) / 2];
      if (joints.length === 3) {
        const m = joints[1];
        c = [m[0] + 0.55 * (m[0] - c[0]), m[1] + 0.55 * (m[1] - c[1])];
      }
      const P2 = [];
      for (let i = 0; i <= 16; i++) {
        const t = i / 16, u = 1 - t;
        P2.push([u * u * s[0] + 2 * u * t * c[0] + t * t * e[0], u * u * s[1] + 2 * u * t * c[1] + t * t * e[1]]);
      }
      const side = (sgn) => P2.map((p, i) => {
        const q = P2[Math.min(P2.length - 1, i + 1)], o = P2[Math.max(0, i - 1)];
        const dx = q[0] - o[0], dy = q[1] - o[1], l = Math.hypot(dx, dy) || 1;
        return [p[0] - dy / l * half * sgn, p[1] + dx / l * half * sgn];
      });
      const L = side(1), R = side(-1);
      fill.setAttribute("d", "M" + L.map(pt).join("L") + "L" + R.slice().reverse().map(pt).join("L") + "Z");
      const cut = (arr, gap) => arr.slice(0, arr.length - Math.round(gap * 2));
      a.setAttribute("d", "M" + cut(L, endGap[0]).map(pt).join("L"));
      b.setAttribute("d", "M" + cut(R, endGap[1]).map(pt).join("L"));
    }
  };
}
function solid(l, colour = INK) {
  const n = l.g.querySelector("path");
  if (n) {
    n.classList.remove("pp");
    n.setAttribute("fill", colour);
  }
  return l;
}
function inkDefs(svg, id = "ink") {
  if (!svg.style.color) svg.style.color = INK_DAY;
  const defs = el("defs", {}, svg);
  const flt = el("filter", { id: `${id}-edge`, x: "-2%", y: "-2%", width: "104%", height: "104%" }, defs);
  el("feTurbulence", { type: "fractalNoise", baseFrequency: "0.6", numOctaves: 1, seed: 7, result: "n" }, flt);
  el("feDisplacementMap", { in: "SourceGraphic", in2: "n", scale: 0.45, xChannelSelector: "R", yChannelSelector: "G", result: "d" }, flt);
  el("feGaussianBlur", { in: "d", stdDeviation: 0.12 }, flt);
  const stripes = el("pattern", { id: `${id}-stripes`, width: 4, height: 2.2, patternUnits: "userSpaceOnUse", patternTransform: "rotate(-12)" }, defs);
  el("rect", { width: 4, height: 2.2, fill: PAPER }, stripes);
  el("rect", { width: 4, height: 1, fill: INK }, stripes);
  return { defs, filter: `url(#${id}-edge)`, stripes: `url(#${id}-stripes)` };
}

// lib/gait.ts
var clamp = (x, a, b) => Math.max(a, Math.min(b, x));
var smooth = (e0, e1, x) => {
  const t = clamp((x - e0) / (e1 - e0), 0, 1);
  return t * t * (3 - 2 * t);
};
var minJerk = (s) => s * s * s * (10 - 15 * s + 6 * s * s);
function knee(hip, ankle, l1, l2) {
  const dx = ankle[0] - hip[0], dy = ankle[1] - hip[1];
  const d = Math.min(Math.hypot(dx, dy), l1 + l2 - 0.01);
  const th = Math.atan2(dy, dx);
  const al = Math.acos(clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1));
  const c1 = [hip[0] + l1 * Math.cos(th - al), hip[1] + l1 * Math.sin(th - al)];
  const c2 = [hip[0] + l1 * Math.cos(th + al), hip[1] + l1 * Math.sin(th + al)];
  return c1[0] > c2[0] ? c1 : c2;
}
var GAIT_PRESETS = {
  // natural adult walk, ~2 steps/s
  walk: { period: 1, duty: 0.62, stride: 24, lift: 3.4, heelOff: 15, heelKick: 0, thigh: 23, shin: 23, ankleY: 118.4, ground: 120, toe: 4.2 },
  // kimono, tight skirt, geta: shorter stride, very low lift
  shuffle: { period: 0.9, duty: 0.64, stride: 18, lift: 2.4, heelOff: 12, heelKick: 0, thigh: 23, shin: 23, ankleY: 116, ground: 120, toe: 4.2 },
  // child's or adult's run: short ground contact, flight phase, heel kick
  run: { period: 0.5, duty: 0.36, stride: 16, lift: 12, heelOff: 10, heelKick: 3.5, thigh: 13, shin: 13, ankleY: 118, ground: 120, toe: 3 }
};
function gait(opts = {}) {
  const kind = opts.kind ?? "walk";
  const o = { ...GAIT_PRESETS[kind], ...opts, kind };
  const { period, duty, stride: S, lift, heelOff, heelKick, thigh, shin, ankleY, ground, toe } = o;
  const reach2 = (thigh + shin) * 0.983;
  const restHip = ankleY - reach2;
  const speed = S / (duty * period);
  const foot = (u) => {
    u = (u % 1 + 1) % 1;
    if (u < duty) {
      const x2 = 40 + S / 2 - S * u / duty;
      const peel = smooth(duty - 0.14, duty, u);
      const th = heelOff * peel * Math.PI / 180;
      const px = x2 + toe, py = ground, ox = -toe, oy = ankleY - ground;
      return { ankle: [px + ox * Math.cos(th) - oy * Math.sin(th), py + ox * Math.sin(th) + oy * Math.cos(th)], pitch: heelOff * peel, stance: true };
    }
    const s = (u - duty) / (1 - duty);
    const x = 40 - S / 2 + S * minJerk(s) - heelKick * Math.sin(Math.PI * Math.min(1, s * 1.6));
    const y = ankleY - lift * Math.pow(Math.sin(Math.PI * Math.pow(s, heelKick ? 0.7 : 1)), 1.2);
    return { ankle: [x, y], pitch: heelOff * Math.pow(1 - smooth(0, 0.55, s), 1.4), stance: false };
  };
  return {
    ...o,
    speed,
    pose(phase, go = 1) {
      const raw = [foot(phase), foot(phase + 0.5)];
      if (go < 1) raw.forEach((fo, i) => {
        const rest = 40 + (i ? -2 : 2);
        fo.ankle = [rest + (fo.ankle[0] - rest) * go, ankleY + (fo.ankle[1] - ankleY) * go];
        fo.pitch *= go;
        fo.stance = true;
      });
      let hipY = restHip;
      const half = (phase % 0.5 + 0.5) % 0.5;
      if (heelKick && go >= 1) {
        hipY = half < duty ? restHip + 1.4 * Math.sin(Math.PI * half / duty) : restHip - 2.6 * Math.sin(Math.PI * (half - duty) / (0.5 - duty));
      } else {
        for (const fo of raw) if (fo.stance) {
          const dx = fo.ankle[0] - 40;
          hipY = Math.max(hipY, fo.ankle[1] - Math.sqrt(Math.max(1, reach2 * reach2 - dx * dx)));
        }
      }
      const hip = [40, hipY];
      const feet = raw.map((fo) => ({ ...fo, knee: knee(hip, fo.ankle, thigh, shin) }));
      const front = feet[0].ankle[0] >= feet[1].ankle[0] ? 0 : 1;
      return { hip, feet, front, bob: hipY - restHip };
    }
  };
}

// lib/motion.ts
var clamp2 = (x, a, b) => Math.max(a, Math.min(b, x));
var lerp = (a, b, t) => a + (b - a) * t;
var smooth2 = (e0, e1, x) => {
  const t = clamp2((x - e0) / (e1 - e0), 0, 1);
  return t * t * (3 - 2 * t);
};
var ease = (t) => smooth2(0, 1, t);
var wobble = (t, k = 1) => Math.sin(t * 1.3 * k) * 0.6 + Math.sin(t * 2.7 * k + 1.7) * 0.3 + Math.sin(t * 5.1 * k + 4.1) * 0.1;
function spring(stiffness = 40, damping = 6, x = 0) {
  return {
    x,
    v: 0,
    step(target, dt) {
      this.v += (stiffness * (target - this.x) - damping * this.v) * dt;
      this.x += this.v * dt;
      return this.x;
    },
    kick(v) {
      this.v += v;
    }
  };
}
function pendulum(stiffness = 10, damping = 1.1, a = 0) {
  return {
    a,
    v: 0,
    step(force, dt) {
      this.v += (-this.a * stiffness + force - this.v * damping) * dt;
      this.a += this.v * dt;
      return this.a;
    },
    kick(v) {
      this.v += v;
    }
  };
}

// cast/tinh-cach.ts
var GESTURES = ["wave", "point", "present", "talk", "bow", "nod"];
var EXPRS = ["neutral", "happy", "wink", "deadpan", "surprised", "worried"];
function tinhCachById(id) {
  const all = globalThis.TINH_CACH ?? {};
  const tc = all[id];
  if (!tc) throw new Error(`khong co tinh cach ${id} (tinh-cach.js co: ${Object.keys(all).join(", ") || "khong co"}; chay lai inject.py)`);
  return tc;
}
function applyTinhCach(c, id) {
  const tc = id ? tinhCachById(id) : void 0;
  const cc = tc?.cu_chi ?? {}, bc = tc?.bieu_cam ?? {};
  const act = c.act.bind(c);
  c.act = (name, seconds) => act(cc[name] ?? name, seconds);
  if (c.expr) {
    const expr = c.expr.bind(c);
    c.expr = (name, seconds) => expr(bc[name] ?? name, seconds);
    if (bc["binh-thuong"] && c.exprBase) c.exprBase(bc["binh-thuong"]);
  }
  const d = c;
  d.noi = (s) => {
    if (c.say) {
      c.say(s);
      if (cc["khi-noi"]) act(cc["khi-noi"], s);
    } else act(cc["khi-noi"] ?? "talk", s);
  };
  d.nghe = (s) => {
    if (bc["nghe"] && c.expr) c.expr(bc["nghe"], s);
    if (cc["khi-nghe"]) act(cc["khi-nghe"], Math.min(s, 1.6));
  };
  return d;
}

// cast/rig.ts
var ADULT = { thigh: 23, shin: 23, torso: 31, neck: 4.2, rx: 4, ry: 4.9, upper: 16, fore: 15.5, legW: 4.2, armW: 3.6, chest: 6.4, back: 5.6, swing: 15, foot: 1, gait: { kind: "walk" } };
var BODIES = {
  adult: ADULT,
  child: {
    thigh: 14,
    shin: 14,
    torso: 19.5,
    neck: 2.6,
    rx: 5.5,
    ry: 6.1,
    upper: 9.6,
    fore: 9.4,
    legW: 3.6,
    armW: 3,
    chest: 4.6,
    back: 4.2,
    swing: 24,
    foot: 0.7,
    gait: { kind: "walk", thigh: 14, shin: 14, stride: 13, period: 0.64, lift: 3.2, toe: 3, heelOff: 12, ankleY: 118.8 }
  },
  elder: { ...ADULT, swing: 7, gait: { kind: "walk", stride: 14, period: 1.3, lift: 2, heelOff: 6, duty: 0.66 } }
};
var RAD = Math.PI / 180;
var lerpP = (a, b, t) => [lerp(a[0], b[0], t), lerp(a[1], b[1], t)];
var P = (...pts) => pts.map(pt).join(" ");
function ik(a, b, l1, l2, prefer) {
  const dx = b[0] - a[0], dy = b[1] - a[1];
  const d = Math.max(0.01, Math.min(Math.hypot(dx, dy), l1 + l2 - 0.01));
  const th = Math.atan2(dy, dx);
  const al = Math.acos(clamp2((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1));
  const c1 = [a[0] + l1 * Math.cos(th - al), a[1] + l1 * Math.sin(th - al)];
  const c2 = [a[0] + l1 * Math.cos(th + al), a[1] + l1 * Math.sin(th + al)];
  if (prefer === "down") return c1[1] > c2[1] ? c1 : c2;
  if (prefer === "fwd") return c1[0] > c2[0] ? c1 : c2;
  return c1[0] < c2[0] ? c1 : c2;
}
var reach = (from, to, len) => {
  const dx = to[0] - from[0], dy = to[1] - from[1], d = Math.hypot(dx, dy);
  return d <= len ? to : [from[0] + dx / d * len, from[1] + dy / d * len];
};
function shoePath(ankle, toe, k) {
  const r = toe * RAD, c = Math.cos(r), s = Math.sin(r);
  const S = (x, y) => [ankle[0] + (x * c - y * s) * k, ankle[1] + (x * s + y * c) * k];
  return `M${pt(S(-1.6, -0.6))} L${pt(S(4.6, -0.2))} Q${pt(S(6.6, 0.4))} ${pt(S(5.6, 1.6))} L${pt(S(-1.4, 1.5))} Q${pt(S(-2.2, 0.5))} ${pt(S(-1.6, -0.6))}Z`;
}
var HOLDS = ["clipboard", "books", "ganh", "suitcase", "cane"];
function createCharacter(parent, spec, opt) {
  const B = BODIES[spec.build];
  const walk = gait({ ...B.gait, ...spec.gait });
  const R = walk.ankleY - (walk.thigh + walk.shin) * 0.983;
  const S = [41, R - B.torso];
  const hc = [S[0] + 1.4 * (B.rx / 4), S[1] - B.neck - B.ry + 0.6];
  const extras = new Set(spec.extras ?? []);
  const prop = spec.prop ?? "none";
  const hat = spec.hat ?? "none";
  const hairC = spec.hairColor ?? "currentColor";
  const shoeC = spec.shoeColor ?? "currentColor";
  const gArm = HOLDS.includes(prop) ? "far" : "near";
  const pw = B.foot < 1 ? PEN * 0.9 : PEN;
  const g = el("g", {}, parent);
  const behind = el("g", {}, g);
  const up = () => el("g", {}, g);
  const upBack = up();
  const flapBack = el("g", {}, g);
  const legG = el("g", {}, g);
  const lower = el("g", {}, g);
  const baseFront = el("g", {}, g);
  const upFront = up();
  const mkArm = (parent2) => {
    const a = limb(parent2, B.armW, pw);
    const sleeveL = spec.sleeve === "long" ? solid(a, spec.top === "coat" ? PAPER : spec.topColor) : a;
    if (spec.sleeve === "long" && spec.top === "coat") {
      const n = a.g.querySelector("path");
      n?.classList.add("pp");
    }
    const short = spec.sleeve === "short" ? solid(limb(parent2, B.armW + 2, pw), spec.topColor) : null;
    const hand = el("ellipse", { rx: B.armW * 0.5, ry: B.armW * 0.44, fill: PAPER, stroke: "currentColor", "stroke-width": pw * 0.7 }, parent2);
    return { a: sleeveL, short, hand };
  };
  const far = mkArm(upBack);
  const legs = [0, 1].map(() => {
    const lg = el("g", {}, legG);
    const wide = spec.bottom === "wide";
    const l = limb(lg, wide ? B.legW + 1.4 : B.legW, pw);
    if (spec.bottom === "trousers" || wide) solid(l, spec.bottomColor);
    const sh = spec.bottom === "shorts" ? solid(limb(lg, B.legW + 2.4, pw), spec.bottomColor) : null;
    const shoe = el("path", { fill: shoeC, stroke: "currentColor", "stroke-width": shoeC === "currentColor" ? 0 : pw * 0.6 }, lg);
    return { lg, l, sh, shoe };
  });
  const skirt = spec.top === "coat" || spec.top === "dress" ? paint(lower, spec.top === "coat" ? PAPER : spec.topColor, pw) : null;
  if (skirt && spec.top === "coat") skirt.classList.add("pp");
  const skirtLine = skirt ? pen(lower, pw * 0.55) : null;
  const flapB = spec.top === "aodai" ? paint(flapBack, spec.topColor, pw) : null;
  const flapF = spec.top === "aodai" ? paint(lower, spec.topColor, pw) : null;
  const flapPat = spec.top === "aodai" ? el("path", { fill: "none", stroke: "#f6f1e4", "stroke-width": pw * 0.5, "stroke-linecap": "round" }, lower) : null;
  const cane = prop === "cane" ? pen(baseFront, pw * 1.2) : null;
  const caneTop = prop === "cane" ? pen(baseFront, pw * 1.2) : null;
  if (cane) {
    cane.setAttribute("stroke", spec.propColor ?? "#6e5236");
    caneTop.setAttribute("stroke", spec.propColor ?? "#6e5236");
  }
  const suit = prop === "suitcase" ? {
    handle: pen(behind, pw * 0.8),
    body: paint(behind, spec.propColor ?? "#2f5d6b", pw),
    rib: pen(behind, pw * 0.5),
    wheel: el("circle", { r: 2.3, fill: PAPER, stroke: "currentColor", "stroke-width": pw * 0.8 }, behind),
    spoke: pen(behind, pw * 0.5)
  } : null;
  const pack = prop === "backpack" ? paint(upFront, spec.propColor ?? "#3f6ea8", pw) : null;
  const packFlap = pack ? pen(upFront, pw * 0.6) : null;
  const longHair = spec.hair === "long" || spec.hair === "ponytail" || spec.hair === "pigtails" ? el("path", { fill: hairC, stroke: "currentColor", "stroke-width": hairC === "currentColor" ? 0 : pw * 0.5 }, upFront) : null;
  const neck = limb(upFront, B.foot < 1 ? 2.6 : 2.9, pw);
  const torso = paint(upFront, spec.top === "coat" ? PAPER : spec.topColor, pw);
  if (spec.top === "coat") torso.classList.add("pp");
  const torsoLine = pen(upFront, pw * 0.55);
  const vest = extras.has("vest") ? paint(upFront, "#e07a3a", pw * 0.9) : null;
  const vestStrip = vest ? el("path", { fill: "none", stroke: "#f3e9b8", "stroke-width": 1.6 }, upFront) : null;
  const tie = extras.has("tie") ? paint(upFront, "#a33a2e", pw * 0.6) : null;
  const scarf = extras.has("redscarf") ? paint(upFront, "#c8372d", pw * 0.6) : null;
  const steth = extras.has("stethoscope") ? pen(upFront, pw * 0.75) : null;
  const stethEnd = steth ? el("circle", { r: 1.3, fill: "#9aa3ab", stroke: "currentColor", "stroke-width": pw * 0.6 }, upFront) : null;
  const lany = extras.has("lanyard") ? el("path", { fill: "none", stroke: "#3f6ea8", "stroke-width": 0.8 }, upFront) : null;
  const badge = lany ? shape(upFront, pw * 0.6) : null;
  const packStrap = pack ? pen(upFront, pw * 0.8) : null;
  const headG = el("g", {}, upFront);
  const head = el("ellipse", { cx: hc[0], cy: hc[1], rx: B.rx, ry: B.ry, fill: PAPER, stroke: "currentColor", "stroke-width": pw }, headG);
  const hair = el("path", { fill: hairC, stroke: "currentColor", "stroke-width": hairC === "currentColor" ? 0 : pw * 0.55 }, headG);
  const mask = extras.has("mask") ? paint(headG, "#b9d4e6", pw * 0.55) : null;
  const maskLoop = mask ? pen(headG, pw * 0.4) : null;
  const glasses = extras.has("glasses") ? pen(headG, pw * 0.6) : null;
  const hatG = el("g", {}, headG);
  const hatA = hat !== "none" ? paint(hatG, spec.hatColor ?? "#e8d6a0", pw * 0.85) : null;
  const hatB = hat !== "none" ? el("path", { fill: "currentColor" }, hatG) : null;
  const hatC = hat !== "none" ? pen(hatG, pw * 0.45) : null;
  const propBack = el("g", {}, upFront);
  const near = mkArm(upFront);
  const propFront = el("g", {}, upFront);
  const board = prop === "clipboard" ? { b: paint(propFront, spec.propColor ?? "#b98a55", pw * 0.8), paper: shape(propFront, pw * 0.5), clip: blot(propFront), lines: pen(propFront, pw * 0.35) } : null;
  const books = prop === "books" ? ["#4f6b55", "#a33a2e", "#d3a24c"].map((c2) => paint(propFront, c2, pw * 0.7)) : null;
  const hangG = prop === "briefcase" || prop === "basket" ? el("g", {}, propBack) : null;
  const hangA = hangG ? paint(hangG, spec.propColor ?? (prop === "basket" ? "#c9a46a" : "#6b4a32"), pw * 0.8) : null;
  const hangB = hangG ? pen(hangG, pw * 0.6) : null;
  const hangC = hangG && prop === "basket" ? el("path", { fill: "#5f8a4a", stroke: "currentColor", "stroke-width": pw * 0.5 }, hangG) : null;
  const ganh = prop === "ganh" ? {
    pole: el("path", { fill: "none", stroke: "#8a6a3c", "stroke-width": 2, "stroke-linecap": "round" }, propFront),
    poleInk: pen(propFront, pw * 0.5),
    baskets: [0, 1].map(() => {
      const bg = el("g", {}, propFront);
      return { bg, rope: pen(bg, pw * 0.5), load: el("path", { fill: "#6f9a4e", stroke: "currentColor", "stroke-width": pw * 0.5 }, bg), fruit: el("path", { fill: "#d8743a", stroke: "currentColor", "stroke-width": pw * 0.5 }, bg), body: paint(bg, "#c9a46a", pw * 0.8), weave: pen(bg, pw * 0.4) };
    })
  } : null;
  if (ganh) g.appendChild(propFront);
  let phase = opt.phase ?? 0, go = 0, target = null;
  let actName = null, actT = 0, actDur = 0;
  const armS = [spring(60, 9), spring(60, 9)];
  const hangP = pendulum(14, 1.8);
  const hairS = spring(30, 4.5);
  const flapS = spring(24, 3.6);
  const flapF_S = spring(36, 5);
  const ganhP = [pendulum(9, 1.2), pendulum(9, 1.2)];
  const ganhY = spring(70, 6);
  let lastBob = 0, rolled = 0;
  const seed = spec.id.length * 1.7;
  const c = {
    spec,
    g,
    x: opt.x,
    y: opt.y,
    dir: opt.dir ?? 1,
    scale: (opt.scale ?? 1) * (spec.height ?? 1),
    get go() {
      return go;
    },
    walkTo(x) {
      target = x;
    },
    face(d) {
      if (go < 0.05) c.dir = d;
    },
    act(name, seconds = 2.4) {
      actName = name;
      actT = 0;
      actDur = seconds;
    },
    update(t, dt, wind = 0) {
      const sp = walk.speed * c.scale;
      let want = 0;
      if (target !== null && !actName) {
        const d = target - c.x;
        if (Math.abs(d) > 0.5) {
          const nd = d > 0 ? 1 : -1;
          if (go < 0.05) c.dir = nd;
          want = clamp2(Math.abs(d) / (sp * 0.45), 0, 1);
        }
        if (Math.abs(d) < 0.6 && go < 0.03) {
          c.x = target;
          target = null;
        }
      }
      go = clamp2(go + clamp2(want - go, -dt * 2.6, dt * 2.6), 0, 1);
      const ge = ease(go);
      phase += dt / walk.period * ge;
      c.x += c.dir * sp * dt * ge;
      rolled += sp * dt * ge / c.scale;
      g.setAttribute("transform", `translate(${f(c.x)} ${f(c.y)}) scale(${f(c.dir * c.scale)} ${f(c.scale)}) translate(-40 -120)`);
      let w = 0;
      if (actName) {
        actT += dt;
        w = actT < 0.45 ? ease(actT / 0.45) : actT > actDur - 0.45 ? ease((actDur - actT) / 0.45) : 1;
        if (go > 0.05) {
          w = 0;
          actT = Math.min(actT, 1e-4);
        }
        if (actT >= actDur) {
          actName = null;
          w = 0;
        }
      }
      const bowW = actName === "bow" ? w : 0;
      const nodW = actName === "nod" ? w : 0;
      const armW = actName && actName !== "bow" && actName !== "nod" ? w : 0;
      const p = walk.pose(phase, ge);
      const breath = Math.sin(t * 1.7 + seed) * 0.35 * (1 - ge);
      const bob = p.bob + breath;
      p.feet.forEach((fo, i) => {
        const L = legs[i];
        L.l.draw([p.hip, fo.knee, fo.ankle], [0.3, 0.8]);
        L.sh?.draw([p.hip, lerpP(p.hip, fo.knee, spec.build === "child" ? 0.75 : 0.6)], [0, 0]);
        L.shoe.setAttribute("d", shoePath(fo.ankle, fo.pitch, B.foot));
      });
      legG.appendChild(legs[p.front].lg);
      const lean = (spec.stoop ?? 0) + 2 * ge + bowW * 30;
      const tr = `translate(0 ${f(bob)}) rotate(${f(lean)} 40 ${f(R)})`;
      upBack.setAttribute("transform", tr);
      upFront.setAttribute("transform", tr);
      const lr = lean * RAD, cl = Math.cos(lr), sl = Math.sin(lr);
      const toLocal = (q) => {
        const x = q[0] - 40, y = q[1] - bob - R;
        return [40 + x * cl + y * sl, R - x * sl + y * cl];
      };
      const toBase = (q) => {
        const x = q[0] - 40, y = q[1] - R;
        return [40 + x * cl - y * sl, R + bob + x * sl + y * cl];
      };
      const hemExt = spec.top === "baba" ? 10 : spec.top === "jacket" ? 5 : spec.top === "coat" ? 3 : 1;
      const flare = spec.top === "baba" ? 1.6 : 0;
      const Bw = [40 - B.back - flare, R + hemExt], Bs = [S[0] - B.back + 0.8, S[1] + 2];
      const Fs = [S[0] + 3.2, S[1] + 0.6], Fc = [S[0] + B.chest, S[1] + B.torso * 0.3], Fw = [40 + B.chest - 0.4 + flare, R + hemExt];
      torso.setAttribute("d", `M${pt(Bw)} Q${f(Bs[0] - 1.2)} ${f((Bw[1] + Bs[1]) / 2)} ${pt(Bs)} Q${f(S[0])} ${f(S[1] - 1.4)} ${pt(Fs)} Q${f(Fc[0] + 0.3)} ${f(Fs[1] + 2)} ${pt(Fc)} Q${f(Fc[0] + 0.6)} ${f((Fc[1] + Fw[1]) / 2)} ${pt(Fw)} Q${f(40)} ${f(Fw[1] + 0.8)} ${pt(Bw)}Z`);
      const tl = [];
      if (spec.top === "coat" || spec.top === "jacket") tl.push(`M${f(Fs[0] + 0.4)} ${f(Fs[1] + 1)} Q${f(Fc[0] - 2.4)} ${f(Fc[1])} ${f(Fw[0] - 2)} ${f(Fw[1])}`);
      if (spec.top === "coat") tl.push(`M${f(Fw[0] - 6)} ${f(R - 4)} l4 0`);
      if (spec.top === "baba") tl.push(`M${f(Bw[0] + 1.2)} ${f(R + 4)} L${f(Bw[0] + 0.8)} ${pt(Bw).split(" ")[1]}`, `M${f(Fc[0] - 1.6)} ${f(Fc[1] + 2)} L${f(Fw[0] - 2.6)} ${f(Fw[1] - 0.4)}`);
      if (spec.top === "shirt" || spec.top === "scrubs") tl.push(`M${f(Bw[0] + 0.6)} ${f(R - 1)} L${f(Fw[0] - 0.6)} ${f(R - 1)}`);
      if (spec.top === "scrubs") tl.push(`M${pt(Fs)} L${f(Fs[0] + 2.2)} ${f(Fs[1] + 5)} L${f(Fs[0] + 3.6)} ${f(Fs[1] + 0.8)}`);
      if (spec.top === "aodai") tl.push(`M${f(Fs[0] - 1)} ${f(Fs[1] - 0.2)} L${f(Fs[0] - 1)} ${f(Fs[1] - 2.6)} L${f(Fs[0] + 1.8)} ${f(Fs[1] - 2.2)}`, `M${f(Fs[0] + 0.6)} ${f(Fs[1] + 1.6)} Q${f(Fc[0] - 1.6)} ${f(Fc[1] - 2)} ${f(Fc[0] + 0.2)} ${f(Fc[1] + 1)}`);
      torsoLine.setAttribute("d", tl.join(" "));
      if (vest && vestStrip) {
        const v1 = [Bw[0] + 0.8, R - 1], v2 = [Bs[0] + 0.6, Bs[1] + 3.4], v3 = [S[0] + 1, S[1] + 3], v4 = [Fc[0] - 0.4, Fc[1] + 1], v5 = [Fw[0] - 0.6, R - 1];
        vest.setAttribute("d", `M${P(v1)} L${P(v2)} Q${f(S[0] - 1)} ${f(S[1] + 1.2)} ${P(v3)} L${P(v4)} L${P(v5)}Z`);
        const yS = S[1] + B.torso * 0.62;
        vestStrip.setAttribute("d", `M${f(Bw[0] + 1.4)} ${f(yS)} L${f(Fw[0] - 1.2)} ${f(yS)}`);
      }
      if (tie) tie.setAttribute("d", `M${f(Fs[0] + 0.4)} ${f(Fs[1] + 0.6)} L${f(Fs[0] + 2.4)} ${f(Fs[1] + 1.2)} L${f(Fc[0] - 0.2)} ${f(Fc[1] + 7)} L${f(Fc[0] - 1.6)} ${f(Fc[1] + 8.6)} L${f(Fs[0] + 1.6)} ${f(Fs[1] + 2.6)}Z`);
      if (scarf) {
        const k = [Fs[0] + 1.2, Fs[1] + 1.8];
        const sw = Math.sin(t * 5 + seed) * 0.6 * ge;
        scarf.setAttribute("d", `M${f(Bs[0] + 1)} ${f(Bs[1] - 0.6)} Q${f(S[0])} ${f(S[1] + 2.6)} ${pt(k)} L${f(k[0] + 2.4 + sw)} ${f(k[1] + 6)} L${f(k[0] + 0.6 + sw)} ${f(k[1] + 6.6)} L${f(k[0] - 0.2)} ${f(k[1] + 2.4)} L${f(k[0] - 1.6 + sw)} ${f(k[1] + 7)} L${f(k[0] - 2.8 + sw)} ${f(k[1] + 6.2)} L${f(k[0] - 1)} ${f(k[1] + 0.6)} Q${f(S[0] - 1)} ${f(S[1] + 1)} ${f(Bs[0] + 0.6)} ${f(Bs[1] - 2)}Z`);
      }
      if (steth && stethEnd) {
        const e = [Fc[0] - 1.6, Fc[1] + 7 + Math.sin(phase * Math.PI * 4) * 0.4 * ge];
        steth.setAttribute("d", `M${f(Bs[0] + 1.4)} ${f(Bs[1] - 0.4)} Q${f(S[0])} ${f(S[1] + 4.8)} ${f(Fs[0] + 0.6)} ${f(Fs[1] + 1.2)} M${f(Bs[0] + 2)} ${f(Bs[1])} Q${f(S[0] - 1)} ${f(Fc[1] + 1)} ${pt(e)}`);
        stethEnd.setAttribute("cx", f(e[0]));
        stethEnd.setAttribute("cy", f(e[1] + 1));
      }
      if (lany && badge) {
        const bdg = [Fc[0] - 2.2, Fc[1] + 5];
        lany.setAttribute("d", `M${f(Bs[0] + 1.6)} ${f(Bs[1] - 0.2)} Q${f(S[0] - 0.6)} ${f(S[1] + 6)} ${pt(bdg)} M${f(Fs[0] - 0.2)} ${f(Fs[1] + 0.8)} L${pt(bdg)}`);
        badge.setAttribute("d", `M${f(bdg[0] - 1.4)} ${f(bdg[1])} l2.8 0 l0 3.8 l-2.8 0Z`);
      }
      if (pack && packFlap && packStrap) {
        const top = [Bs[0] - 0.4, Bs[1] + 1.2], bot = [Bw[0] + 0.4, R - 4];
        const d = B.foot < 1 ? 6.4 : 7.6;
        pack.setAttribute("d", `M${pt(top)} Q${f(top[0] - d - 1)} ${f(top[1] - 0.6)} ${f(top[0] - d)} ${f(top[1] + 4)} L${f(bot[0] - d + 0.4)} ${f(bot[1] - 1)} Q${f(bot[0] - d)} ${f(bot[1] + 1.2)} ${f(bot[0] - 1)} ${f(bot[1] + 0.6)}Z`);
        packFlap.setAttribute("d", `M${f(top[0] - d + 0.4)} ${f(top[1] + 5)} Q${f(top[0] - d / 2)} ${f(top[1] + 7)} ${f(top[0] - 0.6)} ${f(top[1] + 5.6)}`);
        packStrap.setAttribute("d", `M${f(Bs[0] + 0.4)} ${f(Bs[1] - 0.6)} Q${f(S[0] + 2.6)} ${f(S[1] + 0.6)} ${f(S[0] + 2.8)} ${f(S[1] + 6)} Q${f(S[0] + 2)} ${f(S[1] + B.torso * 0.5)} ${f(Bw[0] + 2)} ${f(R - 4)}`);
      }
      neck.draw([[S[0] + 0.6, S[1] + 1.2], [hc[0] - 0.4, hc[1] + B.ry - 0.8]], [0, 0]);
      const talkW = actName === "talk" ? w : 0;
      const nod = nodW * Math.sin(Math.min(1, actT / Math.max(0.1, actDur)) * Math.PI * 3) * 9 + nodW * 4 + talkW * (Math.sin(actT * 5.2) * 2.6 + Math.sin(actT * 2.3) * 1.4);
      const look = Math.sin(t * 0.37 + seed) * 1.6 * (1 - ge);
      headG.setAttribute("transform", `rotate(${f(nod + look - (spec.stoop ?? 0) * 0.7 - bowW * 8)} ${f(S[0] + 0.6)} ${f(S[1])})`);
      const rx = B.rx, ry = B.ry, [hx, hy] = hc;
      const hairPaths = {
        short: `M${f(hx - rx - 0.1)} ${f(hy + ry * 0.35)} Q${f(hx - rx - 0.7)} ${f(hy - ry - 0.9)} ${f(hx + 0.6)} ${f(hy - ry - 0.5)} Q${f(hx + rx + 0.7)} ${f(hy - ry * 0.7)} ${f(hx + rx * 0.85)} ${f(hy - ry * 0.3)} Q${f(hx)} ${f(hy - ry * 0.62)} ${f(hx - rx * 0.4)} ${f(hy + 0.2)} Q${f(hx - rx * 0.5)} ${f(hy + ry * 0.45)} ${f(hx - rx - 0.1)} ${f(hy + ry * 0.35)}Z`,
        side: `M${f(hx - rx - 0.2)} ${f(hy + ry * 0.3)} Q${f(hx - rx - 0.9)} ${f(hy - ry - 1.2)} ${f(hx + 1)} ${f(hy - ry - 0.8)} Q${f(hx + rx + 1)} ${f(hy - ry * 0.8)} ${f(hx + rx * 0.95)} ${f(hy - ry * 0.15)} Q${f(hx + rx * 0.2)} ${f(hy - ry * 0.85)} ${f(hx - rx * 0.35)} ${f(hy)} Q${f(hx - rx * 0.55)} ${f(hy + ry * 0.4)} ${f(hx - rx - 0.2)} ${f(hy + ry * 0.3)}Z`,
        bun: "",
        long: "",
        ponytail: "",
        pigtails: ""
      };
      const crown = `M${f(hx - rx - 0.2)} ${f(hy + ry * 0.45)} Q${f(hx - rx - 0.8)} ${f(hy - ry - 0.9)} ${f(hx + 0.8)} ${f(hy - ry - 0.5)} Q${f(hx + rx + 0.4)} ${f(hy - ry * 0.75)} ${f(hx + rx * 0.9)} ${f(hy - ry * 0.25)} Q${f(hx + rx * 0.1)} ${f(hy - ry * 0.7)} ${f(hx - rx * 0.45)} ${f(hy + 0.4)} Q${f(hx - rx * 0.4)} ${f(hy + ry * 0.6)} ${f(hx - rx - 0.2)} ${f(hy + ry * 0.45)}Z`;
      let hp = hairPaths[spec.hair] || crown;
      if (spec.hair === "bun") hp += ` M${f(hx - rx - 2.4)} ${f(hy - ry * 0.25)} a2.4 2.2 0 1 0 0.1 0Z`;
      if (spec.hair === "pigtails") hp += ` M${f(hx - rx * 0.9)} ${f(hy - ry * 0.7)} a1.2 1.2 0 1 0 0.1 0Z`;
      hair.setAttribute("d", hp);
      if (longHair) {
        const sway = hairS.step(-ge * 2.6 - wind * 1.2 + Math.sin(phase * Math.PI * 4) * 0.8 * ge, dt);
        const root = [hx - rx * 0.6, hy - ry * 0.55];
        if (spec.hair === "long") {
          const end = [hx - rx - 2.2 + sway * 0.7, S[1] + B.torso * 0.42];
          longHair.setAttribute("d", `M${pt(root)} Q${f(hx - rx - 2.6)} ${f(hy)} ${f(hx - rx - 1.6 + sway * 0.3)} ${f(S[1])} Q${f(end[0] - 1)} ${f(end[1] - 4)} ${pt(end)} L${f(end[0] + 3.4)} ${f(end[1] - 0.6)} Q${f(hx - rx + 1.6)} ${f(S[1] - 1)} ${f(hx - rx + 1.2)} ${f(hy + ry * 0.6)}Z`);
        } else if (spec.hair === "ponytail") {
          const tie2 = [hx - rx - 0.6, hy - ry * 0.35];
          const end = [tie2[0] - 4 + sway, tie2[1] + 9];
          longHair.setAttribute("d", `M${f(tie2[0] + 0.8)} ${f(tie2[1] - 1.2)} Q${f(tie2[0] - 4 + sway * 0.3)} ${f(tie2[1] - 1)} ${pt(end)} Q${f(tie2[0] - 1 + sway * 0.6)} ${f(tie2[1] + 4)} ${f(tie2[0] + 0.6)} ${f(tie2[1] + 1.2)}Z`);
        } else {
          const tie2 = [hx - rx * 0.95, hy + ry * 0.05];
          const end = [tie2[0] - 1.6 + sway * 0.8, tie2[1] + 7];
          longHair.setAttribute("d", `M${f(tie2[0] + 0.6)} ${f(tie2[1] - 1)} Q${f(tie2[0] - 2.6)} ${f(tie2[1])} ${pt(end)} Q${f(tie2[0] + 0.4 + sway * 0.4)} ${f(tie2[1] + 3)} ${f(tie2[0] + 1.2)} ${f(tie2[1] + 0.8)}Z`);
          upFront.appendChild(longHair);
          upFront.insertBefore(longHair, headG);
        }
      }
      if (mask && maskLoop) {
        mask.setAttribute("d", `M${f(hx + rx * 0.15)} ${f(hy - ry * 0.05)} L${f(hx + rx + 0.7)} ${f(hy + ry * 0.05)} Q${f(hx + rx + 0.9)} ${f(hy + ry * 0.7)} ${f(hx + rx * 0.3)} ${f(hy + ry * 0.92)} Q${f(hx - rx * 0.05)} ${f(hy + ry * 0.5)} ${f(hx + rx * 0.15)} ${f(hy - ry * 0.05)}Z`);
        maskLoop.setAttribute("d", `M${f(hx + rx * 0.15)} ${f(hy)} Q${f(hx - rx * 0.4)} ${f(hy + ry * 0.1)} ${f(hx - rx * 0.2)} ${f(hy + ry * 0.4)} Q${f(hx)} ${f(hy + ry * 0.6)} ${f(hx + rx * 0.3)} ${f(hy + ry * 0.85)}`);
      }
      if (glasses) glasses.setAttribute("d", `M${f(hx + rx * 0.45)} ${f(hy - ry * 0.18)} a1.3 1.1 0 1 0 2.6 0 a1.3 1.1 0 1 0 -2.6 0 M${f(hx + rx * 0.45)} ${f(hy - ry * 0.2)} L${f(hx - rx * 0.4)} ${f(hy - ry * 0.3)}`);
      if (hatA && hatB && hatC) {
        const top = hy - ry;
        if (hat === "nonla") {
          const by = hy - ry * 0.3, hw = rx * 2.7, ap = [hx + 0.4, top - 8.2];
          hatA.setAttribute("d", `M${f(hx - hw)} ${f(by)} Q${f(hx - hw * 0.45)} ${f(by - 3.4)} ${pt(ap)} Q${f(hx + hw * 0.45)} ${f(by - 3.4)} ${f(hx + hw)} ${f(by)} Q${f(hx)} ${f(by + 1.8)} ${f(hx - hw)} ${f(by)}Z`);
          hatC.setAttribute("d", `M${f(hx - hw * 0.62)} ${f(by - 1.6)} Q${f(hx)} ${f(by - 0.2)} ${f(hx + hw * 0.62)} ${f(by - 1.6)} M${f(hx - hw * 0.32)} ${f(by - 4.4)} Q${f(hx)} ${f(by - 3.4)} ${f(hx + hw * 0.34)} ${f(by - 4.4)} M${f(hx + rx * 0.2)} ${f(by + 0.8)} L${f(hx + rx * 0.7)} ${f(hy + ry - 0.2)}`);
          hatB.setAttribute("d", "");
        } else if (hat === "cap") {
          hatA.setAttribute("d", `M${f(hx - rx - 0.4)} ${f(hy - ry * 0.25)} Q${f(hx - rx - 0.6)} ${f(top - 1.6)} ${f(hx + 0.4)} ${f(top - 1.4)} Q${f(hx + rx + 0.6)} ${f(top - 1)} ${f(hx + rx + 0.3)} ${f(hy - ry * 0.3)}Z`);
          hatB.setAttribute("d", `M${f(hx + rx * 0.6)} ${f(hy - ry * 0.36)} L${f(hx + rx + 4.6)} ${f(hy - ry * 0.22)} Q${f(hx + rx + 4.8)} ${f(hy - ry * 0.05)} ${f(hx + rx + 4)} ${f(hy - ry * 0.05)} L${f(hx + rx * 0.6)} ${f(hy - ry * 0.12)}Z`);
          hatC.setAttribute("d", "");
        } else if (hat === "hardhat") {
          hatA.setAttribute("d", `M${f(hx - rx - 1.6)} ${f(hy - ry * 0.3)} Q${f(hx - rx - 0.8)} ${f(top - 2.6)} ${f(hx + 0.4)} ${f(top - 2.4)} Q${f(hx + rx + 1)} ${f(top - 2)} ${f(hx + rx + 1.2)} ${f(hy - ry * 0.35)} L${f(hx + rx + 3)} ${f(hy - ry * 0.28)} L${f(hx + rx + 2.8)} ${f(hy - ry * 0.12)} L${f(hx - rx - 1.8)} ${f(hy - ry * 0.12)}Z`);
          hatC.setAttribute("d", `M${f(hx + 0.4)} ${f(top - 2.4)} L${f(hx + 0.6)} ${f(hy - ry * 0.3)}`);
          hatB.setAttribute("d", "");
        } else if (hat === "officer") {
          hatA.setAttribute("d", `M${f(hx - rx - 0.6)} ${f(hy - ry * 0.3)} Q${f(hx - rx - 1.6)} ${f(top - 3.4)} ${f(hx + 0.6)} ${f(top - 3)} Q${f(hx + rx + 2.4)} ${f(top - 2.8)} ${f(hx + rx + 0.8)} ${f(hy - ry * 0.4)}Z`);
          hatB.setAttribute("d", `M${f(hx + rx * 0.4)} ${f(hy - ry * 0.42)} L${f(hx + rx + 3.6)} ${f(hy - ry * 0.18)} Q${f(hx + rx + 3)} ${f(hy - ry * 0.02)} ${f(hx + rx * 0.5)} ${f(hy - ry * 0.2)}Z M${f(hx + rx * 0.35)} ${f(top - 0.6)} a0.9 0.9 0 1 0 0.1 0Z`);
          hatC.setAttribute("d", `M${f(hx - rx - 0.4)} ${f(hy - ry * 0.48)} L${f(hx + rx + 0.6)} ${f(hy - ry * 0.55)}`);
        } else if (hat === "nurse") {
          hatA.setAttribute("d", `M${f(hx - rx * 0.7)} ${f(top + 0.6)} L${f(hx - rx * 0.6)} ${f(top - 2.8)} L${f(hx + rx * 0.7)} ${f(top - 2.2)} L${f(hx + rx * 0.75)} ${f(top + 0.9)} Q${f(hx)} ${f(top - 0.2)} ${f(hx - rx * 0.7)} ${f(top + 0.6)}Z`);
          hatC.setAttribute("d", "");
          hatB.setAttribute("d", `M${f(hx - rx * 0.62)} ${f(top - 1.6)} L${f(hx + rx * 0.72)} ${f(top - 1.1)} L${f(hx + rx * 0.72)} ${f(top - 0.4)} L${f(hx - rx * 0.62)} ${f(top - 0.9)}Z`);
          hatB.setAttribute("fill", "#3f6ea8");
        }
      }
      const legSwing = (p.feet[0].ankle[0] - 40) / (walk.stride / 2);
      const farA = armS[0].step((-legSwing * B.swing + 3) * ge + 4 * (1 - ge), dt) * RAD;
      const nearA = armS[1].step((legSwing * B.swing * 0.9 + 3) * ge + 3 * (1 - ge), dt) * RAD;
      const shF = [S[0] - 1, S[1] + 2.2], shN = [S[0] + 1.4, S[1] + 2.6];
      const L1 = B.upper, L2 = B.fore;
      const natural = (sh, a) => {
        const e = [sh[0] + L1 * Math.sin(a), sh[1] + L1 * Math.cos(a)];
        return [e, [e[0] + L2 * Math.sin(a + 0.18), e[1] + L2 * Math.cos(a + 0.18)]];
      };
      const gestureHand = (sh) => {
        const k = (L1 + L2) / 31.5;
        if (actName === "wave") return { h: [sh[0] + (5 + Math.sin(actT * 10) * 3.4 * w) * k, sh[1] - 21 * k], prefer: "fwd" };
        if (actName === "talk") return { h: [sh[0] + 12 * k, sh[1] + 17 * k + Math.sin(actT * 4.1) * 1.6], prefer: "down" };
        if (actName === "point") return { h: [sh[0] + 29 * k, sh[1] + 5 * k], prefer: "down" };
        return { h: [sh[0] + 17 * k, sh[1] + 12 * k + Math.sin(actT * 3) * 1.2], prefer: "down" };
      };
      const drawArm = (arm, sh, e, h) => {
        arm.a.draw([sh, e, h], [0.2, 0.45]);
        arm.short?.draw([sh, lerpP(sh, e, 0.5)], [0, 0]);
        arm.hand.setAttribute("cx", f(h[0]));
        arm.hand.setAttribute("cy", f(h[1]));
      };
      const blendArm = (sh, base, prefer, gw) => {
        if (gw <= 1e-3) return base;
        const gh = gestureHand(sh);
        const h = reach(sh, lerpP(base[1], gh.h, gw), L1 + L2 - 0.05);
        return [ik(sh, h, L1, L2, gw > 0.5 ? gh.prefer : prefer), h];
      };
      let fe = natural(shF, farA);
      if (gArm === "far") fe = blendArm(shF, fe, "down", armW);
      drawArm(far, shF, fe[0], fe[1]);
      let ne = natural(shN, nearA);
      if (prop === "clipboard" || prop === "books") {
        const h = [S[0] + (B.chest + 3.4), S[1] + B.torso * 0.5];
        ne = [ik(shN, h, L1, L2, "down"), h];
      } else if (prop === "cane") {
        const fo = p.feet[1];
        const tipB = [fo.ankle[0] + 13, Math.min(120, fo.ankle[1] + 1.6)];
        const topB = [tipB[0] - 2, tipB[1] - 40];
        const h = reach(shN, toLocal(topB), L1 + L2 - 0.2);
        ne = [ik(shN, h, L1, L2, "back"), h];
        const hb = toBase(h);
        cane.setAttribute("d", `M${pt(tipB)} Q${f((tipB[0] + hb[0]) / 2 + 0.6)} ${f((tipB[1] + hb[1]) / 2)} ${pt(hb)}`);
        caneTop.setAttribute("d", `M${pt(hb)} Q${f(hb[0] + 1.4)} ${f(hb[1] - 3)} ${f(hb[0] + 3.4)} ${f(hb[1] - 0.6)}`);
      } else if (prop === "ganh") {
        const h = [S[0] + 12, S[1] - 1.4 + ganhY.x * 0.4];
        ne = [ik(shN, h, L1, L2, "down"), h];
      } else if (prop === "suitcase") {
        const h = [40 - 9, R - 1 + Math.sin(phase * Math.PI * 4) * 0.5 * ge];
        ne = [ik(shN, reach(shN, h, L1 + L2 - 0.1), L1, L2, "fwd"), reach(shN, h, L1 + L2 - 0.1)];
      }
      if (gArm === "near") ne = blendArm(shN, ne, "down", armW);
      drawArm(near, shN, ne[0], ne[1]);
      const hand = ne[1];
      if (board) {
        const o = [hand[0] + 0.6, hand[1] + 1];
        const rot = (q) => {
          const a = -22 * RAD;
          return [o[0] + q[0] * Math.cos(a) - q[1] * Math.sin(a), o[1] + q[0] * Math.sin(a) + q[1] * Math.cos(a)];
        };
        const r4 = (x0, y0, x1, y1) => `M${P(rot([x0, y0]))} L${P(rot([x1, y0]))} L${P(rot([x1, y1]))} L${P(rot([x0, y1]))}Z`;
        board.b.setAttribute("d", r4(-3, -15, 5, 2));
        board.paper.setAttribute("d", r4(-2.2, -13.2, 4.2, 1.2));
        board.clip.setAttribute("d", r4(-0.2, -16, 2.4, -13.8));
        board.lines.setAttribute("d", [-10.4, -8, -5.6, -3.2].map((y) => `M${P(rot([-1.2, y]))} L${P(rot([3.2, y]))}`).join(" "));
      }
      if (books) {
        books.forEach((bk, i) => {
          const o = [hand[0] - 2.6, hand[1] - 1 - i * 2.6];
          bk.setAttribute("d", `M${f(o[0] - 3.6 + i * 0.6)} ${f(o[1] - 2.4)} L${f(o[0] + 5.6 - i * 0.4)} ${f(o[1] - 2.4)} L${f(o[0] + 5.6 - i * 0.4)} ${f(o[1])} L${f(o[0] - 3.6 + i * 0.6)} ${f(o[1])}Z`);
        });
      }
      if (hangG && hangA && hangB) {
        const accel = Math.cos(2 * Math.PI * phase * 2) * 1.6 * ge;
        const a = hangP.step(-accel - wind * 0.3, dt);
        hangG.setAttribute("transform", `rotate(${f(a * 57.3)} ${pt(hand)})`);
        if (prop === "briefcase") {
          hangB.setAttribute("d", `M${f(hand[0] - 2.4)} ${f(hand[1] + 2.4)} Q${pt(hand)} ${f(hand[0] + 2.4)} ${f(hand[1] + 2.4)}`);
          hangA.setAttribute("d", `M${f(hand[0] - 8)} ${f(hand[1] + 2.4)} L${f(hand[0] + 8)} ${f(hand[1] + 2.4)} L${f(hand[0] + 8)} ${f(hand[1] + 13)} L${f(hand[0] - 8)} ${f(hand[1] + 13)}Z`);
        } else {
          const y0 = hand[1] + 6;
          hangB.setAttribute("d", `M${f(hand[0] - 5.4)} ${f(y0)} Q${f(hand[0])} ${f(hand[1] - 3.4)} ${f(hand[0] + 5.4)} ${f(y0)} M${f(hand[0] - 4.8)} ${f(y0 + 3)} L${f(hand[0] + 4.8)} ${f(y0 + 3)} M${f(hand[0] - 4.4)} ${f(y0 + 5.6)} L${f(hand[0] + 4.4)} ${f(y0 + 5.6)}`);
          hangA.setAttribute("d", `M${f(hand[0] - 6.4)} ${f(y0)} L${f(hand[0] + 6.4)} ${f(y0)} L${f(hand[0] + 4.8)} ${f(y0 + 8)} L${f(hand[0] - 4.8)} ${f(y0 + 8)}Z`);
          hangC.setAttribute("d", `M${f(hand[0] - 5)} ${f(y0)} Q${f(hand[0] - 3)} ${f(y0 - 4)} ${f(hand[0])} ${f(y0 - 1)} Q${f(hand[0] + 3)} ${f(y0 - 4.4)} ${f(hand[0] + 5)} ${f(y0)}Z`);
          propBack.appendChild(hangB);
        }
      }
      if (ganh) {
        const vel = (bob - lastBob) / Math.max(dt, 1e-3);
        lastBob = bob;
        const flex = ganhY.step(vel * 0.06 * ge, dt);
        const y0 = S[1] - 1.4, xA = S[0] - 30, xB = S[0] + 32;
        const endY = y0 + 2.2 + flex;
        ganh.pole.setAttribute("d", `M${f(xA)} ${f(endY)} Q${f(S[0] + 1)} ${f(y0 - 1.6)} ${f(xB)} ${f(endY)}`);
        ganh.poleInk.setAttribute("d", `M${f(xA)} ${f(endY - 1)} Q${f(S[0] + 1)} ${f(y0 - 2.6)} ${f(xB)} ${f(endY - 1)} M${f(xA)} ${f(endY + 1)} Q${f(S[0] + 1)} ${f(y0 - 0.6)} ${f(xB)} ${f(endY + 1)}`);
        const accel = Math.cos(2 * Math.PI * phase * 2) * 1.2 * ge;
        [xA + 1.6, xB - 1.6].forEach((x0, i) => {
          const k = ganh.baskets[i];
          const a = ganhP[i].step(-accel * (i ? 1 : 1.2) - wind * 0.25, dt);
          k.bg.setAttribute("transform", `rotate(${f(a * 57.3)} ${f(x0)} ${f(endY)})`);
          const by = endY + 40, bw = 8.4;
          k.rope.setAttribute("d", `M${f(x0)} ${f(endY)} L${f(x0 - bw)} ${f(by)} M${f(x0)} ${f(endY)} L${f(x0 + bw)} ${f(by)} M${f(x0)} ${f(endY)} L${f(x0 - 1.2)} ${f(by)}`);
          k.load.setAttribute("d", i ? `M${f(x0 - 7)} ${f(by + 0.4)} Q${f(x0 - 4)} ${f(by - 5)} ${f(x0)} ${f(by - 2)} Q${f(x0 + 4)} ${f(by - 5.4)} ${f(x0 + 7)} ${f(by + 0.4)}Z` : `M${f(x0 - 7)} ${f(by + 0.4)} Q${f(x0 - 6)} ${f(by - 3)} ${f(x0 - 3)} ${f(by - 3.2)} Q${f(x0)} ${f(by - 6)} ${f(x0 + 2.4)} ${f(by - 3)} Q${f(x0 + 6)} ${f(by - 3.4)} ${f(x0 + 7)} ${f(by + 0.4)}Z`);
          k.fruit.setAttribute("d", i ? `M${f(x0 - 2)} ${f(by - 1.6)} a2 1.9 0 1 0 0.1 0Z M${f(x0 + 3)} ${f(by - 0.8)} a1.8 1.7 0 1 0 0.1 0Z` : `M${f(x0 + 1)} ${f(by - 1)} a1.6 1.5 0 1 0 0.1 0Z`);
          k.body.setAttribute("d", `M${f(x0 - bw)} ${f(by)} L${f(x0 + bw)} ${f(by)} Q${f(x0 + bw - 0.4)} ${f(by + 7)} ${f(x0 + bw - 2)} ${f(by + 8.6)} L${f(x0 - bw + 2)} ${f(by + 8.6)} Q${f(x0 - bw + 0.4)} ${f(by + 7)} ${f(x0 - bw)} ${f(by)}Z`);
          k.weave.setAttribute("d", `M${f(x0 - bw + 0.6)} ${f(by + 3)} L${f(x0 + bw - 0.6)} ${f(by + 3)} M${f(x0 - bw + 1.2)} ${f(by + 5.8)} L${f(x0 + bw - 1.2)} ${f(by + 5.8)}`);
        });
      }
      if (suit) {
        const hb = toBase(hand);
        const Wc = [40 - 31, 117.7];
        const dx = hb[0] - Wc[0], dy = hb[1] - Wc[1], l = Math.hypot(dx, dy), u = [dx / l, dy / l], n = [u[1], -u[0]];
        const at = (s, o) => [Wc[0] + u[0] * s + n[0] * o, Wc[1] + u[1] * s + n[1] * o];
        suit.body.setAttribute("d", `M${P(at(0.4, 1))} L${P(at(24, 1))} Q${P(at(25, 1))} ${P(at(25, 2))} L${P(at(25, 13))} Q${P(at(25, 14))} ${P(at(24, 14))} L${P(at(1.4, 14))} Q${P(at(0.4, 14))} ${P(at(0.4, 13))}Z`);
        suit.rib.setAttribute("d", `M${P(at(5, 4.2))} L${P(at(21, 4.2))} M${P(at(5, 10.6))} L${P(at(21, 10.6))}`);
        suit.handle.setAttribute("d", `M${P(at(24.8, 6.6))} L${pt(hb)} M${P(at(24.8, 8.2))} L${f(hb[0] + n[0] * 1.4)} ${f(hb[1] + n[1] * 1.4)}`);
        suit.wheel.setAttribute("cx", f(Wc[0]));
        suit.wheel.setAttribute("cy", f(Wc[1]));
        const ang = rolled / 2.3;
        suit.spoke.setAttribute("d", `M${f(Wc[0] - Math.cos(ang) * 1.6)} ${f(Wc[1] - Math.sin(ang) * 1.6)} L${f(Wc[0] + Math.cos(ang) * 1.6)} ${f(Wc[1] + Math.sin(ang) * 1.6)}`);
      }
      const iF = p.front, kF = p.feet[iF].knee, aF = p.feet[iF].ankle, kR = p.feet[1 - iF].knee, aR = p.feet[1 - iF].ankle;
      const wB = toBase([40 - B.back + 0.2, R + 1]), wF = toBase([40 + B.chest - 0.8, R + 1]);
      if (skirt && skirtLine) {
        if (spec.top === "coat") {
          const hemY = R + 25, fx = Math.max(kF[0] + 1.6, wF[0] + 0.8);
          skirt.setAttribute("d", `M${pt(wB)} L${pt(wF)} Q${f(wF[0] + 0.6)} ${f(kF[1] - 8)} ${f(fx)} ${f(Math.min(kF[1], hemY - 2))} L${f(Math.max(fx - 0.4, aF[0] - 3))} ${f(hemY)} L${f(Math.min(wB[0] - 2.4, kR[0] - 3))} ${f(hemY + 0.8)} Q${f(wB[0] - 1.6)} ${f(R + 12)} ${pt(wB)}Z`);
          skirtLine.setAttribute("d", `M${f(wF[0] - 2)} ${f(wF[1])} L${f(fx - 1.6)} ${f(hemY - 0.4)} M${f(wF[0] - 5.6)} ${f(R + 8)} l4 0`);
        } else {
          const hemY = Math.max(kF[1], kR[1]) + 3.2;
          const fx = Math.max(kF[0] + 2.6, wF[0] + 1.6), bx = Math.min(kR[0] - 3, wB[0] - 2.4);
          skirt.setAttribute("d", `M${pt(wB)} L${pt(wF)} Q${f(fx - 0.6)} ${f((wF[1] + hemY) / 2)} ${f(fx)} ${f(hemY)} Q${f((fx + bx) / 2)} ${f(hemY + 1.4)} ${f(bx)} ${f(hemY)} Q${f(wB[0] - 1)} ${f((wB[1] + hemY) / 2)} ${pt(wB)}Z`);
          skirtLine.setAttribute("d", `M${f(wB[0] + 0.6)} ${f(wB[1] - 0.2)} L${f(wF[0] - 0.6)} ${f(wF[1] - 0.2)}`);
        }
      }
      if (flapB && flapF && flapPat) {
        const trail = flapS.step(-ge * 2.4 - wind * 1.4 + Math.sin(phase * Math.PI * 4) * 1.2 * ge, dt);
        const kick = flapF_S.step(Math.max(0, kF[0] - 46) * 0.8, dt);
        const hemY = 111.4;
        const bTop = [wB[0] + 0.4, wB[1]], bTopF = toBase([40 - 0.6, R + 1]);
        const bHem = [wB[0] - 2.4 + trail, hemY], bHemF = [bHem[0] + 8.6, hemY + 0.6];
        flapB.setAttribute("d", `M${pt(bTop)} L${pt(bTopF)} Q${f(bTopF[0] - 1)} ${f((bTopF[1] + hemY) / 2)} ${pt(bHemF)} L${pt(bHem)} Q${f(wB[0] - 2 + trail * 0.4)} ${f((wB[1] + hemY) / 2)} ${pt(bTop)}Z`);
        const fTop = toBase([40 + 0.6, R + 1]);
        const fHem = [Math.max(wF[0] + 2, aF[0] + 1.6) + kick * 0.3 + trail * 0.15, hemY], fHemB = [fHem[0] - 8.6, hemY + 0.6];
        flapF.setAttribute("d", `M${pt(fTop)} L${pt(wF)} Q${f(Math.max(wF[0] + 1, kF[0] + 2.4))} ${f(kF[1] - 6)} ${pt(fHem)} L${pt(fHemB)} Q${f(fTop[0] + 0.6)} ${f((fTop[1] + hemY) / 2)} ${pt(fTop)}Z`);
        flapPat.setAttribute("d", "");
      }
    }
  };
  return c;
}

// cast/roster.ts
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

// cast/skins.ts
var fromRoster = (id, label) => {
  const s = byId(id);
  return {
    id: label,
    label: s.role,
    outfit: {
      top: s.top,
      topColor: s.topColor,
      sleeve: s.sleeve,
      bottom: s.bottom,
      bottomColor: s.bottomColor,
      hat: s.hat,
      hatColor: s.hatColor,
      extras: (s.extras ?? []).filter((e) => e !== "glasses"),
      prop: s.prop,
      propColor: s.propColor,
      shoeColor: s.shoeColor
    }
  };
};
var LIST = [
  // Bo do rieng cho cac vai ngoai dan
  {
    id: "sep",
    label: "Sep / giam doc",
    outfit: { top: "jacket", topColor: "#2f3441", sleeve: "long", bottom: "trousers", bottomColor: "#1f232b", extras: ["tie"], prop: "none", shoeColor: "#1b1b1b" }
  },
  {
    id: "luat-su",
    label: "Luat su",
    outfit: { top: "jacket", topColor: "#3b3f4a", sleeve: "long", bottom: "trousers", bottomColor: "#2b2d34", extras: [], prop: "books", propColor: "#6b4f3a", shoeColor: "#1b1b1b" }
  },
  {
    id: "nhan-vien-van-phong",
    label: "Nhan vien van phong",
    outfit: { top: "shirt", topColor: "#ece6d6", sleeve: "long", bottom: "trousers", bottomColor: "#2f3540", extras: ["tie"], prop: "briefcase" }
  },
  // Bo do theo nghe da co trong dan: ai cung mac duoc
  fromRoster("bac-si-minh", "bac-si"),
  fromRoster("dieu-duong-lan", "dieu-duong"),
  fromRoster("can-bo-thu", "can-bo-kiem-dich"),
  fromRoster("anh-tuan", "cong-nhan"),
  fromRoster("anh-khoa", "hanh-khach")
];
var SKINS = Object.fromEntries(LIST.map((s) => [s.id, s]));
var skinById = (id) => {
  const s = SKINS[id];
  if (!s) throw new Error(`unknown skin ${id} (co: ${Object.keys(SKINS).join(", ")})`);
  return s;
};
function withSkin(spec, skinId) {
  if (!skinId) return spec;
  const sk = skinById(skinId);
  const glasses = (spec.extras ?? []).includes("glasses");
  const extras = [...sk.outfit.extras ?? []];
  if (glasses && !extras.includes("glasses")) extras.push("glasses");
  return { ...spec, ...sk.outfit, extras };
}

// cast/stage.ts
var STEP = 1 / 60;
var windAt = (t) => 0.18 + 0.25 * Math.sin(t * 0.21) + 0.15 * Math.sin(t * 0.67);
function createLineStage(svg, opt) {
  const { width, height } = opt;
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.style.color = opt.ink ?? "#1c1c1c";
  svg.style.setProperty("--paper", opt.paper ?? "#fdfcf8");
  const { filter } = inkDefs(svg, "ls");
  const bg = el("rect", { width, height, fill: opt.paper ?? "#fdfcf8" }, svg);
  bg.setAttribute("data-bg", "1");
  const scene = el("g", { filter }, svg);
  const back = el("g", {}, scene), people = el("g", {}, scene), front = el("g", {}, scene);
  let setupFn = null;
  let cast = [];
  let cues = [];
  let simT = 0, built = false;
  const shadows = [];
  const windows = [];
  const L = {
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
      const spec = withSkin(typeof who === "string" ? byId(who) : who, o.skin);
      const w0 = o.from ?? -Infinity, w1 = o.until ?? Infinity;
      checkWindow(spec.id, w0, w1, o.from !== void 0 || o.until !== void 0);
      const sh = el("ellipse", { rx: 9 * (o.scale ?? 1), ry: 1.4 * (o.scale ?? 1), fill: "#1c1c1c", opacity: 0.07, cy: o.y + 1 }, people);
      const c = applyTinhCach(createCharacter(people, spec, o), o.tinhCach);
      cast.push(c);
      shadows.push([c, sh]);
      if (o.from !== void 0 || o.until !== void 0) windows.push([c, sh, w0, w1]);
      return c;
    },
    at(t, fn) {
      cues.push({ t, fn, done: false });
    },
    ground(y, x0 = 0, x1 = width, weight = 0.9) {
      const p = pen(back, weight);
      p.setAttribute("d", `M${f(x0)} ${f(y + 1)} L${f(x1)} ${f(y + 1)}`);
      return p;
    },
    render(t) {
      if (!built || t < simT - 1e-6) rebuild();
      fire(simT);
      while (simT < t - 1e-9) {
        const dt = Math.min(STEP, t - simT);
        simT += dt;
        fire(simT);
        const w = windAt(simT);
        for (const c of cast) c.update(simT, dt, w);
      }
      for (const [c, sh] of shadows) sh.setAttribute("cx", f(c.x));
      for (const [c, sh, w0, w1] of windows) {
        const d = simT >= w0 - 1e-9 && simT < w1 - 1e-9 ? "" : "none";
        c.g.style.display = d;
        sh.style.display = d;
      }
    }
  };
  function fire(now) {
    for (const q of cues) if (!q.done && q.t <= now + 1e-9) {
      q.done = true;
      q.fn();
    }
  }
  const spans = {};
  function checkWindow(id, w0, w1, windowed) {
    if (!(w0 < w1)) throw new Error(`${id}: from (${w0}) phai nho hon until (${w1})`);
    const list = spans[id] ?? (spans[id] = []);
    for (const [a, b, wd] of list) if ((windowed || wd) && w0 < b - 1e-9 && a < w1 - 1e-9)
      throw new Error(`${id} da co tren san khau trong khoang ${a}..${b}: mot nhan vat chi hien mot ban cung luc (doi skin thi dat from/until noi tiep)`);
    list.push([w0, w1, windowed]);
  }
  function rebuild() {
    for (const layer of [back, people, front]) while (layer.firstChild) layer.removeChild(layer.firstChild);
    cast = [];
    cues = [];
    shadows.length = 0;
    windows.length = 0;
    simT = 0;
    for (const k of Object.keys(spans)) delete spans[k];
    setupFn?.(L);
    for (const c of cast) c.update(0, 0, windAt(0));
    built = true;
  }
  return L;
}
export {
  EXPRS,
  GESTURES,
  PAPER,
  PEN,
  ROSTER,
  SKINS,
  applyTinhCach,
  blot,
  byId,
  clamp2 as clamp,
  createCharacter,
  createLineStage,
  ease,
  el,
  f,
  inkDefs,
  lerp,
  limb,
  paint,
  pen,
  pendulum,
  pt,
  shape,
  skinById,
  smooth2 as smooth,
  solid,
  spring,
  tinhCachById,
  windAt,
  withSkin,
  wobble
};
