<!-- ========================================================= -->
<!--                        HERO IMAGE                         -->
<!-- ========================================================= -->

<img width="1536" height="1024" alt="SystemPI Tool Banner" src="https://github.com/user-attachments/assets/02229b07-af74-4bc4-9f3d-37cb8799fb77" />

# systempi

Real-time Raspberry Pi system monitoring dashboard for Linux terminals with live telemetry, hardware health analysis, and low-flicker rendering.

---

# FEATURES

- Real-time CPU, RAM, swap, disk, and network monitoring
- Raspberry Pi hardware telemetry through `vcgencmd`
- Power, throttling, undervoltage, and frequency-capping detection
- Dynamic system health, storage health, and stability scoring
- Dynamic "Health Why" explainability diagnostics
- Model-aware thermal thresholds and health scoring for multiple Raspberry Pi generations
- Historical mini-graphs for health and temperature, with expanded CPU, RAM, and network trends in Doctor mode
- Persistent alert event logging with watch/history support
- Lightweight active alert detection for CPU, RAM, disk, temperature, and Pi power/throttle events
- Raspberry Pi hardware intelligence with model/arch/RAM/top-process insight rows
- 13 built-in themes including matrix, wasteland, ocean, lava, mono, amber, crt, vaulttec, synthwave, ice, biohazard, and more
- 4 dashboard variations: Balanced, Compact, Minimal, and Doctor
- Responsive low-flicker partial terminal redraw renderer with dynamic terminal resizing
- Adaptive dashboard scaling based on terminal width
- Live per-core CPU visualization, disk I/O rates, network throughput, load average, and uptime

---

# DASHBOARD MODES

| Mode | Purpose |
|------|----------|
| Balanced | Full monitoring dashboard |
| Compact | Smaller terminal optimized |
| Minimal | Essential-only clean mode |
| Doctor | Diagnostic & alert-focused mode |

Each variation is designed for a different monitoring workflow — from lightweight minimal monitoring to deep diagnostic analysis.
---

# SCREENSHOTS / THEMES

## Balanced Mode — Main Dashboard

```bash
systempi --variation balanced --theme wasteland
```

<img YOUR_BALANCED_WASTELAND_IMAGE />

---

## Doctor Mode — Diagnostic & Alert Intelligence

```bash
systempi --variation doctor --theme vaulttec
```

<img YOUR_DOCTOR_VAULTTEC_IMAGE />

---

## Compact Mode — Smaller Terminal Optimized

```bash
systempi --variation compact --theme crt
```

<img YOUR_COMPACT_CRT_IMAGE />

---

## Minimal Mode — Essential Clean Monitoring

```bash
systempi --variation minimal --theme ice
```

<img YOUR_MINIMAL_ICE_IMAGE />

---

## Matrix Theme

```bash
systempi --theme matrix
```

<img YOUR_MATRIX_IMAGE />

---

## Biohazard Theme

```bash
systempi --variation doctor --theme biohazard
```

<img YOUR_BIOHAZARD_IMAGE />

---

## Ocean Theme

```bash
systempi --theme ocean
```

<img YOUR_OCEAN_IMAGE />

---

## Synthwave Theme

```bash
systempi --theme synthwave
```

<img YOUR_SYNTHWAVE_IMAGE />

---

# INSTALLATION

```bash
git clone https://github.com/WastelandSYS/systempi.git
cd systempi
chmod +x install.sh uninstall.sh
sudo ./install.sh
```

Launch with:

```bash
systempi
```

---

# UNINSTALLATION

```bash
cd systempi
chmod +x uninstall.sh
sudo ./uninstall.sh
```

Optional dependency cleanup:

```bash
sudo ./uninstall.sh --remove-deps
```

The uninstaller removes the global `systempi` shortcut from `/usr/local/bin`. It does not delete your cloned repository folder.

---

# USAGE / Variations

Default launch:

```bash
systempi
```

One-shot snapshot mode (render once and exit):

```bash
systempi --once
```

Compact mode:

```bash
systempi --variation compact
```

Minimal mode:

```bash
systempi --variation minimal
```

Balanced mode:

```bash
systempi --variation balanced
```

Doctor mode (diagnostic-focused):

```bash
systempi --variation doctor
```

Once + export snapshot:

```bash
systempi --once --export text --output report.txt
systempi --once --export json --output report.json
```

Live alert event logging with watch/history support:

```bash
systempi --watch
systempi --history
```

`--watch` records newly active alert events, and `--history` prints recent events from:

`~/.local/state/systempi/events.log`

Theme selection examples:

```bash
systempi --theme ocean
systempi --theme matrix
systempi --theme wasteland
```

Refresh interval examples:

```bash
systempi --refresh 0.5
systempi --refresh 2
```

Pin network metrics to a specific interface:

```bash
systempi --interface eth0
systempi --interface wlan0
```

Disable ANSI colors:

```bash
systempi --no-color
```

Combine options:

```bash
systempi --variation compact --theme mono --refresh 2 --interface wlan0 --no-color
```

Help menu:

```bash
systempi -h
```

---

# AVAILABLE THEMES

- default
- matrix
- ocean
- wasteland
- lava
- mono
- girly
- amber
- crt
- vaulttec
- synthwave
- ice
- biohazard

---

# COMPATIBILITY

Designed primarily for Linux systems.

Tested on:

- Raspberry Pi OS
- Kali Linux ARM
- Raspberry Pi 4B

Notes:

- Raspberry Pi hardware metrics require `vcgencmd`.
- General system metrics require `psutil`, which is installed by `install.sh`.
- Non-Raspberry Pi systems can still provide standard CPU, memory, disk, and network metrics, but Pi-specific temperature, frequency, and throttling telemetry may show as unavailable.

---

# WHY SYSTEMPI?

systempi was built to make Raspberry Pi monitoring feel modern, responsive, and visually enjoyable instead of cluttered or outdated.

The dashboard focuses on:
- fast live telemetry
- clean terminal aesthetics
- low-flicker rendering
- meaningful hardware insight
- responsive layouts across terminal sizes

---

# LICENSE

MIT License ( Coming soon)

---

# AUTHOR

[WastelandSYS](https://github.com/WastelandSYS)
