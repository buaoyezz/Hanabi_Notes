chcp 65001
@echo off

echo [信息] 正在清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /f /q *.spec

echo [信息] 正在安装必要的依赖...
pip install -r requirements.txt
pip install pyinstaller

echo [信息] 正在创建打包配置...
echo # -*- mode: python ; coding: utf-8 -*- > Hanabi_Notes.spec
echo. >> Hanabi_Notes.spec
echo import os >> Hanabi_Notes.spec
echo import sys >> Hanabi_Notes.spec
echo from PyInstaller.utils.hooks import collect_data_files, collect_submodules >> Hanabi_Notes.spec
echo. >> Hanabi_Notes.spec
echo block_cipher = None >> Hanabi_Notes.spec
echo. >> Hanabi_Notes.spec
echo # 获取项目根目录 >> Hanabi_Notes.spec
echo project_root = os.path.abspath(os.path.dirname('__file__')) >> Hanabi_Notes.spec
echo. >> Hanabi_Notes.spec
echo # 收集所有Python模块 >> Hanabi_Notes.spec
echo hidden_imports = [ >> Hanabi_Notes.spec
echo     'PySide6.QtCore', >> Hanabi_Notes.spec
echo     'PySide6.QtGui', >> Hanabi_Notes.spec
echo     'PySide6.QtWidgets', >> Hanabi_Notes.spec
echo     'PySide6.QtNetwork', >> Hanabi_Notes.spec
echo     'markdown', >> Hanabi_Notes.spec
echo ] + collect_submodules('Aya_Hanabi') >> Hanabi_Notes.spec
echo. >> Hanabi_Notes.spec
echo # 收集数据文件 >> Hanabi_Notes.spec
echo datas = [ >> Hanabi_Notes.spec
echo     ('Hanabi/Fonts/*', 'Hanabi/Fonts'), >> Hanabi_Notes.spec
echo     ('Hanabi/Image/*', 'Hanabi/Image'), >> Hanabi_Notes.spec
echo     ('Aya_Hanabi/Hanabi_Core/ThemeManager/custom_themes/*', 'Aya_Hanabi/Hanabi_Core/ThemeManager/custom_themes'), >> Hanabi_Notes.spec
echo     ('Aya_Hanabi/plugins', 'Aya_Hanabi/plugins'), >> Hanabi_Notes.spec
echo ] >> Hanabi_Notes.spec
echo. >> Hanabi_Notes.spec
echo a = Analysis( >> Hanabi_Notes.spec
echo     ['Hanabi_Notes.py'], >> Hanabi_Notes.spec
echo     pathex=[project_root], >> Hanabi_Notes.spec
echo     binaries=[], >> Hanabi_Notes.spec
echo     datas=datas, >> Hanabi_Notes.spec
echo     hiddenimports=hidden_imports, >> Hanabi_Notes.spec
echo     hookspath=[], >> Hanabi_Notes.spec
echo     hooksconfig={}, >> Hanabi_Notes.spec
echo     runtime_hooks=[], >> Hanabi_Notes.spec
echo     excludes=[], >> Hanabi_Notes.spec
echo     win_no_prefer_redirects=False, >> Hanabi_Notes.spec
echo     win_private_assemblies=False, >> Hanabi_Notes.spec
echo     cipher=block_cipher, >> Hanabi_Notes.spec
echo     noarchive=False, >> Hanabi_Notes.spec
echo ) >> Hanabi_Notes.spec
echo. >> Hanabi_Notes.spec
echo pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher) >> Hanabi_Notes.spec
echo. >> Hanabi_Notes.spec
echo exe = EXE( >> Hanabi_Notes.spec
echo     pyz, >> Hanabi_Notes.spec
echo     a.scripts, >> Hanabi_Notes.spec
echo     [], >> Hanabi_Notes.spec
echo     exclude_binaries=True, >> Hanabi_Notes.spec
echo     name='HanabiNotes', >> Hanabi_Notes.spec
echo     debug=False, >> Hanabi_Notes.spec
echo     bootloader_ignore_signals=False, >> Hanabi_Notes.spec
echo     strip=False, >> Hanabi_Notes.spec
echo     upx=True, >> Hanabi_Notes.spec
echo     console=False, >> Hanabi_Notes.spec
echo     disable_windowed_traceback=False, >> Hanabi_Notes.spec
echo     argv_emulation=False, >> Hanabi_Notes.spec
echo     target_arch=None, >> Hanabi_Notes.spec
echo     codesign_identity=None, >> Hanabi_Notes.spec
echo     entitlements_file=None, >> Hanabi_Notes.spec
echo     icon=os.path.join(project_root, 'Hanabi', 'Image', 'Hanabi_logo.png'), >> Hanabi_Notes.spec
echo ) >> Hanabi_Notes.spec
echo. >> Hanabi_Notes.spec
echo coll = COLLECT( >> Hanabi_Notes.spec
echo     exe, >> Hanabi_Notes.spec
echo     a.binaries, >> Hanabi_Notes.spec
echo     a.zipfiles, >> Hanabi_Notes.spec
echo     a.datas, >> Hanabi_Notes.spec
echo     strip=False, >> Hanabi_Notes.spec
echo     upx=True, >> Hanabi_Notes.spec
echo     upx_exclude=[], >> Hanabi_Notes.spec
echo     name='HanabiNotes', >> Hanabi_Notes.spec
echo ) >> Hanabi_Notes.spec

echo [信息] 正在打包应用程序...
pyinstaller --clean Hanabi_Notes.spec

echo [信息] 打包完成！
echo [信息] 可执行文件位于 dist\HanabiNotes 目录中
pause 