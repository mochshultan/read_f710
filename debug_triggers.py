"""
debug_triggers.py — Baca semua axis & button F710 secara raw
Jalankan: python debug_triggers.py
Tekan Ctrl+C untuk keluar.
"""

import pygame
import os
import time

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("Tidak ada joystick terdeteksi!")
    exit()

js = pygame.joystick.Joystick(0)
js.init()

print(f"Device  : {js.get_name()}")
print(f"Axes    : {js.get_numaxes()}")
print(f"Buttons : {js.get_numbuttons()}")
print(f"Hats    : {js.get_numhats()}")
print("=" * 50)
print("Gerakkan LT / RT untuk lihat axis mana yang berubah")
print("Ctrl+C untuk keluar\n")

try:
    while True:
        pygame.event.pump()
        os.system("cls" if os.name == "nt" else "clear")

        print(f"=== {js.get_name()} ===\n")

        print("AXES (semua):")
        for i in range(js.get_numaxes()):
            v = js.get_axis(i)
            bar_len = 20
            filled = int((v + 1) / 2 * bar_len)
            filled = max(0, min(bar_len, filled))
            bar = "█" * filled + "░" * (bar_len - filled)
            arrow = " ← BERGERAK" if abs(v) > 0.05 else ""
            print(f"  axis[{i}] = {v:+.4f}  [{bar}]{arrow}")

        print()
        print("BUTTONS (semua):")
        line = ""
        for i in range(js.get_numbuttons()):
            b = js.get_button(i)
            line += f"  btn[{i}]={'●' if b else '○'}"
            if (i + 1) % 6 == 0:
                print(line); line = ""
        if line:
            print(line)

        print()
        if js.get_numhats() > 0:
            print("HATS:")
            for i in range(js.get_numhats()):
                print(f"  hat[{i}] = {js.get_hat(i)}")

        time.sleep(0.05)

except KeyboardInterrupt:
    pass

js.quit()
pygame.joystick.quit()
pygame.quit()
print("\nSelesai.")
