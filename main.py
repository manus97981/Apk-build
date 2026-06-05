#!/usr/bin/env python3
"""
Prime Shani — Sensi Generator
Free Fire Sensitivity Tool
"""

import os, re, subprocess, platform, time, threading
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line, Ellipse, RoundedRectangle
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.metrics import dp, sp
from kivy.animation import Animation
from kivy.properties import NumericProperty, StringProperty, BooleanProperty
from kivy.core.window import Window
from kivy.utils import get_color_from_hex as C

# ── Palette ────────────────────────────────────────────────────────────────
BG       = C("#030508")
BG2      = C("#080d18")
BG3      = C("#0d1424")
ACCENT   = C("#00ff88")
ACCENT2  = C("#00cc6a")
CYAN     = C("#00e5ff")
DIM      = C("#1a2540")
MUTED    = C("#3a4f70")
TEXT     = C("#c8daf0")
WHITE    = C("#ffffff")
DANGER   = C("#ff4444")

Window.clearcolor = BG

# ── Sensitivity Engine ─────────────────────────────────────────────────────
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

def _getprop(k):
    try:
        r = subprocess.run(["getprop", k], capture_output=True, text=True, timeout=4)
        return (r.stdout or "").strip()
    except:
        return ""

def _read_file(path):
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            return f.read().strip()
    except:
        return ""

def detect_device():
    info = {}
    # Device name
    brand = _getprop("ro.product.brand") or _getprop("ro.product.vendor.brand")
    model = _getprop("ro.product.model")
    info["device"] = f"{brand} {model}".strip() if brand else (model or platform.node() or "Unknown")

    # Chipset from cpuinfo
    cpuinfo = _read_file("/proc/cpuinfo")
    hw = ""
    for line in cpuinfo.splitlines():
        if "Hardware" in line or "model name" in line or "Processor" in line:
            hw = line.split(":")[-1].strip()
            break
    if not hw:
        hw = _getprop("ro.hardware") or _getprop("ro.product.board") or "Unknown"
    info["chipset"] = hw

    # RAM
    try:
        with open("/proc/meminfo", encoding="utf-8") as f:
            for ln in f:
                if ln.startswith("MemTotal:"):
                    info["ram"] = round(int(ln.split()[1]) / (1024*1024), 1)
                    break
    except:
        info["ram"] = 0.0

    # Screen
    try:
        wm = subprocess.run(["wm","size"], capture_output=True, text=True, timeout=4).stdout
        m = re.search(r"(\d{3,4})x(\d{3,4})", wm)
        if m:
            info["w"], info["h"] = int(m.group(1)), int(m.group(2))
        else:
            info["w"], info["h"] = int(Window.width), int(Window.height)
    except:
        info["w"], info["h"] = int(Window.width), int(Window.height)

    try:
        dn = subprocess.run(["wm","density"], capture_output=True, text=True, timeout=4).stdout
        m2 = re.search(r"(\d+)\s*dpi", dn, re.I)
        info["dpi"] = int(m2.group(1)) if m2 else 400
    except:
        info["dpi"] = 400

    # Refresh rate
    hz = 60
    for path in ("/sys/class/graphics/fb0/mode", "/sys/class/drm/sde-crtc-0/mode"):
        txt = _read_file(path).lower()
        for r in (144, 120, 90):
            if str(r) in txt:
                hz = r
                break
        if hz != 60:
            break
    info["hz"] = hz

    # Touch sampling
    touch = 0
    for path in ("/sys/class/input/input0/sampling_rate", "/sys/class/input/input1/sampling_rate"):
        try:
            touch = int(float(_read_file(path)))
            break
        except:
            pass
    info["touch"] = touch or 120

    # Battery
    try:
        ds = subprocess.run(["dumpsys","battery"], capture_output=True, text=True, timeout=4).stdout
        m3 = re.search(r"level:\s*(\d+)", ds)
        info["battery"] = int(m3.group(1)) if m3 else 80
    except:
        info["battery"] = 80

    # Load
    try:
        info["load"] = round(os.getloadavg()[0], 2)
    except:
        info["load"] = 1.0

    return info

def get_tier(chip):
    h = chip.lower()
    order = ["budget","mid","upper_mid","flagship"]
    best = "mid"
    for k, v in TIER_DB.items():
        if k in h and order.index(v) > order.index(best):
            best = v
    return best

