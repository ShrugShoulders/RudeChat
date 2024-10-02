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

    print(f"Options in backup file after merge:")
    for section in backup_config.sections():
        for key, value in backup_config.items(section):
            print(f"[{section}] {key} = {value}")

    write_ini_file(backup_config, backup_file)
    print(f"Completed merge for {backup_file}")

def backup_files(src_dir, dest_dir, file_ext=None, specific_files=None):
    os.makedirs(dest_dir, exist_ok=True)
    
    # Back up files with the specified extension
    if file_ext:
        for file_path in glob.glob(os.path.join(src_dir, f'*{file_ext}')):
            shutil.copy(file_path, dest_dir)
    
    # Back up specific files
    if specific_files:
        for file_name in specific_files:
            src_file = os.path.join(src_dir, file_name)
            if os.path.exists(src_file):
                shutil.copy(src_file, dest_dir)
            else:
                print(f"Specific file not found: {src_file}")

def clone_and_install_repo(repo_url, dest_dir):
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
    subprocess.run(['git', 'clone', repo_url, dest_dir], check=True)
    
    # Change to the destination directory and run pip install
    subprocess.run(['pip', 'install', '.'], cwd=dest_dir, check=True)

def update_files_with_rude(src_dir, backup_dir, file_ext, merge_function, special_merge_file):
    backup_files = glob.glob(os.path.join(backup_dir, f'*{file_ext}'))
    print(f"Updating backup files in {backup_dir} with extensions {file_ext}")
    if not backup_files:
        print(f"No backup files found with extension {file_ext} in {backup_dir}")

    for backup_file in backup_files:
        print(f"Processing backup file: {backup_file} with special merge file: {special_merge_file}")
        merge_function(special_merge_file, backup_file)

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

def restore_files(src_dir, backup_dir, file_ext, specific_files=None):
    # Restore files with the specified extension
    backup_files = glob.glob(os.path.join(backup_dir, f'*{file_ext}'))
    for backup_file in backup_files:
        file_name = os.path.basename(backup_file)
        src_file = os.path.join(src_dir, file_name)
        if os.path.exists(src_file):
            os.remove(src_file)
        shutil.copy(backup_file, src_dir)
    
    # Restore specific files
    if specific_files:
        for file_name in specific_files:
            backup_file = os.path.join(backup_dir, file_name)
            src_file = os.path.join(src_dir, file_name)
            if os.path.exists(backup_file):
                if os.path.exists(src_file):
                    os.remove(src_file)
                shutil.copy(backup_file, src_dir)
            else:
                print(f"Specific file not found in backup: {backup_file}")
                
def remove_directory(dir_path):
    if os.path.exists(dir_path):
        print(f"Removing directory: {dir_path}")
        shutil.rmtree(dir_path)
    else:
        print(f"Directory not found: {dir_path}")

def main():
    HOME = os.path.expanduser("~")
    REPO_URL = "https://github.com/ShrugShoulders/RudeChat"
    DEST_DIR = os.path.join(HOME, "Documents", "RudeChatUpdate")
    BACKUP_DIR = os.path.join(HOME, "Documents", "backup_rudechat_files")
    PYTHON_LIB_DIR = os.path.join(HOME, ".local", "lib", "python3.12", "site-packages", "rudechat3")
    specific_files = ['filtered_channels.txt', 'ignore_list.txt', 'first_run.txt', 'friend_list.txt']
    special_merge_file = os.path.join(PYTHON_LIB_DIR, 'conf.libera.rude')

    remove_directory(DEST_DIR)
    remove_directory(BACKUP_DIR)
    
    # Backup .rude and .ini files
    backup_files(PYTHON_LIB_DIR, BACKUP_DIR, '.rude')
    backup_files(PYTHON_LIB_DIR, BACKUP_DIR, '.ini')
    backup_files(PYTHON_LIB_DIR, BACKUP_DIR, '.json')
    backup_files(PYTHON_LIB_DIR, BACKUP_DIR, None, specific_files)
    
    # Clone and install the repository
    clone_and_install_repo(REPO_URL, DEST_DIR)
    
    # Update .ini files
    update_files(PYTHON_LIB_DIR, BACKUP_DIR, '.ini', merge_ini_files)
    
    # Restore .ini files to the Python lib directory
    restore_files(PYTHON_LIB_DIR, BACKUP_DIR, '.ini')
    
    # Update .rude files
    update_files_with_rude(PYTHON_LIB_DIR, BACKUP_DIR, '.rude', merge_ini_files, special_merge_file)
    
    # Restore .rude files to the Python lib directory
    restore_files(PYTHON_LIB_DIR, BACKUP_DIR, '.rude')
    restore_files(PYTHON_LIB_DIR, BACKUP_DIR, '.json', specific_files)

    remove_directory(DEST_DIR)

if __name__ == "__main__":
    main()
