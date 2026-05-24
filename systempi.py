#!/usr/bin/env python3

# =========================================================
# systempi
# Real-time Raspberry Pi monitoring dashboard
#
# Copyright (c) 2026 WastelandSYS
# Licensed under GPLv3
# =========================================================

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

import psutil

# Constants
# Fallback thermal thresholds used when no model-specific profile is available.
TEMP_WARNING = 60
TEMP_CRITICAL = 75
# Model-aware thermal interpretation profiles.
# These values adjust health scoring and warning thresholds only.
# Raw telemetry still comes directly from Raspberry Pi firmware utilities.
# Pi 5 values are conservative estimates and may be refined with future hardware testing.
PI_THERMAL_PROFILES = {
    "default": {"warning": 60, "critical": 75, "health_temp_start": 50, "health_penalty": 1.2},
    "pi3": {"warning": 60, "critical": 75, "health_temp_start": 50, "health_penalty": 1.2},
    "pi4": {"warning": 60, "critical": 75, "health_temp_start": 50, "health_penalty": 1.2},
    "pi400": {"warning": 65, "critical": 78, "health_temp_start": 55, "health_penalty": 1.0},
    "pi5": {"warning": 70, "critical": 82, "health_temp_start": 60, "health_penalty": 0.9},
    "zero2": {"warning": 60, "critical": 75, "health_temp_start": 50, "health_penalty": 1.2},
}
CPU_THRESHOLD_LOW = 60
CPU_THRESHOLD_MEDIUM = 85
RESET = "\033[0m"

