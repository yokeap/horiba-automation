# -*- mode: python ; coding: utf-8 -*-
# horiba_automation.spec
# Based on your working PyInstaller command

import os
import sys

block_cipher = None

# ค้นหา AutoItX3 DLL path อัตโนมัติ
def find_autoit_dll():
    """Find AutoItX3_x64.dll automatically"""
    try:
        import autoit
        autoit_path = os.path.dirname(autoit.__file__)
        dll_path = os.path.join(autoit_path, 'lib', 'AutoItX3_x64.dll')
        if os.path.exists(dll_path):
            return dll_path
    except:
        pass
    
    # ค้นหาใน site-packages
    for path in sys.path:
        dll_path = os.path.join(path, 'autoit', 'lib', 'AutoItX3_x64.dll')
        if os.path.exists(dll_path):
            return dll_path
    
    return None

autoit_dll = find_autoit_dll()

# เตรียม datas
datas = []

# เพิ่ม imgdata folder
if os.path.exists('imgdata'):
    datas.append(('imgdata', 'imgdata'))

# เพิ่ม AutoItX3 DLL
if autoit_dll and os.path.exists(autoit_dll):
    datas.append((autoit_dll, 'autoit/lib'))
    print(f"✓ Found AutoItX3 DLL: {autoit_dll}")
else:
    print("⚠ Warning: AutoItX3 DLL not found!")

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtSerialPort',
        'cv2',
        'numpy',
        'PIL',
        'PIL.Image',
        'pyautogui',
        'autoit',
        'serial',
        'datetime',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'pandas',
        'IPython',
        'jupyter',
        'notebook',
        'sphinx',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='HoribaAutomation',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # ไม่แสดง console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
