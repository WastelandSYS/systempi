#!/usr/bin/env python3

import argparse
import os
import re
import shutil
import subprocess
import sys
import time

import psutil

# Constants
TEMP_WARNING = 60
TEMP_CRITICAL = 75
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
        "dim": "\033[2m",
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
        "dim": "\033[2m",
    },
    "ocean": {
        "green": "\033[38;5;86m",
        "yellow": "\033[38;5;117m",
        "red": "\033[38;5;203m",
        "cyan": "\033[38;5;51m",
        "blue": "\033[38;5;39m",
        "magenta": "\033[38;5;99m",
        "white": "\033[97m",
        "bold_cyan": "\033[38;5;51;1m",
        "dim": "\033[2m",
    },
    "matrix": {
        "green": "\033[38;5;46m",
        "yellow": "\033[38;5;118m",
        "red": "\033[38;5;196m",
        "cyan": "\033[38;5;82m",
        "blue": "\033[38;5;40m",
        "magenta": "\033[38;5;34m",
        "white": "\033[38;5;120m",
        "bold_cyan": "\033[38;5;46;1m",
        "dim": "\033[2m",
    },
    "lava": {
        "green": "\033[38;5;208m",
        "yellow": "\033[38;5;220m",
        "red": "\033[38;5;196m",
        "cyan": "\033[38;5;202m",
        "blue": "\033[38;5;130m",
        "magenta": "\033[38;5;166m",
        "white": "\033[38;5;230m",
        "bold_cyan": "\033[38;5;214;1m",
        "dim": "\033[38;5;240m",
    },
    "mono": {
        "green": "\033[97m",
        "yellow": "\033[37m",
        "red": "\033[1;97m",
        "cyan": "\033[37m",
        "blue": "\033[90m",
        "magenta": "\033[97m",
        "white": "\033[97m",
        "bold_cyan": "\033[1;97m",
        "dim": "\033[2m",
    },
}

COLORS = THEMES["default"].copy()


def apply_theme(theme_name):
    global COLORS
    COLORS = THEMES.get(theme_name, THEMES["default"]).copy()

class SystemState:
    def __init__(self):
        self.prev_sent = 0
        self.prev_recv = 0
        self.prev_disk_read = 0
        self.prev_disk_write = 0
        self.health_history = []
        self.network_interface = None
        self.last_net_time = time.time()
        self.last_disk_time = time.time()
        self.throttle_occurred_latch = False

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

def sparkline(values, width=24):
    if not values:
        return ""

    samples = values[-width:]
    blocks = "▁▂▃▄▅▆▇█"
    low = min(samples)
    high = max(samples)

    if high == low:
        return colorize(blocks[-1] * len(samples), "green")

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

def calculate_system_health(cpu, temp, mem, disk, throttle):
    health = 100.0

    # CPU (continuous penalty)
    cpu_pressure = max(0, cpu - 5)
    health -= cpu_pressure * 0.4

    # Temperature (only above safe zone)
    if temp is not None:
        temp_excess = max(0, temp - 50)
        health -= temp_excess * 1.2

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

def health_explainability(cpu, temp, mem, disk, throttle):
    reasons = []
    if cpu > 80:
        reasons.append(f"CPU pressure {cpu:.1f}%")
    if temp is not None and temp > TEMP_WARNING:
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
    "balanced": {"compact": False, "show_cores": True, "show_io_details": True, "show_net_details": True},
    "compact": {"compact": True, "show_cores": False, "show_io_details": False, "show_net_details": False},
    "minimal": {"compact": True, "show_cores": False, "show_io_details": False, "show_net_details": False},
    "insight": {"compact": False, "show_cores": True, "show_io_details": True, "show_net_details": True},
}


def resolve_view_config(args):
    view = VARIATIONS[args.variation].copy()
    if args.compact:
        view["compact"] = True
    return view


