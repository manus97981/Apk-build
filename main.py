#!/usr/bin/env python3
"""
Prime Shani — Sensi Generator
Free Fire Sensitivity Tool
"""

import os, re, time, threading
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line, RoundedRectangle
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.metrics import dp, sp
from kivy.core.window import Window
from kivy.utils import get_color_from_hex as C

# Palette
BG    = C("#030508")
BG2   = C("#0a0f1e")
BG3   = C("#0d1424")
GREEN = C("#00ff88")
CYAN  = C("#00e5ff")
MUTED = C("#3a4f70")
TEXT  = C("#c8daf0")
WHITE = C("#ffffff")

Window.clearcolor = BG

# ── Tier DB ────────────────────────────────────────────────────────────────
TIER_DB = {
    "snapdragon 8 gen 3":"flagship","snapdragon 8 gen 2":"flagship",
    "snapdragon 8+ gen 1":"flagship","snapdragon 8 gen 1":"flagship",
    "snapdragon 888":"flagship","dimensity 9300":"flagship","dimensity 9200":"flagship",
    "dimensity 8300":"upper_mid","snapdragon 7+ gen 3":"upper_mid",
    "snapdragon 7+ gen 2":"upper_mid","snapdragon 782g":"upper_mid",
    "dimensity 7200":"upper_mid","snapdragon 7s gen 2":"upper_mid",
    "snapdragon 695":"mid","snapdragon 680":"mid","snapdragon 685":"mid",
    "helio g99":"mid","helio g96":"mid","helio g91":"mid","helio g88":"mid",
    "helio g85":"budget","helio g36":"budget","helio g25":"budget",
    "unisoc":"budget","tiger t":"budget",
}

# ── Device Detection ───────────────────────────────────────────────────────
def _getprop(k):
    try:
        import subprocess
        r = subprocess.run(["getprop", k], capture_output=True, text=True, timeout=3)
        return (r.stdout or "").strip()
    except:
        return ""

def _read(path):
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            return f.read().strip()
    except:
        return ""

def detect_device():
    info = {}
    try:
        brand = _getprop("ro.product.brand")
        model = _getprop("ro.product.model")
        info["device"] = f"{brand} {model}".strip() or "Unknown"
    except:
        info["device"] = "Unknown"

    try:
        hw = ""
        for line in _read("/proc/cpuinfo").splitlines():
            if "Hardware" in line or "model name" in line:
                hw = line.split(":")[-1].strip()
                break
        if not hw:
            hw = _getprop("ro.hardware") or _getprop("ro.product.board") or "Unknown"
        info["chipset"] = hw
    except:
        info["chipset"] = "Unknown"

    try:
        for line in _read("/proc/meminfo").splitlines():
            if line.startswith("MemTotal:"):
                info["ram"] = round(int(line.split()[1]) / (1024*1024), 1)
                break
    except:
        info["ram"] = 4.0

    try:
        import subprocess
        out = subprocess.run(["wm","size"], capture_output=True, text=True, timeout=3).stdout
        m = re.search(r"(\d{3,4})x(\d{3,4})", out)
        info["w"] = int(m.group(1)) if m else int(Window.width)
        info["h"] = int(m.group(2)) if m else int(Window.height)
        out2 = subprocess.run(["wm","density"], capture_output=True, text=True, timeout=3).stdout
        m2 = re.search(r"(\d+)", out2)
        info["dpi"] = int(m2.group(1)) if m2 else 400
    except:
        info["w"] = int(Window.width)
        info["h"] = int(Window.height)
        info["dpi"] = 400

    hz = 60
    for path in ("/sys/class/graphics/fb0/mode", "/sys/class/drm/sde-crtc-0/mode"):
        txt = _read(path)
        for r in (144, 120, 90):
            if str(r) in txt:
                hz = r
                break
        if hz != 60:
            break
    info["hz"] = hz

    touch = 120
    for path in ("/sys/class/input/input0/sampling_rate",
                 "/sys/class/input/input1/sampling_rate"):
        try:
            touch = int(float(_read(path)))
            break
        except:
            pass
    info["touch"] = touch

    try:
        import subprocess
        ds = subprocess.run(["dumpsys","battery"], capture_output=True, text=True, timeout=3).stdout
        m3 = re.search(r"level:\s*(\d+)", ds)
        info["battery"] = int(m3.group(1)) if m3 else 80
    except:
        info["battery"] = 80

    try:
        info["load"] = round(os.getloadavg()[0], 2)
    except:
        info["load"] = 1.0

    return info

