#!/bin/bash

install_pip() {
    local os_name="$1"
    case "$os_name" in
        "fedora")
            echo "Fedora detected. Installing pip..."
            sudo dnf install -y python3-pip
            ;;
        "debian" | "ubuntu")
            echo "Debian/Ubuntu detected. Installing pip..."
            sudo apt-get update
            sudo apt-get install -y python3-pip
            ;;
        *)
            echo "Unable to determine package manager. Please install pip manually."
            exit 1
            ;;
    esac
}

install_dependencies() {
    local os_name="$1"
    case "$os_name" in
        "debian" | "ubuntu")
            echo "Debian/Ubuntu detected. Installing Python dependencies using apt-get..."
            sudo apt-get update
            sudo apt-get install -y python3-pytz python3-asyncio python3-irctokens python3-aiofiles python3-plyer python3-tk python3-colorchooser
            ;;
        *)
            echo "Non-Debian system detected. Installing Python dependencies using pip..."
            pip install pytz asyncio irctokens aiofiles plyer tkcolorpicker colorchooser
            ;;
    esac
}

# Check if /etc/os-release file exists
if [ -f /etc/os-release ]; then
    # Source the file to load the variables
    . /etc/os-release

    # Check if the distribution ID variable exists
    if [ -n "$ID" ]; then
        echo "Linux distribution: $ID"
        
        # Install pip if not installed
        install_pip "$ID"
        
        # Install Python dependencies
        install_dependencies "$ID"

        # Install RudeChat
        pip install .
    else
        echo "Unable to determine Linux distribution"
    fi
else
    echo "Unable to determine Linux distribution"
fi
