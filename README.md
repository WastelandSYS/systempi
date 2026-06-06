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
- Doctor mode package update availability monitoring with non-blocking background checks
- Optional Raspberry Pi AI Hat+ / AI Hat+2 Hailo telemetry monitoring with NPU load, temperature, memory, and utilization metrics
- 14 built-in themes including matrix, wasteland, ocean, raspberrypi, mono, amber, crt, vaulttec, synthwave, ice, biohazard, and more
- 4 dashboard variations: Balanced, Compact, Minimal, and Doctor
- Responsive low-flicker partial terminal redraw renderer with dynamic terminal resizing
- Keyboard shortcuts including `q` for instant dashboard exit
- Adaptive dashboard scaling based on terminal width
- Live per-core CPU visualization, disk I/O rates, network throughput, load average, and uptime

---

# DASHBOARD MODES

| Mode | Purpose |
|------|----------|
| Balanced | Full monitoring dashboard |
| Compact | Smaller terminal optimized |
| Minimal | Essential-only clean mode |
| Doctor | Diagnostic, alert, and update-monitoring mode |

Each variation is designed for a different monitoring workflow — from lightweight minimal monitoring to deep diagnostic analysis.

---

# SCREENSHOTS / THEMES

## Balanced Mode — Main Dashboard

```bash
systempi --variation balanced --theme wasteland
```

##### Note: `--variant` and `--var` may also be used as aliases for `--variation`.

<p align="center">
<img width="705" height="585" alt="SystempiBalancedWastelandV2 1 1" src="https://github.com/user-attachments/assets/377ad0b0-0830-4303-a428-4ea830490767" />
</p>

---

## Doctor Mode — Diagnostic, Alert & System Insight

```bash
systempi --variation doctor --theme vaulttec
```

<p align="center">
<img width="705" height="774" alt="SystempiDoctorVaulttecV2 1 1" src="https://github.com/user-attachments/assets/a376eb0a-5936-40e6-b2c5-994598d4ee32" />
</p>

---

## Compact Mode — Smaller Terminal Optimized

```bash
systempi --variation compact --theme crt
```

<p align="center">
<img width="609" height="330" alt="SystempiCompactCrtV2 1 1" src="https://github.com/user-attachments/assets/2c9c3984-6929-4a94-b965-4c5d206a4e0f" />
</p>

---

## Minimal Mode — Essential Clean Monitoring

```bash
systempi --variation minimal --theme ice
```

<p align="center">
<img width="585" height="245" alt="SystempiMinimalIceV2 1 1" src="https://github.com/user-attachments/assets/d0c2973e-778d-46ef-a273-555293b1b0e0" />
</p>

---

## Raspberrypi Theme

```bash
systempi --theme raspberrypi
```

<p align="center">
<img width="657" height="585" alt="SystempiBalancedRaspberrypiV2 1 1" src="https://github.com/user-attachments/assets/1569d749-2846-4a41-9449-c7e1c73a68b8" />
</p>

---

## Biohazard Theme

```bash
systempi --variation doctor --theme biohazard
```

<p align="center">
<img width="705" height="773" alt="SystempiDoctorBiohazardV2 1 1" src="https://github.com/user-attachments/assets/edb28211-f095-4983-88af-81f6ef0935a8" />
</p>

---

## Ocean Theme

```bash
systempi --theme ocean
```

<p align="center">
<img width="705" height="585" alt="SystempiBalancedOceanV2 1 1" src="https://github.com/user-attachments/assets/1a1eea57-1a30-4db9-8295-0c6876be63a7" />
</p>

---

## Synthwave Theme

```bash
systempi --theme synthwave
```

<p align="center">
<img width="705" height="585" alt="SystempiBalancedSynthwaveV2 1 1" src="https://github.com/user-attachments/assets/ff95bc51-6c9b-491a-998a-06bfcbfc8061" />
</p>

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

Press `q` at any time to exit the live dashboard.

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
- raspberrypi

---

# COMPATIBILITY

Designed primarily for Linux systems.

Tested on:

- Raspberry Pi OS
- Kali Linux ARM
- Raspberry Pi 4B
- Raspberry Pi 5

Notes:

- Raspberry Pi hardware metrics require `vcgencmd`.
- General system metrics require `psutil`, which is installed by `install.sh`.
- Raspberry Pi AI Hat+ / AI Hat+2 telemetry is automatically detected when the Hailo software stack and `hailortcli` are available.
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

Systempi is released under the GNU General Public License v3.0. See [`LICENSE`](LICENSE) for the full license text.

---

# AUTHOR

[WastelandSYS](https://github.com/WastelandSYS)
