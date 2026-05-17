#!/usr/bin/env python3

import os
import re
import shutil
import subprocess
import time
import psutil

# Constants
TEMP_WARNING = 60
TEMP_CRITICAL = 75
CPU_THRESHOLD_LOW = 60
CPU_THRESHOLD_MEDIUM = 85
RESET = "\033[0m"
COLORS = {
    "green": "\033[92m",
    "yellow": "\033[93m",
    "red": "\033[91m",
    "cyan": "\033[96m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "white": "\033[97m",
    "bold_cyan": "\033[96;1m",
    "dim": "\033[2m",
}

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
            text=True
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
            "throttled": bool(value & 0x1),
            "freq_capped": bool(value & 0x2),
            "undervoltage": bool(value & 0x10000),
            "throttling_occurred": bool(value & 0x20000)
        }

        return temperature, frequency, throttle

    except Exception as e:
        print(f"Error retrieving Pi stats: {e}")
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

    except Exception as e:
        print(f"Error retrieving network usage: {e}")
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

    except Exception as e:
        print(f"Error retrieving disk I/O stats: {e}")
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

def cleanup_terminal():
    print("\033[?25h", end="")      # restore cursor
    print("\033[H\033[J", end="", flush=True)    # clear screen

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
    return panel_line(colorize(title, "bold_cyan"), width)

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

def render_dashboard(metrics, state):
    terminal_width = shutil.get_terminal_size((88, 24)).columns
    width = max(72, min(terminal_width, 86))
    bar_width = 18 if width < 86 else 24

    lines = []
    lines.append("╭" + "─" * (width - 0) + "╮")
    title = colorize("SYSTEMPI v2.1 Dashboard", "bold_cyan")
    subtitle = f"Interface: {metrics['network_interface'] or 'N/A'} | Refresh: 1s"
    title_padding = max(1, width - 4 - len(strip_ansi(title)) - len(subtitle))
    lines.append(panel_line(f"{title}{' ' * title_padding}{COLORS['dim']}{subtitle}{RESET}", width))
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
    lines.append(metric_row("Disk Read", f"{metrics['disk_read_per_sec']:.2f}", "KiB/s", color="magenta", width=width))
    lines.append(metric_row("Disk Write", f"{metrics['disk_write_per_sec']:.2f}", "KiB/s", color="magenta", width=width))

    lines.append(divider(width))
    lines.append(section_title("NETWORK", width))
    lines.append(metric_row("Sent", f"{metrics['network_sent_per_sec']:.2f}", "KiB/s", color="white", width=width))
    lines.append(metric_row("Received", f"{metrics['network_recv_per_sec']:.2f}", "KiB/s", color="white", width=width))
    lines.append(metric_row("Total", f"{metrics['network_sent_per_sec'] + metrics['network_recv_per_sec']:.2f}", "KiB/s", color="white", width=width))

    lines.append(divider(width))
    lines.append(section_title("POWER / HEALTH", width))
    throttle = metrics["throttle"]
    if throttle is None:
        lines.append(metric_row("Throttled", "N/A", width=width))
        lines.append(metric_row("Occurred", "N/A", width=width))
        lines.append(metric_row("Undervoltage", "N/A", width=width))
    else:
        throttle_color = "red" if throttle["throttled"] else "green"
        occurred_color = "red" if state.throttle_occurred_latch else "green"
        undervolt_color = "red" if throttle["undervoltage"] else "green"
        lines.append(metric_row("Throttled", "YES" if throttle["throttled"] else "NO", color=throttle_color, width=width))
        lines.append(metric_row("Occurred", "YES" if state.throttle_occurred_latch else "NO", color=occurred_color, width=width))
        lines.append(metric_row("Undervoltage", "YES" if throttle["undervoltage"] else "NO", color=undervolt_color, width=width))

    trend = sparkline(state.health_history, width=24 if width >= 86 else 16)
    lines.append(panel_line(f"Health Trend{' ' * 22}{trend}", width))
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

def main():
    boot_time = psutil.boot_time()
    state = SystemState()

    psutil.cpu_percent(interval=None)
    print("\033[?25l", end="", flush=True)  # hide cursor while dashboard is active

    while True:
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
            or throttle.get("throttling_occurred")
        ):
            state.throttle_occurred_latch = True

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
        }

        print("\033[H\033[J", end="", flush=True)
        print(render_dashboard(metrics, state), flush=True)

        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        cleanup_terminal()