THEMES = {
    "default": {
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "cyan": "\033[96m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "white": "\033[97m",
        "bold_cyan": "\033[96;1m",
        "dim": "\033[38;5;245m",
    },
    "girly": {
        "green": "\033[95m",
        "yellow": "\033[97m",
        "red": "\033[91m",
        "cyan": "\033[95m",
        "blue": "\033[38;5;219m",
        "magenta": "\033[38;5;213m",
        "white": "\033[97m",
        "bold_cyan": "\033[95;1m",
        "dim": "\033[2m",
    },
    "wasteland": {
        "green": "\033[38;5;148m",
        "yellow": "\033[38;5;179m",
        "red": "\033[38;5;203m",
        "cyan": "\033[38;5;180m",
        "blue": "\033[38;5;109m",
        "magenta": "\033[38;5;137m",
        "white": "\033[38;5;223m",
        "bold_cyan": "\033[38;5;186;1m",
        "dim": "\033[38;5;240m",
    },
    "ocean": {
        "green": "\033[38;5;86m",
        "yellow": "\033[38;5;117m",
        "red": "\033[38;5;203m",
        "cyan": "\033[38;5;51m",
        "blue": "\033[38;5;33m",
        "magenta": "\033[38;5;99m",
        "white": "\033[97m",
        "bold_cyan": "\033[38;5;45;1m",
        "dim": "\033[38;5;244m",
    },
    "matrix": {
        "green": "\033[38;5;46m",
        "yellow": "\033[38;5;118m",
        "red": "\033[38;5;196m",
        "cyan": "\033[38;5;82m",
        "blue": "\033[38;5;22m",
        "magenta": "\033[38;5;34m",
        "white": "\033[38;5;120m",
        "bold_cyan": "\033[38;5;46;1m",
        "dim": "\033[38;5;238m",
    },
    "lava": {
        "green": "\033[38;5;208m",
        "yellow": "\033[38;5;214m",
        "red": "\033[38;5;196m",
        "cyan": "\033[38;5;203m",
        "blue": "\033[38;5;88m",
        "magenta": "\033[38;5;166m",
        "white": "\033[38;5;230m",
        "bold_cyan": "\033[38;5;202;1m",
        "dim": "\033[38;5;238m",
    },
    "mono": {
        "green": "\033[38;5;252m",
        "yellow": "\033[38;5;250m",
        "red": "\033[1;97m",
        "cyan": "\033[38;5;248m",
        "blue": "\033[38;5;242m",
        "magenta": "\033[38;5;255m",
        "white": "\033[97m",
        "bold_cyan": "\033[1;97m",
        "dim": "\033[38;5;240m",
    },
    "amber": {
        "green": "\033[38;5;214m",
        "yellow": "\033[38;5;220m",
        "red": "\033[38;5;202m",
        "cyan": "\033[38;5;180m",
        "blue": "\033[38;5;172m",
        "magenta": "\033[38;5;179m",
        "white": "\033[38;5;230m",
        "bold_cyan": "\033[38;5;222;1m",
        "dim": "\033[38;5;240m",
    },
    "crt": {
        "green": "\033[38;5;120m",
        "yellow": "\033[38;5;156m",
        "red": "\033[38;5;203m",
        "cyan": "\033[38;5;84m",
        "blue": "\033[38;5;77m",
        "magenta": "\033[38;5;114m",
        "white": "\033[38;5;194m",
        "bold_cyan": "\033[38;5;120;1m",
        "dim": "\033[38;5;239m",
    },
    "vaulttec": {
        "green": "\033[38;5;226m",
        "yellow": "\033[38;5;220m",
        "red": "\033[38;5;196m",
        "cyan": "\033[38;5;39m",
        "blue": "\033[38;5;27m",
        "magenta": "\033[38;5;179m",
        "white": "\033[38;5;230m",
        "bold_cyan": "\033[38;5;39;1m",
        "dim": "\033[38;5;240m",
    },
    "synthwave": {
        "green": "\033[38;5;141m",
        "yellow": "\033[38;5;219m",
        "red": "\033[38;5;198m",
        "cyan": "\033[38;5;51m",
        "blue": "\033[38;5;99m",
        "magenta": "\033[38;5;201m",
        "white": "\033[38;5;225m",
        "bold_cyan": "\033[38;5;117;1m",
        "dim": "\033[38;5;60m",
    },
    "ice": {
        "green": "\033[38;5;123m",
        "yellow": "\033[38;5;159m",
        "red": "\033[38;5;167m",
        "cyan": "\033[38;5;87m",
        "blue": "\033[38;5;111m",
        "magenta": "\033[38;5;147m",
        "white": "\033[38;5;231m",
        "bold_cyan": "\033[38;5;123;1m",
        "dim": "\033[38;5;250m",
    },
    "biohazard": {
        "green": "\033[38;5;154m",
        "yellow": "\033[38;5;190m",
        "red": "\033[38;5;196m",
        "cyan": "\033[38;5;148m",
        "blue": "\033[38;5;58m",
        "magenta": "\033[38;5;214m",
        "white": "\033[38;5;230m",
        "bold_cyan": "\033[38;5;190;1m",
        "dim": "\033[38;5;239m",
    },
}

COLORS = THEMES["default"].copy()


def apply_theme(theme_name):
    global COLORS
    COLORS = THEMES.get(theme_name, THEMES["default"]).copy()


def disable_colors():
    global COLORS, RESET
    COLORS = {key: "" for key in THEMES["default"].keys()}
    RESET = ""

class SystemState:
    def __init__(self, interface=None):
        self.prev_sent = 0
        self.prev_recv = 0
        self.prev_disk_read = 0
        self.prev_disk_write = 0
        self.health_history = []
        self.network_interface = interface
        self.interface_locked = interface is not None
        self.last_net_time = time.time()
        self.last_disk_time = time.time()
        self.throttle_occurred_latch = False
        self.history = {
            "cpu": deque(maxlen=60),
            "ram": deque(maxlen=60),
            "temp": deque(maxlen=60),
            "net": deque(maxlen=60),
            "health": deque(maxlen=60),
        }
        self.active_alerts = []
        self.session_alert_counts = {}
        self.event_log_path = default_log_path()
        self.last_top_cpu_process = "N/A"

def default_log_path():
    home = Path.home()
    return home / ".local" / "state" / "systempi" / "events.log"

def run_vcgencmd(args):
    try:
        return subprocess.check_output(
            ["vcgencmd"] + args,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=2,
        ).strip()
    except Exception:
        return None

def get_pi_stats():
    try:
        temp_out = run_vcgencmd(["measure_temp"])
        freq_out = run_vcgencmd(["measure_clock", "arm"])
        throttle_out = run_vcgencmd(["get_throttled"])

        if not temp_out or not freq_out or not throttle_out:
            raise ValueError("vcgencmd returned None")

        # Temperature
        temperature = float(temp_out.split('=')[1].replace("'C", "").strip())

        # Frequency
        frequency = int(freq_out.split("=")[1])

        # Throttle parsing (safe fallback)
        parts = throttle_out.split("=")
        value = int(parts[1], 16) if len(parts) > 1 else 0

        throttle = {
            "undervoltage": bool(value & 0x1),
            "freq_capped": bool(value & 0x2),
            "throttled": bool(value & 0x4),
            "soft_temp_limit": bool(value & 0x8),
            "undervoltage_occurred": bool(value & 0x10000),
            "freq_capped_occurred": bool(value & 0x20000),
            "throttling_occurred": bool(value & 0x40000),
            "soft_temp_limit_occurred": bool(value & 0x80000),
        }

        return temperature, frequency, throttle

    except Exception:
        return None, None, None

def get_network_usage(state):
    try:
        net = psutil.net_io_counters(pernic=True)

        if state.interface_locked:
            if state.network_interface not in net:
                return 0.0, 0.0
            stats = net[state.network_interface]
        else:
            # Select interface once (avoid lo)
            if state.network_interface is None:
                for iface, stats in net.items():
                    if iface != "lo" and (stats.bytes_sent > 0 or stats.bytes_recv > 0):
                        state.network_interface = iface
                        break

            if not state.network_interface or state.network_interface not in net:
                candidates = [(iface, s.bytes_sent + s.bytes_recv) for iface, s in net.items() if iface != "lo"]
                if not candidates:
                    return 0.0, 0.0

                state.network_interface = max(candidates, key=lambda x: x[1])[0]

            stats = net[state.network_interface]

        if state.prev_sent == 0 and state.prev_recv == 0:
            state.prev_sent = stats.bytes_sent
            state.prev_recv = stats.bytes_recv
            return 0.0, 0.0

        current_time = time.time()
        elapsed = current_time - state.last_net_time

        if elapsed <= 0:
            return 0.0, 0.0

        sent_delta = max(0, stats.bytes_sent - state.prev_sent)
        recv_delta = max(0, stats.bytes_recv - state.prev_recv)

        sent = sent_delta / 1024 / elapsed
        recv = recv_delta / 1024 / elapsed

        state.prev_sent = stats.bytes_sent
        state.prev_recv = stats.bytes_recv
        state.last_net_time = current_time

        return sent, recv

    except Exception:
        return 0.0, 0.0

def get_disk_io(state):
    try:
        stats = psutil.disk_io_counters()

        if not stats:
            return 0.0, 0.0

        if state.prev_disk_read == 0 and state.prev_disk_write == 0:
            state.prev_disk_read = stats.read_bytes
            state.prev_disk_write = stats.write_bytes
            return 0.0, 0.0

        current_time = time.time()
        elapsed = current_time - state.last_disk_time

        if elapsed <= 0:
            return 0.0, 0.0

        read_delta = max(0, stats.read_bytes - state.prev_disk_read)
        write_delta = max(0, stats.write_bytes - state.prev_disk_write)

        read = read_delta / 1024 / elapsed
        write = write_delta / 1024 / elapsed

        state.prev_disk_read = stats.read_bytes
        state.prev_disk_write = stats.write_bytes
        state.last_disk_time = current_time

        return read, write

    except Exception:
        return 0.0, 0.0

def get_system_load_average():
    try:
        return os.getloadavg()
    except Exception:
        return (0.0, 0.0, 0.0)

def colorize(text, color):
    return f"{COLORS[color]}{text}{RESET}"

def severity_color(value, warning, critical, inverse=False):
    if inverse:
        if value >= warning:
            return "green"
        if value >= critical:
            return "yellow"
        return "red"

    if value < warning:
        return "green"
    if value < critical:
        return "yellow"
    return "red"

def status_badge(value, warning, critical, inverse=False):
    if inverse:
        if value >= warning:
            return "OK", "green"
        if value >= critical:
            return "WARN", "yellow"
        return "CRIT", "red"

    if value < warning:
        return "OK", "green"
    if value < critical:
        return "WARN", "yellow"
    return "CRIT", "red"

def percent_bar(value, width=18, warning=60, critical=85, inverse=False):
    value = max(0, min(100, value))
    filled = int(round((value / 100) * width))
    bar = "█" * filled + "░" * (width - filled)
    color = severity_color(value, warning, critical, inverse=inverse)
    return colorize(bar, color)

def colored_core(value):
    blocks = "▁▂▃▄▅▆▇█"
    color = severity_color(value, CPU_THRESHOLD_LOW, CPU_THRESHOLD_MEDIUM)
    index = int((max(0, min(100, value)) / 100) * (len(blocks) - 1))
    return colorize(blocks[index], color)

def sparkline(values, width=24, fixed_min=None, fixed_max=None):
    if not values:
        return ""

    samples = values[-width:]
    blocks = "▁▂▃▄▅▆▇█"

    if fixed_min is not None and fixed_max is not None:
        low = fixed_min
        high = fixed_max
    else:
        low = min(samples)
        high = max(samples)

    if high == low:
        return colorize(blocks[0] * len(samples), "green")

    points = []
    for value in samples:
        index = int(((value - low) / (high - low)) * (len(blocks) - 1))
        points.append(blocks[index])

    avg = sum(samples) / len(samples)
    color = severity_color(avg, 80, 50, inverse=True)
    return colorize("".join(points), color)

class TerminalRenderer:
    def __init__(self):
        self.previous_lines = []
        self.enabled = sys.stdout.isatty()
        self.last_terminal_size = None

    def start(self):
        if not self.enabled:
            return
        # Alternate screen + hidden cursor keeps the shell scrollback stable and
        # avoids repainting over the user's prompt while the dashboard is live.
        sys.stdout.write("\033[?1049h\033[?25l\033[H\033[2J")
        sys.stdout.flush()

    def render(self, frame):
        if not self.enabled:
            print(frame, flush=True)
            return

        current_size = shutil.get_terminal_size((88, 24))
        lines = frame.splitlines()
        output = []

        if current_size != self.last_terminal_size:
            output.append("\033[H\033[2J")
            self.previous_lines = []
            self.last_terminal_size = current_size

        # Only redraw lines that changed. This keeps terminal writes small and
        # avoids the visible flash caused by clearing/repainting the full screen.
        for index, line in enumerate(lines):
            if index >= len(self.previous_lines) or line != self.previous_lines[index]:
                output.append(f"\033[{index + 1};1H\033[2K{line}")

        for index in range(len(lines), len(self.previous_lines)):
            output.append(f"\033[{index + 1};1H\033[2K")

        if output:
            sys.stdout.write("".join(output))
            sys.stdout.flush()

        self.previous_lines = lines

    def stop(self):
        if not self.enabled:
            return
        sys.stdout.write("\033[?25h\033[?1049l")
        sys.stdout.flush()

def cleanup_terminal(renderer=None):
    if renderer:
        renderer.stop()
    else:
        print("\033[?25h", end="", flush=True)      # restore cursor

def get_swap_usage():
    try:
        return psutil.swap_memory().percent
    except Exception:
        return 0.0

def calculate_system_health(cpu, temp, mem, disk, throttle, thermal_profile):
    health = 100.0

    # CPU (continuous penalty)
    cpu_pressure = max(0, cpu - 5)
    health -= cpu_pressure * 0.4

    # Temperature (only above safe zone)
    if temp is not None:
        temp_excess = max(0, temp - thermal_profile["health_temp_start"])
        health -= temp_excess * thermal_profile["health_penalty"]

    # Memory (continuous)
    ram_pressure = max(0, mem - 60)
    health -= ram_pressure * 0.5

    # Disk pressure (only penalize high usage)
    disk_pressure = max(0, disk - 80)
    health -= disk_pressure * 0.6

    # Throttling (hard penalty, still valid as event)
    if throttle and throttle.get("throttled"):
        health -= 35
    if throttle and throttle.get("undervoltage"):
        health -= 25

    return max(0, int(health))

def get_cpu_cores():
    try:
        return psutil.cpu_percent(interval=None, percpu=True)
    except Exception:
        return []

def health_explainability(cpu, temp, mem, disk, throttle, temp_warning):
    reasons = []
    if cpu > 80:
        reasons.append(f"CPU pressure {cpu:.1f}%")
    if temp is not None and temp > temp_warning:
        reasons.append(f"Temp high {temp:.1f}C")
    if mem > 80:
        reasons.append(f"RAM high {mem:.1f}%")
    if disk > 90:
        reasons.append(f"Disk near full {disk:.1f}%")
    if throttle and throttle.get("throttled"):
        reasons.append("Active throttling")
    if throttle and throttle.get("undervoltage"):
        reasons.append("Undervoltage detected")
    if throttle and throttle.get("freq_capped"):
        reasons.append("Frequency capped")
    return reasons[:3]


def render_health_why_line(health_why_reasons, width):
    def color_reason(reason):
        reason_lower = reason.lower()
        if "undervoltage" in reason_lower or "throttling" in reason_lower:
            return colorize(reason, "red")
        if "temp" in reason_lower or "cpu" in reason_lower:
            return colorize(reason, "yellow")
        if "ram" in reason_lower or "disk" in reason_lower or "freq" in reason_lower:
            return colorize(reason, "magenta")
        return colorize(reason, "white")

    if health_why_reasons:
        colored_reasons = [color_reason(reason) for reason in health_why_reasons]
        bullets = colorize(" • ", "dim").join(colored_reasons)

        label = colorize(f"{'Health Why:':<14}", "bold_cyan")
        text = f"{label}{bullets}"

    else:
        label = colorize(f"{'Health Why:':<14}", "bold_cyan")
        text = f"{label}{colorize('All systems stable', 'green')}"

    return panel_line(truncate_display(text, width - 4), width)

def calculate_storage_health(disk_usage, write_rate):
    health = 100

    # Disk usage impact
    if disk_usage > 95:
        health -= 40
    elif disk_usage > 85:
        health -= 20

    # Write activity impact
    if write_rate > 1000:
        health -= 30
    elif write_rate > 500:
        health -= 15

    return max(0, health)

def doctor_status_color(value):
    value_lower = str(value).lower()

    if any(word in value_lower for word in ("critical", "active undervoltage", "active throttling")):
        return "red"

    if any(word in value_lower for word in ("warm", "struggling", "getting tight", "heavy", "pressure", "past")):
        return "yellow"

    if any(word in value_lower for word in ("stable", "low", "idle")):
        return "green"

    return "white"

def cooling_assessment(metrics):
    temperature = metrics.get("temperature")
    cpu_load = metrics.get("cpu_load", 0.0)

    if temperature is None:
        return "Pi temperature unavailable"
    temp_warning = metrics.get("temp_warning", TEMP_WARNING)
    temp_critical = metrics.get("temp_critical", TEMP_CRITICAL)

    if temperature >= temp_critical or (temperature >= temp_warning + 8 and cpu_load >= 85):
        return "Critical thermal pressure"
    if temperature >= temp_warning + 5 and cpu_load >= 70:
        return "Cooling struggling under load"
    if temperature >= temp_warning or cpu_load >= 70:
        return "Warm but manageable"
    return "Thermals stable"

def power_stability_assessment(metrics, state):
    throttle = metrics.get("throttle")
    if not throttle:
        return "Power telemetry unavailable"
    if throttle.get("undervoltage"):
        return "Active undervoltage detected"
    if throttle.get("throttled") or throttle.get("soft_temp_limit"):
        return "Active throttling detected"
    if throttle.get("freq_capped"):
        return "Frequency cap active"
    if state.throttle_occurred_latch:
        return "Past power/throttle event detected"
    return "Power delivery stable"

def workload_profile(metrics):
    cpu_load = metrics.get("cpu_load", 0.0)
    mem_percent = metrics.get("mem_percent", 0.0)
    disk_read_per_sec = metrics.get("disk_read_per_sec", 0.0)
    disk_write_per_sec = metrics.get("disk_write_per_sec", 0.0)
    load_avg = metrics.get("load_avg") or [0.0]
    load_1m = load_avg[0] if load_avg else 0.0

    if disk_read_per_sec > 600 or disk_write_per_sec > 600:
        return "Heavy disk I/O workload"
    if mem_percent >= 85:
        return "Memory pressure workload"
    if cpu_load >= 80 or load_1m >= 3.0:
        return "Heavy CPU-bound workload"
    if cpu_load < 20 and mem_percent < 55 and disk_read_per_sec < 80 and disk_write_per_sec < 80:
        return "Mostly idle"
    return "Moderate mixed workload"

def storage_insight(metrics):
    disk_usage = metrics.get("disk_usage", 0.0)
    storage_health = metrics.get("storage_health", 100)
    disk_write_per_sec = metrics.get("disk_write_per_sec", 0.0)

    if disk_usage >= 95 or storage_health <= 50:
        return "Critical free-space pressure"
    if disk_write_per_sec > 700:
        return "Heavy write activity detected"
    if disk_usage >= 85 or storage_health <= 75:
        return "Storage getting tight"
    return "Storage pressure low"

def truncate_display(text, max_width):
    plain_width = len(strip_ansi(text))
    if plain_width <= max_width:
        return text
    if max_width <= 1:
        return ""
    return strip_ansi(text)[:max_width - 1] + "…"

def strip_ansi(text):
    # This renderer only truncates simple fields; stripping all escape sequences keeps fallback safe.
    return re.sub(r"\033\[[0-9;]*m", "", text)

def panel_line(content, width):
    plain_width = len(strip_ansi(content))
    padding = max(0, width - 2 - plain_width)
    return f"│ {content}{' ' * padding} │"

def divider(width):
    return "├" + "─" * (width - 0) + "┤"

def metric_row(label, value, unit="", bar=None, badge=None, color=None, width=72):
    label_text = f"{label:<14}"
    value_text = f"{value:>10}"
    if color:
        value_text = colorize(value_text, color)
    unit_text = f" {unit:<6}" if unit else "       "
    bar_text = f"{' ' * 3}{bar}" if bar else ""
    badge_text = ""
    if badge:
        badge_label, badge_color = badge
        badge_text = f" {colorize(f' {badge_label} ', badge_color)}"
    content = f"{label_text}{value_text}{unit_text}{bar_text}{badge_text}"
    return panel_line(truncate_display(content, width - 4), width)

def section_title(title, width):
    return panel_line(truncate_display(colorize(title, "bold_cyan"), width - 4), width)

def format_frequency(frequency):
    if frequency is None:
        return "N/A", "", None
    mhz = frequency / 1_000_000
    return f"{mhz:.0f}", "MHz", "cyan"

def render_core_line(core_loads, width):
    if not core_loads:
        return panel_line("CPU Cores     N/A", width)

    core_parts = []
    for index, load in enumerate(core_loads, start=1):
        core_label = colorize(f"{index}:", "bold_cyan")
        core_parts.append(f"{core_label}{load:>4.0f}% {colored_core(load)}")

    content = f"CPU Cores{' ' * 11}" + "  ".join(core_parts)
    return panel_line(truncate_display(content, width - 4), width)

VARIATIONS = {
    "balanced": {
        "mode": "balanced",
        "compact": False,
        "show_cores": True,
        "show_io_details": True,
        "show_net_details": True,
        "show_uptime": True,
        "show_load_average": True,
        "show_swap": True,
        "show_power_details": True,
        "show_storage_health": True,
        "show_stability_avg": True,
        "health_trend_width": "normal",
        "bar_profile": "normal",
        "health_why_limit": 3,
    },
    "compact": {
        "mode": "compact",
        "compact": True,
        "show_cores": False,
        "show_io_details": False,
        "show_net_details": False,
        "show_uptime": False,
        "show_load_average": False,
        "show_swap": True,
        "show_power_details": True,
        "show_storage_health": True,
        "show_stability_avg": True,
        "health_trend_width": "short",
        "bar_profile": "short",
        "health_why_limit": 2,
    },
    "minimal": {
        "mode": "minimal",
        "compact": True,
        "show_cores": False,
        "show_io_details": False,
        "show_net_details": False,
        "show_uptime": False,
        "show_load_average": False,
        "show_swap": False,
        "show_power_details": "warning_only",
        "show_storage_health": False,
        "show_stability_avg": False,
        "health_trend_width": "off",
        "bar_profile": "short",
        "health_why_limit": 2,
    },
    "doctor": {
        "mode": "doctor",
        "compact": False,
        "show_cores": True,
        "show_io_details": True,
        "show_net_details": True,
        "show_uptime": True,
        "show_load_average": True,
        "show_swap": True,
        "show_power_details": True,
        "show_storage_health": True,
        "show_stability_avg": True,
        "health_trend_width": "normal",
        "bar_profile": "normal",
        "health_why_limit": 4,
    },
}


def resolve_view_config(args):
    view = VARIATIONS[args.variation].copy()
    if args.compact:
        view["compact"] = True
    return view

def health_why_with_limit(reasons, limit):
    if limit <= 0:
        return []
    return reasons[:limit]

def has_power_warning(throttle, latch):
    if not throttle:
        return False
    return (
        latch
        or throttle.get("throttled")
        or throttle.get("undervoltage")
        or throttle.get("freq_capped")
        or throttle.get("soft_temp_limit")
    )

def render_power_rows(lines, metrics, state, width):
    throttle = metrics["throttle"]
    if throttle is None:
        lines.append(metric_row("Throttled", "N/A", width=width))
        lines.append(metric_row("Freq Capped", "N/A", width=width))
        lines.append(metric_row("Occurred", "N/A", width=width))
        lines.append(metric_row("Undervoltage", "N/A", width=width))
        return

    throttle_color = "red" if throttle["throttled"] else "green"
    freq_capped_color = "yellow" if throttle["freq_capped"] else "green"
    occurred_color = "red" if state.throttle_occurred_latch else "green"
    undervolt_color = "red" if throttle["undervoltage"] else "green"
    lines.append(metric_row("Throttled", "YES" if throttle["throttled"] else "NO", color=throttle_color, width=width))
    lines.append(metric_row("Freq Capped", "YES" if throttle["freq_capped"] else "NO", color=freq_capped_color, width=width))
    lines.append(metric_row("Occurred", "YES" if state.throttle_occurred_latch else "NO", color=occurred_color, width=width))
    lines.append(metric_row("Undervoltage", "YES" if throttle["undervoltage"] else "NO", color=undervolt_color, width=width))

def choose_bar_width(width, compact, profile):
    if profile == "short":
        preferred = 14 if compact else 14
    elif profile == "long":
        preferred = 20 if compact else (24 if width < 86 else 32)
    else:
        preferred = 16 if compact else (20 if width < 86 else 28)
    max_bar_width = max(4, width - 46)
    return max(4, min(preferred, max_bar_width))

def choose_trend_width(width, mode):
    if mode == "off":
        return 0
    if mode == "short":
        preferred = 14 if width < 86 else 18
    elif mode == "long":
        preferred = 28 if width < 86 else 38
    else:
        preferred = 20 if width < 86 else 28
    return max(4, min(preferred, width - 22))

def render_top_panel(lines, width, metrics, refresh_interval):
    lines.append("╭" + "─" * (width - 0) + "╮")
    title = colorize("SYSTEMPI v2.1 Dashboard", "bold_cyan")
    subtitle = f"Interface: {metrics['network_interface'] or 'N/A'} | Refresh: {refresh_interval:g}s"
    title_padding = max(1, width - 4 - len(strip_ansi(title)) - len(subtitle))
    header = f"{title}{' ' * title_padding}{COLORS['dim']}{subtitle}{RESET}"
    lines.append(panel_line(truncate_display(header, width - 4), width))
    lines.append(divider(width))

def key_value_line(label, value, width, label_width=14):
    content = f"{label:<{label_width}}{value}"
    return panel_line(truncate_display(content, width - 4), width)

def compact_dual_metric_row(left_label, left_value, right_label, right_value, width):
    left = f"{left_label:<6} {left_value:>6}"
    right = f"{right_label:<6} {right_value:>7}"
    content = f"{left}    {right}"
    return panel_line(truncate_display(content, width - 4), width)

def doctor_dual_metric_row(left_label, left_value, right_label, right_value, width, left_ratio=0.6):
    # Balanced two-column row for doctor mode: clean spacing first, then safe truncation.
    inner_width = max(24, width - 4)
    separator = f" {colorize('│', 'dim')} "
    sep_width = len(strip_ansi(separator))
    gutter = 2
    available = max(20, inner_width - sep_width - gutter)
    left_ratio = max(0.45, min(0.72, left_ratio))
    left_width = int(available * left_ratio)
    right_width = available - left_width

    left_content = f"{left_label:<9} {left_value}"
    right_content = f"{right_label:<9} {right_value}"
    left = truncate_display(left_content, left_width)
    right = truncate_display(right_content, right_width)

    content = f"{left:<{left_width}}{separator}{right:<{right_width}}"
    return panel_line(truncate_display(content, width - 4), width)

def detect_pi_model():
    model_path = Path("/proc/device-tree/model")
    try:
        if model_path.exists():
            return model_path.read_text(errors="ignore").strip("\x00").strip()
    except Exception:
        pass
    return "Unknown"



def thermal_profile_for_model(model):
    model_lower = (model or "").lower()

    if "raspberry pi 5" in model_lower:
        return "pi5", PI_THERMAL_PROFILES["pi5"]
    if "raspberry pi 400" in model_lower:
        return "pi400", PI_THERMAL_PROFILES["pi400"]
    if "raspberry pi 4" in model_lower:
        return "pi4", PI_THERMAL_PROFILES["pi4"]
    if "raspberry pi 3" in model_lower:
        return "pi3", PI_THERMAL_PROFILES["pi3"]
    if "raspberry pi zero 2" in model_lower:
        return "zero2", PI_THERMAL_PROFILES["zero2"]

    return "default", PI_THERMAL_PROFILES["default"]

def evaluate_alerts(metrics):
    alerts = []
    if metrics["cpu_load"] >= 90:
        alerts.append("high_cpu")
    if metrics["mem_percent"] >= 90:
        alerts.append("high_ram")
    if metrics["disk_usage"] >= 95:
        alerts.append("high_disk")
    if metrics["temperature"] is not None and metrics["temperature"] >= metrics.get("temp_critical", TEMP_CRITICAL):
        alerts.append("high_temp")
    if metrics["disk_write_per_sec"] >= 1024:
        alerts.append("heavy_disk_write")
    throttle = metrics["throttle"] or {}
    if throttle.get("undervoltage"):
        alerts.append("undervoltage")
    if throttle.get("throttled"):
        alerts.append("throttling")
    if throttle.get("freq_capped"):
        alerts.append("frequency_capped")
    if throttle.get("soft_temp_limit"):
        alerts.append("soft_temp_limit")
    return alerts

def log_alert_events(state, active_alerts):
    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    new_alerts = [a for a in active_alerts if a not in state.active_alerts]
    for alert in new_alerts:
        state.session_alert_counts[alert] = state.session_alert_counts.get(alert, 0) + 1
    if not new_alerts:
        return
    try:
        state.event_log_path.parent.mkdir(parents=True, exist_ok=True)
        with state.event_log_path.open("a", encoding="utf-8") as fh:
            for alert in new_alerts:
                fh.write(f"{now} {alert}\n")
    except Exception:
        pass

def prepare_event_log(state):
    try:
        state.event_log_path.parent.mkdir(parents=True, exist_ok=True)
        state.event_log_path.touch(exist_ok=True)
    except Exception:
        pass

def render_minimal_dashboard(lines, metrics, state, width, bar_width, effective_view):
    minimal_bar = max(6, min(bar_width, 14))
    lines.append(section_title("MINIMAL ESSENTIALS", width))

    cpu_badge = status_badge(metrics["cpu_load"], CPU_THRESHOLD_LOW, CPU_THRESHOLD_MEDIUM)
    mem_badge = status_badge(metrics["mem_percent"], 70, 90)

    lines.append(metric_row("CPU Load", f"{metrics['cpu_load']:.1f}", "%", bar=percent_bar(metrics["cpu_load"], minimal_bar, CPU_THRESHOLD_LOW, CPU_THRESHOLD_MEDIUM), badge=cpu_badge, color=cpu_badge[1], width=width))

    if metrics["temperature"] is None:
        lines.append(metric_row("CPU Temp", "N/A", width=width))
    else:
        temp_badge = status_badge(metrics["temperature"], metrics["temp_warning"], metrics["temp_critical"])
        lines.append(metric_row("CPU Temp", f"{metrics['temperature']:.1f}", "°C", bar=" " * minimal_bar, badge=temp_badge, color=temp_badge[1], width=width))

    disk_badge = status_badge(metrics["disk_usage"], 80, 95)

    lines.append(metric_row("RAM Usage", f"{metrics['mem_percent']:.1f}", "%", bar=percent_bar(metrics["mem_percent"], minimal_bar, 70, 90), badge=mem_badge, color=mem_badge[1], width=width))
    lines.append(metric_row("Disk Usage", f"{metrics['disk_usage']:.1f}", "%", bar=percent_bar(metrics["disk_usage"], minimal_bar, 80, 95), badge=disk_badge, color=disk_badge[1], width=width))
    lines.append(metric_row("Net Total", f"{metrics['network_sent_per_sec'] + metrics['network_recv_per_sec']:.2f}", "KiB/s", color="white", width=width))

    lines.append(divider(width))
    lines.append(section_title("MINIMAL HEALTH", width))

    if effective_view["show_power_details"] == "warning_only" and has_power_warning(metrics["throttle"], state.throttle_occurred_latch):
        render_power_rows(lines, metrics, state, width)

    health_badge = status_badge(metrics["system_health"], 80, 50, inverse=True)
    lines.append(metric_row("System Health", f"{metrics['system_health']}", "%", bar=percent_bar(metrics["system_health"], bar_width, 80, 50, inverse=True), badge=health_badge, color=health_badge[1], width=width))
    lines.append(render_health_why_line(health_why_with_limit(metrics["health_why"], effective_view.get("health_why_limit", 2)), width))
    lines.append(key_value_line(colorize("Profile ", "dim"), colorize("Minimal monitoring", "dim"), width))

def render_compact_dashboard(lines, metrics, state, width, bar_width):
    cpu_color = severity_color(metrics["cpu_load"], CPU_THRESHOLD_LOW, CPU_THRESHOLD_MEDIUM)
    temp_value = "N/A" if metrics["temperature"] is None else f"{metrics['temperature']:.0f}C"
    temp_color = "white" if metrics["temperature"] is None else severity_color(metrics["temperature"], metrics["temp_warning"], metrics["temp_critical"])
    mem_color = severity_color(metrics["mem_percent"], 70, 90)
    disk_color = severity_color(metrics["disk_usage"], 80, 95)
    net_total = metrics["network_sent_per_sec"] + metrics["network_recv_per_sec"]
    health_color = severity_color(metrics["system_health"], 80, 50, inverse=True)
    cpu_pct = f"{metrics['cpu_load']:.0f}%"
    ram_pct = f"{metrics['mem_percent']:.0f}%"
    disk_pct = f"{metrics['disk_usage']:.0f}%"
    health_pct = f"{metrics['system_health']}%"
    lines.append(section_title("COMPACT SNAPSHOT", width))
    lines.append(compact_dual_metric_row(colorize("CPU", "bold_cyan"), colorize(cpu_pct, cpu_color), colorize("TEMP", "bold_cyan"), colorize(temp_value, temp_color), width))
    lines.append(compact_dual_metric_row(colorize("RAM", "bold_cyan"), colorize(ram_pct, mem_color), colorize("DISK", "bold_cyan"), colorize(disk_pct, disk_color), width))
    lines.append(compact_dual_metric_row(colorize("NET", "bold_cyan"), colorize(f"{net_total:.0f}k", "white"), colorize("HEALTH", "bold_cyan"), colorize(health_pct, health_color), width))
    lines.append(divider(width))

    compact_bar = max(6, min(bar_width, 14))
    lines.append(section_title("COMPACT SYSTEM", width))
    lines.append(metric_row("CPU Load", f"{metrics['cpu_load']:.1f}", "%", bar=percent_bar(metrics["cpu_load"], compact_bar, CPU_THRESHOLD_LOW, CPU_THRESHOLD_MEDIUM), color=cpu_color, width=width))
    lines.append(metric_row("RAM Usage", f"{metrics['mem_percent']:.1f}", "%", bar=percent_bar(metrics["mem_percent"], compact_bar, 70, 90), color=mem_color, width=width))
    lines.append(metric_row("Disk Usage", f"{metrics['disk_usage']:.1f}", "%", bar=percent_bar(metrics["disk_usage"], compact_bar, 80, 95), color=disk_color, width=width))
    lines.append(metric_row("Net Total", f"{net_total:.2f}", "KiB/s", color="white", width=width))
    lines.append(divider(width))
    lines.append(section_title("COMPACT HEALTH", width))
    trend = sparkline(
        state.health_history,
        width=max(8, min(12, width - 24)),
        fixed_min=0,
        fixed_max=100,
    )
    lines.append(key_value_line("Trend", trend, width, label_width=18))
    lines.append(metric_row("System Health", f"{metrics['system_health']}", "%", bar=percent_bar(metrics["system_health"], compact_bar, 80, 50, inverse=True), color=health_color, width=width))
    lines.append(render_health_why_line(health_why_with_limit(metrics["health_why"], 2), width))
    lines.append(key_value_line(colorize("Profile ", "dim"), colorize("Compact monitoring", "dim"), width))

def render_dashboard(metrics, state, view, refresh_interval):
    terminal_width = shutil.get_terminal_size((88, 24)).columns
    compact = view["compact"] or terminal_width < 72
    if view.get("mode") == "minimal":
        max_width = 74
    elif view.get("mode") == "compact":
        max_width = 76
    else:
        max_width = 86
    width = min(max(2, terminal_width - 2), max_width)
    bar_width = choose_bar_width(width, compact, view.get("bar_profile", "normal"))
    effective_view = view.copy()

    if width < 72:
        effective_view["show_cores"] = False
    if width < 64:
        effective_view["show_io_details"] = False
        effective_view["show_net_details"] = False

    lines = []
    render_top_panel(lines, width, metrics, refresh_interval)
    if view.get("mode") == "minimal":
        render_minimal_dashboard(lines, metrics, state, width, bar_width, effective_view)
        lines.append("╰" + "─" * (width - 0) + "╯")
        return "\n".join(lines)
    if view.get("mode") == "compact":
        render_compact_dashboard(lines, metrics, state, width, bar_width)
        lines.append("╰" + "─" * (width - 0) + "╯")
        return "\n".join(lines)

    lines.append(section_title("CPU / THERMAL", width))
    cpu_badge = status_badge(metrics["cpu_load"], CPU_THRESHOLD_LOW, CPU_THRESHOLD_MEDIUM)
    lines.append(metric_row(
        "CPU Load",
        f"{metrics['cpu_load']:.1f}",
        "%",
        bar=percent_bar(metrics["cpu_load"], bar_width, CPU_THRESHOLD_LOW, CPU_THRESHOLD_MEDIUM),
        badge=cpu_badge,
        color=cpu_badge[1],
        width=width,
    ))
    if effective_view["show_cores"]:
        lines.append(render_core_line(metrics["core_loads"], width))

    if metrics["temperature"] is None:
        lines.append(metric_row("CPU Temp", "N/A", width=width))
    else:
        temp_badge = status_badge(metrics["temperature"], metrics["temp_warning"], metrics["temp_critical"])
        lines.append(metric_row(
            "CPU Temp",
            f"{metrics['temperature']:.1f}",
            "°C",
            badge=temp_badge,
            color=temp_badge[1],
            width=width,
        ))
    if view.get("mode") == "doctor":
        cpu_trend = sparkline(list(state.history["cpu"]), width=max(8, min(16, width - 24)))
        ram_trend = sparkline(list(state.history["ram"]), width=max(8, min(16, width - 24)))
        lines.append(key_value_line("CPU Trend", cpu_trend, width))
        lines.append(key_value_line("RAM Trend", ram_trend, width))

    freq_value, freq_unit, freq_color = format_frequency(metrics["frequency"])
    lines.append(metric_row("ARM Freq", freq_value, freq_unit, color=freq_color, width=width))
    if effective_view["show_uptime"]:
        lines.append(metric_row("Uptime", metrics["uptime"], width=width))
    if effective_view["show_load_average"]:
        lines.append(metric_row(
            "Load Avg",
            f"{metrics['load_avg'][0]:.2f} / {metrics['load_avg'][1]:.2f} / {metrics['load_avg'][2]:.2f}",
            "1/5/15",
            color="white",
            width=width,
        ))

    lines.append(divider(width))
    mem_title = "MEMORY / STORAGE" if view.get("mode") != "compact" else "COMPACT MEMORY / STORAGE"
    lines.append(section_title(mem_title, width))
    mem_badge = status_badge(metrics["mem_percent"], 70, 90)
    lines.append(metric_row(
        "RAM Usage",
        f"{metrics['mem_percent']:.1f}",
        "%",
        bar=percent_bar(metrics["mem_percent"], bar_width, 70, 90),
        badge=mem_badge,
        color=mem_badge[1],
        width=width,
    ))
    if effective_view["show_swap"]:
        swap_badge = status_badge(metrics["swap_percent"], 40, 75)
        lines.append(metric_row(
            "Swap Usage",
            f"{metrics['swap_percent']:.1f}",
            "%",
            bar=percent_bar(metrics["swap_percent"], bar_width, 40, 75),
            badge=swap_badge,
            color=swap_badge[1],
            width=width,
        ))
    disk_badge = status_badge(metrics["disk_usage"], 80, 95)
    lines.append(metric_row(
        "Disk Usage",
        f"{metrics['disk_usage']:.1f}",
        "%",
        bar=percent_bar(metrics["disk_usage"], bar_width, 80, 95),
        badge=disk_badge,
        color=disk_badge[1],
        width=width,
    ))
    if effective_view["show_io_details"]:
        lines.append(metric_row("Disk Read", f"{metrics['disk_read_per_sec']:.2f}", "KiB/s", color="magenta", width=width))
        lines.append(metric_row("Disk Write", f"{metrics['disk_write_per_sec']:.2f}", "KiB/s", color="magenta", width=width))

    lines.append(divider(width))
    net_title = "NETWORK" if view.get("mode") != "compact" else "COMPACT NETWORK"
    lines.append(section_title(net_title, width))
    if effective_view["show_net_details"]:
        lines.append(metric_row("Sent", f"{metrics['network_sent_per_sec']:.2f}", "KiB/s", color="white", width=width))
        lines.append(metric_row("Received", f"{metrics['network_recv_per_sec']:.2f}", "KiB/s", color="white", width=width))
    lines.append(metric_row("Net Total", f"{metrics['network_sent_per_sec'] + metrics['network_recv_per_sec']:.2f}", "KiB/s", color="white", width=width))
    if view.get("mode") == "doctor":
        net_trend = sparkline(list(state.history["net"]), width=max(8, min(16, width - 24)))
        lines.append(key_value_line("Net Trend", net_trend, width))

    lines.append(divider(width))
    lines.append(section_title("POWER / HEALTH", width))
    if effective_view["show_power_details"] is True:
        render_power_rows(lines, metrics, state, width)
    elif effective_view["show_power_details"] == "warning_only" and has_power_warning(metrics["throttle"], state.throttle_occurred_latch):
        render_power_rows(lines, metrics, state, width)

    trend_width = choose_trend_width(width, effective_view.get("health_trend_width", "normal"))
    if trend_width > 0:
        trend = sparkline(
            list(state.history["health"]),
            width=trend_width,
            fixed_min=0,
            fixed_max=100,
        )
        lines.append(key_value_line("Health Trend", trend, width, label_width=34))
    if metrics["temperature"] is not None and view.get("mode") in ("balanced", "doctor"):
        temp_trend = sparkline(list(state.history["temp"]), width=max(8, min(16, width - 24)))
        lines.append(key_value_line("Temp Trend", temp_trend, width))
    health_badge = status_badge(metrics["system_health"], 80, 50, inverse=True)
    lines.append(metric_row(
        "System Health",
        f"{metrics['system_health']}",
        "%",
        bar=percent_bar(metrics["system_health"], bar_width, 80, 50, inverse=True),
        badge=health_badge,
        color=health_badge[1],
        width=width,
    ))
    if effective_view["show_storage_health"]:
        storage_badge = status_badge(metrics["storage_health"], 80, 50, inverse=True)
        lines.append(metric_row(
            "Storage Health",
            f"{metrics['storage_health']}",
            "%",
            bar=percent_bar(metrics["storage_health"], bar_width, 80, 50, inverse=True),
            badge=storage_badge,
            color=storage_badge[1],
            width=width,
        ))
    stability_badge = status_badge(metrics["system_stability"], 80, 50, inverse=True)
    lines.append(render_health_why_line(health_why_with_limit(metrics["health_why"], effective_view.get("health_why_limit", 3)), width))
    if effective_view["show_stability_avg"]:
        lines.append(metric_row(
            "Stability Avg",
            f"{metrics['system_stability']:.1f}",
            "%",
            bar=percent_bar(metrics["system_stability"], bar_width, 80, 50, inverse=True),
            badge=stability_badge,
            color=stability_badge[1],
            width=width,
        ))
    if view.get("mode") == "doctor":
        lines.append(divider(width))
        lines.append(section_title("DOCTOR INSIGHT", width))
        doctor_pairs = [
            ("Cooling", metrics["cooling_status"], "Power", metrics["power_stability"]),
            ("Workload", metrics["workload_profile"], "Storage", metrics["storage_insight"]),
            ("System", f"{metrics['pi_model']} [{metrics['thermal_profile_name']}]", "Arch", metrics["architecture"]),
            ("Total RAM", f"{metrics['total_ram_gb']:.1f} GiB", "Alerts", f"{len(metrics.get('active_alerts', []))}"),
        ]
        left_lengths = [len(f"{label:<9} {value}") for label, value, _, _ in doctor_pairs]
        right_lengths = [len(f"{label:<9} {value}") for _, _, label, value in doctor_pairs]
        max_left = max(left_lengths) if left_lengths else 20
        max_right = max(right_lengths) if right_lengths else 20
        total = max_left + max_right
        dynamic_ratio = (max_left / total) if total else 0.6
        dynamic_ratio = max(0.45, min(0.72, dynamic_ratio))
        for left_label, left_value, right_label, right_value in doctor_pairs:
            lines.append(doctor_dual_metric_row(left_label, left_value, right_label, right_value, width, left_ratio=dynamic_ratio))
        lines.append(metric_row("Top CPU Proc", metrics["top_cpu_process"], width=width))
        lines.append(metric_row("Top RAM Proc", metrics["top_mem_process"], width=width))
        active_alerts = metrics.get("active_alerts", [])
        alert_text = ", ".join(active_alerts[:3]) if active_alerts else "none"
        lines.append(metric_row("Active Alerts", alert_text, width=width))
    lines.append("╰" + "─" * (width - 0) + "╯")

    return "\n".join(lines)

def format_uptime(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours}h {minutes}m {secs}s"

def collect_metrics(state, boot_time):
    temperature, frequency, throttle = get_pi_stats()
    pi_model = detect_pi_model()
    thermal_profile_name, thermal_profile = thermal_profile_for_model(pi_model)
    mem_percent = psutil.virtual_memory().percent
    core_loads = psutil.cpu_percent(interval=None, percpu=True)

    if core_loads:
        cpu_load = sum(core_loads) / len(core_loads)
    else:
        cpu_load = 0.0
    disk_usage = psutil.disk_usage('/').percent  # Monitor root disk usage
    disk_read_per_sec, disk_write_per_sec = get_disk_io(state)
    network_sent_per_sec, network_recv_per_sec = get_network_usage(state)
    system_load_avg = get_system_load_average()
    swap_percent = get_swap_usage()

    system_health = calculate_system_health(
        cpu_load,
        temperature,
        mem_percent,
        disk_usage,
        throttle,
        thermal_profile
    )

    state.health_history.append(system_health)

    system_stability = (
        sum(state.health_history) / len(state.health_history)
        if state.health_history else 100
    )
    storage_health = calculate_storage_health(
        disk_usage,
        disk_write_per_sec
    )

    if throttle and (
        throttle.get("throttled")
        or throttle.get("undervoltage")
        or throttle.get("freq_capped")
        or throttle.get("soft_temp_limit")
        or throttle.get("undervoltage_occurred")
        or throttle.get("freq_capped_occurred")
        or throttle.get("throttling_occurred")
        or throttle.get("soft_temp_limit_occurred")
    ):
        state.throttle_occurred_latch = True

    net_total = network_sent_per_sec + network_recv_per_sec
    state.history["cpu"].append(cpu_load)
    state.history["ram"].append(mem_percent)
    state.history["net"].append(net_total)
    state.history["health"].append(system_health)
    if temperature is not None:
        state.history["temp"].append(temperature)

    top_cpu_process = state.last_top_cpu_process
    top_mem_process = "N/A"
    try:
        mem_procs = []
        cpu_procs = []
        for proc in psutil.process_iter(["name", "memory_percent", "cpu_percent"]):
            name = proc.info.get("name") or "unknown"
            mem_procs.append((name, proc.info.get("memory_percent") or 0.0))
            cpu = proc.info.get("cpu_percent")
            if cpu and cpu > 0:
                cpu_procs.append((name, cpu))
        if mem_procs:
            top_mem = max(mem_procs, key=lambda x: x[1])
            top_mem_process = f"{top_mem[0]} {top_mem[1]:.1f}%"
        if cpu_procs:
            top_cpu = max(cpu_procs, key=lambda x: x[1])
            top_cpu_process = f"{top_cpu[0]} {top_cpu[1]:.1f}%"
    except Exception:
        pass
    state.last_top_cpu_process = top_cpu_process

    metrics = {
        "temperature": temperature,
        "frequency": frequency,
        "throttle": throttle,
        "mem_percent": mem_percent,
        "core_loads": core_loads,
        "cpu_load": cpu_load,
        "disk_usage": disk_usage,
        "disk_read_per_sec": disk_read_per_sec,
        "disk_write_per_sec": disk_write_per_sec,
        "network_sent_per_sec": network_sent_per_sec,
        "network_recv_per_sec": network_recv_per_sec,
        "network_interface": state.network_interface,
        "load_avg": system_load_avg,
        "swap_percent": swap_percent,
        "system_health": system_health,
        "system_stability": system_stability,
        "storage_health": storage_health,
        "uptime": format_uptime(time.time() - boot_time),
        "health_why": health_explainability(cpu_load, temperature, mem_percent, disk_usage, throttle, thermal_profile["warning"]),
        "pi_model": pi_model,
        "thermal_profile_name": thermal_profile_name,
        "temp_warning": thermal_profile["warning"],
        "temp_critical": thermal_profile["critical"],
        "architecture": platform.machine(),
        "total_ram_gb": psutil.virtual_memory().total / (1024**3),
        "top_cpu_process": top_cpu_process,
        "top_mem_process": top_mem_process,
    }
    metrics["cooling_status"] = cooling_assessment(metrics)
    metrics["power_stability"] = power_stability_assessment(metrics, state)
    metrics["workload_profile"] = workload_profile(metrics)
    metrics["storage_insight"] = storage_insight(metrics)
    return metrics

def snapshot_to_text(metrics):
    plain = [
        "SystemPi Snapshot Report",
        "=======================",
    ]
    for key in sorted(metrics.keys()):
        plain.append(f"{key}: {metrics[key]}")
    return "\n".join(plain)

def export_snapshot(metrics, export_format, output_path):
    if export_format == "json":
        payload = json.dumps(metrics, indent=2, sort_keys=True, default=str)
    else:
        payload = snapshot_to_text(metrics)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(payload + "\n")

def parse_args():
    parser = argparse.ArgumentParser(description="systempi realtime dashboard")
    parser.add_argument("--compact", action="store_true", help="smaller layout for narrow terminals")
    parser.add_argument("--theme", choices=sorted(THEMES.keys()), default="default", help="color theme")
    parser.add_argument("--refresh", type=float, default=1.0, help="refresh interval in seconds (example: 0.5)")
    parser.add_argument("--interface", help="network interface to monitor (example: eth0, wlan0)")
    parser.add_argument("--no-color", action="store_true", help="disable ANSI colors")
    parser.add_argument("--once", action="store_true", help="render one snapshot and exit")
    parser.add_argument("--export", choices=["text", "json"], help="export once snapshot to file")
    parser.add_argument("--output", help="export output path for --once")
    parser.add_argument("--watch", action="store_true", help="enable background alert event logging")
    parser.add_argument("--history", action="store_true", help="print recent alert event history and exit")
    parser.add_argument(
        "--variation",
        choices=sorted(VARIATIONS.keys()),
        default="balanced",
        help=(
            "dashboard layout variation: balanced (full default dashboard), "
            "compact (same style, smaller terminal friendly), "
            "minimal (clean essential-only mode), doctor (diagnostic-focused mode)"
        ),
    )
    args = parser.parse_args()
    if args.refresh <= 0:
        parser.error("--refresh must be greater than 0")
    if args.export and not args.once:
        parser.error("--export requires --once")
    if args.export and not args.output:
        parser.error("--output is required when using --export")
    return args

def main():
    args = parse_args()

    if args.no_color:
        disable_colors()
    else:
        apply_theme(args.theme)

    view = resolve_view_config(args)
    boot_time = psutil.boot_time()
    state = SystemState(interface=args.interface)
    if args.watch:
        prepare_event_log(state)
    if args.history:
        if state.event_log_path.exists():
            lines = state.event_log_path.read_text(encoding="utf-8").splitlines()[-40:]
            print("\n".join(lines) if lines else "No event history yet.")
        else:
            print("No event history yet.")
        return

    if args.interface:
        interfaces = psutil.net_io_counters(pernic=True)
        if args.interface not in interfaces:
            available = ", ".join(sorted(interfaces.keys())) or "none"
            print(
                f"error: interface '{args.interface}' not found. Available interfaces: {available}",
                file=sys.stderr,
            )
            sys.exit(2)

    renderer = TerminalRenderer()

    psutil.cpu_percent(interval=None)

    if not args.once:
        renderer.start()

    try:
        while True:
            metrics = collect_metrics(state, boot_time)
            metrics["active_alerts"] = evaluate_alerts(metrics)
            if args.watch:
                log_alert_events(state, metrics["active_alerts"])
            state.active_alerts = metrics["active_alerts"]
            frame = render_dashboard(
                metrics,
                state,
                view=view,
                refresh_interval=args.refresh,
            )

            if args.once:
                print(frame)
                if args.export:
                    export_snapshot(metrics, args.export, args.output)
            else:
                renderer.render(frame)

            if args.once:
                break

            time.sleep(args.refresh)

    finally:
        if not args.once:
            cleanup_terminal(renderer)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