def benchmark():
    try:
        st = time.perf_counter()
        n, ops = 123456789, 0
        deadline = st + 1.2
        while time.perf_counter() < deadline:
            n = (n * 1103515245 + 12345) & 0x7FFFFFFF
            n ^= n >> 13
            ops += 1
        cpu_ops = ops / max(time.perf_counter() - st, 0.001)
        sz = 512 * 1024
        try:
            a, b = bytearray(sz), bytearray(sz)
            st2 = time.perf_counter()
            tb = 0
            deadline2 = st2 + 0.5
            while time.perf_counter() < deadline2:
                b[:] = a
                a[0] = (a[0]+1)%256
                tb += sz*2
            mem_mb = (tb/(1024*1024)) / max(time.perf_counter()-st2, 0.001)
        except:
            mem_mb = 200.0
        return cpu_ops, mem_mb
    except:
        return 50_000_000.0, 200.0

def calc_sensi(info):
    chip_tier = get_tier(info.get("chipset",""))
    ram = info.get("ram", 4)
    hz = info.get("hz", 60)
    touch = info.get("touch", 120)
    battery = info.get("battery", 80)
    load = info.get("load", 1.0)
    resW = info.get("w", 1080)
    resH = info.get("h", 2400)
    dpi = info.get("dpi", 400)
    cpu_ops = info.get("cpu_ops", 0)
    mem_mb = info.get("mem_mb", 0)

    # Performance score
    R1, R2 = 120_000_000.0, 800.0
    cs = min(100, (cpu_ops/R1)*100) if cpu_ops > 0 else 40
    ms = min(100, (mem_mb/R2)*100) if mem_mb > 0 else 40
    tier_base_score = {"budget":28,"mid":48,"upper_mid":68,"flagship":84}
    gp = tier_base_score.get(chip_tier, 48)
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
    perf = max(0, min(100, cs*0.42 + ms*0.22 + gp*0.36))

    # Sensitivity base
    tb = {"budget":98,"mid":122,"upper_mid":148,"flagship":175}.get(chip_tier,122)
    base = tb + (perf - 50) * 0.92
    hz_bonus = {60:0,90:9,120:16,144:20}.get(hz,0)
    base += hz_bonus

    # Screen
    if resW > 0 and resH > 0:
        dg = (resW**2 + resH**2)**0.5
        df = (dpi or 400)/400
        if dg >= 2600: base -= 10
        elif dg >= 2350: base -= 5
        elif dg < 2000: base += 5
        base -= (df - 1.0) * 11

    # RAM
    if ram < 4: base -= 14
    elif ram < 6: base -= 7
    elif ram >= 12: base += 8

    # Latency
    lat = max(4.0, 1000/touch) if touch > 0 else 16.0
    if 0 < lat < 8: base += 6
    elif lat > 12: base -= 4

    # Battery boost
    if battery >= 40 and load < 2.0: base += 8*0.35

    # HS mode
    hs = 0
    if perf >= 55 and chip_tier in ("upper_mid","flagship"): hs += 6
    if 0 < lat <= 10: hs += 4
    if hz >= 90: hs += 3

    def cl(v): return max(1, min(200, int(round(v))))

    g = cl(base + hs)
    sx = {
        "General": g,
        "Red Dot": cl(min(g*0.91, g-6)),
        "2x Scope": cl(min(g*0.83, cl(min(g*0.91,g-6))-9)),
        "4x Scope": cl(min(g*0.73, cl(min(g*0.83, cl(min(g*0.91,g-6))-9))-11)),
        "Sniper":   cl(min(g*0.67, cl(min(g*0.73, cl(min(g*0.83, cl(min(g*0.91,g-6))-9))-11))-9)),
        "Free Look":cl(max(g*0.94, g-14)),
    }
    if perf >= 60:
        sx["Red Dot"] = cl(min(sx["Red Dot"]+2, g-4))

    return {
        "sx": sx, "tier": chip_tier, "perf": round(perf,1),
        "hs": hs > 0, "lat": round(lat,1),
    }

# ── UI Components ──────────────────────────────────────────────────────────

class GlowButton(Button):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.background_normal = ""
        self.background_color = (0,0,0,0)
        self.color = C("#030508")
        self.font_size = sp(15)
        self.bold = True
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *a):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*C("#00ff88"))
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(6)])

    def on_press(self):
        Animation(opacity=0.7, duration=0.08).start(self)

    def on_release(self):
        Animation(opacity=1.0, duration=0.1).start(self)


