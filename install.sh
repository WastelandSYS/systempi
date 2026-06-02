#!/bin/bash

set -euo pipefail

SYSTEMPI_BIN="/usr/local/bin/systempi"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYSTEMPI_SCRIPT="$REPO_DIR/systempi.py"
BASE_PACKAGES=(python3 python3-psutil)

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

detect_os_codename() {
    local codename="unknown"

    if [ -r /etc/os-release ]; then
        . /etc/os-release
        codename="${VERSION_CODENAME:-unknown}"
    fi

    printf '%s\n' "$codename"
}

package_installable() {
    local package="$1"
    local candidate

    candidate="$(apt-cache policy "$package" 2>/dev/null | awk '/^[[:space:]]*Candidate:/ {print $2; exit}' || true)"
    [ -n "$candidate" ] && [ "$candidate" != "(none)" ]
}

install_packages() {
    apt-get install -y "$@"
}

install_raspberry_pi_tools() {
    local codename
    local packages=()

    codename="$(detect_os_codename)"

    if package_installable raspi-utils-core; then
        packages=(raspi-utils-core)
        if package_installable raspi-utils-dt; then
            packages+=(raspi-utils-dt)
        fi
    elif package_installable raspberrypi-utils; then
        packages=(raspberrypi-utils)
    elif package_installable libraspberrypi-bin; then
        packages=(libraspberrypi-bin)
    fi

    if [ "${#packages[@]}" -gt 0 ]; then
        echo "Installing Raspberry Pi utilities for ${codename}: ${packages[*]}"
        install_packages "${packages[@]}"
    else
        echo "Info: No installable Raspberry Pi vcgencmd package found in apt repositories on this system."
        echo "      SystemPi will still run; Pi-specific telemetry may show as unavailable."
    fi
}

install_python_requirements() {
    if python3 -c "import psutil" >/dev/null 2>&1; then
        echo "Python requirements verified."
        return
    fi

    echo "Error: python3-psutil was installed, but psutil is not importable."
    echo "Try running:"
    echo "  sudo apt-get install --reinstall python3-psutil"
    exit 1
}

apt-get update
install_packages "${BASE_PACKAGES[@]}"

install_raspberry_pi_tools
install_python_requirements

chmod +x "$SYSTEMPI_SCRIPT"
ln -sf "$SYSTEMPI_SCRIPT" "$SYSTEMPI_BIN"

echo
echo "Installation complete!"
echo "Command installed at: $SYSTEMPI_BIN"
echo "Run from anywhere with:"
echo "  systempi"
