# -*- mode: python ; coding: utf-8 -*-
# Syspath already contains these:
#  'C:/msys64/mingw64/lib/python37.zip',
#  'C:/msys64/mingw64/lib/python3.7',
#  'C:/msys64/mingw64/bin',
#  'C:/msys64/mingw64/lib/python3.7/lib-dynload',
#  'C:/msys64/mingw64/lib/python3.7/site-packages',
#  'C:/msys64/mingw64/lib/python3.7/site-packages/setuptools-33.1.1-py3.7.egg',
#  'C:/msys64/mingw64/lib/python3.7/site-packages/pyinstaller-4.0.dev0+g4065d2c2-py3.7.egg'
#					'C:\\msys64\\mingw64\\lib\\python3.7\\site-packages\\PyInstaller\\hooks\\pre_safe_import_module',
#					'C:\\msys64\\mingw64\\lib\\python3.7\\site-packages\\pgi\\clib\\gir',
#					'C:\\msys64\\mingw64\\lib\\python3.7\\site-packages\\gi',
#					'C:\\msys64\\mingw64\\lib\\python3.7\\site-packages\\regex',
#					'C:\\msys64\\mingw64\\lib\\python3.7\\site-packages\\gi\\overrides',
#					'C:\\msys64\\mingw64\\lib\\python3.7\\site-packages\\pgi',
#					'C:\\msys64\\mingw64\\lib\\python3.7\\site-packages',
#					'C:\\msys64\\mingw64\\lib\\gcc\\x86_64-w64-mingw32\\9.2.0',
#					'C:\\msys64\\usr\\lib\\gcc\\x86_64-pc-msys\\9.1.0',
#					'C:\\msys64\\mingw64\\bin',
#					'D:\\Temp\Allmsys64zipFiles',
#					'D:\\Temp\\Allmsys64dllFiles',

#					'C:\\msys64\\mingw64\\lib\\python3.7\\site-packages\\PyInstaller-4.0.dev0+g4065d2c2-py3.7.egg\\PyInstaller\\hooks',
#					'C:\\msys64\\mingw64\\lib\\python3.7\\site-packages\\PyInstaller-4.0.dev0+g4065d2c2-py3.7.egg', 
#					'D:\Temp\Allmsys64pyFiles',
#					'D:\\Temp\\AllmsysPYCfiles',

