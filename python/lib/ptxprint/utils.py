import gettext
import locale, codecs, traceback
import os, sys, re
import xml.etree.ElementTree as et
from inspect import currentframe
from struct import unpack
from ptxprint.ptsettings import books

APP = 'ptxprint'

_ = gettext.gettext

lang = None

def setup_i18n(i18nlang):
    global lang    
    localedir = os.path.join(getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__))), "mo")
    if i18nlang is not None:
        os.environ["LANG"] = i18nlang
        lang = i18nlang
    else:
        lang, enc = locale.getdefaultlocale(("LANG", "LANGUAGE"))
    enc = "UTF-8"
    if sys.platform.startswith('win'):
        from ctypes import cdll, windll
        from ctypes.util import find_msvcrt
        putenv('LANG', lang)
        msvcrt = find_msvcrt()
        msvcrtname = str(msvcrt).split('.')[0] if '.' in msvcrt else str(msvcrt)
        cdll.LoadLibrary(msvcrt)._putenv('LANG={}'.format(lang))        
        windll.kernel32.SetEnvironmentVariableW("LANG", lang)
        libintl = cdll.LoadLibrary("libintl-8.dll")
        libintl.bindtextdomain(APP, localedir)
        libintl.textdomain(APP)
        locale.setlocale(locale.LC_ALL, '')
    else:
        locale.setlocale(locale.LC_ALL, (lang, enc))
        locale.bindtextdomain(APP, localedir)
    # print(f"Lang = ({lang}, {enc}) from {i18nlang} and LANG={os.environ['LANG']}")
    gettext.bindtextdomain(APP, localedir=localedir)
    gettext.textdomain(APP)
    if "_" in lang:
        lang = lang[:lang.find("_")].lower()
    
def putenv(k, v):
    if sys.platform.startswith('win'):
        from ctypes import cdll
        from ctypes.util import find_msvcrt
        cdll.msvcrt._putenv('{}={}'.format(k, v))
    os.putenv(k, v)
    
def getlang():
    global lang
    return lang.replace('-','_').split('_')

def f_(s):
    frame = currentframe().f_back
    return eval("f'{}'".format(_(s)), frame.f_locals, frame.f_globals)

def refKey(r, info=""):
    print(r)
    m = re.match(r"^(\d?\D+)?\s*(\d*)\.?(\d*)(\S*?)(\s+.*)?$", r)
    print(m)
    if m:
        return (books.get(m.group(1)[:3], 100), int(m.group(2) or 0), int(m.group(3) or 0), m.group(1)[3:], info, m.group(4))
    else:
        return (100, 0, 0, r, info, "")

def coltotex(s):
    vals = s[s.find("(")+1:-1].split(",")
    try:
        return "x"+"".join("{:02X}".format(int(x)) for x in vals[:3])
    except (ValueError, TypeError):
        return ""

def textocol(s):
    if s.startswith("x"):
        try:
            vals = [int(s[1:3], 16), int(s[3:5], 16), int(s[5:7], 16)]
        except (ValueError, TypeError):
            vals = [0, 0, 0]
    else:
        try:
            v = int(s)
        except (ValueError, TypeError):
            v = 0
        vals = []
        while v:
            vals.append(v % 256)
            v //= 256
        vals.extend([0] * (3 - len(vals)))
    return "rgb({0},{1},{2})".format(*vals)

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
    try:
        fh = open(fname, "r", encoding="utf-16")
        fh.readline()
        failed = False
    except UnicodeError:
        failed = True
    if failed:
        try:
            fh = open(fname, 'r', encoding="cp1252")
            fh.readline()
            failed = False
        except UnicodeError:
            return None
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
        if not os.path.exists(valuepath):
            return None
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

    def openkey(path):
        try:
            k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\\" + path.replace("/", "\\"))
        except FileNotFoundError:
            k = None
        return k

    def queryvalue(base, value):
        return winreg.QueryValueEx(base, value)[0]

