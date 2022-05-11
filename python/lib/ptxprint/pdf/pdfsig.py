#!/usr/bin/python3

import math
from dataclasses import dataclass
from typing import Tuple, Union
from ptxprint.pdfrw.objects import PdfObject, PdfDict, PdfArray, PdfName, IndirectPdfDict
from ptxprint.pdfrw import PdfReader, PdfWriter, PageMerge

def applycm(cm, p):
    return [cm[0] * p[0] + cm[2] * p[1] + cm[4],
            cm[1] * p[0] + cm[3] * p[1] + cm[5]]

def mergedict(base, new):
    if base == new or new is None:
        return base
    if base.indirect:
        base = base.real_value()
    if new.indirect:
        new = new.real_value()
    for k, v in new.iteritems():
        if k not in base:
            base[k] = v
            continue
        if v == base[k]:
            continue
        if isinstance(v, PdfDict):
            mergedict(base[k], v)
        elif isinstnace(v, PdfArray):
            base[k].extend([x for x in v if x not in base[k]])
        else:
            raise ValueError(f"Dictionary collision at {k} of {base[k]} and {v}")
    return base

def mapnamepages(names, pagemap):
    if names is None:
        return
    if names.Kids is not None:
        for k in names.Kids:
            mapnamepages(k, pagemap)
    if names.Names is not None:
        for v in names.Names[1::2]:
            if v[0].pid in pagemap:
                v[0] = pagemap[v[0].pid]

pagesizes = {
    'a4': (595, 842),
    'ltr': (612, 792),
    'lgl': (612, 1008),
    'a3': (842, 1191),
    'a2': (1190, 1684)
}

@dataclass
class PL:
    crops: int
    x: int
    y: int
    page: int = 0
    invert: int = 0

@dataclass
class Size:
    w: float
    h: float

    def swap(self):
        self.w, self.h = self.h, self.w

layouts = {
    4:  (PL(3, 0, 1), PL(12, 0, 0, 1), PL(3, 0, 1, 1), PL(12, 0, 0)),                     # 4 1           # 2 3

    8:  (PL(3, 1, 0), PL(12, 0, 0, 1), PL(12, 0, 1, 1, 1), PL(3, 1, 1, 0, 1),             # 5 4           # 3 6
         PL(12, 0, 1, 0, 1), PL(3, 1, 1, 1, 1), PL(3, 1, 0, 1), PL(12, 0, 0)),            # 8 1           # 2 7

    16: (PL(3, 1, 3), PL(12, 1, 0, 1), PL(3, 1, 3, 1), PL(12, 1, 0),                      # 5 12  9 8     # 7 10 11 6
         PL(3, 0, 0, 0, 1), PL(12, 0, 3, 1, 1), PL(3, 0, 0, 1, 1), PL(12, 0, 3, 0, 1),    # 4 13 16 1     # 2 15 14 3
         PL(3, 0, 2, 0, 1), PL(12, 0, 1, 1, 1), PL(3, 0, 2, 1, 1), PL(12, 0, 1, 0, 1),
         PL(3, 1, 1), PL(12, 1, 2, 1), PL(3, 1, 1, 1), PL(12, 1, 2))

}