def render_dashboard(metrics, state, view):
    terminal_width = shutil.get_terminal_size((88, 24)).columns
    compact = view["compact"] or terminal_width < 72
    max_width = 78 if compact else 86
    width = min(max(2, terminal_width - 2), max_width)
    preferred_bar_width = 16 if compact else (20 if width < 86 else 28)
    max_bar_width = max(4, width - 46)
    bar_width = max(4, min(preferred_bar_width, max_bar_width))
    effective_view = view.copy()

    if width < 72:
        effective_view["show_cores"] = False
    if width < 64:
        effective_view["show_io_details"] = False
        effective_view["show_net_details"] = False

    lines = []
    lines.append("╭" + "─" * (width - 0) + "╮")
    title = colorize("SYSTEMPI v2.1 Dashboard", "bold_cyan")
    subtitle = f"Interface: {metrics['network_interface'] or 'N/A'} | Refresh: 1s"
    title_padding = max(1, width - 4 - len(strip_ansi(title)) - len(subtitle))
    header = f"{title}{' ' * title_padding}{COLORS['dim']}{subtitle}{RESET}"
    lines.append(panel_line(truncate_display(header, width - 4), width))
    lines.append(divider(width))

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
        temp_badge = status_badge(metrics["temperature"], TEMP_WARNING, TEMP_CRITICAL)
        lines.append(metric_row(
            "CPU Temp",
            f"{metrics['temperature']:.1f}",
            "°C",
            badge=temp_badge,
            color=temp_badge[1],
            width=width,
        ))

    freq_value, freq_unit, freq_color = format_frequency(metrics["frequency"])
    lines.append(metric_row("ARM Freq", freq_value, freq_unit, color=freq_color, width=width))
    lines.append(metric_row("Uptime", metrics["uptime"], width=width))
    lines.append(metric_row(
        "Load Avg",
        f"{metrics['load_avg'][0]:.2f} / {metrics['load_avg'][1]:.2f} / {metrics['load_avg'][2]:.2f}",
        "1/5/15",
        color="white",
        width=width,
    ))

    lines.append(divider(width))
    lines.append(section_title("MEMORY / STORAGE", width))
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
    lines.append(section_title("NETWORK", width))
    if effective_view["show_net_details"]:
        lines.append(metric_row("Sent", f"{metrics['network_sent_per_sec']:.2f}", "KiB/s", color="white", width=width))
        lines.append(metric_row("Received", f"{metrics['network_recv_per_sec']:.2f}", "KiB/s", color="white", width=width))
    lines.append(metric_row("Net Total", f"{metrics['network_sent_per_sec'] + metrics['network_recv_per_sec']:.2f}", "KiB/s", color="white", width=width))

    lines.append(divider(width))
    lines.append(section_title("POWER / HEALTH", width))
    throttle = metrics["throttle"]
    if throttle is None:
        lines.append(metric_row("Throttled", "N/A", width=width))
        lines.append(metric_row("Freq Capped", "N/A", width=width))
        lines.append(metric_row("Occurred", "N/A", width=width))
        lines.append(metric_row("Undervoltage", "N/A", width=width))
    else:
        throttle_color = "red" if throttle["throttled"] else "green"
        freq_capped_color = "yellow" if throttle["freq_capped"] else "green"
        occurred_color = "red" if state.throttle_occurred_latch else "green"
        undervolt_color = "red" if throttle["undervoltage"] else "green"
        lines.append(metric_row("Throttled", "YES" if throttle["throttled"] else "NO", color=throttle_color, width=width))
        lines.append(metric_row("Freq Capped", "YES" if throttle["freq_capped"] else "NO", color=freq_capped_color, width=width))
        lines.append(metric_row("Occurred", "YES" if state.throttle_occurred_latch else "NO", color=occurred_color, width=width))
        lines.append(metric_row("Undervoltage", "YES" if throttle["undervoltage"] else "NO", color=undervolt_color, width=width))

    preferred_trend_width = 20 if width < 86 else 28
    trend_width = max(4, min(preferred_trend_width, width - 22))
    trend = sparkline(state.health_history, width=trend_width)
    lines.append(panel_line(truncate_display(f"Health Trend{' ' * 22}{trend}", width - 4), width))
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
    lines.append(render_health_why_line(metrics["health_why"], width))
    lines.append(metric_row(
        "Stability Avg",
        f"{metrics['system_stability']:.1f}",
        "%",
        bar=percent_bar(metrics["system_stability"], bar_width, 80, 50, inverse=True),
        badge=stability_badge,
        color=stability_badge[1],
        width=width,
    ))
    lines.append("╰" + "─" * (width - 0) + "╯")

    return "\n".join(lines)

def format_uptime(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours}h {minutes}m {secs}s"

def collect_metrics(state, boot_time):
    temperature, frequency, throttle = get_pi_stats()
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
        throttle
    )

    state.health_history.append(system_health)

    if len(state.health_history) > 60:
        state.health_history.pop(0)

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

    return {
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
        "health_why": health_explainability(cpu_load, temperature, mem_percent, disk_usage, throttle),
    }

def parse_args():
    parser = argparse.ArgumentParser(description="systempi realtime dashboard")
    parser.add_argument("--compact", action="store_true", help="smaller layout for narrow terminals")
    parser.add_argument("--theme", choices=sorted(THEMES.keys()), default="default", help="color theme")
    parser.add_argument("--variation", choices=sorted(VARIATIONS.keys()), default="balanced", help="dashboard layout variation")
    return parser.parse_args()

def main():
    args = parse_args()
    apply_theme(args.theme)
    view = resolve_view_config(args)
    boot_time = psutil.boot_time()
    state = SystemState()
    renderer = TerminalRenderer()

    psutil.cpu_percent(interval=None)
    renderer.start()

    try:
        while True:
            metrics = collect_metrics(state, boot_time)
            renderer.render(render_dashboard(metrics, state, view=view))
            time.sleep(1)
    finally:
        cleanup_terminal(renderer)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
