#!/bin/bash

set -euo pipefail

SYSTEMPI_BIN="/usr/local/bin/systempi"
SYSTEMPI_LIB_DIR="/usr/local/lib/systempi"
SYSTEMPI_INSTALLED_SCRIPT="$SYSTEMPI_LIB_DIR/systempi.py"
SYSTEMPI_PACKAGE_STATE="$SYSTEMPI_LIB_DIR/installed-packages"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYSTEMPI_SCRIPT="$REPO_DIR/systempi.py"
BASE_PACKAGES=(python3 python3-psutil)
INSTALLED_BY_SYSTEMPI=()

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
    local package
    local before=()

    for package in "$@"; do
        if package_installed "$package"; then
            before+=("$package")
        fi
    done

    apt-get install -y "$@"

    for package in "$@"; do
        if package_was_absent "$package" "${before[@]}" && package_installed "$package"; then
            INSTALLED_BY_SYSTEMPI+=("$package")
        fi
    done
}

package_installed() {
    local package="$1"
    local status

    status="$(dpkg-query -W -f='${Status}' "$package" 2>/dev/null || true)"
    [ "$status" = "install ok installed" ]
}

package_was_absent() {
    local package="$1"
    shift
    local installed_before

    for installed_before in "$@"; do
        if [ "$installed_before" = "$package" ]; then
            return 1
        fi
    done

    return 0
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

if ! command -v vcgencmd >/dev/null 2>&1; then
    echo "Warning: vcgencmd is unavailable. Pi-specific telemetry will show as unavailable."
fi

install_python_requirements

install -d -m 755 "$SYSTEMPI_LIB_DIR"
install -m 755 "$SYSTEMPI_SCRIPT" "$SYSTEMPI_INSTALLED_SCRIPT"
if [ "${#INSTALLED_BY_SYSTEMPI[@]}" -gt 0 ]; then
    printf '%s\n' "${INSTALLED_BY_SYSTEMPI[@]}" | sort -u > "$SYSTEMPI_PACKAGE_STATE"
else
    : > "$SYSTEMPI_PACKAGE_STATE"
fi
chmod 644 "$SYSTEMPI_PACKAGE_STATE"
ln -sf "$SYSTEMPI_INSTALLED_SCRIPT" "$SYSTEMPI_BIN"

echo
echo "Installation complete!"
echo "Command installed at: $SYSTEMPI_BIN"
echo "Run from anywhere with:"
echo "  systempi"
