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
- Doctor mode package update monitoring with responsive local APT state checks and optional repository freshness checks
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
systempi --variation balanced --theme raspberrypi
```

##### Note: `--variant` and `--var` may also be used as aliases for `--variation`.

<p align="center">
<img width="706" height="586" alt="SystempiBalancedRaspberrypi~" src="https://github.com/user-attachments/assets/1e008088-f26a-4a3e-8694-76b889102e95" />
</p>

---

## Doctor Mode — Diagnostic, Alert & System Insight

```bash
systempi --variation doctor --repo-check --theme vaulttec
```

<p align="center">
<img width="706" height="774" alt="SystempiDoctorVaulttec~" src="https://github.com/user-attachments/assets/7b23558b-e360-43ab-9d12-e86e41569972" />
</p>

---

## Compact Mode — Smaller Terminal Optimized

```bash
systempi --variation compact --theme crt
```

<p align="center">
<img width="626" height="332" alt="SystempiCompactCRT~" src="https://github.com/user-attachments/assets/e5aba316-2553-4177-8cec-0faf5f2bd667" />
</p>

---

## Minimal Mode — Essential Clean Monitoring

```bash
systempi --variation minimal --theme ice
```

<p align="center">
<img width="611" height="280" alt="SystempiMinimalICE~" src="https://github.com/user-attachments/assets/c22080c6-001a-4463-abb5-9483a9e37dcf" />
</p>

---

## Wasteland Theme

```bash
systempi --variation balanced --theme wasteland
```

<p align="center">
<img width="706" height="589" alt="SystempiBalancedWasteland~" src="https://github.com/user-attachments/assets/ae35ed54-f916-4390-b546-b62632a5a33c" />
</p>

---

## Biohazard Theme

```bash
systempi --variation doctor --theme biohazard
```

<p align="center">
<img width="706" height="775" alt="SystempiDoctorBiohazard~" src="https://github.com/user-attachments/assets/4d40afc9-7a13-4af7-a3ff-9e14b1e40191" />
</p>

---

## Ocean Theme

```bash
systempi --variation balanced --theme ocean
```

<p align="center">
<img width="706" height="588" alt="SystempiBalancedOcean~" src="https://github.com/user-attachments/assets/1efdbe21-60d8-4138-879f-1ed53718ec3c" />
</p>

---

## Synthwave Theme

```bash
systempi --variation doctor --theme synthwave
```

<p align="center">
<img width="706" height="775" alt="SystempiDoctorSynthwave~" src="https://github.com/user-attachments/assets/6d7c0d8c-a576-45bf-bdff-d80885412213" />
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

Doctor mode with optional repository freshness checking:

```bash
systempi --variation doctor --repo-check
```

Doctor mode refreshes its normal `Updates` count when local package state changes. The count still comes from `apt list --upgradable`; SystemPi only uses package-state changes as a trigger to ask APT again. This requires no sudo/root access and does not install, remove, or upgrade packages.

`--repo-check` is opt-in and only valid with Doctor mode. It contacts the APT repositories already configured on the machine, stores isolated user-owned metadata under ~/.cache/systempi/apt/, and refreshes asynchronously every three hours without modifying the system APT cache.

`Updates` means updates currently known to the machine's normal APT metadata. `Repo` means the result from SystemPi's optional private repository freshness check. For example, `Updates 8 available` and `Repo 9 available` means the system currently knows about 8 available updates, while the isolated repository check sees 9 total available packages.

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
- Optional `--repo-check` support is intended for Debian/APT-based systems and uses the user's configured APT repositories.
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
