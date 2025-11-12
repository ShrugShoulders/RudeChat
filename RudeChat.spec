# rudechat4.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/rudechat4/__main__.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('src/rudechat4/Client/*', 'rudechat4/Client'),
        ('src/rudechat4/GUI/*', 'rudechat4/GUI'),
        ('src/rudechat4/Util/*', 'rudechat4/Util'),
        ('src/rudechat4/DefaultConfig/*', 'rudechat4/DefaultConfig'),
        ('src/rudechat4/Components/*', 'rudechat4/Components'),
        ('src/rudechat4/Resources/Splashes/*', 'rudechat4/Resources/Splashes'),
        ('src/rudechat4/Resources/Sounds/*', 'rudechat4/Resources/Sounds'),
        ('src/rudechat4/Resources/Macros/*', 'rudechat4/Resources/Macros'),
        ('src/rudechat4/Resources/Icons/*', 'rudechat4/Resources/Icons'),
        ('src/rudechat4/Resources/Fortunes/*', 'rudechat4/Resources/Fortunes'),
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
    icon='src/rudechat4/Resources/Icons/rude.ico'
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