# ── Safe Benchmark (no large memory alloc) ────────────────────────────────
def benchmark():
    try:
        st = time.perf_counter()
        n, ops = 123456789, 0
        deadline = st + 1.2
        while time.perf_counter() < deadline:
            n = (n * 1103515245 + 12345) & 0x7FFFFFFF
            n ^= n >> 13
            ops += 1
        elapsed = max(time.perf_counter() - st, 0.001)
        cpu_ops = ops / elapsed

        # Small safe memory test
        sz = 512 * 1024  # 512KB only — safe on Android
        try:
            a = bytearray(sz)
            b = bytearray(sz)
            st2 = time.perf_counter()
            tb = 0
            deadline2 = st2 + 0.5
            while time.perf_counter() < deadline2:
                b[:] = a
                a[0] = (a[0] + 1) % 256
                tb += sz * 2
            elapsed2 = max(time.perf_counter() - st2, 0.001)
            mem_mb = (tb / (1024 * 1024)) / elapsed2
        except:
            mem_mb = 200.0

        return cpu_ops, mem_mb
    except Exception as e:
        return 50_000_000.0, 200.0

# ── Sensitivity Engine ────────────────────────────────────────────────────
def get_tier(chip):
    h = chip.lower()
    order = ["budget", "mid", "upper_mid", "flagship"]
    best = "mid"
    for k, v in TIER_DB.items():
        if k in h and order.index(v) > order.index(best):
            best = v
    return best

def calc_sensi(info):
    try:
        chip_tier = get_tier(info.get("chipset", ""))
        ram = float(info.get("ram", 4) or 4)
        hz = int(info.get("hz", 60) or 60)
        touch = int(info.get("touch", 120) or 120)
        battery = int(info.get("battery", 80) or 80)
        load = float(info.get("load", 1.0) or 1.0)
        resW = int(info.get("w", 1080) or 1080)
        resH = int(info.get("h", 2400) or 2400)
        dpi = int(info.get("dpi", 400) or 400)
        cpu_ops = float(info.get("cpu_ops", 50_000_000))
        mem_mb = float(info.get("mem_mb", 200))

        R1, R2 = 120_000_000.0, 600.0
        cs = min(100, (cpu_ops / R1) * 100)
        ms = min(100, (mem_mb / R2) * 100)

        tier_base = {"budget": 28, "mid": 48, "upper_mid": 68, "flagship": 84}
        gp = tier_base.get(chip_tier, 48)
        if ram >= 12: gp += 12
        elif ram >= 8: gp += 7
        elif ram >= 6: gp += 3
        elif ram < 4: gp -= 8
        if touch >= 240: gp += 10
        elif touch >= 120: gp += 5
        if hz >= 120: gp += 6
        elif hz >= 90: gp += 3
        if battery >= 50: gp += 4
        if battery < 20: gp -= 10
        if load > 4: gp -= 8
        elif load > 2.5: gp -= 4
        perf = max(0.0, min(100.0, cs * 0.42 + ms * 0.22 + gp * 0.36))

        tb = {"budget": 98, "mid": 122, "upper_mid": 148, "flagship": 175}.get(chip_tier, 122)
        base = float(tb) + (perf - 50) * 0.92
        hz_bonus = {60: 0, 90: 9, 120: 16, 144: 20}.get(hz, 0)
        base += hz_bonus

        if resW > 0 and resH > 0:
            dg = (resW ** 2 + resH ** 2) ** 0.5
            df = (dpi or 400) / 400.0
            if dg >= 2600: base -= 10
            elif dg >= 2350: base -= 5
            elif dg < 2000: base += 5
            base -= (df - 1.0) * 11

        if ram < 4: base -= 14
        elif ram < 6: base -= 7
        elif ram >= 12: base += 8

        lat = max(4.0, 1000.0 / touch) if touch > 0 else 16.0
        if 0 < lat < 8: base += 6
        elif lat > 12: base -= 4
        if battery >= 40 and load < 2.0: base += 3

        hs = 0
        if perf >= 55 and chip_tier in ("upper_mid", "flagship"): hs += 6
        if 0 < lat <= 10: hs += 4
        if hz >= 90: hs += 3

        def cl(v):
            return max(1, min(200, int(round(float(v)))))

        g = cl(base + hs)
        rd = cl(min(g * 0.91, g - 6))
        x2 = cl(min(g * 0.83, rd - 9))
        x4 = cl(min(g * 0.73, x2 - 11))
        sn = cl(min(g * 0.67, x4 - 9))
        fl = cl(max(g * 0.94, g - 14))
        if perf >= 60:
            rd = cl(min(rd + 2, g - 4))

        return {
            "sx": {"General": g, "Red Dot": rd, "2x Scope": x2,
                   "4x Scope": x4, "Sniper": sn, "Free Look": fl},
            "tier": chip_tier,
            "perf": round(perf, 1),
            "hs": hs > 0,
            "lat": round(lat, 1),
        }
    except Exception as e:
        return {
            "sx": {"General": 100, "Red Dot": 90, "2x Scope": 80,
                   "4x Scope": 70, "Sniper": 60, "Free Look": 95},
            "tier": "mid", "perf": 50.0, "hs": False, "lat": 8.3,
        }

