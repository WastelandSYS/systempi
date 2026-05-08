#!/usr/bin/env python3

import os
import subprocess
import time
import psutil

# Constants
TEMP_WARNING = 60
TEMP_CRITICAL = 75

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
    except:
        return (0.0, 0.0, 0.0)

def colored_core(value):
    blocks = "▁▂▃▄▅▆▇█"

    if value < 60:
        color = "\033[92m"  # green
    elif value < 85:
        color = "\033[93m"  # yellow
    else:
        color = "\033[91m"  # red

    index = int((value / 100) * (len(blocks) - 1))
    return f"{color}{blocks[index]}\033[0m"

def cleanup_terminal():
    print("\033[?25h", end="")      # restore cursor
    print("\033[H\033[J", end="", flush=True)    # clear screen

def get_swap_usage():
    try:
        return psutil.swap_memory().percent
    except:
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
    except:
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

CPU_THRESHOLD_LOW = 60
CPU_THRESHOLD_MEDIUM = 85

def main():
    boot_time = psutil.boot_time()
    state = SystemState()
    
    psutil.cpu_percent(interval=None)

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

        if temperature is None:
            color_code_temp = "\033[0m"
        else:
            color_code_temp = (
                "\033[92m" if temperature < TEMP_WARNING else
                "\033[93m" if temperature < TEMP_CRITICAL else
                "\033[91m"
        )
        color_code_freq = "\033[96m"
        color_code_mem = "\033[94m"
        color_code_disk = "\033[95m"
        color_code_net = "\033[97m"
        color_code_systempi = "\033[96;1m"  # Box Color with Nameplate
        color_code_load_avg = "\033[0m"  # Default color
        color_code_numbers = "\033[91m"  # Red color for numbers

        uptime = time.time() - boot_time
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        seconds = int(uptime % 60)

        print("\033[H\033[J", end="", flush=True)

        # ASCII Box
        box_top = f"{color_code_systempi}{'='*31}\033[0m"
        box_bottom = f"{color_code_systempi}{'='*31}\033[0m"

        print(box_top)
        print(f"{color_code_systempi}   SYSTEMPI - v2 - Dashboard \033[0m")
        print(box_top)

        color_code_cpu = (
    "\033[92m" if cpu_load < CPU_THRESHOLD_LOW else
    "\033[93m" if cpu_load < CPU_THRESHOLD_MEDIUM else
    "\033[91m"
)         
        print(f"  CPU load = {color_code_cpu}{cpu_load:.1f}%\033[0m")   
        if core_loads:
            core_str = " ".join(colored_core(c or 0) for c in core_loads)
            print(f"  CPU cores = {core_str}")            
        if temperature is None:
            print("  CPU temp = N/A")
        else:
            print(f"  CPU temp = {color_code_temp}{temperature:.1f}\033[0m °C")
        print(f"  MEM usage = {color_code_mem}{mem_percent:.1f}%\033[0m")
        print(f"  Disk usage = {color_code_disk}{disk_usage:.1f}%\033[0m")
        print(f"  Disk read = {color_code_disk}{disk_read_per_sec:.2f} KiB/s\033[0m")
        print(f"  Disk write = {color_code_disk}{disk_write_per_sec:.2f} KiB/s\033[0m")
        if frequency is None:
            print("  ARM freq = N/A")
        else:
            print(f"  ARM freq = {color_code_freq}{frequency}\033[0m Hz")
        print(f"  Uptime = {hours}h {minutes}m {seconds}s")
        
        # Modified line for load average
        load_avg_str = f"  Load average:\n    1m = {color_code_numbers}{round(system_load_avg[0], 2)}\033[0m\n    5m = {color_code_numbers}{round(system_load_avg[1], 2)}\033[0m\n   15m = {color_code_numbers}{round(system_load_avg[2], 2)}\033[0m"
        print(f"{color_code_load_avg}{load_avg_str}")
        
        print(f"  Swap usage = {color_code_disk}{swap_percent:.1f}%\033[0m")
        print(f"  Network:")
        print(f"    Sent = {color_code_net}{network_sent_per_sec:.2f} KiB/s\033[0m")
        print(f"    Received = {color_code_net}{network_recv_per_sec:.2f} KiB/s\033[0m")
        print(f"    Total = {color_code_net}{network_sent_per_sec + network_recv_per_sec:.2f} KiB/s\033[0m")

        print(f"  Throttle:")

        if throttle is None:
            print("    Active = N/A")
            print("    Occurred = N/A")
            print("    Undervoltage = N/A")
        else:
            color_code_warn = "\033[91m" if throttle['throttled'] or throttle['undervoltage'] else "\033[92m"
       
            if (
                throttle.get("throttled")
                or throttle.get("undervoltage")
                or throttle.get("freq_capped")
                or throttle.get("throttling_occurred")
            ):
                state.throttle_occurred_latch = True

            print(f"    Active = {color_code_warn}{'YES' if throttle['throttled'] else 'NO'}\033[0m")
            print(f"    Occurred = {color_code_warn}{'YES' if state.throttle_occurred_latch else 'NO'}\033[0m")
            print(f"    Undervoltage = {color_code_warn}{'YES' if throttle['undervoltage'] else 'NO'}\033[0m")

        # System Health Display
        if system_health >= 80:
            system_health_color = "\033[92m"
        elif system_health >= 50:
            system_health_color = "\033[93m"
        else:
            system_health_color = "\033[91m"

        print(f"  System Health = {system_health_color}{system_health}%\033[0m")
        
        # Storage Health Display
        if storage_health >= 80:
            storage_health_color = "\033[92m"
        elif storage_health >= 50:
            storage_health_color = "\033[93m"
        else:
            storage_health_color = "\033[91m"

        print(f"  Storage Health = {storage_health_color}{storage_health}%\033[0m")

        if system_stability >= 80:
            stability_color = "\033[92m"
        elif system_stability >= 50:
            stability_color = "\033[93m"
        else:
            stability_color = "\033[91m"

        print(f"  Stability Avg = {stability_color}{system_stability:.1f}%\033[0m")

        print(box_bottom)
        
        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        cleanup_terminal()