class ScanButton(Button):
    scanning = BooleanProperty(False)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.background_normal = ""
        self.background_color = (0,0,0,0)
        self.font_size = sp(16)
        self.bold = True
        self.color = BG
        self._anim = None
        self.bind(pos=self._redraw, size=self._redraw, scanning=self._redraw)

    def _redraw(self, *a):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.scanning:
                Color(*MUTED)
            else:
                Color(*ACCENT)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8)])


class InfoCard(BoxLayout):
    def __init__(self, label, value, unit="", **kw):
        super().__init__(orientation="vertical", **kw)
        self.padding = [dp(12), dp(10)]
        self.spacing = dp(2)
        self.size_hint_y = None
        self.height = dp(72)

        with self.canvas.before:
            Color(*BG3)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(6)])
            Color(*ACCENT, 0.5)
            self._line = Line(rounded_rectangle=[*self.pos, *self.size, dp(6)], width=1)
        self.bind(pos=self._upd, size=self._upd)

        self.lbl = Label(text=label.upper(), font_size=sp(9), color=MUTED,
                         halign="left", valign="middle", size_hint_y=None, height=dp(16))
        self.lbl.bind(size=lambda i,v: setattr(i,"text_size",v))

        row = BoxLayout(orientation="horizontal")
        self.val = Label(text=str(value), font_size=sp(22), color=ACCENT,
                         bold=True, halign="left", valign="middle")
        self.val.bind(size=lambda i,v: setattr(i,"text_size",v))
        self.unt = Label(text=unit, font_size=sp(11), color=MUTED,
                         halign="left", valign="bottom", size_hint_x=None, width=dp(36))
        row.add_widget(self.val)
        row.add_widget(self.unt)
        self.add_widget(self.lbl)
        self.add_widget(row)

    def _upd(self, *a):
        self._rect.pos = self.pos
        self._rect.size = self.size
        self._line.rounded_rectangle = [*self.pos, *self.size, dp(6)]

    def set_value(self, v):
        self.val.text = str(v)


class SensiBar(BoxLayout):
    def __init__(self, label, value, max_val=200, highlight=False, **kw):
        super().__init__(orientation="vertical", **kw)
        self.padding = [dp(14), dp(12)]
        self.spacing = dp(6)
        self.size_hint_y = None
        self.height = dp(80) if highlight else dp(70)

        border_color = ACCENT if highlight else CYAN

        with self.canvas.before:
            Color(*BG3)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(6)])
            Color(*border_color, 0.4)
            self._line = Line(rounded_rectangle=[*self.pos, *self.size, dp(6)], width=1.2 if highlight else 1)
        self.bind(pos=self._upd, size=self._upd)

        top = BoxLayout(orientation="horizontal")
        lbl = Label(text=label, font_size=sp(10), color=MUTED if not highlight else TEXT,
                    bold=highlight, halign="left", valign="middle")
        lbl.bind(size=lambda i,v: setattr(i,"text_size",v))
        val_size = sp(28) if highlight else sp(22)
        val_color = ACCENT if highlight else WHITE
        self._val_lbl = Label(text=str(value), font_size=val_size,
                              color=val_color, bold=True, halign="right", valign="middle")
        self._val_lbl.bind(size=lambda i,v: setattr(i,"text_size",v))
        top.add_widget(lbl)
        top.add_widget(self._val_lbl)
        self.add_widget(top)

        # Progress bar
        bar_bg = Widget(size_hint_y=None, height=dp(4))
        with bar_bg.canvas:
            Color(*DIM)
            self._bar_bg = RoundedRectangle(pos=bar_bg.pos, size=bar_bg.size, radius=[dp(2)])
        bar_bg.bind(pos=lambda i,v: setattr(self._bar_bg,"pos",v),
                    size=lambda i,v: setattr(self._bar_bg,"size",v))

        self._bar_fill_w = value / max_val
        self._bar_widget = Widget(size_hint_y=None, height=dp(4))
        with self._bar_widget.canvas:
            Color(*border_color)
            self._bar_fill = RoundedRectangle(
                pos=self._bar_widget.pos,
                size=(self._bar_widget.width * self._bar_fill_w, self._bar_widget.height),
                radius=[dp(2)]
            )
        self._bar_widget.bind(
            pos=lambda i,v: setattr(self._bar_fill,"pos",v),
            size=lambda i,v: setattr(self._bar_fill,"size",
                (v[0]*self._bar_fill_w, v[1]))
        )
        self.add_widget(bar_bg)
        self.add_widget(self._bar_widget)

    def _upd(self, *a):
        self._rect.pos = self.pos
        self._rect.size = self.size
        self._line.rounded_rectangle = [*self.pos, *self.size, dp(6)]


class ScanScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._device_info = {}
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical")

        # Header
        header = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(110),
                           padding=[dp(20), dp(16)])
        with header.canvas.before:
            Color(*BG2)
            self._hdr_rect = Rectangle(pos=header.pos, size=header.size)
            Color(*ACCENT, 0.6)
            self._hdr_line = Line(points=[0,0,0,0], width=1.5)
        header.bind(pos=self._upd_hdr, size=self._upd_hdr)

        title = Label(
            text="PRIME SHANI", font_size=sp(26), bold=True, color=ACCENT,
            halign="left", size_hint_y=None, height=dp(36)
        )
        title.bind(size=lambda i,v: setattr(i,"text_size",v))

        sub = Label(
            text="SENSI GENERATOR  //  FREE FIRE", font_size=sp(11), color=MUTED,
            halign="left", size_hint_y=None, height=dp(20)
        )
        sub.bind(size=lambda i,v: setattr(i,"text_size",v))

        self._status = Label(
            text="// READY TO SCAN", font_size=sp(10), color=CYAN,
            halign="left", size_hint_y=None, height=dp(18)
        )
        self._status.bind(size=lambda i,v: setattr(i,"text_size",v))

        header.add_widget(title)
        header.add_widget(sub)
        header.add_widget(self._status)

        # Scroll content
        scroll = ScrollView()
        content = BoxLayout(orientation="vertical", padding=[dp(16), dp(16)],
                            spacing=dp(12), size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))

        # Info cards grid
        grid_lbl = Label(text="// DEVICE INFO", font_size=sp(10), color=MUTED,
                         halign="left", size_hint_y=None, height=dp(20))
        grid_lbl.bind(size=lambda i,v: setattr(i,"text_size",v))
        content.add_widget(grid_lbl)

        # Device name (full width)
        self._card_device = InfoCard("Device", "Scanning...", "")
        self._card_device.size_hint_x = 1
        content.add_widget(self._card_device)

        self._card_chip = InfoCard("Chipset", "—", "")
        content.add_widget(self._card_chip)

        row1 = BoxLayout(orientation="horizontal", spacing=dp(10),
                         size_hint_y=None, height=dp(72))
        self._card_ram   = InfoCard("RAM",     "—", "GB",  size_hint_x=1)
        self._card_hz    = InfoCard("Refresh", "—", "Hz",  size_hint_x=1)
        self._card_batt  = InfoCard("Battery", "—", "%",   size_hint_x=1)
        row1.add_widget(self._card_ram)
        row1.add_widget(self._card_hz)
        row1.add_widget(self._card_batt)
        content.add_widget(row1)

        row2 = BoxLayout(orientation="horizontal", spacing=dp(10),
                         size_hint_y=None, height=dp(72))
        self._card_res   = InfoCard("Resolution","—","",    size_hint_x=1)
        self._card_touch = InfoCard("Touch",    "—", "Hz",  size_hint_x=1)
        self._card_load  = InfoCard("Load",     "—", "",    size_hint_x=1)
        row2.add_widget(self._card_res)
        row2.add_widget(self._card_touch)
        row2.add_widget(self._card_load)
        content.add_widget(row2)

        # Scan button
        content.add_widget(Widget(size_hint_y=None, height=dp(8)))
        self._btn = ScanButton(text="⚡  SCAN & GENERATE",
                               size_hint_y=None, height=dp(56))
        self._btn.bind(on_release=self._on_scan)
        content.add_widget(self._btn)
        content.add_widget(Widget(size_hint_y=None, height=dp(20)))

        scroll.add_widget(content)
        root.add_widget(header)
        root.add_widget(scroll)
        self.add_widget(root)

        # Auto-detect on load
        Clock.schedule_once(lambda dt: self._quick_detect(), 0.3)

    def _upd_hdr(self, w, *a):
        self._hdr_rect.pos = w.pos
        self._hdr_rect.size = w.size
        x, y = w.pos
        self._hdr_line.points = [x, y, x+w.width, y]

    def _quick_detect(self):
        self._status.text = "// DETECTING DEVICE..."
        threading.Thread(target=self._detect_thread, daemon=True).start()

    def _detect_thread(self):
        info = detect_device()
        Clock.schedule_once(lambda dt: self._fill_info(info))

    def _fill_info(self, info):
        self._device_info = info
        self._card_device.set_value(info.get("device","Unknown")[:24])
        self._card_chip.set_value(info.get("chipset","Unknown")[:28])
        self._card_ram.set_value(f"{info.get('ram',0)}")
        self._card_hz.set_value(f"{info.get('hz',60)}")
        self._card_batt.set_value(f"{info.get('battery',100)}")
        w, h = info.get("w",0), info.get("h",0)
        self._card_res.set_value(f"{w}x{h}" if w else "?")
        self._card_touch.set_value(f"{info.get('touch',120)}")
        self._card_load.set_value(f"{info.get('load',0):.1f}")
        self._status.text = "// DEVICE DETECTED — READY"

    def _on_scan(self, *a):
        if self._btn.scanning:
            return
        self._btn.scanning = True
        self._btn.text = "  BENCHMARKING..."
        self._status.text = "// RUNNING CPU & RAM BENCHMARK..."
        threading.Thread(target=self._scan_thread, daemon=True).start()

    def _scan_thread(self):
        cpu_ops, mem_mb = benchmark()
        self._device_info["cpu_ops"] = cpu_ops
        self._device_info["mem_mb"] = mem_mb
        result = calc_sensi(self._device_info)
        Clock.schedule_once(lambda dt: self._show_result(result))

    def _show_result(self, result):
        self._btn.scanning = False
        self._btn.text = "⚡  SCAN & GENERATE"
        self._status.text = "// COMPLETE — SENSITIVITY GENERATED"
        app = App.get_running_app()
        app.last_result = result
        app.last_info = self._device_info
        self.manager.current = "result"


class ResultScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._built = False

    def on_enter(self):
        self.clear_widgets()
        self._build_ui()

    def _build_ui(self):
        app = App.get_running_app()
        result = getattr(app, "last_result", {})
        info = getattr(app, "last_info", {})
        sx = result.get("sx", {})
        tier = result.get("tier","mid")
        perf = result.get("perf",50)
        hs = result.get("hs",False)
        lat = result.get("lat",16)

        tier_colors = {
            "flagship": ACCENT, "upper_mid": CYAN,
            "mid": C("#ffcc00"), "budget": MUTED
        }
        tier_labels = {
            "flagship":"FLAGSHIP","upper_mid":"UPPER MID",
            "mid":"MID RANGE","budget":"BUDGET"
        }
        tc = tier_colors.get(tier, CYAN)

        root = BoxLayout(orientation="vertical")

        # Header
        header = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(90),
                           padding=[dp(20), dp(12)])
        with header.canvas.before:
            Color(*BG2)
            Rectangle(pos=header.pos, size=header.size)
            Color(*tc, 0.5)
            Line(points=[0,0,0,0], width=1.5)

        def upd_hdr(w, *a):
            header.canvas.before.children[1].pos = w.pos
            header.canvas.before.children[1].size = w.size
            x,y = w.pos
            header.canvas.before.children[3].points = [x,y,x+w.width,y]
        header.bind(pos=upd_hdr, size=upd_hdr)

        title = Label(text="PRIME SHANI", font_size=sp(22), bold=True,
                      color=ACCENT, halign="left", size_hint_y=None, height=dp(30))
        title.bind(size=lambda i,v: setattr(i,"text_size",v))

        device_name = info.get("device","Unknown")
        sub = Label(text=f"{device_name[:30]}  //  {tier_labels.get(tier,tier).upper()}",
                    font_size=sp(10), color=tc, halign="left",
                    size_hint_y=None, height=dp(18))
        sub.bind(size=lambda i,v: setattr(i,"text_size",v))

        hs_txt = "  HS MODE: ON ●" if hs else "  HS MODE: OFF ○"
        hs_lbl = Label(text=f"POWER {perf:.0f}/100  |  LAT {lat}ms  |{hs_txt}",
                       font_size=sp(9), color=ACCENT if hs else MUTED,
                       halign="left", size_hint_y=None, height=dp(16))
        hs_lbl.bind(size=lambda i,v: setattr(i,"text_size",v))

        header.add_widget(title)
        header.add_widget(sub)
        header.add_widget(hs_lbl)

        # Scroll
        scroll = ScrollView()
        content = BoxLayout(orientation="vertical", padding=[dp(16),dp(14)],
                            spacing=dp(10), size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))

        sec = Label(text="// SENSITIVITY VALUES", font_size=sp(10), color=MUTED,
                    halign="left", size_hint_y=None, height=dp(20))
        sec.bind(size=lambda i,v: setattr(i,"text_size",v))
        content.add_widget(sec)

        ORDER = ["General","Red Dot","2x Scope","4x Scope","Sniper","Free Look"]
        for k in ORDER:
            v = sx.get(k, 0)
            bar = SensiBar(k, v, highlight=(k=="General"))
            content.add_widget(bar)

        # Report text
        content.add_widget(Widget(size_hint_y=None, height=dp(4)))
        sec2 = Label(text="// FULL REPORT", font_size=sp(10), color=MUTED,
                     halign="left", size_hint_y=None, height=dp(20))
        sec2.bind(size=lambda i,v: setattr(i,"text_size",v))
        content.add_widget(sec2)

        report = self._make_report(info, result)
        report_box = BoxLayout(size_hint_y=None, padding=[dp(12),dp(10)])
        with report_box.canvas.before:
            Color(0,0,0,1)
            RoundedRectangle(pos=report_box.pos, size=report_box.size, radius=[dp(6)])
            Color(*ACCENT, 0.15)
            Line(rounded_rectangle=[*report_box.pos,*report_box.size,dp(6)], width=1)
        report_box.bind(
            pos=lambda i,v: [setattr(i.canvas.before.children[1],"pos",v),
                              setattr(i.canvas.before.children[3],"rounded_rectangle",[*v,*i.size,dp(6)])],
            size=lambda i,v: [setattr(i.canvas.before.children[1],"size",v),
                               setattr(i.canvas.before.children[3],"rounded_rectangle",[*i.pos,*v,dp(6)])]
        )
        rl = Label(text=report, font_size=sp(10), color=C("#7ecfb0"),
                   halign="left", valign="top",
                   size_hint_y=None)
        rl.bind(texture_size=lambda i,v: setattr(i,"height",v[1]+dp(10)))
        rl.bind(width=lambda i,v: setattr(i,"text_size",(v,None)))
        report_box.bind(minimum_height=report_box.setter("height"))
        report_box.add_widget(rl)
        content.add_widget(report_box)

        # Buttons
        content.add_widget(Widget(size_hint_y=None, height=dp(10)))
        self._copy_btn = GlowButton(text="📋  COPY REPORT",
                                    size_hint_y=None, height=dp(50))
        self._copy_btn._report = report
        self._copy_btn.bind(on_release=self._copy)
        content.add_widget(self._copy_btn)

        back_btn = Button(
            text="← RESCAN", size_hint_y=None, height=dp(44),
            background_normal="", background_color=(0,0,0,0),
            color=MUTED, font_size=sp(13)
        )
        back_btn.bind(on_release=lambda *a: setattr(self.manager,"current","scan"))
        content.add_widget(back_btn)
        content.add_widget(Widget(size_hint_y=None, height=dp(24)))

        scroll.add_widget(content)
        root.add_widget(header)
        root.add_widget(scroll)
        self.add_widget(root)

    def _make_report(self, info, result):
        sx = result.get("sx",{})
        ORDER = ["General","Red Dot","2x Scope","4x Scope","Sniper","Free Look"]
        sep = "=" * 40
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

    def _copy(self, btn, *a):
        Clipboard.copy(btn._report)
        btn.text = "✅  COPIED!"
        Clock.schedule_once(lambda dt: setattr(btn,"text","📋  COPY REPORT"), 2)


class PrimeShaniApp(App):
    last_result = {}
    last_info = {}

    def build(self):
        self.title = "Prime Shani — Sensi Generator"
        sm = ScreenManager(transition=FadeTransition(duration=0.2))
        sm.add_widget(ScanScreen(name="scan"))
        sm.add_widget(ResultScreen(name="result"))
        return sm


if __name__ == "__main__":
    PrimeShaniApp().run()