# ── Simple KV-style helpers ───────────────────────────────────────────────
def make_card(bg=BG3, border=GREEN):
    w = Widget()
    with w.canvas:
        Color(*bg)
        w._bg = RoundedRectangle(pos=w.pos, size=w.size, radius=[dp(6)])
        Color(*border, 0.35)
        w._bd = Line(rounded_rectangle=[*w.pos, *w.size, dp(6)], width=1)
    def upd(*a):
        w._bg.pos = w.pos
        w._bg.size = w.size
        w._bd.rounded_rectangle = [*w.pos, *w.size, dp(6)]
    w.bind(pos=upd, size=upd)
    return w

# ── Screens ───────────────────────────────────────────────────────────────
class ScanScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._info = {}
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical")

        # ── Header ──
        hdr = BoxLayout(orientation="vertical",
                        size_hint_y=None, height=dp(100),
                        padding=[dp(18), dp(14)])
        with hdr.canvas.before:
            Color(*BG2)
            self._hbg = Rectangle(pos=hdr.pos, size=hdr.size)
            Color(*GREEN, 0.7)
            self._hline = Line(points=[0,0,0,0], width=1.5)
        def upd_h(*a):
            self._hbg.pos = hdr.pos
            self._hbg.size = hdr.size
            x, y = hdr.pos
            self._hline.points = [x, y, x + hdr.width, y]
        hdr.bind(pos=upd_h, size=upd_h)

        hdr.add_widget(Label(text="PRIME SHANI", font_size=sp(24), bold=True,
                             color=GREEN, halign="left", valign="middle",
                             size_hint_y=None, height=dp(32),
                             text_size=(None, None)))
        hdr.add_widget(Label(text="SENSI GENERATOR  //  FREE FIRE",
                             font_size=sp(10), color=MUTED,
                             halign="left", valign="middle",
                             size_hint_y=None, height=dp(18),
                             text_size=(None, None)))
        self._status_lbl = Label(text="// INITIALIZING...",
                                  font_size=sp(10), color=CYAN,
                                  halign="left", valign="middle",
                                  size_hint_y=None, height=dp(16),
                                  text_size=(None, None))
        hdr.add_widget(self._status_lbl)

        # ── Scroll ──
        sv = ScrollView()
        body = BoxLayout(orientation="vertical",
                         padding=[dp(14), dp(14)],
                         spacing=dp(10), size_hint_y=None)
        body.bind(minimum_height=body.setter("height"))

        # Section label
        body.add_widget(self._sec("// DEVICE INFO"))

        # Cards
        self._c_dev   = self._info_card("DEVICE",      "Scanning...")
        self._c_chip  = self._info_card("CHIPSET",     "—")
        body.add_widget(self._c_dev)
        body.add_widget(self._c_chip)

        row1 = GridLayout(cols=3, spacing=dp(8), size_hint_y=None, height=dp(68))
        self._c_ram  = self._mini_card("RAM",     "—", "GB")
        self._c_hz   = self._mini_card("REFRESH", "—", "Hz")
        self._c_bat  = self._mini_card("BATTERY", "—", "%")
        row1.add_widget(self._c_ram)
        row1.add_widget(self._c_hz)
        row1.add_widget(self._c_bat)
        body.add_widget(row1)

        row2 = GridLayout(cols=3, spacing=dp(8), size_hint_y=None, height=dp(68))
        self._c_res   = self._mini_card("SCREEN",  "—", "")
        self._c_touch = self._mini_card("TOUCH",   "—", "Hz")
        self._c_load  = self._mini_card("LOAD",    "—", "")
        row2.add_widget(self._c_res)
        row2.add_widget(self._c_touch)
        row2.add_widget(self._c_load)
        body.add_widget(row2)

        body.add_widget(Widget(size_hint_y=None, height=dp(10)))

        # Generate button
        self._btn = Button(
            text="⚡  SCAN & GENERATE",
            size_hint_y=None, height=dp(54),
            bold=True, font_size=sp(16),
            background_normal="", background_color=(0,0,0,0),
            color=BG
        )
        with self._btn.canvas.before:
            Color(*GREEN)
            self._btn_bg = RoundedRectangle(
                pos=self._btn.pos, size=self._btn.size, radius=[dp(8)])
        self._btn.bind(
            pos=lambda i, v: setattr(self._btn_bg, "pos", v),
            size=lambda i, v: setattr(self._btn_bg, "size", v),
            on_release=self._on_scan
        )
        body.add_widget(self._btn)
        body.add_widget(Widget(size_hint_y=None, height=dp(24)))

        sv.add_widget(body)
        root.add_widget(hdr)
        root.add_widget(sv)
        self.add_widget(root)

        Clock.schedule_once(lambda dt: self._start_detect(), 0.4)

    def _sec(self, txt):
        l = Label(text=txt, font_size=sp(10), color=MUTED,
                  halign="left", valign="middle",
                  size_hint_y=None, height=dp(20))
        l.bind(size=lambda i, v: setattr(i, "text_size", v))
        return l

    def _info_card(self, lbl, val):
        box = BoxLayout(orientation="vertical",
                        size_hint_y=None, height=dp(64),
                        padding=[dp(12), dp(8)])
        with box.canvas.before:
            Color(*BG3)
            b = RoundedRectangle(pos=box.pos, size=box.size, radius=[dp(6)])
            Color(*GREEN, 0.3)
            ln = Line(rounded_rectangle=[*box.pos, *box.size, dp(6)], width=1)
        def upd(*a):
            b.pos = box.pos; b.size = box.size
            ln.rounded_rectangle = [*box.pos, *box.size, dp(6)]
        box.bind(pos=upd, size=upd)

        lbl_w = Label(text=lbl, font_size=sp(9), color=MUTED,
                      halign="left", valign="middle",
                      size_hint_y=None, height=dp(14))
        lbl_w.bind(size=lambda i, v: setattr(i, "text_size", v))
        val_w = Label(text=val, font_size=sp(18), color=GREEN,
                      bold=True, halign="left", valign="middle")
        val_w.bind(size=lambda i, v: setattr(i, "text_size", v))
        box.add_widget(lbl_w)
        box.add_widget(val_w)
        box._val = val_w
        return box

    def _mini_card(self, lbl, val, unit):
        box = BoxLayout(orientation="vertical",
                        padding=[dp(8), dp(6)])
        with box.canvas.before:
            Color(*BG3)
            b = RoundedRectangle(pos=box.pos, size=box.size, radius=[dp(5)])
            Color(*CYAN, 0.2)
            ln = Line(rounded_rectangle=[*box.pos, *box.size, dp(5)], width=1)
        def upd(*a):
            b.pos = box.pos; b.size = box.size
            ln.rounded_rectangle = [*box.pos, *box.size, dp(5)]
        box.bind(pos=upd, size=upd)

        lbl_w = Label(text=lbl, font_size=sp(8), color=MUTED,
                      halign="center", valign="middle",
                      size_hint_y=None, height=dp(14))
        lbl_w.bind(size=lambda i, v: setattr(i, "text_size", v))
        val_row = BoxLayout(orientation="horizontal")
        val_w = Label(text=val, font_size=sp(16), color=CYAN,
                      bold=True, halign="center", valign="middle")
        val_w.bind(size=lambda i, v: setattr(i, "text_size", v))
        if unit:
            unt_w = Label(text=unit, font_size=sp(9), color=MUTED,
                          halign="left", valign="bottom",
                          size_hint_x=None, width=dp(24))
            val_row.add_widget(val_w)
            val_row.add_widget(unt_w)
        else:
            val_row.add_widget(val_w)
        box.add_widget(lbl_w)
        box.add_widget(val_row)
        box._val = val_w
        return box

    def _set(self, card, v):
        card._val.text = str(v)

    def _start_detect(self):
        self._status_lbl.text = "// DETECTING DEVICE..."
        threading.Thread(target=self._detect_thread, daemon=True).start()

    def _detect_thread(self):
        try:
            info = detect_device()
        except:
            info = {"device":"Unknown","chipset":"Unknown","ram":4,
                    "hz":60,"battery":80,"w":1080,"h":2400,
                    "dpi":400,"touch":120,"load":1.0}
        Clock.schedule_once(lambda dt: self._fill(info))

    def _fill(self, info):
        self._info = info
        self._set(self._c_dev,   info.get("device","?")[:22])
        self._set(self._c_chip,  info.get("chipset","?")[:26])
        self._set(self._c_ram,   info.get("ram","?"))
        self._set(self._c_hz,    info.get("hz","?"))
        self._set(self._c_bat,   info.get("battery","?"))
        w, h = info.get("w",0), info.get("h",0)
        self._set(self._c_res,   f"{w}x{h}" if w else "?")
        self._set(self._c_touch, info.get("touch","?"))
        self._set(self._c_load,  f"{info.get('load',0):.1f}")
        self._status_lbl.text = "// READY — TAP GENERATE"

    def _on_scan(self, *a):
        if getattr(self, "_scanning", False):
            return
        self._scanning = True
        self._btn.text = "  BENCHMARKING..."
        with self._btn.canvas.before:
            Color(*MUTED)
            self._btn_bg = RoundedRectangle(
                pos=self._btn.pos, size=self._btn.size, radius=[dp(8)])
        self._status_lbl.text = "// RUNNING BENCHMARK..."
        threading.Thread(target=self._scan_thread, daemon=True).start()

    def _scan_thread(self):
        try:
            cpu_ops, mem_mb = benchmark()
            self._info["cpu_ops"] = cpu_ops
            self._info["mem_mb"] = mem_mb
            result = calc_sensi(self._info)
        except:
            result = calc_sensi(self._info)
        Clock.schedule_once(lambda dt: self._done(result))

    def _done(self, result):
        self._scanning = False
        self._btn.text = "⚡  SCAN & GENERATE"
        with self._btn.canvas.before:
            Color(*GREEN)
            self._btn_bg = RoundedRectangle(
                pos=self._btn.pos, size=self._btn.size, radius=[dp(8)])
        app = App.get_running_app()
        app.last_result = result
        app.last_info = self._info
        self.manager.current = "result"


class ResultScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        self._build()

    def _build(self):
        app = App.get_running_app()
        result = getattr(app, "last_result", {})
        info   = getattr(app, "last_info", {})
        sx     = result.get("sx", {})
        tier   = result.get("tier", "mid")
        perf   = result.get("perf", 50)
        hs     = result.get("hs", False)
        lat    = result.get("lat", 8.0)

        tier_c = {"flagship": GREEN, "upper_mid": CYAN,
                  "mid": C("#ffcc00"), "budget": MUTED}.get(tier, CYAN)
        tier_l = {"flagship":"FLAGSHIP","upper_mid":"UPPER MID",
                  "mid":"MID RANGE","budget":"BUDGET"}.get(tier, tier.upper())

        root = BoxLayout(orientation="vertical")

        # Header
        hdr = BoxLayout(orientation="vertical",
                        size_hint_y=None, height=dp(88),
                        padding=[dp(18), dp(12)])
        with hdr.canvas.before:
            Color(*BG2)
            bg = Rectangle(pos=hdr.pos, size=hdr.size)
            Color(*tier_c, 0.6)
            ln = Line(points=[0,0,0,0], width=1.5)
        def upd_h(*a):
            bg.pos = hdr.pos; bg.size = hdr.size
            x, y = hdr.pos
            ln.points = [x, y, x + hdr.width, y]
        hdr.bind(pos=upd_h, size=upd_h)

        hdr.add_widget(Label(
            text="PRIME SHANI", font_size=sp(22), bold=True,
            color=GREEN, halign="left", valign="middle",
            size_hint_y=None, height=dp(30), text_size=(None,None)))
        hdr.add_widget(Label(
            text=f"{info.get('device','?')[:26]}  //  {tier_l}",
            font_size=sp(10), color=tier_c,
            halign="left", valign="middle",
            size_hint_y=None, height=dp(16), text_size=(None,None)))
        hdr.add_widget(Label(
            text=f"POWER {perf:.0f}/100  |  LAT {lat}ms  |  HS {'ON ●' if hs else 'OFF ○'}",
            font_size=sp(9), color=GREEN if hs else MUTED,
            halign="left", valign="middle",
            size_hint_y=None, height=dp(14), text_size=(None,None)))

        # Body
        sv = ScrollView()
        body = BoxLayout(orientation="vertical",
                         padding=[dp(14), dp(12)],
                         spacing=dp(8), size_hint_y=None)
        body.bind(minimum_height=body.setter("height"))

        body.add_widget(self._sec("// SENSITIVITY VALUES"))

        ORDER = ["General","Red Dot","2x Scope","4x Scope","Sniper","Free Look"]
        for k in ORDER:
            v = sx.get(k, 0)
            body.add_widget(self._sensi_row(k, v, highlight=(k=="General"), tc=tier_c))

        body.add_widget(Widget(size_hint_y=None, height=dp(6)))
        body.add_widget(self._sec("// FULL REPORT"))

        report = self._make_report(info, result)
        rbox = BoxLayout(size_hint_y=None, padding=[dp(10), dp(8)])
        with rbox.canvas.before:
            Color(0,0,0,1)
            rb = RoundedRectangle(pos=rbox.pos, size=rbox.size, radius=[dp(6)])
            Color(*GREEN, 0.12)
            rl = Line(rounded_rectangle=[*rbox.pos,*rbox.size,dp(6)], width=1)
        def upd_r(*a):
            rb.pos = rbox.pos; rb.size = rbox.size
            rl.rounded_rectangle = [*rbox.pos,*rbox.size,dp(6)]
        rbox.bind(pos=upd_r, size=upd_r)
        rlbl = Label(text=report, font_size=sp(10), color=C("#7ecfb0"),
                     halign="left", valign="top", size_hint_y=None)
        rlbl.bind(texture_size=lambda i,v: setattr(i,"height",v[1]+dp(8)))
        rlbl.bind(width=lambda i,v: setattr(i,"text_size",(v,None)))
        rbox.bind(minimum_height=rbox.setter("height"))
        rbox.add_widget(rlbl)
        body.add_widget(rbox)

        body.add_widget(Widget(size_hint_y=None, height=dp(8)))

        # Copy button
        cbtn = Button(text="📋  COPY REPORT",
                      size_hint_y=None, height=dp(50),
                      bold=True, font_size=sp(14),
                      background_normal="", background_color=(0,0,0,0),
                      color=BG)
        with cbtn.canvas.before:
            Color(*GREEN)
            cb = RoundedRectangle(pos=cbtn.pos, size=cbtn.size, radius=[dp(7)])
        cbtn.bind(pos=lambda i,v: setattr(cb,"pos",v),
                  size=lambda i,v: setattr(cb,"size",v))
        cbtn._report = report
        def do_copy(btn, *a):
            try:
                Clipboard.copy(btn._report)
            except:
                pass
            btn.text = "✅  COPIED!"
            Clock.schedule_once(lambda dt: setattr(btn,"text","📋  COPY REPORT"), 2)
        cbtn.bind(on_release=do_copy)
        body.add_widget(cbtn)

        # Back button
        bbtn = Button(text="← RESCAN",
                      size_hint_y=None, height=dp(42),
                      background_normal="", background_color=(0,0,0,0),
                      color=MUTED, font_size=sp(13))
        bbtn.bind(on_release=lambda *a: setattr(self.manager,"current","scan"))
        body.add_widget(bbtn)
        body.add_widget(Widget(size_hint_y=None, height=dp(24)))

        sv.add_widget(body)
        root.add_widget(hdr)
        root.add_widget(sv)
        self.add_widget(root)

    def _sec(self, txt):
        l = Label(text=txt, font_size=sp(10), color=MUTED,
                  halign="left", valign="middle",
                  size_hint_y=None, height=dp(20))
        l.bind(size=lambda i,v: setattr(i,"text_size",v))
        return l

    def _sensi_row(self, label, value, highlight=False, tc=GREEN):
        h = dp(72) if highlight else dp(58)
        box = BoxLayout(orientation="vertical",
                        size_hint_y=None, height=h,
                        padding=[dp(14), dp(8)], spacing=dp(4))
        bc = tc if highlight else CYAN
        fs = sp(14) if highlight else sp(11)
        vs = sp(30) if highlight else sp(22)
        vc = tc if highlight else WHITE

        with box.canvas.before:
            Color(*BG3)
            bg = RoundedRectangle(pos=box.pos, size=box.size, radius=[dp(6)])
            Color(*bc, 0.3 if highlight else 0.2)
            ln = Line(rounded_rectangle=[*box.pos,*box.size,dp(6)],
                      width=1.4 if highlight else 1.0)
        def upd(*a):
            bg.pos = box.pos; bg.size = box.size
            ln.rounded_rectangle = [*box.pos,*box.size,dp(6)]
        box.bind(pos=upd, size=upd)

        row = BoxLayout(orientation="horizontal")
        lbl = Label(text=label, font_size=fs, color=TEXT if highlight else MUTED,
                    bold=highlight, halign="left", valign="middle")
        lbl.bind(size=lambda i,v: setattr(i,"text_size",v))
        val = Label(text=str(value), font_size=vs, color=vc,
                    bold=True, halign="right", valign="middle")
        val.bind(size=lambda i,v: setattr(i,"text_size",v))
        row.add_widget(lbl)
        row.add_widget(val)
        box.add_widget(row)

        # Bar
        pct = value / 200.0
        bar_bg = Widget(size_hint_y=None, height=dp(3))
        with bar_bg.canvas:
            Color(*C("#1a2540"))
            bar_bg_r = RoundedRectangle(pos=bar_bg.pos, size=bar_bg.size, radius=[dp(2)])
        bar_bg.bind(pos=lambda i,v: setattr(bar_bg_r,"pos",v),
                    size=lambda i,v: setattr(bar_bg_r,"size",v))

        bar_fill = Widget(size_hint_y=None, height=dp(3))
        with bar_fill.canvas:
            Color(*bc)
            bar_fill_r = RoundedRectangle(
                pos=bar_fill.pos,
                size=(bar_fill.width * pct, bar_fill.height),
                radius=[dp(2)])
        bar_fill.bind(
            pos=lambda i,v: setattr(bar_fill_r,"pos",v),
            size=lambda i,v: setattr(bar_fill_r,"size",
                (v[0]*pct, v[1])))
        box.add_widget(bar_bg)
        box.add_widget(bar_fill)
        return box

    def _make_report(self, info, result):
        sx = result.get("sx", {})
        ORDER = ["General","Red Dot","2x Scope","4x Scope","Sniper","Free Look"]
        sep = "=" * 38
        lines = [
            sep,
            "  PRIME SHANI — SENSI GENERATOR",
            "  FREE FIRE SENSITIVITY TOOL",
            sep,
            f"DEVICE  : {info.get('device','?')}",
            f"CHIP    : {info.get('chipset','?')}",
            f"RAM     : {info.get('ram','?')} GB",
            f"SCREEN  : {info.get('w','?')}x{info.get('h','?')} @{info.get('hz','?')}Hz",
            f"BATTERY : {info.get('battery','?')}%",
            f"TOUCH   : {info.get('touch','?')} Hz",
            f"TIER    : {result.get('tier','?').upper()}",
            f"POWER   : {result.get('perf','?')}/100",
            f"HS MODE : {'ON' if result.get('hs') else 'OFF'}",
            "",
            "--- IN-GAME SENSITIVITY ---",
        ]
        for k in ORDER:
            lines.append(f"{k:<16}: {sx.get(k,'?')}")
        lines.extend(["", sep])
        return "\n".join(lines)


class PrimeShaniApp(App):
    last_result = {}
    last_info = {}

    def build(self):
        self.title = "Prime Shani"
        sm = ScreenManager(transition=FadeTransition(duration=0.15))
        sm.add_widget(ScanScreen(name="scan"))
        sm.add_widget(ResultScreen(name="result"))
        return sm

if __name__ == "__main__":
    PrimeShaniApp().run()
