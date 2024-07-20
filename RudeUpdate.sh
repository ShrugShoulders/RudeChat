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

# Restore specific files
echo "Restoring specific files from backup..."

# Create diff files and apply patches
for file in $(find "$BACKUP_DIR" \( -name "*.json" -o -name "gui_config.ini" -o -name "*.rude" -o -name "filtered_channels.txt" -o -name "ignore_list.txt" \)); do
    # Get the base name of the file
    base_file=$(basename "$file")

    # Generate corresponding file path in destination directory
    dest_file="$PYTHON_LIB_DIR/$base_file"

    # Check if the destination file exists
    if [ -f "$dest_file" ]; then
        # Generate diff file
        diff -u "$dest_file" "$file" > "$BACKUP_DIR/${base_file}.diff"

        # Apply diff file if it contains differences
        if [ -s "$BACKUP_DIR/${base_file}.diff" ]; then
            echo "Updating $dest_file from backup..."
            patch "$dest_file" < "$BACKUP_DIR/${base_file}.diff"
        else
            echo "$dest_file is up-to-date."
            rm "$BACKUP_DIR/${base_file}.diff"  # Remove empty diff files
        fi
    else
        # If the destination file does not exist, copy the backup file
        echo "$dest_file does not exist. Copying from backup..."
        cp "$file" "$dest_file"
    fi
done

# Remove the destination directory
echo "Removing directories..."
rm -rf "$DEST_DIR" || { echo "Failed to remove $DEST_DIR"; exit 1; }
rm -rf "$BACKUP_DIR" || { echo "Failed to remove $BACKUP_DIR"; exit 1; }

echo "Done!"