def pt_bindir():
    res = getattr(sys, '_MEIPASS', os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
    return res

def get_ptsettings():
    pt_settings = None
    ptob = openkey("Paratext/8")
    if ptob is None:
        tempstr = ("C:\\My Paratext {} Projects" if sys.platform == "win32" else
                    os.path.expanduser("~/Paratext{}Projects"))
        for v in ('9', '8'):
            path = tempstr.format(v)
            if os.path.exists(path):
                pt_settings = path
    else:
        pt_settings = queryvalue(ptob, 'Settings_Directory')
    return pt_settings

headermappings = {
    "First Reference":           r"\firstref",
    "Last Reference":            r"\lastref",
    "Reference Range":           r"\rangeref",
    "Page Number":               r"\pagenumber",
    "Time (HH:MM)":              r"\hrsmins",
    "Date (YYYY-MM-DD)":         r"\isodate",
    "-empty-":                   r"\empty"
}

def localhdrmappings():
    return {
        _("First Reference"):           r"\firstref",
        _("Last Reference"):            r"\lastref",
        _("Reference Range"):           r"\rangeref",
        _("Page Number"):               r"\pagenumber",
        _("Time (HH:MM)"):              r"\hrsmins",
        _("Date (YYYY-MM-DD)"):         r"\isodate",
        _("-empty-"):                   r"\empty"
    }

def local2globalhdr(s):
    revglobal = {v:k for k,v in headermappings.items()}
    mkr = localhdrmappings().get(s, None)
    if mkr is not None:
        return revglobal.get(mkr, mkr)
    else:
        return s

def global2localhdr(s):
    revlocal = {v:k for k,v in localhdrmappings().items()}
    mkr = headermappings.get(s, None)
    if mkr is not None:
        return revlocal.get(mkr, mkr)
    else:
        return s

def asfloat(v, d):
    try:
        return float(v)
    except (ValueError, TypeError):
        return d

def pluralstr(s, l):
    """CLDR plural rules"""
    if len(l) == 0:
        return ""
    elif len(l) == 1:
        return l[0]
    elif str(len(l)) in s:
        return s[str(len(l))].format(*l)
    if "end" in s:
        curr = s["end"].format(l[-2], l[-1])
        l = l[:-2]
    if "middle" in s:
        while len(l) > 1:
            curr = s["middle"].format(l.pop(), curr)
    if "start" in s:
        curr = s["start"].format(l[0], curr)
    elif "middle" in s:
        curr = s["middle"].format(l[0], curr)
    return curr

def multstr(template, lang, num, text, addon=""):
    if str(num) in template:
        res = template[str(num)].format(text)
    elif num > 1 and "mult" in template:
        res = template["mult"].format(text)
    else:
        res = ""
    if len(addon):
        res += " " + addon
    return res

def xdvigetpages(xdv):
    with open(xdv, "rb") as inf:
        inf.seek(-12, 2)
        dat = inf.read(12).rstrip(b"\xdf")
        postamble = unpack(">I", dat[-5:-1])[0]
        inf.seek(postamble, 0)
        dat = inf.read(5)
        lastpage = unpack(">I", dat[1:])[0]
        inf.seek(lastpage, 0)
        dat = inf.read(5)
        res = unpack(">I", dat[1:])[0]
    return res

def brent(left, right, mid, fn, tol, log=None, maxiter=20):
    '''Brent method, see Numerical Recipes in C Ed. 2 p404'''
    GOLD = 0.3819660
    a = left
    b = right
    e = 0.
    x = w = v = mid
    fw = fv = fx = fn(mid)
    for i in range(maxiter):
        xm = 0.5 * (a + b)
        t1 = tol * abs(x) + 1e-8
        t2 = 2 * t1
        if abs(x - xm) <= t2 - 0.5 * (b - a):
            return x
        if abs(e) > t1:
            r = (x - w) * (fx - fv)
            q = (x - v) * (fx - fw)
            p = (x - v) * q - (x - w) * r
            q = 2 * (q - r)
            if q > 0:
                p = -p
            q = abs(q)
            etemp = e
            e = d
            if abs(p) > abs(0.5 * q * etemp) or p <= q * (a -x ) or p >= q * (b - x):
                e = a - x if x >= xm else b - x
                d = GOLD * e
            else:
                d = p / q
                u = x + d
                if u - a < t2 or b - u < t2:
                    return xm
        else:
            e = a - x if x >= xm else b - x
            d = GOLD * e
        u = x + d if abs(x) >= t1 else x + (t1 if d > 0. else -t1)
        fu = fn(u)
        if fu is None:
            fu = fx + d
        if log is not None:
            log.append((u, fu))
        if fu <= fx:
            if u >= x:
                a = x
            else:
                b = x
            v = w; w = x; x = u
            fv = fw; fw = fx; fx = fu
        else:
            if u < x:
                a = u
            else:
                b = u
            if fu <= fw or w == x:
                v = w; w = u
                fv = fw; fw = fu
            elif fu <= fv or v == x or v == w:
                v = u
                fv = fu
    return xm

