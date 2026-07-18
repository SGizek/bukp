# -*- mode: python ; coding: utf-8 -*-
import os
from kivy_deps import sdl2, glew, angle

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('screens', 'screens'),
        ('theme.py', '.'),
        ('widgets.py', '.'),
        ('network.py', '.'),
        ('settings.py', '.'),
        ('utils.py', '.'),
    ],
    hiddenimports=[
        'screens.connect_screen',
        'screens.chat_screen',
        'screens.settings_screen',
        'screens.ipinfo_screen',
        'kivy',
        'kivy.app',
        'kivy.uix.screenmanager',
        'kivy.uix.boxlayout',
        'kivy.uix.gridlayout',
        'kivy.uix.scrollview',
        'kivy.uix.label',
        'kivy.uix.textinput',
        'kivy.uix.button',
        'kivy.uix.popup',
        'kivy.uix.progressbar',
        'kivy.uix.image',
        'kivy.graphics',
        'kivy.graphics.texture',
        'kivy.graphics.context_instructions',
        'kivy.graphics.vertex_instructions',
        'kivy.clock',
        'kivy.metrics',
        'kivy.utils',
        'plyer',
        'PIL',
        'PIL.Image',
        'requests',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest'],
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
    name='BukpMobile',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    *[Tree(p) for p in sdl2.dep_bins + glew.dep_bins + angle.dep_bins],
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BukpMobile',
)
