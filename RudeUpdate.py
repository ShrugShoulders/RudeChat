import os
import shutil
import subprocess
import configparser
import glob

def read_ini_file(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)
    return config

def write_ini_file(config, file_path):
    with open(file_path, 'w') as configfile:
        config.write(configfile)

def merge_ini_files(updated_file, backup_file):
    updated_config = read_ini_file(updated_file)
    backup_config = read_ini_file(backup_file)

    print(f"Called merge_ini_files with: updated_file={updated_file}, backup_file={backup_file}")

    # Print existing options in backup file
    print(f"Existing options in backup file before merge:")
    for section in backup_config.sections():
        for key, value in backup_config.items(section):
            print(f"[{section}] {key} = {value}")

    # Iterate over all sections in the updated configuration
    for section in updated_config.sections():
        # If the section doesn't exist in the backup config, add it
        if not backup_config.has_section(section):
            print(f"Adding new section: {section}")
            backup_config.add_section(section)
        
        # Update or add new keys in the section without changing existing ones
        for key, value in updated_config.items(section):
            if not backup_config.has_option(section, key):
                print(f"Adding new option: [{section}] {key} = {value}")
                backup_config.set(section, key, value)
            else:
                print(f"Existing option: [{section}] {key} = {value} (not updated)")

    # Print options in backup file after merge
    print(f"Options in backup file after merge:")
    for section in backup_config.sections():
        for key, value in backup_config.items(section):
            print(f"[{section}] {key} = {value}")

    # Write the merged configuration back to the backup file
    write_ini_file(backup_config, backup_file)
    print(f"Completed merge for {backup_file}")

def backup_files(src_dir, dest_dir, file_ext):
    os.makedirs(dest_dir, exist_ok=True)
    for file_path in glob.glob(os.path.join(src_dir, f'*{file_ext}')):
        shutil.copy(file_path, dest_dir)

def clone_and_install_repo(repo_url, dest_dir):
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
    subprocess.run(['git', 'clone', repo_url, dest_dir], check=True)
    
    # Change to the destination directory and run pip install
    subprocess.run(['pip', 'install', '.'], cwd=dest_dir, check=True)

def update_files(src_dir, backup_dir, file_ext, merge_function):
    updated_files = glob.glob(os.path.join(src_dir, f'*{file_ext}'))
    print(f"Updating files from {src_dir} with extensions {file_ext}")
    if not updated_files:
        print(f"No files found with extension {file_ext} in {src_dir}")
    
    for updated_file in updated_files:
        file_name = os.path.basename(updated_file)
        backup_file = os.path.join(backup_dir, file_name)
        print(f"Processing file: {file_name}")
        if os.path.exists(backup_file):
            print(f"Found backup file: {backup_file}")
            merge_function(updated_file, backup_file)
        else:
            print(f"No backup file found for: {file_name}")

def restore_files(src_dir, backup_dir, file_ext):
    backup_files = glob.glob(os.path.join(backup_dir, f'*{file_ext}'))
    for backup_file in backup_files:
        file_name = os.path.basename(backup_file)
        src_file = os.path.join(src_dir, file_name)
        if os.path.exists(src_file):
            os.remove(src_file)
        shutil.copy(backup_file, src_dir)

def main():
    HOME = os.path.expanduser("~")
    REPO_URL = "https://github.com/ShrugShoulders/RudeChat"
    DEST_DIR = os.path.join(HOME, "Documents", "RudeChatUpdate")
    BACKUP_DIR = os.path.join(HOME, "Documents", "backup_rudechat_files")
    PYTHON_LIB_DIR = os.path.join(HOME, ".local", "lib", "python3.12", "site-packages", "rudechat3")
    
    # Backup .rude and .ini files
    backup_files(PYTHON_LIB_DIR, BACKUP_DIR, '.rude')
    backup_files(PYTHON_LIB_DIR, BACKUP_DIR, '.ini')
    
    # Clone and install the repository
    clone_and_install_repo(REPO_URL, DEST_DIR)
    
    # Update .ini files
    update_files(PYTHON_LIB_DIR, BACKUP_DIR, '.ini', merge_ini_files)
    
    # Restore .ini files to the Python lib directory
    restore_files(PYTHON_LIB_DIR, BACKUP_DIR, '.ini')
    
    # Update .rude files (if needed, add similar logic for .rude files)
    update_files(PYTHON_LIB_DIR, BACKUP_DIR, '.rude', merge_ini_files)
    
    # Restore .rude files to the Python lib directory
    restore_files(PYTHON_LIB_DIR, BACKUP_DIR, '.rude')

if __name__ == "__main__":
    main()
