#!/bin/bash

set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root:"
    echo "sudo ./install.sh"
    exit 1
fi

# Make sure systempi.py exists
if [ ! -f "systempi.py" ]; then
    echo "Error: systempi.py not found in this folder."
    echo "Run this installer from the same folder as systempi.py."
    exit 1
fi

# Install required packages
apt-get update
apt-get install -y python3 python3-pip python3-psutil libraspberrypi-bin

# Make script executable
chmod +x systempi.py

# Create/update shortcut
ln -sf "$(pwd)/systempi.py" /usr/local/bin/systempi

clear

echo "Installation complete!"
echo "You can now run SystemPi from anywhere with:"
echo "systempi"
