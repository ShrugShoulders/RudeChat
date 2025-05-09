# rudechat4.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/rudechat4/__main__.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('src/rudechat4/*.py', 'rudechat4'),
        ('src/rudechat4/*.ini', 'rudechat4'),
        ('src/rudechat4/*.ico', 'rudechat4'),
        ('src/rudechat4/*.png', 'rudechat4'),
        ('src/rudechat4/libera.rudeserver', 'rudechat4'),
        ('src/rudechat4/Art/*', 'rudechat4/Art'),
        ('src/rudechat4/Sounds/*', 'rudechat4/Sounds'),
        ('src/rudechat4/Splash/*', 'rudechat4/Splash'),
        ('src/rudechat4/Fortune Lists/*', 'rudechat4/Fortune Lists'),
        ('/home/irish/.local/lib/python3.13/site-packages/emoji/unicode_codes/emoji.json', 'emoji/unicode_codes')
    ],
    hiddenimports=['emoji'],
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
    name='rudechat4',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='src/rudechat4/rude.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='rudechat4',
)
