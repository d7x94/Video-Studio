#!/usr/bin/env python3
"""Kiem tra bo cuc tu dong bang so do: mo composition trong Chrome, tua toi nhieu moc, do vi tri chu,
phu de va nhan vat (line-art, chibi). Khong ve gi, khong sua composition.

Dung:  python3 kiem_bo_cuc.py BUILD_DIR [--json FILE] [--moi-canh 3]
       (vd ~/studio/<slug>/build/portrait; chay sau inject.py, truoc render ban cuoi)

Moc do: moi canh --moi-canh moc (dau, giua, cuoi khung hinh cua canh) va giua moi dong phu de dot.
Loi (LOI, thoat 1):
  CHU-RA-NGOAI     chu cua canh tran ra ngoai khung hinh
  CHU-DE-PHU-DE    chu cua canh nam de len phu de
  DAU-BI-CAT       mep tren hoac duoi khung cat dau nhan vat (con thay 15 den 85% dau)
Canh bao (CANH BAO, can mat nguoi xem lai, co the la co y):
  CHU-CHONG-CHU    hai khoi chu cua canh chong len nhau
  CHU-VUNG-NUT     khung doc: chu cua canh nam o day khung (duoi 300 px cuoi) hoac cot nut ben phai
                   (120 px phai, nua duoi), noi giao dien TikTok/Shorts che
  DAU-BI-CAT-MEP   mep trai/phai cat dau nhan vat (thuong la luc di vao, di ra; dung yen ma bi cat thi sua)
  NGUOI-BI-CAT-MEP than nhan vat bi mep trai/phai cat, con thay 15 den 85% be rong
  PHU-DE-CHE-MAT   phu de che mat nhan vat (hon 25% dien tich dau)
  CHU-CHE-MAT      chu cua canh che mat nhan vat (hon 25% dien tich dau)
Nhan vat 3D (Three.js ve len canvas) chua do duoc nhan vat, chi do chu va phu de.

Cach lam: chep index.html thanh __bocuc.html trong BUILD_DIR, chen mot doan script do, mo bang Chrome
khong giao dien (HYPERFRAMES_BROWSER_PATH trong studio.env), doc bao cao qua --dump-dom, xoa file tam.
"""
import argparse
import html
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

