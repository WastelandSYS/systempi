<!-- ========================================================= -->
<!--                        HERO IMAGE                         -->
<!-- ========================================================= -->

<img width="1536" height="1024" alt="SystempiMainBnr" src="https://github.com/user-attachments/assets/780a4c7d-c3a8-4df4-ae9c-e383d9753907" />

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
- 15 built-in themes including matrix, wasteland, ocean, raspberrypi, mono, amber, crt, vaulttec, synthwave, ice, biohazard, and more
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
<img width="706" height="586" alt="SystempiBalancedWasteland" src="https://github.com/user-attachments/assets/c0e55295-7e37-45a4-a840-fdf9a78dd8d3" />
</p>

---

## Doctor Mode — Diagnostic, Alert & System Insight

```bash
systempi --variation doctor --theme vaulttec
```

<p align="center">
<img width="706" height="774" alt="SystempiDoctorVaulttec" src="https://github.com/user-attachments/assets/bcbf6b21-afc4-4e97-b001-f51e3bf4b321" />
</p>

---

## Compact Mode — Smaller Terminal Optimized

```bash
systempi --variation compact --theme crt
```

<p align="center">
<img width="626" height="332" alt="SystempiCompactCrt" src="https://github.com/user-attachments/assets/2bf660b6-fcee-4b15-875d-999a6d9be85e" />
</p>

---

## Minimal Mode — Essential Clean Monitoring

```bash
systempi --variation minimal --theme ice
```

<p align="center">
<img width="611" height="280" alt="SystempiMinimalICE" src="https://github.com/user-attachments/assets/72503e24-e71c-4e1a-ae8f-d626ef291693" />
</p>

---

## Raspberrypi Theme

```bash
systempi --theme raspberrypi
```

<p align="center">
<img width="706" height="589" alt="SystempiBalancedRaspberrypi" src="https://github.com/user-attachments/assets/3b1d02e2-37c9-4723-8276-b49bb419756b" />
</p>

---

## Biohazard Theme

```bash
systempi --variation doctor --theme biohazard
```

<p align="center">
<img width="706" height="775" alt="SystempiDoctorBiohazard" src="https://github.com/user-attachments/assets/99d16d21-a0e8-4445-8ed2-38479a0d1a66" />
</p>

---

## Ocean Theme

```bash
systempi --theme ocean
```

<p align="center">
<img width="706" height="588" alt="SystempiBalancedOcean" src="https://github.com/user-attachments/assets/5d3088d6-8f57-4c08-8f54-4601460afe42" />
</p>

---

## Synthwave Theme

```bash
systempi --theme synthwave
```

<p align="center">
<img width="706" height="587" alt="SystempiBalancedSynthwave" src="https://github.com/user-attachments/assets/cbf5075c-760f-4ae3-99ce-fc3ebdf67dce" />
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

Version information:

```bash
systempi --version
```

Terminal glyph selection:

```bash
systempi --glyphs auto
systempi --glyphs unicode
systempi --glyphs ascii
```

`auto` automatically selects the most compatible glyph set for the active terminal. `unicode` forces full Unicode rendering, while `ascii` uses a plain ASCII fallback for maximum compatibility.

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
- bubblegum
- synthwave
- ice
- biohazard
- raspberrypi

---

# COMPATIBILITY

Designed primarily for Linux systems.

Tested on:

- Raspberry Pi OS
- Raspberry Pi 5
- Raspberry Pi 4B
- Raspberry Pi Zero 2w
- Kali Linux ARM

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
