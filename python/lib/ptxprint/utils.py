import gettext
import locale
import os, sys

APP = 'ptxprint'
MODIR = os.path.join(os.path.dirname(__file__), 'mo')

_ = gettext.gettext

def setup_i18n():
    if sys.platform.startswith('win'):
        if os.getenv('LANG') is None:
            lang, enc = locale.getdefaultlocale()
            os.environ['LANG'] = lang
    else:
        locale.bindtextdomain(APP, MODIR)
    locale.setlocale(locale.LC_ALL, '')
    gettext.bindtextdomain(APP, MODIR)
