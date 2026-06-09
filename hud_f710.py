"""
xox.py — Logitech F710 Gamepad Monitor
=======================================
Mendukung KEDUA mode controller:
  • DirectInput (switch = 'D') — DISARANKAN untuk Linux/ROS2
    LT & RT = button digital (bukan axis)
  • XInput     (switch = 'X') — LT & RT juga button digital

Run modes:
  python xox.py               — Live HUD otomatis deteksi mode
  python xox.py calibrate     — Wizard kalibrasi interaktif
  python xox.py indices       — Print semua axis/button index lalu keluar
  python xox.py direct        — Paksa DirectInput preset
  python xox.py xinput        — Paksa XInput preset
"""

import time
import os
import sys
import json
import math
import pygame

try:
    from rich.live import Live
    from rich.table import Table
    from rich.panel import Panel
    from rich.console import Group
    from rich.text import Text
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# ─────────────────────────────────────────────────────────────────────────────
# F710 MAPPING PRESETS
#
# MASALAH TRIGGER DI LINUX:
#   XInput mode (switch=X) → kernel xpad driver menggabungkan LT+RT ke
#   SATU axis Z (index 2). LT = +1, RT = -1 pada axis yang sama.
#   Akibatnya: tidak bisa tekan LT+RT bersamaan, dan nilai bertabrakan.
#
#   DirectInput mode (switch=D) → LT = axis 4, RT = axis 5 (TERPISAH).
#   Ini cara yang benar untuk Linux & ROS2.
#
# Referensi:
#   http://wiki.ros.org/joy#Logitech_Wireless_Gamepad_F710_.28DirectInput_Mode.29
#   http://wiki.ros.org/joy#Logitech_Wireless_Gamepad_F710_.28XInput_Mode.29
# ─────────────────────────────────────────────────────────────────────────────

F710_DIRECT = {
    # Switch controller ke 'D' (DirectInput) — DIREKOMENDASIKAN di Linux
    # jstest melaporkan: 6 axes, 12 buttons, 1 hat
    "preset": "direct",
    "trigger_mode": "button",        # LT dan RT sebagai button digital
    "axes": {
        "LX":  0,   # Left stick horizontal   (-1=kiri, +1=kanan)
        "LY":  1,   # Left stick vertical      (-1=atas,  +1=bawah)
        "RX":  2,   # Right stick horizontal   (-1=kiri, +1=kanan)
        "RY":  3,   # Right stick vertical     (-1=atas,  +1=bawah)
    },
    "buttons": {
        # Di DirectInput, urutan berbeda dari XInput
        "X":     0,
        "A":     1,
        "B":     2,
        "Y":     3,
        "LB":    4,
        "RB":    5,
        "LT":    6,   # Left trigger sebagai button
        "RT":    7,   # Right trigger sebagai button
        "BACK":  8,
        "START": 9,
        "L3":    10,
        "R3":    11,
    },
    "hats": 0,
}

F710_XINPUT = {
    # Switch controller ke 'X' (XInput) — XInput juga support LT/RT sebagai button
    # jstest melaporkan: 8 axes (termasuk Hat0X/Hat0Y), 11 buttons
    "preset": "xinput",
    "trigger_mode": "button",          # LT+RT sebagai button digital
    "axes": {
        "LX":      0,   # Left stick horizontal
        "LY":      1,   # Left stick vertical
        "RX":      3,   # Right stick horizontal
        "RY":      4,   # Right stick vertical
    },
    "buttons": {
        "A":     0,
        "B":     1,
        "X":     2,
        "Y":     3,
        "LB":    4,
        "RB":    5,
        "BACK":  6,
        "START": 7,
        "L3":    8,
        "R3":    9,
        "LT":    10,
        "RT":    11,
    },
    "hats": 0,
}

SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
MAPPING_FILE  = os.path.join(SCRIPT_DIR, "config/f710_mapping.json")
DEAD_ZONE     = 0.08
POLL_INTERVAL = 0.01


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def dz(v, threshold=DEAD_ZONE):
    """Apply dead zone: kembalikan 0 jika nilai terlalu kecil."""
    return 0.0 if abs(v) < threshold else round(v, 3)

