# -*- mode: python ; coding: utf-8 -*-
import os
import transliterate
import pypinyin
pypinyin_dir = os.path.dirname(pypinyin.__file__)
transliterate_dir = os.path.dirname(transliterate.__file__)
languages_dir = os.path.join(transliterate_dir, "contrib", "languages")

a = Analysis(
    ['rank_promotion_checker_new10_AI.py'],
    pathex=[],
    binaries=[],
    datas=[
		
	    # ceremony images
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
        ('rank.ico', '.'),
	   
	    (languages_dir, 'transliterate/contrib/languages'),
	    (os.path.join(pypinyin_dir, "phrases_dict.json"), "pypinyin"),
	    (os.path.join(pypinyin_dir, "pinyin_dict.json"), "pypinyin"),
	    (os.path.join(pypinyin_dir, "standard.py"), "pypinyin"),
	    (os.path.join(pypinyin_dir, "phrases_dict.py"), "pypinyin"),
	    (os.path.join(pypinyin_dir, "pinyin_dict.py"), "pypinyin"),
	],
	   
	   
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
