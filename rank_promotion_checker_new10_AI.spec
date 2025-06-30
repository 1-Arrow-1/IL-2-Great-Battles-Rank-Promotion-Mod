# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['rank_promotion_checker_new10_AI.py'],
    pathex=[],
    binaries=[],
    datas=[# ceremony images
       ('Ceremony_DE.png', '.'),
       ('Ceremony_GB.png', '.'),
       ('Ceremony_RU.png', '.'),
       ('Ceremony_US.png', '.'),

       # certificate templates
       ('certificate_template.png',    '.'),
       ('Promotion_certificate_US.png','.'), 
       ('Promotion_certificate_RU.png','.'), 
       ('Promotion_certificate_GB.png','.'), 

       # fonts
       ('SpecialElite.ttf',        '.'),
       ('Kyiv Machine.ttf',        '.'),
       ('DejaVuSans.ttf',          '.'),
       ('NotoSansSC-Regular.otf',  '.'),
	   ('Darwin Pro Light.otf',    '.'),

       # icon (optional if you also reference at runtime)
       ('rank.ico', '.'),],
    hiddenimports=['psutil'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='rank_promotion_checker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['rank.ico'],
)
