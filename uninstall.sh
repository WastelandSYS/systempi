#!/bin/bash

set -euo pipefail

SYSTEMPI_BIN="/usr/local/bin/systempi"
SYSTEMPI_LIB_DIR="/usr/local/lib/systempi"
SYSTEMPI_INSTALLED_SCRIPT="$SYSTEMPI_LIB_DIR/systempi.py"
SYSTEMPI_PACKAGE_STATE="$SYSTEMPI_LIB_DIR/installed-packages"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LEGACY_REPO_SCRIPT="$REPO_DIR/systempi.py"
REMOVE_DEPS=false

show_help() {
    cat <<HELP
SystemPi uninstaller

Usage:
  sudo ./uninstall.sh [--remove-deps]

Options:
  --remove-deps   Also remove packages install.sh may have installed only when
                  apt can remove them without removing other installed packages.
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

package_installed() {
    local package="$1"
    local status

    status="$(dpkg-query -W -f='${Status}' "$package" 2>/dev/null || true)"
    [ "$status" = "install ok installed" ]
}

safe_remove_package() {
    local package="$1"
    local planned

    if ! package_installed "$package"; then
        return
    fi

    planned="$(apt-get -s remove "$package" 2>/dev/null | awk '/^Remv / {print $2}' || true)"

    if [ "$planned" = "$package" ]; then
        apt-get remove -y "$package" || true
        return
    fi

    echo "Skipping dependency removal for $package because apt would remove additional packages."
}

remove_shortcut() {
    if [ -L "$SYSTEMPI_BIN" ]; then
        local target

        target="$(readlink "$SYSTEMPI_BIN")"
        if [ "$target" = "$SYSTEMPI_INSTALLED_SCRIPT" ] || [ "$target" = "$LEGACY_REPO_SCRIPT" ]; then
            rm -f "$SYSTEMPI_BIN"
            echo "Removed shortcut: $SYSTEMPI_BIN"
        else
            echo "Warning: $SYSTEMPI_BIN points to $target, not this SystemPi install."
            echo "Leaving it in place so this script does not remove an unrelated command."
        fi
    elif [ -e "$SYSTEMPI_BIN" ]; then
        echo "Warning: $SYSTEMPI_BIN exists but is not a symlink."
        echo "Leaving it in place so this script does not delete an unrelated file."
    else
        echo "Shortcut not found: $SYSTEMPI_BIN"
    fi
}

remove_installed_files() {
    if [ -f "$SYSTEMPI_INSTALLED_SCRIPT" ]; then
        rm -f "$SYSTEMPI_INSTALLED_SCRIPT"
        echo "Removed installed script: $SYSTEMPI_INSTALLED_SCRIPT"
    fi
}

remove_package_state() {
    if [ -f "$SYSTEMPI_PACKAGE_STATE" ]; then
        rm -f "$SYSTEMPI_PACKAGE_STATE"
    fi
}

remove_optional_dependencies() {
    if command -v apt-get >/dev/null 2>&1; then
        local package

        if [ ! -f "$SYSTEMPI_PACKAGE_STATE" ]; then
            echo "No SystemPi package state found. Skipping dependency removal."
            return
        fi

        while IFS= read -r package; do
            [ -n "$package" ] || continue
            safe_remove_package "$package"
        done < "$SYSTEMPI_PACKAGE_STATE"

        rm -f "$SYSTEMPI_PACKAGE_STATE"
        echo "Removed packages recorded as installed by SystemPi."
        echo "Run 'sudo apt autoremove' manually if you want to review unused packages."
    else
        echo "Warning: apt-get not found. Skipping dependency removal."
    fi
}

remove_shortcut
remove_installed_files

if [ "$REMOVE_DEPS" = true ]; then
    remove_optional_dependencies
else
    remove_package_state
fi

rmdir "$SYSTEMPI_LIB_DIR" 2>/dev/null || true

echo "SystemPi uninstall complete."
echo "Your cloned repository folder was not deleted. Remove it manually if desired."
