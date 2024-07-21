import os
import shutil
import subprocess
import configparser
from urllib.parse import urlparse
import tempfile

# Define variables
HOME = os.path.expanduser("~")
REPO_URL = "https://github.com/ShrugShoulders/RudeChat"
DEST_DIR = os.path.join(HOME, "Documents", "RudeChatUpdate")
BACKUP_DIR = os.path.join(HOME, "Documents", "backup_rudechat_files")
PYTHON_LIB_DIR = os.path.join(HOME, ".local", "lib", "python3.12", "site-packages", "rudechat3")

# Ensure backup directory exists
os.makedirs(BACKUP_DIR, exist_ok=True)

# Function to copy specific files to backup directory
def backup_files(source_dir, backup_dir, extensions=[".json", ".txt", ".rude", ".ini"]):
    for root, _, files in os.walk(source_dir):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                src_file = os.path.join(root, file)
                dest_file = os.path.join(backup_dir, file)
                shutil.copy2(src_file, dest_file)
                print(f"Copied {src_file} to {dest_file}")

# Function to clone the repository
def clone_repo(repo_url, dest_dir):
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
    subprocess.run(["git", "clone", repo_url, dest_dir], check=True)
    print(f"Cloned repository to {dest_dir}")

# Function to compare and update configuration files
def compare_and_update_config_files(new_dir, backup_dir):
    for root, _, files in os.walk(new_dir):
        for file in files:
            if file.endswith(".rude") or file.endswith(".ini"):
                new_file = os.path.join(root, file)
                backup_file = os.path.join(backup_dir, file)

                if os.path.exists(backup_file):
                    new_config = configparser.ConfigParser()
                    backup_config = configparser.ConfigParser()
                    new_config.read(new_file)
                    backup_config.read(backup_file)

                    for section in new_config.sections():
                        if not backup_config.has_section(section):
                            backup_config.add_section(section)
                        for key, value in new_config.items(section):
                            if not backup_config.has_option(section, key):
                                backup_config.set(section, key, value)

                    with open(backup_file, 'w') as f:
                        backup_config.write(f)
                    print(f"Updated backup config file {backup_file}")
                else:
                    shutil.copy2(new_file, backup_file)
                    print(f"Copied new config file {new_file} to backup directory")

# Function to restore backup files to the library directory
def restore_backup_files(backup_dir, lib_dir):
    for root, _, files in os.walk(backup_dir):
        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(lib_dir, file)
            shutil.copy2(src_file, dest_file)
            print(f"Restored {src_file} to {dest_file}")

# Step 1: Backup files from the Python library directory
backup_files(PYTHON_LIB_DIR, BACKUP_DIR)

# Step 2: Clone the repository and install
clone_repo(REPO_URL, DEST_DIR)
subprocess.run(["python3", "-m", "pip", "install", "-e", DEST_DIR], check=True)

# Step 3: Compare and update configuration files
compare_and_update_config_files(DEST_DIR, BACKUP_DIR)

# Step 4: Restore backup files to the Python library directory
restore_backup_files(BACKUP_DIR, PYTHON_LIB_DIR)

print("Update and backup process completed.")
