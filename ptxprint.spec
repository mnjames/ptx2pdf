# -*- mode: python ; coding: utf-8 -*-
# Syspath already contains these:
#  'C:/msys64/mingw64/lib/python37.zip',
#  'C:/msys64/mingw64/lib/python3.7',
#  'C:/msys64/mingw64/bin',
#  'C:/msys64/mingw64/lib/python3.7/lib-dynload',
#  'C:/msys64/mingw64/lib/python3.7/site-packages',
#  'C:/msys64/mingw64/lib/python3.7/site-packages/setuptools-33.1.1-py3.7.egg',
#  C:/msys64/mingw64/lib/python3.7/site-packages/pyinstaller-4.0.dev0+g4065d2c2-py3.7.egg'


block_cipher = None


a = Analysis(['python\\scripts\\ptxprint'],
             pathex=['python/lib', 'C:\\ptx2pdf'], 
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