#					'C:\\msys64\\usr\\include\\termios.h',
#					('C:\\msys64\\mingw64\\lib\\girepository-1.0\\Atk-1.0.typelib','girepository-1.0/Atk-1.0.typelib'),
#					('C:\\msys64\\mingw64\\lib\\girepository-1.0\\cairo-1.0.typelib','girepository-1.0/cairo-1.0.typelib'),
#					('C:\\msys64\\mingw64\\lib\\girepository-1.0\\DBus-1.0.typelib','girepository-1.0/DBus-1.0.typelib'),
#					('C:\\msys64\\mingw64\\lib\\girepository-1.0\\DBusGLib-1.0.typelib','girepository-1.0/DBusGLib-1.0.typelib'),
#					('C:\\msys64\\mingw64\\lib\\girepository-1.0\\freetype2-2.0.typelib','girepository-1.0/freetype2-2.0.typelib'),
#					('C:\\msys64\\mingw64\\lib\\girepository-1.0\\Gdk-3.0.typelib','girepository-1.0/Gdk-3.0.typelib'),
#					('C:\\msys64\\mingw64\\lib\\girepository-1.0\\GdkPixbuf-2.0.typelib','girepository-1.0/GdkPixbuf-2.0.typelib'),
#					('C:\\msys64\\mingw64\\lib\\girepository-1.0\\GdkPixdata-2.0.typelib','girepository-1.0/GdkPixdata-2.0.typelib'),
#					('C:\\msys64\\mingw64\\lib\\girepository-1.0\\GdkWin32-3.0.typelib','girepository-1.0/GdkWin32-3.0.typelib'),
#					('C:\\msys64\\mingw64\\lib\\girepository-1.0\\Gio-2.0.typelib','girepository-1.0/Gio-2.0.typelib'),
#					('C:\\msys64\\mingw64\\lib\\girepository-1.0\\GL-1.0.typelib','girepository-1.0/GL-1.0.typelib'),
#					('C:\\msys64\\mingw64\\lib\\girepository-1.0\\Gladeui-2.0.typelib','girepository-1.0/Gladeui-2.0.typelib'),
#					('C:\\msys64\\mingw64\\lib\\girepository-1.0\\GLib-2.0.typelib','girepository-1.0/GLib-2.0.typelib'),
#					('C:\\msys64\\mingw64\\lib\\girepository-1.0\\GModule-2.0.typelib','girepository-1.0/GModule-2.0.typelib'),
#					('C:\\msys64\\mingw64\\lib\\girepository-1.0\\HarfBuzz-0.0.typelib','girepository-1.0/HarfBuzz-0.0.typelib'),
#					('C:\\msys64\\mingw64\\lib\\girepository-1.0\\Json-1.0.typelib','girepository-1.0/Json-1.0.typelib'),
#					('C:\\msys64\\mingw64\\lib\\girepository-1.0\\libxml2-2.0.typelib','girepository-1.0/libxml2-2.0.typelib'),
#					('C:\\msys64\\mingw64\\lib\\girepository-1.0\\PangoCairo-1.0.typelib','girepository-1.0/PangoCairo-1.0.typelib'),
#					('C:\\msys64\\mingw64\\lib\\girepository-1.0\\PangoFT2-1.0.typelib','girepository-1.0/PangoFT2-1.0.typelib'),
#					('C:\\msys64\\mingw64\\lib\\girepository-1.0\\Rsvg-2.0.typelib','girepository-1.0/Rsvg-2.0.typelib'),
#					('C:\\msys64\\mingw64\\lib\\girepository-1.0\\typeliblist.txt','girepository-1.0/typeliblist.txt'),
#					('C:\\msys64\\mingw64\\lib\\girepository-1.0\\xfixes-4.0.typelib','girepository-1.0/xfixes-4.0.typelib'),
#					('C:\\msys64\\mingw64\\lib\\girepository-1.0\\xft-2.0.typelib','girepository-1.0/xft-2.0.typelib'),
#					('C:\\msys64\\mingw64\\lib\\girepository-1.0\\xlib-2.0.typelib','girepository-1.0/xlib-2.0.typelib'),
#					('C:\\msys64\\mingw64\\lib\\girepository-1.0\\xrandr-1.3.typelib','girepository-1.0/xrandr-1.3.typelib'),

block_cipher = None

a = Analysis(['python/scripts/ptxprint'],
             pathex=['python/lib', 'C:\\ptx2pdf',
					'C:\\msys64\\mingw64\\lib',
					'C:\\msys64\\usr\\lib\\python3.7\\site-packages',
					'C:\\msys64\\mingw64\\lib\\python3.7',
					'C:\\pyinstaller'],
             binaries=[ ('C:\\msys64\\mingw64\\lib\\girepository-1.0\\Gtk-3.0.typelib','girepository-1.0/Gtk-3.0.typelib'),
						('C:\\msys64\\mingw64\\lib\\girepository-1.0\\GIRepository-2.0.typelib','girepository-1.0/GIRepository-2.0.typelib'),
						('C:\\msys64\\mingw64\\lib\\girepository-1.0\\Gtk-3.0.typelib','girepository-1.0/Gtk-3.0.typelib'),
						('C:\\msys64\\mingw64\\lib\\girepository-1.0\\Pango-1.0.typelib','girepository-1.0/Pango-1.0.typelib'),
						('C:\\msys64\\mingw64\\lib\\girepository-1.0\\GObject-2.0.typelib','girepository-1.0/GObject-2.0.typelib'),
						('C:\\msys64\\mingw64\\lib\\girepository-1.0\\fontconfig-2.0.typelib','girepository-1.0/fontconfig-2.0.typelib'),
						('C:\\msys64\\mingw64\\lib\\girepository-1.0\\win32-1.0.typelib','girepository-1.0/win32-1.0.typelib')],
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
