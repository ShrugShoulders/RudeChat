#!/bin/bash

if [ "$(uname -s)" = "Linux" ] && [ -f "/etc/debian_version" ]; then
    echo "Debian detected. Using pip with --break-system-packages option."
    pip_install="pip install --break-system-packages"
else
    echo "Non-Debian system detected. Using pip without --break-system-packages option."
    pip_install="pip install"
fi

echo "Installing RudeChat3..."
$pip_install pytz
$pip_install asyncio
$pip_install irctokens
$pip_install aiofiles
$pip_install plyer
$pip_install tkcolorpicker
$pip_install colorchooser
$pip_install .

echo "Installation completed."
