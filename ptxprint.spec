# -*- mode: python ; coding: utf-8 -*-
# Syspath already contains these:
#  'C:/msys64/mingw64/lib/python37.zip',
#  'C:/msys64/mingw64/lib/python3.7',
#  'C:/msys64/mingw64/bin',
#  'C:/msys64/mingw64/lib/python3.7/lib-dynload',
#  'C:/msys64/mingw64/lib/python3.7/site-packages',
#  'C:/msys64/mingw64/lib/python3.7/site-packages/setuptools-33.1.1-py3.7.egg',
#  'C:/msys64/mingw64/lib/python3.7/site-packages/pyinstaller-4.0.dev0+g4065d2c2-py3.7.egg'

#					'C:\\msys64\\usr\\lib\\python3.7\\site-packages',
#					'C:\\msys64\\mingw64\\lib\\python3.7\\site-packages\\PyInstaller-4.0.dev0+g4065d2c2-py3.7.egg\\PyInstaller\\hooks',
#					'C:\\msys64\\mingw64\\lib\\python3.7\\site-packages\\PyInstaller-4.0.dev0+g4065d2c2-py3.7.egg', 
#					'D:\Temp\Allmsys64pyFiles',
#					'D:\\Temp\\AllmsysPYCfiles',

#					'C:\\msys64\\usr\\include\\termios.h',

block_cipher = None


a = Analysis(['python/scripts/ptxprint'],
             pathex=['python/lib', 'C:\\ptx2pdf', 'C:\\',
					'C:\\msys64\\mingw64\\lib',
					'C:\\msys64\\mingw64\\lib\\python3.7',
					'C:\\msys64\\mingw64\\lib\\python3.7\\site-packages\\PyInstaller\\hooks\\pre_safe_import_module',
					'C:\\msys64\\mingw64\\lib\\python3.7\\site-packages\\pgi\\clib\\gir',
					'C:\\msys64\\mingw64\\lib\\python3.7\\site-packages\\gi',
					'C:\\msys64\\mingw64\\lib\\python3.7\\site-packages\\regex',
					'C:\\msys64\\mingw64\\lib\\python3.7\\site-packages\\gi\\overrides',
					'C:\\msys64\\mingw64\\lib\\python3.7\\site-packages\\pgi',
					'C:\\msys64\\mingw64\\lib\\python3.7\\site-packages',
					'C:\\msys64\\mingw64\\lib\\gcc\\x86_64-w64-mingw32\\9.2.0',
					'C:\\msys64\\usr\\lib\\gcc\\x86_64-pc-msys\\9.1.0',
					'C:\\msys64\\mingw64\\bin',
					'D:\\Temp\Allmsys64zipFiles',
					'D:\\Temp\\Allmsys64dllFiles',
					'C:\\pyinstaller'],
             binaries=[],
             datas=[('python/lib/ptxprint/ptxprint.glade', 'ptxprint'),
					('python/lib/ptxprint/template.tex', 'ptxprint'),
					('python/lib/ptxprint/A5-Draft.pdf', 'ptxprint'),
					('python/lib/ptxprint/DiglotSample700px.png', 'ptxprint')],
             hiddenimports=['_winreg'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [('v', None, 'OPTION')],
          name='ptxprint',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
