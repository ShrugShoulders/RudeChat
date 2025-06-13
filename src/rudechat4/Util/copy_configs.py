#!/usr/bin/env python3
from rudechat4.shared_imports import *
from rudechat4.global_variables import *

def CopyConfigs():
    source_dir = G_SOURCE_DIR + "/DefaultConfig"
    dest_dir = G_CONFIG_DIR

    if len(os.listdir(dest_dir)) == 0:
        shutil.copytree(source_dir, dest_dir, dirs_exist_ok=True)