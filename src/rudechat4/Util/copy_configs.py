#!/usr/bin/env python3
"""Copies the default config files into the user's config folder on first run."""
from rudechat4.shared_imports import *
from rudechat4.global_variables import *

def CopyConfigs():
"""Seed the config folder with the files from DefaultConfig.

    Copies ``DefaultConfig/`` into ``G_CONFIG_DIR`` only when that folder is
    empty, so existing user configs are never overwritten. The destination
    folder must already exist; ``os.listdir`` raises if it doesn't.
"""
    source_dir = G_SOURCE_DIR + "/DefaultConfig"
    dest_dir = G_CONFIG_DIR

    if len(os.listdir(dest_dir)) == 0:
        shutil.copytree(source_dir, dest_dir, dirs_exist_ok=True)