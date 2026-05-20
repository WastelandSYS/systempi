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
- 7 built-in themes including matrix, wasteland, ocean, lava, mono, and more
- Multiple dashboard variations including balanced, compact, and minimal modes
- Responsive low-flicker partial terminal redraw renderer with dynamic terminal resizing
- Adaptive dashboard scaling based on terminal width
- Live per-core CPU visualization, disk I/O rates, network throughput, load average, and uptime

---

# SCREENSHOTS / THEMES

## Default Theme

<img width="900" alt="default theme" src="https://github.com/user-attachments/assets/be4ac555-3395-4379-ad7c-2addd471b192" />

---

## Matrix Theme

<img width="900" alt="matrix theme" src="IMAGE_HERE" />

---

## Ocean Theme

<img width="900" alt="ocean theme" src="IMAGE_HERE" />

---

## Lava Theme

<img width="900" alt="lava theme" src="IMAGE_HERE" />

---

## Wasteland Theme

<img width="900" alt="matrix theme" src="IMAGE_HERE" />

---

## mono Theme

<img width="900" alt="matrix theme" src="IMAGE_HERE" />

---

## girly Theme

<img width="900" alt="matrix theme" src="IMAGE_HERE" />

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

# USAGE

Default launch:

```bash
systempi
```

Compact mode:

```bash
systempi --compact
```

Theme selection examples:

```bash
systempi --theme ocean
systempi --theme matrix
systempi --theme wasteland
```

Alternative layout:

```bash
systempi --variation insight
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

MIT License

---

# AUTHOR

[WastelandSYS](https://github.com/WastelandSYS)
