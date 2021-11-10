#!/usr/bin/python3

import re
from ptxprint.utils import bookcodes, _allbkmap
from ptxprint.sfm.ducet import get_sortkey, SHIFTTRIM, tailored

def parsetoc(infname):
    mode = 0
    tocentries = []
    with open(infname, encoding="utf-8") as inf:
        for l in inf.readlines():
            if mode == 0 and re.match(r"\\defTOC\{main\}", l):
                mode = 1
            elif mode == 1:
                m = re.match(r"\\doTOCline\{(.*)\}\{(.*)\}\{(.*)\}\{(.*)\}\{(.*)\}", l)
                if m:
                    tocentries.append(m.groups())
                elif l.startswith("}"):
                    mode = 0
                    break
    return tocentries

# bkranges = {'ot': (0, 40), 'nt': (40, 68), 'dc': (67, 87)}

bkranges = {'ot':   [b for b, i in _allbkmap.items() if 1  < i < 41],
            'nt':   [b for b, i in _allbkmap.items() if 60 < i < 88],
            'dc':   [b for b, i in _allbkmap.items() if 40 < i < 61],
            'pre':  [b for b, i in _allbkmap.items() if 0 <= i < 2],
            'post': [b for b, i in _allbkmap.items() if 87 < i]}


def sortToC(toc, booklist):
    bknums = {k:i for i,k in enumerate(booklist)}
    return sorted(toc, key=lambda b: bknums.get(b[0], 100))

def createtocvariants(toc, booklist, ducet=None):
    res = {}
    res['main'] = sortToC(toc, booklist)
    for k, r in bkranges.items():
        ttoc = []
        for e in toc:
            try:
                if e[0] in r: # r[0] < int(bookcodes.get(e[0], -1)) < r[1]:
                    ttoc.append(e)
            except ValueError:
                pass
        res[k] = sortToC(ttoc, booklist)
    for i in range(3):
        ttoc = []
        k = "sort"+chr(97+i)
        res[k] = ttoc
        if i == 2:
            ducet = tailored("&[first primary ignorable] << 0 << 1 << 2 << 3 << 4 << 5 << 6 << 7 << 8 << 9", ducet)
        for e in sorted(toc, key=lambda x:get_sortkey(x[i+1], variable=SHIFTTRIM, ducet=ducet)):
            ttoc.append(e)
    return res

def generateTex(alltocs):
    res = []
    for k, v in alltocs.items():
        res.append(r"\defTOC{{{}}}{{".format(k))
        for e in v:
            res.append(r"\doTOCline"+"".join("{"+s+"}" for s in e))
        res.append("}")
    return "\n".join(res)