class Signature:
    def __init__(self, srcsize, tgtsize, pages, sigsheets, fold):
        self.src = Size(*srcsize)
        self.tgt = Size(*tgtsize)
        self.mbox = PdfArray([0, 0, self.tgt.w, self.tgt.h])
        self.pages = pages * 2
        self.sigsheets = sigsheets
        self.rotate = (int(math.log2(self.pages)) & 1) == 0
        self.fold = fold if self.pages != 4 else 0
        if self.rotate:
            self.numy = int(math.sqrt(self.pages))
            self.numx = self.numy // 2
            self.cell = Size(self.tgt.h / self.numy, self.tgt.w / self.numx)
            self.margin = Size(self.cell.w - self.src.w,
                               0.5 * (self.cell.h - self.src.h))
        else:
            self.numx = self.numy = int(math.sqrt(self.pages / 2))
            mult = 1. / self.numx
            self.cell = Size(mult * self.tgt.w, mult * self.tgt.h)
            self.margin = Size((self.cell.w - self.src.w),
                               0.5 * (self.cell.h - self.src.h))
        if (self.pages > 8 and self.margin.w < self.fold) or (self.pages > 4 and self.margin.h < self.fold):
            raise OverflowError(f"Margin {self.margin} less than folding margin {self.fold}")

    def cm(self, i):
        self.crops = []
        res = [0, 1, -1, 0, 0, 0] if self.rotate else [1, 0, 0, 1, 0, 0]
        pos = layouts[self.pages][i]
        if pos.invert != 0:
            res = [-x for x in res]
            xcell, ycell = (pos.x, pos.y + 1) if self.rotate else (pos.x + 1, pos.y + 1)
        else:
            xcell, ycell = (pos.x + 1, pos.y) if self.rotate else (pos.x, pos.y)
        if self.rotate:
            res[4] = xcell * self.cell.h
            res[5] = ycell * self.cell.w
        else:
            res[4] = xcell * self.cell.w
            res[5] = ycell * self.cell.h
        #scale = 1. # 1. / math.sqrt(self.pages / 2)
        #res = [x * scale for x in res]

        bindleft = i & 1 == 0
        if bindleft:
            trans = [0., self.margin.h]
        else:
            trans = [self.margin.w, self.margin.h]
        res = res[:4] + [res[0] * trans[0] + res[2] * trans[1] + res[4],
                         res[1] * trans[0] + res[3] * trans[1] + res[5]]
        if bindleft:
            self.docropmark(res, [self.src.w, 0], 4)
            self.docropmark(res, [self.src.w, self.src.h], 3)
        else:
            self.docropmark(res, [0, 0], 1)
            self.docropmark(res, [0, self.src.h], 2)
        return res

    def pagenum(self, i, maxpages):
        if self.sigsheets == 0:
            ppsig = ((maxpages + self.pages - 1) // self.pages) * self.pages
        else:
            ppsig = self.pages * self.sigsheets
        n = i if i < maxpages // 2 else maxpages - i - 1
        sigid = n // (ppsig // 2)
        sigindex = n % (ppsig // 2)
        if i >= maxpages // 2:
            sigindex = ppsig - sigindex - 1
        # n = sigindex if i < maxpages // 2 else ppsig - sigindex - 1
        print(i, maxpages, ppsig, sigindex, sigid)
        return (sigid, sigid * 2 + layouts[self.pages][sigindex].page, sigindex)

    def docropmark(self, cm, p, n):
        x, y = applycm(cm, p)
        n -= 1
        if cm[0] == -1:
            n += 2
        elif cm[1] == -1:
            n -= 1
        elif cm[1] == 1:
            n += 1
        n = (n % 4) + 1
        self.crops.append([x, y, n])

    def appendpage(self, i, page, p1, p2, maxpages, crops=False):
        sigid, sigsheet, signum = self.pagenum(i, maxpages)
        cm = self.cm(signum)
        pnum = layouts[self.pages][signum].page
        p = p2 if pnum == 1 else p1
        p.add(page)
        p.subpages.append(getattr(page, 'pid', 0))
        pobj = p[-1]
        pobj.Matrix = cm
        if crops:
            pass

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('infile',nargs='?',help='Input PDF file')
    parser.add_argument('-o','--outfile',help='Output PDF file (required if input PDF file)')
    parser.add_argument('-n','--num',type=int,help="Number of pages per side")
    parser.add_argument('-s','--size',help='Paper size: name or widthxheight')
    parser.add_argument('-H','--height',type=float,help="Source page height")
    parser.add_argument('-W','--width',type=float,help="Source page width")
    parser.add_argument('--outheight',type=float,help="Target page height")
    parser.add_argument('--outwidth',type=float,help="Target page width")
    parser.add_argument('-S','--sigsheets',type=int,default=1,help='Number of sheets per signature')
    parser.add_argument('-f','--fold',type=float,default=0.,help='Minimum fold cut margin')
    args = parser.parse_args()

    if args.size is not None:
        if 'x' in args.size:
            args.outwidth, args.outheight = (float(x.strip()) for x in args.size.split('x'))
        elif args.size.lower() in pagesizes:
            args.outwidth, args.outheight = pagesizes[args.size.lower()]
        elif args.size.lower().endswith('l') and args.size.lower()[:-1] in pagesizes:
            args.outheight, args.outwidth = pagesizes[args.size.lower()[:-1]]
        else:
            print(f"Unknown paper size: {args.size}. Keeping going and will probably crash")
    if not args.infile:
        sig = Signature([args.width, args.height], [args.outwidth, args.outheight],
                    args.num, args.sigsheets, args.fold)
        print(f"{sig.margin=}, {sig.cell=}, num=({sig.numx}, {sig.numy})")
        for i in range(2*args.num):
            print(i, sig.pagenum(i, args.num), sig.cm(i), sig.crops)
    elif not args.outfile:
        print("Must specify an output file if processing an input file")
    else:
        trailer = PdfReader(args.infile)
        writer = PdfWriter(args.outfile)
        pages = trailer.pages
        if not args.width:
            mbox = [float(x) for x in pages[0].MediaBox]
            args.width = mbox[2] - mbox[0]
            args.height = mbox[3] - mbox[1]
        sig = Signature([args.width, args.height], [args.outwidth, args.outheight],
                    args.num, args.sigsheets, args.fold)
        merges = []
        for i, p in enumerate(pages):
            p.pid = i
            sign, sigi, sigp = sig.pagenum(i, len(pages))
            if sigi & 1 == 0:
                sigi += 1
            while sigi >= len(merges):
                m = PageMerge()
                merges.append(m)
                m.subpages = []
            p1, p2 = merges[sigi-1:sigi+1]
            sig.appendpage(i, p, p1, p2, len(pages))
        pagemap = {}
        for m in merges:
            m.mbox = sig.mbox
            p = m.render()
            p.Rotate = sig.rotate * 90
            writer.addpage(p)
            for oldp in m.subpages:
                pagemap[oldp] = p
        if trailer.Root.Names is not None:
            mapnamepages(trailer.Root.Names.Dests, pagemap)
        trailer.Root.Pages=IndirectPdfDict(Type=PdfName.Pages,
                                      Count=PdfObject(len(writer.pagearray)),
                                      Kids = writer.pagearray)
        writer.trailer = trailer
        writer.write()
