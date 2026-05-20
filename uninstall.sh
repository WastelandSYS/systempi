#!/bin/bash

set -euo pipefail

SYSTEMPI_BIN="/usr/local/bin/systempi"
REMOVE_DEPS=false

show_help() {
    cat <<HELP
SystemPi uninstaller

Usage:
  sudo ./uninstall.sh [--remove-deps]

Options:
  --remove-deps   Also remove packages install.sh may have installed for SystemPi
                  (python3-psutil plus any available vcgencmd package).
  -h, --help      Show this help message.

This removes the systempi command shortcut. It does not delete your cloned
SystemPi repository folder.
HELP
}

for arg in "$@"; do
    case "$arg" in
        --remove-deps)
            REMOVE_DEPS=true
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $arg"
            echo "Run './uninstall.sh --help' for usage."
            exit 1
            ;;
    esac
done

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root:"
    echo "sudo ./uninstall.sh"
    exit 1
fi

if [ -L "$SYSTEMPI_BIN" ]; then
    rm -f "$SYSTEMPI_BIN"
    echo "Removed shortcut: $SYSTEMPI_BIN"
elif [ -e "$SYSTEMPI_BIN" ]; then
    echo "Warning: $SYSTEMPI_BIN exists but is not a symlink."
    echo "Leaving it in place so this script does not delete an unrelated file."
else
    echo "Shortcut not found: $SYSTEMPI_BIN"
fi

if [ "$REMOVE_DEPS" = true ]; then
    if command -v apt-get >/dev/null 2>&1; then
        apt-get remove -y python3-psutil || true

        if apt-cache show libraspberrypi-bin >/dev/null 2>&1; then
            apt-get remove -y libraspberrypi-bin || true
        fi

        if apt-cache show raspberrypi-utils >/dev/null 2>&1; then
            apt-get remove -y raspberrypi-utils || true
        fi

        apt-get autoremove -y
        echo "Removed optional SystemPi dependencies."
    else
        echo "Warning: apt-get not found. Skipping dependency removal."
    fi
fi

echo "SystemPi uninstall complete."
echo "Your cloned repository folder was not deleted. Remove it manually if desired."