PROBE = r"""
(function () {
  function done(rep) { document.documentElement.setAttribute("data-bocuc", JSON.stringify(rep)); }
  function num(el, k) { return parseFloat(el.getAttribute(k)); }
  function inter(a, b) {
    var w = Math.min(a.r, b.r) - Math.max(a.l, b.l), h = Math.min(a.b, b.b) - Math.max(a.t, b.t);
    return w > 0 && h > 0 ? w * h : 0;
  }
  function area(a) { return Math.max(0, a.r - a.l) * Math.max(0, a.b - a.t); }
  function box(r) { return { l: r.left, t: r.top, r: r.right, b: r.bottom }; }
  function union(rs) {
    var u = null;
    rs.forEach(function (r) {
      if (r.width < 1 || r.height < 1) return;
      u = u ? { l: Math.min(u.l, r.left), t: Math.min(u.t, r.top), r: Math.max(u.r, r.right), b: Math.max(u.b, r.bottom) } : box(r);
    });
    return u;
  }
  function shown(el, root) {
    if (!el.getClientRects().length) return false;
    var o = 1;
    for (var e = el; e && e !== root.parentNode; e = e.parentElement) {
      var cs = getComputedStyle(e);
      if (cs.display === "none" || cs.visibility === "hidden") return false;
      o *= parseFloat(cs.opacity);
      if (e.style && e.style.display === "none") return false;
    }
    return o > 0.1;
  }
  function label(el) {
    var t = (el.textContent || "").trim().replace(/\s+/g, " ");
    return (el.id ? "#" + el.id + " " : "") + "\"" + t.slice(0, 40) + (t.length > 40 ? "..." : "") + "\"";
  }
  function run() {
    var root = document.getElementById("root");
    var tl = window.__timelines && window.__timelines.main;
    if (!root || !tl) return false;
    var W = num(root, "data-width"), H = num(root, "data-height"), portrait = H > W;
    var clips = Array.prototype.filter.call(root.querySelectorAll("[data-start][data-duration]"), function (e) { return e !== root; });
    var scenes = Array.prototype.filter.call(root.querySelectorAll("section[id^='sc-']"), function (e) { return e.hasAttribute("data-start"); });
    var caps = Array.prototype.slice.call(root.querySelectorAll(".cap"));
    var per = window.__BOCUC_PER || 3, times = [];
    scenes.forEach(function (s) {
      var a = num(s, "data-start"), d = num(s, "data-duration");
      for (var i = 0; i < per; i++) {
        var f = per === 1 ? 0.5 : i / (per - 1);
        times.push({ t: Math.min(a + d - 0.05, Math.max(a + 0.05, a + 0.35 + (d - 0.7) * f)), why: s.id.slice(3) });
      }
    });
    caps.forEach(function (c) { times.push({ t: num(c, "data-start") + num(c, "data-duration") / 2, why: c.id }); });
    times.sort(function (x, y) { return x.t - y.t; });
    var found = {}, out = [];
    function add(level, code, t, msg) {
      var key = code + "|" + msg.replace(/\d+%/g, "");
      if (found[key]) { found[key].n++; return; }
      found[key] = { level: level, code: code, t: Math.round(t * 100) / 100, msg: msg, n: 1 };
      out.push(found[key]);
    }
    times.forEach(function (it) {
      var t = it.t;
      clips.forEach(function (c) {
        var a = num(c, "data-start"), d = num(c, "data-duration");
        c.style.display = (t >= a && t < a + d) ? "" : "none";
      });
      tl.seek(t, false);
      var capBox = null;
      caps.forEach(function (c) {
        if (c.style.display === "none") return;
        var sp = c.querySelector("span") || c;
        var b = union(Array.prototype.slice.call(sp.getClientRects()));
        if (b) capBox = b;
      });
      var texts = [];
      var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
      var byEl = new Map();
      for (var n = walker.nextNode(); n; n = walker.nextNode()) {
        if (!n.nodeValue.trim()) continue;
        var el = n.parentElement;
        if (!el || el.closest(".cap") || el.closest("script,style,svg,title")) continue;
        if (!shown(el, root)) continue;
        var rg = document.createRange(); rg.selectNodeContents(n);
        var rs = Array.prototype.slice.call(rg.getClientRects());
        var blk = el.closest("div,p,h1,h2,h3,li,section") || el;
        var cur = byEl.get(blk) || [];
        byEl.set(blk, cur.concat(rs));
      }
      byEl.forEach(function (rs, el) { var b = union(rs); if (b) texts.push({ el: el, b: b }); });
      var people = [];
      Array.prototype.forEach.call(root.querySelectorAll("[data-nhan-vat]"), function (g) {
        if (!shown(g, root)) return;
        var b = box(g.getBoundingClientRect());
        if (area(b) < 4) return;
        var hd = g.querySelector("[data-dau]");
        var hb = hd && hd.getClientRects().length ? box(hd.getBoundingClientRect()) : null;
        people.push({ id: g.getAttribute("data-nhan-vat"), b: b, h: hb && area(hb) > 4 ? hb : null });
      });
      var frame = { l: 0, t: 0, r: W, b: H };
      texts.forEach(function (x, i) {
        var b = x.b, nm = label(x.el);
        if (b.l < -4 || b.t < -4 || b.r > W + 4 || b.b > H + 4) add("LOI", "CHU-RA-NGOAI", t, nm + " tran ra ngoai khung");
        if (capBox && inter(b, capBox) > 0.02 * Math.min(area(b), area(capBox))) add("LOI", "CHU-DE-PHU-DE", t, nm + " de len phu de");
        for (var j = i + 1; j < texts.length; j++) {
          var y = texts[j];
          if (x.el.contains(y.el) || y.el.contains(x.el)) continue;
          if (inter(b, y.b) > 0.15 * Math.min(area(b), area(y.b))) add("CANH BAO", "CHU-CHONG-CHU", t, nm + " chong len " + label(y.el));
        }
        if (portrait && (b.b > H - 300 || (b.r > W - 120 && b.b > H * 0.5)))
          add("CANH BAO", "CHU-VUNG-NUT", t, nm + " nam o vung giao dien TikTok/Shorts che (day khung hoac cot nut ben phai)");
        people.forEach(function (p) {
          if (p.h && inter(b, p.h) > 0.25 * area(p.h)) add("CANH BAO", "CHU-CHE-MAT", t, nm + " che mat " + p.id);
        });
      });
      people.forEach(function (p) {
        if (p.h) {
          var vis = inter(p.h, frame) / area(p.h);
          var tb = p.h.t < 0 || p.h.b > H;   // mep tren/duoi cat dau: loi; mep trai/phai: thuong la luc di vao, ra
          if (vis > 0.15 && vis < 0.85)
            add(tb ? "LOI" : "CANH BAO", tb ? "DAU-BI-CAT" : "DAU-BI-CAT-MEP", t, p.id + ": dau con thay " + Math.round(vis * 100) + "% trong khung");
          if (capBox && inter(capBox, p.h) > 0.25 * area(p.h)) add("CANH BAO", "PHU-DE-CHE-MAT", t, "phu de che mat " + p.id);
        }
        var w = p.b.r - p.b.l, vw = Math.max(0, Math.min(p.b.r, W) - Math.max(p.b.l, 0)) / (w || 1);
        if (vw > 0.15 && vw < 0.85) add("CANH BAO", "NGUOI-BI-CAT-MEP", t, p.id + ": than con thay " + Math.round(vw * 100) + "% be rong");
      });
    });
    done({ w: W, h: H, samples: times.length, people: document.querySelectorAll("[data-nhan-vat]").length, items: out });
    return true;
  }
  var tries = 0;
  function go() {
    tries++;
    try { if (run()) return; } catch (e) { done({ error: String(e && e.stack || e) }); return; }
    if (tries > 60) { done({ error: "khong thay #root hoac window.__timelines.main sau 6 giay" }); return; }
    setTimeout(go, 100);
  }
  window.addEventListener("load", function () {
    (document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve()).then(function () { setTimeout(go, 300); });
  });
})();
"""


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def browser():
    b = os.environ.get("HYPERFRAMES_BROWSER_PATH")
    if not b:
        env = Path(os.environ.get("STUDIO_HOME", Path.home() / "studio")) / "studio.env"
        if env.exists():
            m = re.search(r'HYPERFRAMES_BROWSER_PATH="?([^"\n]+)', env.read_text())
            b = m.group(1) if m else None
    if not b or not Path(b).exists():
        sys.exit("[LOI] Khong tim thay Chrome: chay setup.sh truoc (ghi HYPERFRAMES_BROWSER_PATH vao studio.env)")
    return b


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("build")
    ap.add_argument("--json", help="ghi bao cao day du ra file nay")
    ap.add_argument("--moi-canh", type=int, default=3, help="so moc do moi canh (mac dinh 3)")
    a = ap.parse_args()
    build = Path(a.build).resolve()
    index = build / "index.html"
    if not index.exists():
        sys.exit(f"[LOI] Khong co {index}")
    src = index.read_text(encoding="utf-8")
    m = re.search(r'data-width="(\d+)"[^>]*data-height="(\d+)"', src)
    w, h = (m.group(1), m.group(2)) if m else ("1080", "1920")
    probe = f"<script>window.__BOCUC_PER = {max(1, a.moi_canh)};</script><script src=\"__bocuc.js\"></script>"
    page = src.replace("</body>", probe + "\n</body>", 1) if "</body>" in src else src + probe
    tmp_html, tmp_js = build / "__bocuc.html", build / "__bocuc.js"
    tmp_html.write_text(page, encoding="utf-8")
    tmp_js.write_text(PROBE, encoding="utf-8")
    port = free_port()
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1", "--directory", str(build)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        import time
        time.sleep(0.8)
        with tempfile.TemporaryDirectory() as prof:
            r = subprocess.run([browser(), "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                                f"--user-data-dir={prof}", f"--window-size={w},{h}", "--virtual-time-budget=20000",
                                "--dump-dom", f"http://127.0.0.1:{port}/__bocuc.html"],
                               capture_output=True, text=True, timeout=300)
    finally:
        srv.terminate()
        tmp_html.unlink(missing_ok=True)
        tmp_js.unlink(missing_ok=True)
    m = re.search(r'data-bocuc="([^"]*)"', r.stdout)
    if not m:
        sys.exit("[LOI] Khong doc duoc bao cao bo cuc: composition co loi script? Chay hyperframes check truoc")
    rep = json.loads(html.unescape(m.group(1)))
    if rep.get("error"):
        sys.exit(f"[LOI] Script do bo cuc loi: {rep['error']}")
    if a.json:
        Path(a.json).write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    items = rep["items"]
    for it in sorted(items, key=lambda x: (x["level"] != "LOI", x["t"])):
        more = f" (lap lai o {it['n']} moc)" if it["n"] > 1 else ""
        print(f"[{it['level']}] {it['t']:6.2f}s {it['code']}: {it['msg']}{more}")
    n_err = sum(1 for x in items if x["level"] == "LOI")
    n_warn = len(items) - n_err
    print(f"Da do {rep['samples']} moc, {rep['people']} nhan vat danh dau. KET QUA: "
          + ("DAT" if not n_err else f"{n_err} LOI") + (f", {n_warn} canh bao" if n_warn else ""))
    sys.exit(1 if n_err else 0)


if __name__ == "__main__":
    main()