def raw_axis(js, idx):
    """Baca axis dengan aman, kembalikan 0 jika index di luar range."""
    if idx is None or idx < 0 or idx >= js.get_numaxes():
        return 0.0
    return js.get_axis(idx)

def raw_btn(js, idx):
    """Baca button dengan aman."""
    if idx is None or idx < 0 or idx >= js.get_numbuttons():
        return False
    return bool(js.get_button(idx))

def trigger_norm(raw):
    """Konversi raw axis trigger (-1..+1) ke 0..1 untuk display."""
    return (raw + 1.0) / 2.0

def load_mapping():
    if os.path.exists(MAPPING_FILE):
        try:
            with open(MAPPING_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None

def save_mapping(m):
    try:
        with open(MAPPING_FILE, "w", encoding="utf-8") as f:
            json.dump(m, f, indent=2)
        print(f"Mapping tersimpan → {MAPPING_FILE}")
    except Exception as e:
        print(f"Gagal simpan mapping: {e}")

def auto_detect_preset(js):
    """
    Deteksi otomatis apakah controller dalam mode Direct atau XInput
    berdasarkan jumlah hat dan axis yang dilaporkan pygame/SDL.
    DirectInput: 4 axes (sticks saja), 12 buttons, 1 hat ← lebih jelas
    XInput:      4 axes (sticks saja), 12 buttons, 0 hat
    """
    n_axes   = js.get_numaxes()
    n_btns   = js.get_numbuttons()
    n_hats   = js.get_numhats()

    if n_hats >= 1:
        # DirectInput punya hat/dpad terpisah
        return "direct", F710_DIRECT
    else:
        # XInput tidak punya hat, atau fallback
        return "xinput", F710_XINPUT


# ─────────────────────────────────────────────────────────────────────────────
# Baca state trigger — menangani mode shared vs separate
# ─────────────────────────────────────────────────────────────────────────────

def read_triggers(js, cfg):
    """
    Baca LT dan RT sebagai button (digital): kembalikan (lt_pressed, rt_pressed) boolean.
    """
    buttons = cfg.get("buttons", {})
    lt_pressed = raw_btn(js, buttons.get("LT"))
    rt_pressed = raw_btn(js, buttons.get("RT"))
    return lt_pressed, rt_pressed


# ─────────────────────────────────────────────────────────────────────────────
# ASCII Joystick visual
# ─────────────────────────────────────────────────────────────────────────────

def render_stick(x, y, radius=4):
    size = radius * 2 + 1
    grid = [["·"] * size for _ in range(size)]
    cx = cy = radius

    for angle in range(0, 360, 5):
        rad = math.radians(angle)
        px  = round(cx + radius * math.cos(rad))
        py  = round(cy + radius * math.sin(rad) * 0.55)
        if 0 <= py < size and 0 <= px < size:
            grid[py][px] = "○"

    dot_x = round(cx + x * (radius - 1))
    dot_y = round(cy + y * (radius - 1) * 0.55)
    dot_x = max(0, min(size - 1, dot_x))
    dot_y = max(0, min(size - 1, dot_y))
    grid[dot_y][dot_x] = "●"

    return ["".join(row) for row in grid]


def render_trigger_bar(norm, width=14):
    """norm: 0.0..1.0"""
    filled = round(norm * width)
    bar    = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {norm * 100:5.1f}%"


def render_dpad(hat):
    arrows = {
        (0,  1): "↑", (0, -1): "↓",
        (-1, 0): "←", (1,  0): "→",
        (1,  1): "↗", (-1, 1): "↖",
        (1, -1): "↘", (-1,-1): "↙",
        (0,  0): "·",
    }
    return arrows.get(tuple(hat), "?")


# ─────────────────────────────────────────────────────────────────────────────
# Rich HUD
# ─────────────────────────────────────────────────────────────────────────────

def make_hud(js_name, cfg, js):
    axes    = cfg["axes"]
    buttons = cfg["buttons"]
    preset  = cfg.get("preset", "?").upper()
    tmode   = cfg.get("trigger_mode", "button")

    lx = dz(raw_axis(js, axes.get("LX", 0)))
    ly = dz(raw_axis(js, axes.get("LY", 1)))
    rx = dz(raw_axis(js, axes.get("RX", 2)))
    ry = dz(raw_axis(js, axes.get("RY", 3)))
    lt_pressed, rt_pressed = read_triggers(js, cfg)
    hat = js.get_hat(0) if js.get_numhats() > 0 else (0, 0)

    # ── Sticks ──
    left_lines  = render_stick(lx, ly)
    right_lines = render_stick(rx, ry)
    mid = len(left_lines) // 2

    sticks_t = Table.grid(padding=(0, 2))
    sticks_t.add_column(justify="right", min_width=18)
    sticks_t.add_column()
    sticks_t.add_column(justify="left",  min_width=18)
    for i, (ll, rl) in enumerate(zip(left_lines, right_lines)):
        if i == mid:
            sticks_t.add_row(
                f"[cyan]L[/cyan] ({lx:+.2f},{ly:+.2f})",
                f"[dim]{ll}[/dim]   [dim]{rl}[/dim]",
                f"[cyan]R[/cyan] ({rx:+.2f},{ry:+.2f})",
            )
        else:
            sticks_t.add_row("", f"[dim]{ll}[/dim]   [dim]{rl}[/dim]", "")

    # ── Triggers (button) ──
    lt_sym = "● PRESSED" if lt_pressed else "○ released"
    rt_sym = "● PRESSED" if rt_pressed else "○ released"
    lt_style = "green bold" if lt_pressed else "dim"
    rt_style = "green bold" if rt_pressed else "dim"

    lb_sym = "● PRESSED" if raw_btn(js, buttons.get("LB")) else "○ released"
    rb_sym = "● PRESSED" if raw_btn(js, buttons.get("RB")) else "○ released"
    lb_style = "green bold" if raw_btn(js, buttons.get("LB")) else "dim"
    rb_style = "green bold" if raw_btn(js, buttons.get("RB")) else "dim"

    trig_t = Table.grid(padding=(0, 1))
    trig_t.add_column(justify="right", min_width=2)
    trig_t.add_column()
    trig_t.add_row("[bold cyan]LT[/bold cyan]", f"[{lt_style}]{lt_sym}[/{lt_style}]")
    trig_t.add_row("[bold cyan]LB[/bold cyan]", f"[{lb_style}]{lb_sym}[/{lb_style}]")
    trig_t.add_row("[bold cyan]RB[/bold cyan]", f"[{rb_style}]{rb_sym}[/{rb_style}]")
    trig_t.add_row("[bold cyan]RT[/bold cyan]", f"[{rt_style}]{rt_sym}[/{rt_style}]")

    # ── Buttons ──
    def b(name):
        pressed = raw_btn(js, buttons.get(name))
        c   = "green bold" if pressed else "dim"
        sym = "●" if pressed else "○"
        return f"[{c}]{sym} {name}[/{c}]"

    btn_t = Table.grid(padding=(0, 2))
    btn_t.add_column(); btn_t.add_column(); btn_t.add_column(); btn_t.add_column()
    btn_t.add_row(b("A"), b("B"), b("X"), b("Y"))
    btn_t.add_row(b("BACK"), b("START"), b("L3"), b("R3"))

    # ── D-Pad ──
    arrow = render_dpad(hat)
    dpad_t = Table.grid(padding=(0, 1))
    dpad_t.add_column(justify="center", min_width=10)
    dpad_t.add_row(f"[bold yellow]{arrow}[/bold yellow]  [dim]{hat}[/dim]")

    # ── Mode badge ──
    badge_color = "green" if preset == "DIRECT" else "yellow"
    header = Text.assemble(
        ("⦿ ", "bold green"),
        (js_name, "bold white"),
        ("  │  mode: ", "dim"),
        (preset, f"bold {badge_color}"),
        ("  │  trigger: ", "dim"),
        ("button ✓" if tmode == "button" else "axis", "green"),
        ("  [Ctrl+C keluar]", "dim"),
    )

    inner = Group(
        Panel(sticks_t, title="[cyan]Analog Sticks[/cyan]",   box=box.SIMPLE, padding=(0, 1)),
        Panel(trig_t,   title="[cyan]Triggers[/cyan]",        box=box.SIMPLE, padding=(0, 1)),
        Panel(btn_t,    title="[cyan]Buttons[/cyan]",         box=box.SIMPLE, padding=(0, 1)),
        Panel(dpad_t,   title="[cyan]D-Pad[/cyan]",           box=box.SIMPLE, padding=(0, 1)),
    )
    return Panel(Group(header, inner),
                 title="[bold]Logitech F710 HUD[/bold]",
                 subtitle="husarion.com/tutorials/ros-equipment/gamepad-f710",
                 box=box.ROUNDED, border_style="bright_blue")


# ─────────────────────────────────────────────────────────────────────────────
# Plain-text HUD (fallback tanpa rich)
# ─────────────────────────────────────────────────────────────────────────────

def print_plain_hud(js_name, cfg, js):
    axes    = cfg["axes"]
    buttons = cfg["buttons"]
    preset  = cfg.get("preset", "?").upper()
    tmode   = cfg.get("trigger_mode", "button")

    lx = dz(raw_axis(js, axes.get("LX", 0)))
    ly = dz(raw_axis(js, axes.get("LY", 1)))
    rx = dz(raw_axis(js, axes.get("RX", 2)))
    ry = dz(raw_axis(js, axes.get("RY", 3)))
    lt_pressed, rt_pressed = read_triggers(js, cfg)
    hat = js.get_hat(0) if js.get_numhats() > 0 else (0, 0)

    os.system("cls" if os.name == "nt" else "clear")
    print(f"═══ F710 HUD ═══  [{preset}] trigger: button")
    print(f"Device: {js_name}")
    print()

    left_lines  = render_stick(lx, ly)
    right_lines = render_stick(rx, ry)
    mid = len(left_lines) // 2
    for i, (ll, rl) in enumerate(zip(left_lines, right_lines)):
        if i == mid:
            print(f"  L({lx:+.2f},{ly:+.2f})  {ll}   {rl}  R({rx:+.2f},{ry:+.2f})")
        else:
            print(f"                  {ll}   {rl}")
    print()
    print()
    lt_sym = "●" if lt_pressed else "○"
    rt_sym = "●" if rt_pressed else "○"
    lb_sym = "●" if raw_btn(js, buttons.get("LB")) else "○"
    rb_sym = "●" if raw_btn(js, buttons.get("RB")) else "○"
    print(f"  {lt_sym} LT          {rb_sym} RB")
    print(f"  {lb_sym} LB          {rt_sym} RT")
    print()
    for name in ["A","B","X","Y","BACK","START","L3","R3"]:
        sym = "●" if raw_btn(js, buttons.get(name)) else "○"
        print(f"  {sym} {name}", end="  ")
    print()
    print()
    print(f"  D-Pad: {render_dpad(hat)}  {hat}")


# ─────────────────────────────────────────────────────────────────────────────
# Kalibrasi
# ─────────────────────────────────────────────────────────────────────────────

def calibrate(js):
    print("\n══ F710 Calibration Wizard ══")
    print("LT dan RT akan dikalibrasi sebagai BUTTON (bukan axis).")
    print()
    pygame.event.clear()
    mapping = {"axes":{}, "buttons":{}, "hats":None, "preset":"calibrated", "trigger_mode":"button"}

    for label in ["A","B","X","Y","LB","RB","LT","RT","BACK","START","L3","R3"]:
        print(f"Tekan dan lepas button: [{label}]  ", end="", flush=True)
        detected = None
        while detected is None:
            for ev in pygame.event.get():
                if ev.type == pygame.JOYBUTTONDOWN and ev.joy == 0:
                    detected = ev.button; break
            time.sleep(POLL_INTERVAL)
        mapping["buttons"][label] = detected
        print(f"→ index {detected}")

    print()
    for label in ["LX","LY","RX","RY"]:
        print(f"Gerakkan [{label}] bolak-balik 3 detik…  ", end="", flush=True)
        start = time.time()
        axis_max = {}
        while time.time() - start < 3.0:
            for ev in pygame.event.get():
                if ev.type == pygame.JOYAXISMOTION and ev.joy == 0:
                    axis_max.setdefault(ev.axis, 0.0)
                    axis_max[ev.axis] = max(axis_max[ev.axis], abs(ev.value))
            time.sleep(POLL_INTERVAL)
        if axis_max:
            best = max(axis_max.items(), key=lambda x: x[1])
            mapping["axes"][label] = int(best[0])
            print(f"→ axis {best[0]} (max {best[1]:.3f})")
        else:
            mapping["axes"][label] = None
            print("→ tidak terdeteksi")

    print(f"\n✓ LT dan RT sudah dikalibrasi sebagai button di atas.")

    if js.get_numhats() > 0:
        print("\nTekan D-Pad ke mana saja…  ", end="", flush=True)
        detected_hat = None
        start = time.time()
        while detected_hat is None and time.time() - start < 5.0:
            for ev in pygame.event.get():
                if ev.type == pygame.JOYHATMOTION and ev.joy == 0:
                    detected_hat = ev.hat; break
            time.sleep(POLL_INTERVAL)
        mapping["hats"] = int(detected_hat) if detected_hat is not None else 0
        print(f"→ hat index {mapping['hats']}")

    save_mapping(mapping)
    return mapping


# ─────────────────────────────────────────────────────────────────────────────
# Show raw indices
# ─────────────────────────────────────────────────────────────────────────────

def show_indices(js):
    print(f"\nDevice : {js.get_name()}")
    print(f"Axes   : {js.get_numaxes()}")
    print(f"Buttons: {js.get_numbuttons()}")
    print(f"Hats   : {js.get_numhats()}")
    print()
    print("Raw axis values (gerakkan stick/trigger untuk identifikasi):")
    for i in range(js.get_numaxes()):
        v = js.get_axis(i)
        print(f"  axis[{i}] = {v:+.3f}")
    print()
    print("Raw button values:")
    for i in range(js.get_numbuttons()):
        print(f"  button[{i}] = {js.get_button(i)}")
    if js.get_numhats() > 0:
        for i in range(js.get_numhats()):
            print(f"  hat[{i}] = {js.get_hat(i)}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("Tidak ada gamepad terdeteksi. Colokkan F710 lalu coba lagi.")
        return

    js = pygame.joystick.Joystick(0)
    js.init()
    js_name = js.get_name()

    arg = sys.argv[1].lower() if len(sys.argv) > 1 else ""

    if arg == "calibrate":
        calibrate(js)
        js.quit(); pygame.joystick.quit(); pygame.quit(); return

    if arg in ("indices", "show-indices"):
        show_indices(js)
        js.quit(); pygame.joystick.quit(); pygame.quit(); return

    # Pilih preset
    saved = load_mapping()
    if arg == "direct":
        cfg = F710_DIRECT
        print(f"[{js_name}] Pakai preset: DirectInput (dipaksa via argumen)")
    elif arg == "xinput":
        cfg = F710_XINPUT
        print(f"[{js_name}] Pakai preset: XInput (dipaksa via argumen)")
    elif saved:
        cfg = saved
        print(f"[{js_name}] Pakai mapping tersimpan: {saved.get('preset','?')} "
              f"(trigger_mode: {saved.get('trigger_mode','?')})")
    else:
        preset_name, cfg = auto_detect_preset(js)
        print(f"[{js_name}] Auto-detect: preset={preset_name} (trigger: button)")

    print("Mulai HUD… (Ctrl+C untuk keluar)\n")
    time.sleep(0.4)

    if RICH_AVAILABLE:
        with Live(make_hud(js_name, cfg, js),
                  refresh_per_second=max(4, int(1/POLL_INTERVAL)),
                  screen=False) as live:
            try:
                while True:
                    pygame.event.pump()
                    live.update(make_hud(js_name, cfg, js))
                    time.sleep(POLL_INTERVAL)
            except KeyboardInterrupt:
                pass
    else:
        try:
            while True:
                pygame.event.pump()
                print_plain_hud(js_name, cfg, js)
                time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            pass

    js.quit(); pygame.joystick.quit(); pygame.quit()


if __name__ == "__main__":
    main()