# rudechat3.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/rudechat3/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('src/rudechat3/*.py', 'rudechat3'),
        ('src/rudechat3/*.txt', 'rudechat3'),
        ('src/rudechat3/*.ini', 'rudechat3'),
        ('src/rudechat3/*.json', 'rudechat3'),
        ('src/rudechat3/*.ico', 'rudechat3'),
        ('src/rudechat3/*.png', 'rudechat3'),
        ('src/rudechat3/conf.libera.rude', 'rudechat3'),
        ('src/rudechat3/Art/*', 'rudechat3/Art'),
        ('src/rudechat3/Sounds/*', 'rudechat3/Sounds'),
        ('src/rudechat3/Splash/*', 'rudechat3/Splash'),
        ('src/rudechat3/Fortune Lists/*', 'rudechat3/Fortune Lists')
    ],
    hiddenimports=['plyer.platforms', 'plyer.platforms.linux', 'plyer.platforms.linux.notification'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='rudechat3',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='src/rudechat3/rude.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='rudechat3',
)
