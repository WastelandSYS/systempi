<img width="1536" height="1024" alt="SystemPI Image May 11, 2026, 01_48_44 AM" src="https://github.com/user-attachments/assets/02229b07-af74-4bc4-9f3d-37cb8799fb77" />




<table>
  <tr>
<img width="828" height="662" alt="systempi101" src="https://github.com/user-attachments/assets/be4ac555-3395-4379-ad7c-2addd471b192" />
 </tr>
</table>







DEPENDANCIES

This tool is currently designed for Raspberry Pi systems, as it relies on vcgencmd for hardware level metrics such as temperature, frequency, and throttling. It is intended for use on Raspberry Pi OS or Kali Linux running on a Pi device.

It requires psutil for system monitoring (CPU, memory, disk, and network statistics). This dependency is automatically installed via install.sh.

Future updates may expand compatibility to non-Raspberry Pi systems where equivalent hardware metrics are available.

-------------------------------

DESCRIPTION


systempi is real time system monitoring dashboard designed for Raspberry Pi devices and Kali Linux systems written in Python. It combines `vcgencmd`, `psutil`, and low-level system metrics to deliver live insights into CPU performance, temperature, memory, disk I/O, network activity, and system load.

Beyond basic monitoring, it features an advanced system health engine that calculates dynamic health, storage condition, and stability trends, along with detection of throttling and undervoltage events. The output is presented in a structured ASCII dashboard with color coded indicators for quick visual interpretation of system state and performance.


-------------------------------
🧠 Core System Monitoring
* CPU Load (Per-Core + Average) – Real-time overall CPU usage plus individual core activity visualization.
* CPU Temperature Monitoring – Live temperature reading from vcgencmd with warning and critical thresholds.
* Memory Usage (RAM) – Percentage of system RAM currently in use.
* Swap Usage – Tracks swap memory utilization for pressure detection.
* Disk Usage (Root FS) – Overall storage consumption of the main filesystem.

⚙️ Performance & Hardware Telemetry
* ARM CPU Frequency Monitoring – Real time processor clock speed in Hz.
* Disk I/O Rates – Live read/write throughput in KiB/s (delta-based calculation).
* System Load Average (1m / 5m / 15m) – Kernel load tracking for short and long term system stress.
* Uptime Tracking – System runtime displayed in readable format.

🌐 Network Monitoring
* Live Network Throughput – Sent and received bandwidth in KiB/s.
* Automatic Network Interface Detection – Dynamically selects active interface (excluding loopback).
* Per-Second Network Rate Calculation – Accurate delta based bandwidth measurement over time.

⚠️ Thermal & Throttling Intelligence
* CPU Throttling Detection – Detects active throttling events via vcgencmd.
* Undervoltage Detection – Identifies power instability conditions.
* Frequency Capping Detection – Flags performance limiting states.
* Throttling Event Latch (History Tracking) – Remembers if throttling has ever occurred during runtime (persistent state flag).

🧮 System Health Engine (Advanced)
* System Health Score (0–100) – Dynamic weighted scoring system based on:
* CPU pressure
* Temperature stress
* Memory usage
* Disk usage
* Throttling / undervoltage events
* Storage Health Score – Separate health metric based on disk usage + write intensity.
* System Stability Average – Rolling average of system health over time (trend-based stability indicator).

📊 Visualization & UI Layer
* ASCII Dashboard Interface – Real time terminal UI with boxed layout.
* Color Coded Metrics System – Green / Yellow / Red scaling for all major stats.
* Per-Core CPU Bar Visualization – Graph-style blocks showing per-core load intensity.
* Colored Load Scaling Bars – Visual CPU intensity representation using block gradients.

🧩 System Behavior & Architecture
* Stateful Monitoring Engine – Persistent runtime state tracking (network, disk, throttling, history).
* Delta-Based Sampling System – Accurate per-second calculations for disk and network metrics.
* Boot time Tracking – Uses system boot timestamp for uptime calculation.
* Graceful Terminal Cleanup – Restores cursor and clears UI cleanly on exit (Ctrl+C safe handling).
* Real time Refresh Loop (1s interval) – Continuous live monitoring update cycle.
-------------------------------

INSTALLATION & USAGE


Git clone installation:

1. 'git clone https://github.com/WastelandSYS/systempi.git'
2. 'cd systempi'
3. 'chmod +x install.sh systempi.py'
4. 'sudo ./install.sh'
5. Exit and open a new terminal to use 'systempi' shortcut

 
-------------------------------

This script was made and tested on an RPI 4b running a kali linux arm.
