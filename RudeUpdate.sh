#!/bin/bash

# Define variables
REPO_URL="https://github.com/ShrugShoulders/RudeChat"
DEST_DIR="$HOME/Documents/RudeChatUpdate"
BACKUP_DIR="$HOME/Documents/backup_rudechat_files"
PYTHON_LIB_DIR="$HOME/.local/lib/python3.12/site-packages/rudechat3/"

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "git is not installed. Please install git and try again."
    exit 1
fi

# Create directories if they do not exist
mkdir -p "$DEST_DIR"
mkdir -p "$BACKUP_DIR"

# Clone the repository
echo "Cloning repository..."
git clone "$REPO_URL" "$DEST_DIR" || { echo "Failed to clone repository"; exit 1; }

# Backup specific files
echo "Backing up specific files..."
find "$PYTHON_LIB_DIR" \( -name "*.json" -o -name "gui_config.ini" -o -name "*.rude" -o -name "filtered_channels.txt" -o -name "ignore_list.txt" \) -exec cp {} "$BACKUP_DIR" \;

# Install the package
echo "Installing package..."
cd "$DEST_DIR" || { echo "Failed to change directory to $DEST_DIR"; exit 1; }

# Check for setup.py or pyproject.toml
if [ ! -f "setup.py" ] && [ ! -f "pyproject.toml" ]; then
    echo "Neither 'setup.py' nor 'pyproject.toml' found. Cannot install package."
    exit 1
fi

pip install . || { echo "Failed to install package"; exit 1; }

# Restore specific files from backup
echo "Comparing and updating files from backup..."

# Find all files in the backup directory
for backup_file in "$BACKUP_DIR"/*; do
    if [ -f "$backup_file" ]; then
        basefile=$(basename "$backup_file")
        destfile="$PYTHON_LIB_DIR/$basefile"

        if [ -f "$destfile" ]; then
            # Compare files
            if ! diff "$backup_file" "$destfile" > /dev/null; then
                echo "Differences found in $basefile. Updating..."
                cp "$backup_file" "$destfile"
            else
                echo "$basefile is up to date."
            fi
        else
            # If the file doesn't exist in the destination, just copy it
            echo "$basefile not found in destination. Copying..."
            cp "$backup_file" "$destfile"
        fi
    fi
done

# Remove the destination directory
echo "Removing directories..."
rm -rf "$DEST_DIR" || { echo "Failed to remove $DEST_DIR"; exit 1; }
rm -rf "$BACKUP_DIR" || { echo "Failed to remove $BACKUP_DIR"; exit 1; }

echo "Done!"