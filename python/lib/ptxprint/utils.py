import gettext
import locale, codecs, traceback
import os, sys, re
import xml.etree.ElementTree as et
from inspect import currentframe
from ptxprint.ptsettings import books

APP = 'ptxprint'

_ = gettext.gettext

def setup_i18n():
    localedir = os.path.join(getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__))), "mo")
    if sys.platform.startswith('win'):
        if os.getenv('LANG') is None:
            lang, enc = locale.getdefaultlocale()
            os.environ['LANG'] = lang
        else:
            lang = os.getenv('LANG')
        from ctypes import cdll, windll
        from ctypes.util import find_msvcrt
        cdll.msvcrt._putenv('LANG={}'.format(lang))
        msvcrt = find_msvcrt()
        msvcrtname = str(msvcrt).split('.')[0] if '.' in msvcrt else str(msvcrt)
        cdll.LoadLibrary(msvcrt)._putenv('LANG={}'.format(lang))        
        windll.kernel32.SetEnvironmentVariableW("LANG", lang)
        libintl = cdll.LoadLibrary("libintl-8.dll")
        libintl.bindtextdomain(APP, localedir)

        libintl.textdomain(APP)
        print(localedir, lang)
    else:
        locale.bindtextdomain(APP, localedir)
    locale.setlocale(locale.LC_ALL, '')
    gettext.bindtextdomain(APP, localedir=localedir)
    gettext.textdomain(APP)
    
def f_(s):
    frame = currentframe().f_back
    return eval("f'{}'".format(_(s)), frame.f_locals, frame.f_globals)

def refKey(r, info=""):
    m = re.match(r"^(\d?\D+)?\s*(\d*)\.?(\d*)(\S*?)$", r)
    if m:
        return (books.get(m.group(1)[:3], 100), int(m.group(2) or 0), int(m.group(3) or 0), m.group(1)[3:], info, m.group(4))
    else:
        return (100, 0, 0, r, info, "")

_wincodepages = {
    'cp950' : 'big5',
    'cp951' : 'big5hkscs',
    'cp20932': 'euc_jp',
    'cp954':  'euc_jp',
    'cp20866': 'ko18_r',
    'cp20936': 'gb2312',
    'cp10000': 'mac_roman',
    'cp10002': 'big5',
    'cp10006': 'mac_greek',
    'cp10007': 'mac_cyrillic',
    'cp10008': 'gb2312',
    'cp10029': 'mac_latin2',
    'cp10079': 'mac_iceland',
    'cp10081': 'mac_turkish',
    'cp1200':  'utf_16_le',
    'cp1201':  'utf_16_be',
    'cp12000': 'utf_32',
    'cp12001': 'utf_32_be',
    'cp65000': 'utf_7',
    'cp65001': 'utf_8'
}
_wincodepages.update({"cp{}".format(i+28590) : "iso8859_{}".format(i) for i in range(2, 17)})

def wincpaliases(enc):
    if enc in _wincodepages:
        return codecs.lookup(_wincodepages[enc])
    return None

codecs.register(wincpaliases)

def universalopen(fname, rewrite=False, cp=65001):
    """ Opens a file with the right codec from a small list and perhaps rewrites as utf-8 """
    encoding = "cp{}".format(cp) if str(cp) != "65001" else "utf-8"
    fh = open(fname, "r", encoding=encoding)
    try:
        fh.readline()
        fh.seek(0)
        return fh
    except ValueError:
        pass
    fh = open(fname, "r", encoding="utf-16")
    fh.readline()
    fh.seek(0)
    if rewrite:
        dat = fh.readlines()
        fh.close()
        with open(fname, "w", encoding="utf-8") as fh:
            for d in dat:
                fh.write(d)
        fh = open(fname, "r", encoding="utf-8", errors="ignore")
    return fh

def print_traceback():
    traceback.print_stack()

if sys.platform == "linux":

    def openkey(path, doError=None):
        basepath = os.path.expanduser("~/.config/paratext/registry/LocalMachine/software")
        valuepath = os.path.join(basepath, path.lower(), "values.xml")
        doc = et.parse(valuepath)
        return doc

    def queryvalue(base, value):
        res = base.getroot().find('.//value[@name="{}"]'.format(value))
        if res is None:
            return ""
        else:
            return res.text

elif sys.platform == "win32":
    import winreg

    def openkey(path, doError=None):
        try:
            k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\\" + path.replace("/", "\\"))
        except FileNotFoundError:
            txt1 = "Unable to locate Registry Key for Paratext installation"
            txt2 = "Sorry - PTXprint cannot work unless Paratext 8 (or later) is installed"
            print("Fatal Error: {}\n{}".format(txt1, txt2))
            if doError is not None:
                doError(txt1, txt2, "PTXprint: Fatal Error")
        return k

    def queryvalue(base, value):
        return winreg.QueryValueEx(base, value)[0]

_pt_bindir = ""

def pt_bindir():
    return _pt_bindir

def get_ptsettings(errorfn):
    global pt_bindir
    pt_settings = "."
    try:
        ptob = openkey("Paratext/8", doError=errorfn)
        ptv = queryvalue(ptob, "ParatextVersion")
    except FileNotFoundError:
        for v in ('9', '8'):
            path = "C:\\My Paratext {} Projects".format(v)
            if os.path.exists(path):
                pt_settings = path
                pt_bindir = "C:\\Program Files\\Paratext {}".format(v)
                if os.path.exists(pt_bindir):
                    break
                else:
                    pt_bindir = "C:\\Program Files (x86)\\Paratext {}".format(v)
                break
    else:
        if ptv:
            version = ptv[:ptv.find(".")]
            try:
                pt_bindir = queryvalue(ptob, 'Paratext{}_Full_Release_AppPath'.format(version))
            except:
                pt_bindir = queryvalue(ptob, 'Program_Files_Directory_Ptw'+version)
        pt_settings = queryvalue(ptob, 'Settings_Directory')
        print("pt_settings:", pt_settings)
        print("pt_bindir:", pt_bindir)
    return pt_settings

