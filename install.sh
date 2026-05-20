#!/bin/bash

set -euo pipefail

SYSTEMPI_BIN="/usr/local/bin/systempi"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYSTEMPI_SCRIPT="$REPO_DIR/systempi.py"

show_help() {
    cat <<HELP
SystemPi installer

Usage:
  sudo ./install.sh

This installer targets Debian-family systems including Raspberry Pi OS and
Kali Linux ARM. It installs Python runtime dependencies and sets up a global
'systempi' command in /usr/local/bin.
HELP
}

for arg in "$@"; do
    case "$arg" in
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $arg"
            echo "Run './install.sh --help' for usage."
            exit 1
            ;;
    esac
done

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root:"
    echo "sudo ./install.sh"
    exit 1
fi

if [ ! -f "$SYSTEMPI_SCRIPT" ]; then
    echo "Error: systempi.py not found in: $REPO_DIR"
    echo "Run this installer from the SystemPi repository folder."
    exit 1
fi

if [ ! -f "$REPO_DIR/requirements.txt" ]; then
    echo "Error: requirements.txt not found in: $REPO_DIR"
    exit 1
fi

if ! command -v apt-get >/dev/null 2>&1; then
    echo "Error: apt-get not found. install.sh supports Raspberry Pi OS / Debian / Kali ARM style systems."
    exit 1
fi

apt-get update
apt-get install -y python3 python3-pip python3-psutil

# Raspberry Pi tooling package name differs across distros/repos.
if apt-cache show libraspberrypi-bin >/dev/null 2>&1; then
    apt-get install -y libraspberrypi-bin
elif apt-cache show raspberrypi-utils >/dev/null 2>&1; then
    apt-get install -y raspberrypi-utils
else
    echo "Info: No Raspberry Pi vcgencmd package found in apt repositories on this system."
    echo "      SystemPi will still run; Pi-specific telemetry may show as unavailable."
fi

# Install Python dependencies from requirements.txt.
# Debian/Kali can enforce externally-managed Python; use fallback if needed.
if ! python3 -m pip install -r "$REPO_DIR/requirements.txt"; then
    python3 -m pip install --break-system-packages -r "$REPO_DIR/requirements.txt"
fi

chmod +x "$SYSTEMPI_SCRIPT"
ln -sf "$SYSTEMPI_SCRIPT" "$SYSTEMPI_BIN"

echo
echo "Installation complete!"
echo "Command installed at: $SYSTEMPI_BIN"
echo "Run from anywhere with:"
echo "  systempi"
