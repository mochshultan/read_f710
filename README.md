# Logitech F710 Gamepad Monitor (hud_f710.py)

Real-time HUD display untuk Logitech F710 gamepad. Menampilkan status analog sticks, triggers, buttons, dan D-pad dengan visual yang jelas menggunakan `rich` library.

## Fitur

- **Live HUD** dengan rendering analog sticks (ASCII art), trigger buttons, dan semua kontrol F710
- **Mode DirectInput & XInput** — auto-detect atau paksa manual
- **Kalibrrai interaktif** — pemetaan tombol & axis otomatis
- **Button triggers** — LT & RT sebagai button digital (bukan analog axis)
- **Fallback console** — HUD plain-text jika `rich` tidak tersedia
- **Mapping persistence** — simpan/load konfigurasi ke JSON

## Instalasi

### Dependensi

```bash
pip install pygame rich
```

### Daftar File

```
hud_f710.py         — Script utama HUD monitor
debug_triggers.py   — Debug raw axis/button/hat values
f710_mapping.json   — Mapping terkalibrasi (auto-generated)
joy2twist_node.py   — ROS 2 Joy → Twist converter (optional)
joy2twist.yaml      — Contoh konfigurasi ROS 2
README.md           — Dokumentasi ini
```

## Penggunaan

### Mode HUD Normal (Rekomendasi)

```bash
python hud_f710.py
```

Menampilkan live HUD dengan:
- Analog sticks (left & right) dengan visualisasi ASCII dot
- Triggers (LT, LB, RB, RT) sebagai button
- 8 action buttons (A, B, X, Y, BACK, START, L3, R3)
- D-Pad dengan arrow indicator

**Kontrol**: Tekan `Ctrl+C` untuk keluar.

### Mode Kalibrasi

```bash
python hud_f710.py calibrate
```

Wizard interaktif yang memandu Anda menekan setiap tombol dan menggerakkan setiap axis. Hasil pemetaan disimpan ke `f710_mapping.json` dan digunakan otomatis di run berikutnya.

**Langkah-langkah**:
1. Tekan 12 tombol (A, B, X, Y, LB, RB, LT, RT, BACK, START, L3, R3)
2. Gerakkan 4 axis (LX, LY, RX, RY) bolak-balik 3 detik masing-masing
3. Tekan D-Pad
4. Mapping tersimpan

### Mode Show Indices

```bash
python hud_f710.py indices
```

Atau:

```bash
python hud_f710.py show-indices
```

Print semua axis & button index mentah dari device. Berguna untuk debugging jika kalibrasi gagal.

**Output contoh**:
```
Device : Logitech Gamepad F710
Axes   : 4
Buttons: 12
Hats   : 1

Raw axis values (gerakkan stick/trigger untuk identifikasi):
  axis[0] = -0.234
  axis[1] = +0.567
  ...
```

### Force Preset

```bash
python hud_f710.py direct
```

Paksa mode DirectInput (aman untuk Linux/ROS2).

```bash
python hud_f710.py xinput
```

Paksa mode XInput.

## DirectInput vs XInput

### DirectInput (Rekomendasi untuk Linux)

- **Switch F710**: Posisi `D`
- **Axes**: 4 (hanya sticks; LT & RT adalah button)
- **Buttons**: 12 (termasuk LT, RT, L3, R3)
- **D-Pad**: Terpisah (hat)
- **Keuntungan**: Trigger terpisah, stabil di Linux

### XInput

- **Switch F710**: Posisi `X`
- **Axes**: 4 (hanya sticks; LT & RT adalah button)
- **Buttons**: 12 (termasuk LT, RT, L3, R3)
- **D-Pad**: Terpisah (hat) atau embedded dalam axes (platform-dependent)
- **Note**: Di beberapa kernel Linux, LT & RT menggunakan shared axis — sudah ditangani di kode ini

## Struktur Tombol & Axis

### Tombol (Button)

```
┌─────────────────────────┐
│  Y    X     RB  RT      │
│  B    A     LB  LT      │
│  BACK START              │
│  L3 (L-stick)  R3 (R-stick) │
└─────────────────────────┘
```

Setiap tombol ditampilkan:
- `●` = pressed (hijau)
- `○` = released (dim)

### Analog Sticks

**Left Stick (LX, LY)**:
```
  L(+0.23,+0.45)
      · · ·
      · ● ·
      · · ·
```

**Right Stick (RX, RY)**:
- Sama dengan left, tapi di sebelah kanan

### Triggers

Ditampilkan sebagai button:
- **LT** (Left Trigger) — press/release
- **LB** (Left Bumper) — press/release
- **RB** (Right Bumper) — press/release
- **RT** (Right Trigger) — press/release

### D-Pad

Menampilkan arrow directional:
- ↑ ↓ ← → (4 arah)
- ↗ ↖ ↘ ↙ (4 diagonal)
- · (center/idle)

## Troubleshooting

### Gamepad tidak terdeteksi

1. Periksa koneksi USB F710
2. Cek apakah driver terinstall:
   - **Linux**: `jstest /dev/input/js0` (pastikan ada output)
   - **Windows**: Device Manager → Human Interface Devices

### Tombol/Axis terdeteksi salah

1. Jalankan kalibrasi ulang:
   ```bash
   python hud_f710.py calibrate
   ```

2. Atau hapus `f710_mapping.json` dan jalankan ulang (auto-detect):
   ```bash
   rm f710_mapping.json
   python hud_f710.py
   ```

3. Lihat index mentah untuk debugging:
   ```bash
   python hud_f710.py indices
   ```

### `rich` library error

Jika `rich` tidak terinstall, script akan fallback ke HUD plain-text. Install jika ingin visual yang lebih baik:

```bash
pip install rich
```

### Exit Code 1 / Script gagal

- Pastikan `pygame` terinstall: `pip install pygame`
- Pastikan gamepad terhubung sebelum menjalankan script
- Coba run mode `indices` untuk diagnostik

## Referensi

- **Logitech F710 Manual**: https://support.logi.com/hc/en-us/articles/360024634294
- **ROS Joy (F710)**: http://wiki.ros.org/joy
- **Pygame Joystick**: https://www.pygame.org/docs/ref/joystick.html

## License

MIT

---

**Last Updated**: 2026-06-09  
**Author**: Husarion Magang UNAIR  
**Device**: Logitech Wireless Gamepad F710
