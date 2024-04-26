#!/bin/bash

install_dependencies() {
    # Check if apt-get is available
    if command -v apt-get &>/dev/null; then
        echo "Debian/Ubuntu detected. Installing Python dependencies using apt-get..."
        sudo apt-get update
        sudo apt-get install -y python3-pytz python3-asyncio python3-irctokens python3-aiofiles python3-plyer python3-tk python3-colorchooser
    else
        echo "Non-Debian system detected. Installing Python dependencies using pip..."
        pip install pytz asyncio irctokens aiofiles plyer tkcolorpicker colorchooser
    fi
}

# Install Python dependencies
install_dependencies

echo "Installing RudeChat3..."
pip install .

echo "Installation completed."
