#!/bin/bash

# Function to install pip if not installed
install_pip() {
    if ! command -v pip &>/dev/null; then
        if command -v dnf &>/dev/null; then
            echo "Fedora detected. Installing pip..."
            sudo dnf install -y python3-pip
        elif command -v apt-get &>/dev/null; then
            echo "Debian/Ubuntu detected. Installing pip..."
            sudo apt-get update
            sudo apt-get install -y python3-pip
        else
            echo "Unable to determine package manager. Please install pip manually."
            exit 1
        fi
    else
        echo "pip is present, moving on..."
    fi
}

# Function to install Python dependencies
install_dependencies() {
    if command -v apt-get &>/dev/null; then
        echo "Debian/Ubuntu detected. Installing Python dependencies using apt-get..."
        sudo apt-get update
        sudo apt-get install -y python3-pytz python3-asyncio python3-irctokens python3-aiofiles python3-plyer python3-tk python3-colorchooser
    else
        echo "Non-Debian system detected. Installing Python dependencies using pip..."
        pip install pytz asyncio irctokens aiofiles plyer tkcolorpicker colorchooser
    fi
}

# Check if /etc/os-release file exists
if [ -f /etc/os-release ]; then
    # Source the file to load the variables
    . /etc/os-release

    # Check if the distribution ID variable exists
    if [ -n "$ID" ]; then
        echo "Linux distribution: $ID"
        
        # Install pip if not installed
        install_pip
        
        # Install Python dependencies
        install_dependencies

        # Install RudeChat
        pip install .
    else
        echo "Unable to determine Linux distribution"
    fi
else
    echo "Unable to determine Linux distribution"
fi
