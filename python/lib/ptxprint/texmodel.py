import configparser, re, os, gi
from shutil import copyfile
from pathlib import Path
import regex
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from ptxprint.font import TTFont
from ptxprint.ptsettings import chaps, books, bookcodes, oneChbooks
from ptxprint.runner import checkoutput
from ptxprint import sfm
from ptxprint.sfm import usfm, style
from ptxprint.usfmutils import Usfm, Sheets

def universalopen(fname, rewrite=False):
    """ Opens a file with the right codec from a small list and perhaps rewrites as utf-8 """
    fh = open(fname, "r", encoding="utf-8")
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

# After universalopen to resolve circular import. Kludge
from ptxprint.snippets import FancyIntro, PDFx1aOutput, Diglot, FancyBorders, ImgCredits

def loosint(x):
    try:
        return int(x)
    except (ValueError, TypeError):
        return 0
    except ValueError:
        return 0

ModelMap = {
    "L_":                       ("c_diglot", lambda w,v: "L" if v else ""),
    "R_":                       ("c_diglot", lambda w,v: "R" if v else ""),
    "date_":                    ("_date", lambda w,v: v),
    "pdfdate_":                 ("_pdfdate", lambda w,v: v),
    "ifusediglotcustomsty_":    ("_diglotcustomsty", lambda w,v: "%"),

    #"config/name":              ("ecb_savedConfig", lambda w,v: v or "default"),
    "config/notes":             ("t_configNotes", lambda w,v: v or ""),
    "config/pwd":               ("t_invisiblePassword", lambda w,v: v or ""),
    "config/version":           ("_version", lambda w,v: "0.9"),

    # "project/id":               ("fcb_project", None),
    "project/hideadvsettings":  ("c_hideAdvancedSettings", None),
    # "project/showlayouttab":    ("c_showLayoutTab", None),
    # "project/showfonttab":      ("c_showFontTab", None),
    # "project/showbodytab":      ("c_showBodyTab", None),
    # "project/showheadfoottab":  ("c_showHeadFootTab", None),
    # "project/showpicturestab":  ("c_showPicturesTab", None),
    # "project/showadvancedtab":  ("c_showAdvancedTab", None),
    # "project/showdiglottab":    ("c_showDiglotBorderTab", None),
    # "project/showviewertab":    ("c_showViewerTab", None),
    "project/keeptempfiles":    ("c_keepTemporaryFiles", None),
    "project/pdfx1acompliant":  ("c_PDFx1aOutput", None),
    "project/blockexperimental": ("c_experimental", lambda w,v: "" if v else "%"),
    "project/multiplebooks":    ("c_multiplebooks", None),
    "project/combinebooks":     ("c_combine", None),
    "project/book":             ("ecb_book", None),
    "project/booklist":         ("t_booklist", lambda w,v: v or ""),
    "project/ifinclfrontpdf":   ("c_inclFrontMatter", None),
    "project/frontincludes":    ("btn_selectFrontPDFs", lambda w,v: "\n".join('\\includepdf{{{}}}'.format(s.as_posix()) \
                                 for s in w.FrontPDFs) if (w.get("c_inclFrontMatter") and w.FrontPDFs is not None and w.FrontPDFs != 'None') else ""),
    "project/ifinclbackpdf":    ("c_inclBackMatter", None),
    "project/backincludes":     ("btn_selectBackPDFs", lambda w,v: "\n".join('\\includepdf{{{}}}'.format(s.as_posix()) \
                                 for s in w.BackPDFs) if (w.get("c_inclBackMatter") and w.BackPDFs is not None and w.BackPDFs != 'None') else ""),
    "project/useprintdraftfolder": ("c_useprintdraftfolder", lambda w,v :"true" if v else "false"),
    "project/processscript":    ("c_processScript", None),
    "project/runscriptafter":   ("c_processScriptAfter", None),
    "project/selectscript":     ("btn_selectScript", lambda w,v: w.customScript.as_posix() if w.customScript is not None else ""),
    "project/usechangesfile":   ("c_usePrintDraftChanges", lambda w,v :"true" if v else "false"),
    "project/ifusemodstex":     ("c_useModsTex", lambda w,v: "" if v else "%"),
    "project/ifusecustomsty":   ("c_useCustomSty", lambda w,v: "" if v else "%"),
    "project/ifusemodssty":     ("c_useModsSty", lambda w,v: "" if v else "%"),
    "project/ifstarthalfpage":  ("c_startOnHalfPage", lambda w,v :"true" if v else "false"),
    "project/randompicposn":    ("c_randomPicPosn", None),
    "project/showlinenumbers":  ("c_showLineNumbers", None),
    "project/canonicalise":     ("c_canonicalise", None),

    "paper/height":             ("ecb_pagesize", lambda w,v: re.sub(r"^.*?,\s*(.+?)\s*(?:\(.*|$)", r"\1", v) or "210mm"),
    "paper/width":              ("ecb_pagesize", lambda w,v: re.sub(r"^(.*?)\s*,.*$", r"\1", v) or "148mm"),
    "paper/pagesize":           ("ecb_pagesize", None),
    "paper/ifwatermark":        ("c_applyWatermark", None),
    "paper/watermarkpdf":       ("btn_selectWatermarkPDF", lambda w,v: '\def\MergePDF{{"{}"}}'.format(w.watermarks.as_posix()) \
                                 if (w.get("c_applyWatermark") and w.watermarks is not None and w.watermarks != 'None') else ""),
    "paper/ifcropmarks":        ("c_cropmarks", lambda w,v :"true" if v else "false"),  
    "paper/ifverticalrule":     ("c_verticalrule", lambda w,v :"true" if v else "false"),
    "paper/margins":            ("s_margins", lambda w,v: round(float(v)) or "14"),
    "paper/topmarginfactor":    ("s_topmarginfactor", lambda w,v: round(float(v), 2) or "1.60"),
    "paper/bottommarginfactor": ("s_bottommarginfactor", lambda w,v: round(float(v), 2) or "1.00"),
    "paper/sidemarginfactor":   ("s_sidemarginfactor", lambda w,v: round(float(v), 2) or "1.00"),
    "paper/ifaddgutter":        ("c_pagegutter", lambda w,v :"true" if v else "false"),
    "paper/gutter":             ("s_pagegutter", lambda w,v: round(float(v)) or "0"),
    "paper/colgutteroffset":    ("s_colgutteroffset", lambda w,v: "{:.1f}".format(float(v)) or "0.0"),
    "paper/columns":            ("c_doublecolumn", lambda w,v: "2" if v else "1"),
    # "paper/fontfactor":         ("s_fontsize", lambda w,v: round((v / 12), 3) or "1.000"),
    "paper/fontfactor":         ("s_fontsize", lambda w,v: "{:.3f}".format(float(v) / 12) or "1.000"),

    "fancy/enableborders":      ("c_borders", lambda w,v: "" if v else "%"),
    "fancy/pageborder":         ("c_inclPageBorder", lambda w,v: "" if v else "%"),
    "fancy/pageborderpdf":      ("btn_selectPageBorderPDF", lambda w,v: w.pageborder.as_posix() \
                                            if (w.pageborder is not None and w.pageborder != 'None') \
                                            else get("/ptxprintlibpath")+"/A5 page border.pdf"),
    "fancy/sectionheader":      ("c_inclSectionHeader", lambda w,v: "" if v else "%"),
    "fancy/sectionheaderpdf":   ("btn_selectSectionHeaderPDF", lambda w,v: w.sectionheader.as_posix() \
                                            if (w.sectionheader is not None and w.sectionheader != 'None') \
                                            else get("/ptxprintlibpath")+"/A5 section head border.pdf"),
    "fancy/endofbook":          ("c_inclEndOfBook", lambda w,v: "" if v else "%"),
    "fancy/endofbookpdf":       ("btn_selectEndOfBookPDF", lambda w,v: w.endofbook.as_posix() \
                                            if (w.endofbook is not None and w.endofbook != 'None') \
                                            else get("/ptxprintlibpath")+"/decoration.pdf"),
    "fancy/versedecorator":     ("c_inclVerseDecorator", lambda w,v: "" if v else "%"),
    "fancy/versedecoratorpdf":  ("btn_selectVerseDecorator", lambda w,v: w.versedecorator.as_posix() \
                                            if (w.versedecorator is not None and w.versedecorator != 'None') \
                                            else get("/ptxprintlibpath")+"/Verse number star.pdf"),
    "fancy/versenumsize":       ("s_verseNumSize", lambda w,v: v or "11.00"),

    "paragraph/varlinespacing":    ("c_variableLineSpacing", lambda w,v: "" if v else "%"),
    "paragraph/useglyphmetrics":   ("c_variableLineSpacing", lambda w,v: "%" if v else ""),
    "paragraph/linespacing":       ("s_linespacing", lambda w,v: "{:.3f}".format(float(v)) or "15.000"),
    # "paragraph/linespacingfactor": ("s_linespacing", lambda w,v: "{:.3f}".format(float(v or "15") / 14)),
    "paragraph/linemin":           ("s_linespacingmin", lambda w,v: "minus {:.3f}pt".format(float(w.get("s_linespacing")) - float(v)) \
                                                     if float(v) < float(w.get("s_linespacing")) else ""),
    "paragraph/linemax":        ("s_linespacingmax", lambda w,v: "plus {:.3f}pt".format(float(v) - float(w.get("s_linespacing"))) \
                                                     if float(v) > float(w.get("s_linespacing")) else ""),
    "paragraph/ifjustify":      ("c_justify", lambda w,v: "true" if v else "false"),
    "paragraph/ifhyphenate":    ("c_hyphenate", lambda w,v: "" if v else "%"),
    "paragraph/ifomithyphen":   ("c_omitHyphen", lambda w,v: "" if v else "%"),
    "paragraph/ifnothyphenate": ("c_hyphenate", lambda w,v: "%" if v else ""),
    "paragraph/ifusefallback":  ("c_useFallbackFont", None),
    "paragraph/missingchars":   ("t_missingChars", lambda w,v: v or ""),

    "document/sensitive":       ("c_sensitive", None),
    "document/title":           (None, lambda w,v: w.ptsettings.get('FullName', "")),
    "document/subject":         ("t_booklist", lambda w,v: v if w.get("c_multiplebooks") else w.get("ecb_book")),
    "document/author":          (None, lambda w,v: w.ptsettings.get('Copyright', "")),
    # "document/author":          (None, lambda w,v: re.sub('"?</?p>"?','',w.ptsettings.get('Copyright', "")).strip('"')),

    "document/startpagenum":    ("s_startPageNum", lambda w,v: int(float(v)) or "1"),
    "document/toc":             ("c_autoToC", lambda w,v: "" if v else "%"),
    "document/toctitle":        ("t_tocTitle", lambda w,v: v or ""),
    "document/usetoc1":         ("c_usetoc1", None),
    "document/usetoc2":         ("c_usetoc2", None),
    "document/usetoc3":         ("c_usetoc3", None),
    "document/chapfrom":        ("fcb_chapfrom", None),
    "document/chapto":          ("fcb_chapto", None),
    "document/colgutterfactor": ("s_colgutterfactor", lambda w,v: round(float(v)*3) or "12"), # Hack to be fixed
    "document/ifrtl":           ("fcb_textDirection", lambda w,v:"true" if v == "Right-to-Left" else "false"),
    "document/toptobottom":     ("fcb_textDirection", lambda w,v: "" if v == "Top-to-Bottom (LTR)" else "%"),
    "document/iflinebreakon":   ("c_linebreakon", lambda w,v: "" if v else "%"),
    "document/linebreaklocale": ("t_linebreaklocale", lambda w,v: v or ""),
    "document/script":          ("fcb_script", lambda w,v: ":script="+v.lower() if v != "Zyyy" else ""),
    "document/digitmapping":    ("fcb_digits", lambda w,v: ':mapping=mappings/'+v.lower()+'digits' if v != "Default" else ""),
    "document/ch1pagebreak":    ("c_ch1pagebreak", None),
    "document/marginalverses":  ("c_marginalverses", lambda w,v: "" if v else "%"),
    "document/columnshift":     ("s_columnShift", lambda w,v: v or "16"),
    "document/ifshowchapternums": ("c_chapterNumber", lambda w,v: "%" if v else ""),
    "document/showxtrachapnums":  ("c_showNonScriptureChapters", lambda w,v: v),
    "document/ifomitsinglechnum": ("c_omitChap1ChBooks", lambda w,v: v),
    "document/ifomitverseone":  ("c_omitverseone", lambda w,v: "true" if v else "false"),
    "document/ifshowversenums":   ("c_verseNumbers", lambda w,v: "%" if v else ""),
    "document/ifmainbodytext":  ("c_mainBodyText", None),
    "document/glueredupwords":  ("c_glueredupwords", None),
    "document/ifinclfigs":      ("c_includeillustrations", lambda w,v: "true" if v else "false"),
    "document/ifusepiclist":    ("c_includeillustrations", lambda w,v :"" if v else "%"),
    "document/iffigfrmpiclist": ("c_usePicList", None),
    "document/iffigexclwebapp": ("c_figexclwebapp", None),
    "document/iffigskipmissing": ("c_skipmissingimages", None),
    "document/iffigplaceholders": ("c_figplaceholders", lambda w,v: "true" if v else "false"),
    "document/iffighiderefs":   ("c_fighiderefs", None),
    "document/usesmallpics":    ("c_useLowResPics", lambda w,v :"" if v else "%"),
    "document/uselargefigs":    ("c_useHighResPics", lambda w,v :"" if v else "%"),
    "document/customfiglocn":   ("c_useCustomFolder", lambda w,v :"" if v else "%"),
    "document/exclusivefolder": ("c_exclusiveFiguresFolder", None),
    "document/customfigfolder": ("btn_selectFigureFolder", lambda w,v: w.customFigFolder.as_posix() if w.customFigFolder is not None else ""),
    "document/customoutputfolder": ("btn_selectOutputFolder", lambda w,v: w.customOutputFolder.as_posix() if w.customOutputFolder is not None else ""),
    "document/imagetypepref":   ("t_imageTypeOrder", None),
    "document/spacecntxtlztn":  ("fcb_spaceCntxtlztn", lambda w,v: str({"None": 0, "Some": 1, "Full": 2}.get(v, loosint(v)))),
    "document/glossarymarkupstyle":  ("fcb_glossaryMarkupStyle", None),
    "document/filterglossary":  ("c_filterGlossary", None),
    "document/hangpoetry":      ("c_hangpoetry", lambda w,v: "" if v else "%"),
    "document/preventorphans":  ("c_preventorphans", None),
    "document/preventwidows":   ("c_preventwidows", None),
    "document/sectionheads":    ("c_sectionHeads", None),
    "document/parallelrefs":    ("c_parallelRefs", None),
    "document/bookintro":       ("c_bookIntro", None),
    "document/introoutline":    ("c_introOutline", None),
    "document/indentunit":      ("s_indentUnit", lambda w,v: round(float(v or "2.0"), 1)),
    "document/firstparaindent": ("c_firstParaIndent", lambda w,v: "true" if v else "false"),
    "document/ifhidehboxerrors": ("c_showHboxErrorBars", lambda w,v :"%" if v else ""),
    "document/elipsizemptyvs":  ("c_elipsizeMissingVerses", None),
    "document/ifspacing":       ("c_spacing", lambda w,v :"" if v else "%"),
    "document/spacestretch":    ("s_maxSpace", lambda w,v : str((int(float(v)) - 100) / 100.)),
    "document/spaceshrink":     ("s_minSpace", lambda w,v : str((100 - int(float(v))) / 100.)),
    "document/ifcolorfonts":    ("c_colorfonts", lambda w,v: "%" if v else ""),

    "document/ifchaplabels":    ("c_useChapterLabel", lambda w,v: "%" if v else ""),
    "document/clabelbooks":     ("t_clBookList", lambda w,v: v.upper()),
    "document/clabel":          ("t_clHeading", None),
    "document/clsinglecol":     ("c_singleColLayout", None),
    "document/clsinglecolbooks":("t_singleColBookList", None),
    "document/cloptimizepoetry": ("c_optimizePoetryLayout", None),

    "document/ifdiglot":        ("c_diglot", lambda w,v : "" if v else "%"),
    "document/diglotprifraction": ("s_diglotPriFraction", lambda w,v : round((float(v)/100), 3) if v is not None else "0.550"),
    "document/diglotsecfraction": ("s_diglotPriFraction", lambda w,v : round(1 - (float(v)/100), 3) if v is not None else "0.450"),
    "document/diglotsecprj":    ("fcb_diglotSecProject", None),
    "document/diglotpicsources": ("fcb_diglotPicListSources", None),
    "document/diglotswapside":  ("c_diglotSwapSide", lambda w,v: v),
    "document/diglotsepnotes":  ("c_diglotSeparateNotes", lambda w,v: "true" if v else "false"),
    "document/diglotsecconfig": ("ecb_diglotSecConfig", None),

    "header/headerposition":    ("s_headerposition", lambda w,v: round(float(v), 2) or "1.00"),
    "header/footerposition":    ("s_footerposition", lambda w,v: round(float(v), 2) or "1.00"),
    "header/ifomitrhchapnum":   ("c_omitrhchapnum", lambda w,v :"true" if v else "false"),
    "header/ifverses":          ("c_hdrverses", lambda w,v :"true" if v else "false"),
    "header/chvseparator":      ("c_sepColon", lambda w,v : ":" if v else "."),
    "header/ifrhrule":          ("c_rhrule", lambda w,v: "" if v else "%"),
    "header/ruleposition":      ("s_rhruleposition", lambda w,v: v or "10"),
    "header/hdrleftpri":        ("c_hdrLeftPri", None),
    "header/hdrleft":           ("ecb_hdrleft", lambda w,v: v or "-empty-"),
    "header/hdrcenterpri":      ("c_hdrCenterPri", None),
    "header/hdrcenter":         ("ecb_hdrcenter", lambda w,v: v or "-empty-"),
    "header/hdrrightpri":       ("c_hdrRightPri", None),
    "header/hdrright":          ("ecb_hdrright", lambda w,v: v or "-empty-"),
    "header/mirrorlayout":      ("c_mirrorpages", lambda w,v: "true" if v else "false"),
    
    "footer/ftrcenterpri":      ("c_ftrCenterPri", None),
    "footer/ftrcenter":         ("ecb_ftrcenter", lambda w,v: v or "-empty-"),
    "footer/ifftrtitlepagenum": ("c_pageNumTitlePage", lambda w,v: "" if v else "%"),
    "footer/ifprintConfigName": ("c_printConfigName", lambda w,v: "" if v else "%"),

    "notes/includefootnotes":   ("c_includeFootnotes", lambda w,v: "%" if v else ""),
    "notes/fnparagraphednotes": ("c_fnparagraphednotes", lambda w,v: "" if v else "%"),
    "notes/fnOverride":         ("c_fnOverride", None),
    "notes/iffnautocallers":    ("c_fnautocallers", lambda w,v :"true" if v else "false"),
    "notes/fncallers":          ("t_fncallers", lambda w,v: v if w.get("c_fnautocallers") else ""),
    "notes/fnresetcallers":     ("c_fnpageresetcallers", lambda w,v: "" if v else "%"),
    "notes/fnomitcaller":       ("c_fnomitcaller", lambda w,v: "%" if v else ""),

    "notes/includexrefs":       ("c_includeXrefs", lambda w,v: "%" if v else ""),
    "notes/xrparagraphednotes": ("c_paragraphedxrefs", lambda w,v: "" if v else "%"),
    "notes/xrOverride":         ("c_xrOverride", None),
    "notes/ifxrautocallers":    ("c_xrautocallers", lambda w,v :"true" if v else "false"),
    "notes/xrcallers":          ("t_xrcallers", lambda w,v: v if w.get("c_xrautocallers") else ""),
    "notes/xrresetcallers":     ("c_xrpageresetcallers", lambda w,v: "" if v else "%"),
    "notes/xromitcaller":       ("c_xromitcaller", lambda w,v: "%" if v else ""),

    "notes/iffootnoterule":     ("c_footnoterule", lambda w,v: "%" if v else ""),
    "notes/ifblendfnxr":        ("c_blendfnxr", None),
    "notes/addcolon":           ("c_addColon", None),
    "notes/keepbookwithrefs":   ("c_keepBookWithRefs", None),
    "notes/glossaryfootnotes":  ("c_glossaryFootnotes", None),

    "notes/abovenotespace":     ("s_abovenotespace", lambda w,v: "{:.3f}".format(float(v))),
    "notes/fnfontsize":         ("s_fnfontsize", lambda w,v: "{:.3f}".format(float(v))),
    "notes/fnlinespacing":      ("s_fnlinespacing", lambda w,v: "{:.3f}".format(float(v))),
    "notes/internotespace":     ("s_internote", lambda w,v: "{:.3f}".format(float(v))),

    "fontregular":              ("bl_fontR", lambda w,v: v[0]),
    "fontbold":                 ("bl_fontB", lambda w,v: v[0]),
    "fontitalic":               ("bl_fontI", lambda w,v: v[0]),
    "fontbolditalic":           ("bl_fontBI", lambda w,v: v[0]),
    "fontextraregular":         ("bl_fontExtraR", lambda w,v: v[0]),
    "versenumfont":             ("bl_verseNumFont", lambda w,v: v[0]),
    "font/features":            ("t_fontfeatures", None),
    "font/usegraphite":         ("c_useGraphite", None),
    "fontbold/fakeit":          ("c_fakebold", None),
    "fontitalic/fakeit":        ("c_fakeitalic", None),
    "fontbolditalic/fakeit":    ("c_fakebolditalic", None),
    "fontbold/embolden":        ("s_boldembolden", lambda w,v: ":embolden={:.2f}".format(float(v)) if float(v) != 0.00 and w.get("c_fakebold") else ""),
    "fontitalic/embolden":      ("s_italicembolden", lambda w,v: ":embolden={:.2f}".format(float(v)) if float(v) != 0.00 and w.get("c_fakeitalic") else ""),
    "fontbolditalic/embolden":  ("s_bolditalicembolden", lambda w,v: ":embolden={:.2f}".format(float(v)) if float(v) != 0.00 and w.get("c_fakebolditalic") else ""),
    "fontbold/slant":           ("s_boldslant", lambda w,v: ":slant={:.4f}".format(float(v)) if float(v) != 0.0000 and w.get("c_fakebold") else ""),
    "fontitalic/slant":         ("s_italicslant", lambda w,v: ":slant={:.4f}".format(float(v)) if float(v) != 0.0000 and w.get("c_fakeitalic") else ""),
    "fontbolditalic/slant":     ("s_bolditalicslant", lambda w,v: ":slant={:.4f}".format(float(v)) if float(v) != 0.0000 and w.get("c_fakebolditalic") else ""),
    "snippets/fancyintro":      ("c_prettyIntroOutline", None),
    "snippets/pdfx1aoutput":    ("c_PDFx1aOutput", None),
    "snippets/diglot":          ("c_diglot", lambda w,v: True if v else False),
    "snippets/fancyborders":    ("c_borders", None),
    "snippets/imgcredits":      ("c_includeillustrations", None),
}

_fontstylemap = {
    '': '',
    'Regular': '',
    'Bold': '/B',
    'Italic': '/I',
    'Bold Italic': '/BI',
    'Oblique': '/I',
    'Bold Oblique': 'BI'
}

class TexModel:
    _peripheralBooks = ["FRT", "INT", "GLO", "TDX", "NDX", "CNC", "OTH", "BAK", "XXA", "XXB", "XXC", "XXD", "XXE", "XXF", "XXG"]
    _fonts = {
        "fontregular":              ("bl_fontR", None, None, None, None),
        "fontbold":                 ("bl_fontB", None, "c_fakebold", "fontbold/embolden", "fontbold/slant"),
        "fontitalic":               ("bl_fontI", None, "c_fakeitalic", "fontitalic/embolden", "fontitalic/slant"),
        "fontbolditalic":           ("bl_fontBI", None, "c_fakebolditalic", "fontbolditalic/embolden", "fontbolditalic/slant"),
        "fontextraregular":         ("bl_fontExtraR", "c_useFallbackFont", None, None, None),
        "versenumfont":             ("bl_verseNumFont", "c_inclVerseDecorator", None, None, None)
    }
    _hdrmappings = {
        "First Reference":           r"\firstref",
        "Last Reference":            r"\lastref",
        "Reference Range":           r"\rangeref",
        "Page Number":               r"\pagenumber",
        "Time (HH:MM)":              r"\hrsmins",
        "Date (YYYY-MM-DD)":         r"\isodate",
        "-empty-":                   r"\empty"
    }
    _mirrorRL = {r'\lastref':    r'\firstref',
                 r'\firstref':   r'\lastref'
    }
    _swapRL = {'left':   'right',
               'center': 'center',
               'right':  'left'
    }
    _glossarymarkup = {
        "None":                    r"\1",
        None:                      r"\1",
        "format as bold":          r"\\bd \1\\bd*",
        "format as italics":       r"\\it \1\\it*",
        "format as bold italics":  r"\\bdit \1\\bdit*",
        "format with emphasis":    r"\\em \1\\em*",
        "with ⸤floor⸥ brackets":   r"\u2E24\1\u2E25",
        "with ⌊floor⌋ characters": r"\u230a\1\u230b",
        "with ⌞corner⌟ characters":r"\u231e\1\u231f",
        "star *before word":       r"*\1",
        "star after* word":        r"\1*",
        "circumflex ^before word": r"^\1",
        "circumflex after^ word":  r"\1^"
    }
    _snippets = {
        "snippets/fancyintro":            ("c_prettyIntroOutline", FancyIntro),
        "snippets/pdfx1aoutput":          ("c_PDFx1aOutput", PDFx1aOutput),
        "snippets/diglot":                ("c_diglot", Diglot),
        "snippets/fancyborders":          ("c_borders", FancyBorders),
        "snippets/imgcredits":            ("c_includeillustrations", ImgCredits)
    }
    _settingmappings = {
        "notes/xrcallers": "crossrefs",
        "notes/fncallers": "footnotes"
    }

    def __init__(self, printer, path, ptsettings, prjid=None):
        from ptxprint.view import VersionStr
        self.VersionStr = VersionStr
        self.printer = printer
        self.ptsettings = ptsettings
        self.changes = None
        self.localChanges = None
        self.debug = False
        libpath = os.path.abspath(os.path.dirname(__file__))
        self.dict = {"/ptxpath": path.replace("\\","/"),
                     "/ptxprintlibpath": libpath.replace("\\","/"),
                     "/iccfpath": os.path.join(libpath, "ps_cmyk.icc").replace("\\","/"),
                     "/ptx2pdf": self.printer.scriptsdir.replace("\\", "/")}
        self.prjid = prjid
        if self.prjid is not None:
            self.dict['project/id'] = self.prjid
        if self.printer is not None:
            self.sheets = Sheets(self.printer.getStyleSheets(generated=True))
            self.update()

    def docdir(self):
        if self.asBool("project/useprintdraftfolder"):
            base = os.path.join(self.dict["/ptxpath"], self.dict["project/id"])
            docdir = os.path.join(base, 'PrintDraft')
        else:
            base = self.printer.working_dir
            docdir = base
        return docdir, base

    def update(self):
        """ Update model from UI """
        j = os.path.join
        rel = lambda x, y:os.path.relpath(x, y).replace("\\", "/")
        self.printer.setDate()  # Update date/time to now
        cpath = self.printer.configPath(self.printer.configName())
        rcpath = self.printer.configPath("")
        self.updatefields(ModelMap.keys())
        docdir, base = self.docdir()
        self.dict["document/directory"] = "." # os.path.abspath(docdir).replace("\\","/")
        self.dict['project/adjlists'] = rel(j(cpath, "AdjLists"), docdir).replace("\\","/") + "/"
        self.dict['project/piclists'] = rel(j(self.printer.working_dir, "tmpPicLists"), docdir).replace("\\","/") + "/"
        self.dict['project/id'] = self.printer.prjid
        self.dict['config/name'] = self.printer.configId
        self.dict['/ptxrpath'] = rel(self.dict['/ptxpath'], docdir)
        self.dict['/cfgrpath'] = rel(cpath, docdir)
        self.readFonts(self.printer)
        self.processFonts(self.printer)
        self.processHdrFtr(self.printer)
        # sort out caseless figures folder. This is a hack
        for p in ("Figures", "figures"):
            picdir = j(base, p)
            if os.path.exists(picdir):
                break
        self.dict["project/picdir"] = rel(picdir, docdir).replace("\\","/")
        # Look in local Config folder for ptxprint-mods.tex, and drop back to shared/ptxprint if not found
        fpath = j(cpath, "ptxprint-mods.tex")
        if not os.path.exists(fpath):
            fpath = j(rcpath, "ptxprint-mods.tex")
        self.dict['/modspath'] = rel(fpath, docdir).replace("\\","/")
        # Look in local Config folder for NestedStyles.sty, and drop back to shared/ptxprint if not found
        fpath = j(cpath, "NestedStyles.sty")
        if not os.path.exists(fpath):
            fpath = j(rcpath, "NestedStyles.sty")
        self.dict['/nststypath'] = rel(fpath, docdir).replace("\\","/")
        # If Diglot, look in local Config folder for NestedStylesR.sty, and drop back to shared/ptxprint if not found
        fpathR = j(cpath, "NestedStylesR.sty")
        if self.dict["document/ifdiglot"] == "":
            if not os.path.exists(fpathR):
                fpathR = j(rcpath, "NestedStylesR.sty")
        if "document/diglotcfgrpath" not in self.dict:
            self.dict["document/diglotcfgrpath"] = ""
        self.dict['/nststypathR'] = rel(fpathR, docdir).replace("\\","/")
        self.dict['paragraph/linespacingfactor'] = "{:.3f}".format(float(self.dict['paragraph/linespacing']) / 14 / float(self.dict['paper/fontfactor']))
        self.dict['paragraph/ifhavehyphenate'] = "" if os.path.exists(os.path.join(self.printer.configPath(""), \
                                                       "hyphen-"+self.dict["project/id"]+".tex")) else "%"
        # forward cleanup. If ask for ptxprint-mods.tex but don't have it, copy PrintDraft-mods.tex
        if self.dict["project/ifusemodssty"] == "":
            modspath = os.path.join(cpath, "ptxprint-mods.sty")
            if not os.path.exists(modspath):
                spath = os.path.join(docdir, "PrintDraft-mods.sty")
                if os.path.exists(spath):
                    copyfile(spath, modspath)

    def updatefields(self, a):
        global get
        def get(k): return self[k]
        for k in a:
            v = ModelMap[k]
            val = self.printer.get(v[0]) if v[0] is not None else None
            if v[1] is not None:
                self.dict[k] = v[1](self.printer, val)
            else:
                self.dict[k] = val

    def __getitem__(self, key):
        return self.dict[key]

    def __setitem__(self, key, value):
        self.dict[key] = value

    def asBool(self, key, true=None, false=None):
        val = self.dict.get(key, None)
        if val is None:
            return False
        elif true is not None:
            return val == true
        elif false is not None:
            return val != false
        elif isinstance(val, bool):
            return val
        elif val == "%" or val == "false":
            return False
        else:
            return True

    def readFonts(self, printer):
        for k, v in self._fonts.items():
            finfo = printer.get(v[0])
            # print(k, v[0], finfo)
            for i, a in enumerate(("name", "style")):
                self.dict[k+"/"+a] = finfo[i]

    def processFonts(self, printer):
        """ Update model fonts from UI """
        badfonts = set()
        for p in self._fonts.keys():
            if p in self.dict:
                del self.dict[p]
        frn = self.dict.get("fontregular/name", "")
        if frn is None or frn == "":
            self.dict["fontregular/name"] = "Arial"     # Fallback
        for p in ['fontregular'] + list(self._fonts.keys()):
            if p in self.dict:
                continue
            name = self.dict.get(p+"/name", "")
            style = self.dict.get(p+"/style", "")
            # import pdb; pdb.set_trace()
            f = TTFont(name, style)
            # print(p, f.filename, f.family, f.style)
            if f.filename is None:
                if self._fonts[p][1] is None or printer.get(self._fonts[p][1]):
                    badfonts.add((name or f.filename or "", style))
                if p != "fontregular" and self._fonts[p][2] is not None:
                    regname = self.dict["fontregular/name"]
                    regstyle = self.dict["fontregular/style"]
                    f = TTFont(regname, regstyle)
                    if printer is not None:
                        printer.set(self._fonts[p][2], True)
                        printer.set(self._fonts[p][0], (name, style))
                        if self._fonts[p][3] is not None:
                            self.updatefields([self._fonts[p][3]])
                        # print("Setting {} to {}".format(p, reg))
            if 'Silf' in f and self.asBool("font/usegraphite"):
                engine = "/GR"
            else:
                engine = ""
            fname = f.family
            #print([p, name, style, f.family, f.style, f.filename])
            if f.style is not None and len(f.style):
                s = _fontstylemap.get(f.style," " + f.style)
                fname = f.family + s
            self.dict[p] = "[{}]".format(f.filename.as_posix()) if f.usepath else fname
            self.dict[p+"/engine"] = engine
        featstring = self.dict["font/features"]
        if featstring is not None and len(featstring):
            if printer is not None:
                printer.set(ModelMap["font/features"][0], featstring)
            f = TTFont(self.dict["fontregular/name"], self.dict["fontregular/style"])
            f.features = {}
            for l in re.split(r'\s*[,;:]\s*|\s+', featstring):
                if '=' in l:
                    k, v = l.split('=')
                    f.features[k.strip()] = v.strip()
            if len(f.features):
                self.dict['font/texfeatures'] = ":"+ ":".join("{0}={1}".format(f.feats.get(fid, fid),
                                                f.featvals.get(fid, {}).get(int(v), v)) for fid, v in f.features.items())
            else:
                self.dict['font/texfeatures'] = ""
        else:
            self.dict['font/texfeatures'] = ""
        badfonts.discard(("", ""))
        if len(badfonts):
            printer.doError("Font(s) missing or incorrectly installed:\n" \
                    + ", ".join("{} {}".format(*x) for x in badfonts if len(x[0])), \
                    secondary="If using Windows, please re-install the font as\n" \
                    + "Administrator, and right-click to 'Install for ALL Users'.", \
                    title="Error: Missing Font(s)")
        
    def processHdrFtr(self, printer):
        """ Update model headers from model UI read values """
        diglot = True if self.dict["document/ifdiglot"] == "" else False
        v = self.dict["footer/ftrcenter"]
        pri = self.dict["footer/ftrcenterpri"] # boolean
        t = self._hdrmappings.get(v, v)
        if diglot:
            t = self._addLR(t, pri)
        self.dict['footer/oddcenter'] = t

        mirror = self.asBool("header/mirrorlayout")
        for side in ('left', 'center', 'right'):
            v = self.dict["header/hdr"+side]
            pri = self.dict["header/hdr"+side+"pri"] # boolean
            t = self._hdrmappings.get(v, v)
            if diglot:
                t = self._addLR(t, pri)
                    
            self.dict['header/odd{}'.format(side)] = t
            if mirror:
                self.dict['header/even{}'.format(self._swapRL[side])] = self.mirrorHeaders(t, diglot)
            else:
                self.dict['header/even{}'.format(side)] = t
                
            if t.startswith((r'\first', r'\last', r'\range')): # ensure noVodd + noVeven is \empty
                self.dict['header/noVodd{}'.format(side)] = r'\empty'
            else:
                self.dict['header/noVodd{}'.format(side)] = t  # copy the other header as is
            if mirror:
                if t.startswith((r'\first', r'\last', r'\range')):
                    self.dict['header/noVeven{}'.format(self._swapRL[side])] = r'\empty'
                else:
                    self.dict['header/noVeven{}'.format(self._swapRL[side])] = self.mirrorHeaders(t, diglot)
            else:
                if t.startswith((r'\first', r'\last', r'\range')): # ensure noVodd + noVeven is \empty
                    self.dict['header/noVeven{}'.format(side)] = r'\empty'
                else:
                    self.dict['header/noVeven{}'.format(side)] = t 

    def _addLR(self, t, pri):
        if t in [r"\firstref", r"\lastref", r"\rangeref", r"\pagenumber", r"\hrsmins", r"\isodate"]:                
            if pri:
                t = t+'L'
            else:
                t = t+'R'
        elif t == r"\empty":
            pass
        else:
            if pri:
                t = "\headfootL{{{}}}".format(t)
            else:
                t = "\headfootR{{{}}}".format(t)
        return t

    def mirrorHeaders(self, h, dig=False):
        if dig and h.endswith(("L", "R")):
            try:
                return self._mirrorRL[h[:-1]]+h[-1:]
            except KeyError:
                return h
        else:
            try:
                return self._mirrorRL[h]
            except KeyError:
                return h
        
    def texfix(self, path):
        return path.replace(" ", r"\ ")

    def asTex(self, template="template.tex", filedir=".", jobname="Unknown"):
        for k, v in self._settingmappings.items():
            if self.dict[k] == "":
                self.dict[k] = self.ptsettings.dict.get(v, "a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,w,x,y,z")
        res = []
        docdir, docbase = self.docdir()
        self.dict['jobname'] = jobname
        with universalopen(os.path.join(os.path.dirname(__file__), template)) as inf:
            for l in inf.readlines():
                if l.startswith(r"\ptxfile"):
                    res.append("\\PtxFilePath={"+os.path.relpath(filedir, docdir).replace("\\","/")+"/}\n")
                    for i, f in enumerate(self.dict['project/bookids']):
                        fname = self.dict['project/books'][i]
                        # if f in ["XXA", "XXB", "XXC", "XXD", "XXE", "XXF", "XXG",
                                # "GLO", "TDX", "NDX", "CNC", "OTH", "BAK"]:
                            # mirror = self.asBool("header/mirrorlayout")
                            # for toe in ['title', 'noVodd', 'noVeven']:
                                # for side in ('left', 'center', 'right'):
                                    # v = self.dict["header/hdr"+side]
                                    # t = self._hdrmappings.get(v, v)
                                    # if not t.endswith("ref"):
                                        # if mirror and side != 'center' and toe == 'noVeven': 
                                            # res.append("\\def\RH{}{}{{{}}}\n".format(toe, self._swapRL[side], t))
                                        # else:
                                            # res.append("\\def\RH{}{}{{{}}}\n".format(toe, side, t))
                                # res.append("\n")
                        if self.asBool('document/ifomitsinglechnum') and \
                           self.asBool('document/showchapternums') and \
                           f in oneChbooks:
                            res.append("\\OmitChapterNumbertrue\n")
                            res.append("\\ptxfile{{{}}}\n".format(fname))
                            res.append("\\OmitChapterNumberfalse\n")
                        elif self.dict['paper/columns'] == '2' and \
                             self.dict['document/clsinglecol'] and \
                             f in self.dict['document/clabelbooks']:
                            res.append("\\BodyColumns=1\n")
                            res.append("\\ptxfile{{{}}}\n".format(fname))
                            res.append("\\BodyColumns=2\n")
                        else:
                            res.append("\\ptxfile{{{}}}\n".format(fname))
                elif l.startswith(r"%\extrafont"):
                    spclChars = re.sub(r"\\[uU]([0-9a-fA-F]{4,6})", lambda m:chr(int(m.group(1), 16)), self.dict["paragraph/missingchars"])
                    # print(spclChars.split(' '), [len(x) for x in spclChars.split(' ')])
                    if self.dict["paragraph/ifusefallback"] and len(spclChars):
                        badlist = "\u2018\u2019\u201c\u201d*#%"
                        a = ["".join(chr(ord(c) + 16 if ord(c) < 58 else ord(c) - 23) for c in str(hex(ord(x)))[2:]).lower() for x in spclChars.split(" ")]
                        b = ["".join((c) for c in str(hex(ord(x)))[2:]).lower() for x in spclChars.split(" ")]
                        c = [x for x in zip(a,b) if chr(int(x[1],16)) not in badlist]
                        if not len(c):
                            continue
                        res.append("% for defname @active+ @+digit => 0->@, 1->a ... 9->i A->j B->k .. F->o\n")
                        res.append("% 12 (size) comes from \\p size\n")
                        res.append('\\def\\extraregular{{"{}"}}\n'.format(self.dict["fontextraregular"]))
                        res.append("\\catcode`\\@=11\n")
                        res.append("\\def\\do@xtrafont{\\x@\\s@textrafont\\ifx\\thisch@rstyle\\undefined\\m@rker\\else\\thisch@rstyle\\fi}\n")
                        for a,b in c:
                            res.append("\\def\\@ctive{}{{{{\\do@xtrafont {}{}}}}}\n".format(a, '^'*len(b), b))
                            res.append("\\DefineActiveChar{{{}{}}}{{\\@ctive{}}}\n".format( '^'*len(b), b, a))
                        res.append("\\@ctivate\n")
                        res.append("\\catcode`\\@=12\n")
                    else:
                        res.append("% No special/missing characters specified for fallback font")
                elif l.startswith(r"%\optimizepoetry"):
                    bks = self.dict["document/clabelbooks"]
                    if self.dict["document/ifchaplabels"] == "%" and len(bks):
                        for bk in bks.split(" "):
                            if bk in self.dict['project/bookids']:
                                res.append("\setbookhook{{start}}{{{}}}{{\gdef\BalanceThreshold{{3}}\clubpenalty=50\widowpenalty=50}}\n".format(bk))
                                res.append("\setbookhook{{end}}{{{}}}{{\gdef\BalanceThreshold{{0}}\clubpenalty=10000\widowpenalty=10000}}\n".format(bk))
                elif l.startswith(r"%\snippets"):
                    for k, c in self._snippets.items():
                        v = self.asBool(k)
                        if v:
                            fn = getattr(c[1], 'generateTex', None)
                            if fn is not None:
                                res.append(fn(v, self))
                            elif c[1].processTex:
                                res.append(c[1].texCode.format(**self.dict))
                            else:
                                res.append(c[1].texCode)
                else:
                    res.append(l.format(**self.dict))
        return "".join(res).replace("\OmitChapterNumberfalse\n\OmitChapterNumbertrue\n","")

    def runConversion(self, infpath, outdir):
        outfpath = infpath
        if self.dict['project/processscript'] and self.dict['project/selectscript']:
            outfpath = os.path.join(outdir, os.path.basename(infpath))
            doti = outfpath.rfind(".")
            if doti > 0:
                outfpath = outfpath[:doti] + "-conv" + outfpath[doti:]
            cmd = [self.dict["project/selectscript"], infpath, outfpath]
            checkoutput(cmd) # dont't pass cmd as list when shell=True
        return outfpath

    def runChanges(self, changes, dat):
        for c in changes:
            if self.debug: print(c)
            if c[0] is None:
                dat = c[1].sub(c[2], dat)
            else:
                newdat = c[0].split(dat)
                for i in range(1, len(newdat), 2):
                    newdat[i] = c[1].sub(c[2], newdat[i])
                dat = "".join(newdat)
        return dat

    def convertBook(self, bk, outdir, prjdir):
        if self.changes is None:
            if self.asBool('project/usechangesfile'):
                # print("Applying PrntDrftChgs:", os.path.join(prjdir, 'PrintDraftChanges.txt'))
                self.changes = self.readChanges(os.path.join(prjdir, 'PrintDraftChanges.txt'))
            else:
                self.changes = []
        printer = self.printer
        self.makelocalChanges(printer, bk)
        customsty = os.path.join(prjdir, 'custom.sty')
        if not os.path.exists(customsty):
            self.dict["/nocustomsty"] = "%"
        else:
            self.dict["/nocustomsty"] = ""
        fbkfm = self.ptsettings['FileNameBookNameForm']
        fprfx = self.ptsettings['FileNamePrePart'] or ""
        fpost = self.ptsettings['FileNamePostPart'] or ""
        bknamefmt = fprfx + fbkfm.replace("MAT","{bkid}").replace("41","{bkcode}") + fpost
        fname = bknamefmt.format(bkid=bk, bkcode=bookcodes.get(bk, 0))
        infpath = os.path.join(prjdir, fname)
        if not self.dict['project/runscriptafter']:
            infpath = self.runConversion(infpath, outdir)
        outfname = os.path.basename(infpath)
        # outfname = fname
        doti = outfname.rfind(".")
        if doti > 0:
            outfname = outfname[:doti] + "-draft" + outfname[doti:]
        outfpath = os.path.join(outdir, outfname)
        with universalopen(infpath) as inf:
            dat = inf.read()
            if self.changes is not None:
                dat = self.runChanges(self.changes, dat)

            if self.dict['project/canonicalise']:
                syntaxErrors = []
                try:
                    doc = Usfm([dat], self.sheets)
                    doc.normalise()
                except SyntaxError as e:
                    print(self.prjid, bk, str(e).split('line', maxsplit=1)[1])
                    syntaxErrors.append("{} {} line:{}".format(self.prjid, bk, str(e).split('line', maxsplit=1)[1]))
                except IndexError as e:
                    syntaxErrors.append("{} {} line:{}".format(self.prjid, bk, str(e)))
                if len(syntaxErrors):
                    self.printer.doError("Failed to canonicalise texts due to a Syntax Error:",        
                    secondary="\n".join(syntaxErrors)+"\n\nIf original USFM text is correct, then check "+ \
                    "if PrintDraftChanges.txt has caused the error(s).", 
                    title="PTXprint [{}] - Canonicalise Text Error!".format(self.VersionStr))
                else:
                    dat = str(doc)

            if self.localChanges is not None:
                dat = self.runChanges(self.localChanges, dat)
        with open(outfpath, "w", encoding="utf-8") as outf:
            outf.write(dat)
        if self.dict['project/runscriptafter']:
            bn = os.path.basename(self.runConversion(outfpath, outdir))
        else:
            bn = os.path.basename(outfpath)

        if '-conv' in bn:
            newname = re.sub("(\-draft\-conv|\-conv\-draft|\-conv)", "-draft", bn)
            copyfile(os.path.join(outdir, bn), os.path.join(outdir, newname))
            os.remove(os.path.join(outdir, bn))
            return newname
        else:
            return bn

    def readChanges(self, fname):
        changes = []
        if not os.path.exists(fname):
            return []
        qreg = r'(?:"((?:[^"\\]|\\.)*?)"|' + r"'((?:[^'\\]|\\.)*?)')"
        with universalopen(fname) as inf:
            for i, l in enumerate(inf.readlines()):
                l = l.strip().replace(u"\uFEFF", "")
                l = re.sub(r"\s*#.*$", "", l)
                if not len(l):
                    continue
                try:
                    m = re.match(r"^"+qreg+r"\s*>\s*"+qreg, l)
                    if m:
                        changes.append((None, regex.compile(m.group(1) or m.group(2), flags=regex.M),
                                        m.group(3) or m.group(4) or ""))
                        continue
                    m = re.match(r"^in\s+"+qreg+r"\s*:\s*"+qreg+r"\s*>\s*"+qreg, l)
                    if m:
                        changes.append((regex.compile("("+(m.group(1) or m.group(2))+")", flags=regex.M), \
                        regex.compile((m.group(3) or m.group(4)), flags=regex.M), (m.group(5) or m.group(6) or "")))
                except regex._regex_core.error as e:
                    self.printer.doError("Regular expression error: {} in changes file at line {}".format(str(e), i+1))
        if not len(changes):
            return None
        if self.printer is not None and self.printer.get("c_tracing"):
            print("List of PrintDraftChanges:-------------------------------------------------------------")
            report = "\n".join("{} -> {}".format(p[1].pattern, p[2]) for p in changes)
            if getattr(self.printer, "logger", None) is not None:
                self.printer.logger.insert_at_cursor(v)
            else:
                try:
                    print(report)
                except UnicodeEncodeError:
                    print("Unable to print details of PrintDraftChanges.txt")
        return changes

    def makelocalChanges(self, printer, bk):
        self.localChanges = []
        if bk == "GLO" and self.dict['document/filterglossary']:
            self.filterGlossary(printer)
        first = int(self.dict["document/chapfrom"])
        last = int(self.dict["document/chapto"])
        
        # Fix things that other parsers accept and we don't
        self.localChanges.append((None, regex.compile(r"(\\[cv] [^ \\\n]+)(\\)", flags=regex.S), r"\1 \2"))
        # This section handles PARTIAL books (from chapter X to chapter Y)
        if self.asBool("document/ifchaplabels", true="%"):
            clabel = self.dict["document/clabel"]
            clbooks = self.dict["document/clabelbooks"].split()
            # print("Chapter label: '{}' for '{}' with {}".format(clabel, " ".join(clbooks), bk))
            if len(clabel) and (not len(clbooks) or bk in clbooks):
                self.localChanges.append((None, regex.compile(r"(\\c 1)(?=\s*\r?\n|\s)", flags=regex.S), r"\\cl {}\n\1".format(clabel)))
        if not self.asBool("project/multiplebooks"):
            if first > 1:
                self.localChanges.append((None, regex.compile(r"\\c 1 ?\r?\n.+(?=\\c {} ?\r?\n)".format(first), flags=regex.S), ""))
            if last < int(chaps.get(bk)):
                self.localChanges.append((None, regex.compile(r"\\c {} ?\r?\n.+".format(last+1), flags=regex.S), ""))

        # Throw out the known "nonpublishable" markers and their text (if any)
        self.localChanges.append((None, regex.compile(r"\\(usfm|ide|rem|sts|restore|pubinfo)( .*?)?\r?\n(?=\\)", flags=regex.M), ""))

        # If a printout of JUST the book introductions is needed (i.e. no scripture text) then this option is very handy
        if not self.asBool("document/ifmainbodytext"):
            self.localChanges.append((None, regex.compile(r"\\c 1 ?\r?\n.+".format(first), flags=regex.S), ""))

        # Elipsize ranges of MISSING/Empty verses in the text (if 3 or more verses in a row are empty...) 
        if self.asBool("document/elipsizemptyvs"):
            self.localChanges.append((None, regex.compile(r"\\v (\d+)([-,]\d+)? ?\r?\n(\\v (\d+)([-,]\d+)? ?\r?\n){1,}", flags=regex.M), r"\\v \1-\4 {...} "))
            # self.localChanges.append((None, regex.compile(r"(\r?\n\\c \d+ ?)(\r?\n\\v 1)", flags=regex.M), r"\1\r\n\\p \2"))
            self.localChanges.append((None, regex.compile(r" (\\c \d+ ?)(\r?\n\\v 1)", flags=regex.M), r" \r\n\1\r\n\\p \2"))
            # self.localChanges.append((None, regex.compile(r"(\{\.\.\.\}) (\\c \d+ ?)\r?\n\\v", flags=regex.M), r"\1\r\n\2\r\n\\p \\v"))
            self.localChanges.append((None, regex.compile(r"(\\c \d+ ?(\r?\n)+\\p (\r?\n)?\\v [\d-]+ \{\.\.\.\} ?(\r?\n)+)(?=\\c)", flags=regex.M), r"\1\\m {...}\r\n"))

        # Probably need to make this more efficient for multi-book and lengthy glossaries (cache the GLO & changes reqd etc.)
        if self.asBool("notes/glossaryfootnotes"):
            self.makeGlossaryFootnotes(printer, bk)

        # Glossary Word markup: Remove the second half of the \w word|glossary-form\w* and apply chosen glossary markup
        v = self.dict["document/glossarymarkupstyle"]
        gloStyle = self._glossarymarkup.get(v, v)
        self.localChanges.append((None, regex.compile(r"\\\+?w (.+?)(\|.+?)?\\\+?w\*", flags=regex.M), gloStyle))
        
        # Remember to preserve \figs ... \figs for books that can't have PicLists (due to no ch:vs refs in them)
        if self.asBool("document/ifinclfigs") and bk in self._peripheralBooks:
            # Remove any illustrations which don't have a |p| 'loc' field IF this setting is on
            if self.asBool("document/iffigexclwebapp"):
                self.localChanges.append((None, regex.compile(r'(?i)\\fig ([^|]*\|){3}([aw]+)\|[^\\]*\\fig\*', flags=regex.M), ''))  # USFM2
                self.localChanges.append((None, regex.compile(r'(?i)\\fig [^\\]*\bloc="[aw]+"[^\\]*\\fig\*', flags=regex.M), ''))    # USFM3

            # Change orig-fname to newbase-name + new extension
            figChangeList = self.figNameChanges(printer, bk)
            if len(figChangeList):
                missingPics = []
                for origfn,tempfn in figChangeList:
                    origfn = re.escape(origfn)
                    if tempfn != "":
                        self.localChanges.append((None, regex.compile(r"(?i)(?<fig>\\fig .*?\|){}(\|.+?\\fig\*)".format(origfn), \
                                                     flags=regex.M), r"\g<fig>{}\2".format(tempfn)))                               #USFM2
                        self.localChanges.append((None, regex.compile(r'(?i)(?<fig>\\fig .*?src="){}(" .+?\\fig\*)'.format(origfn), \
                                                     flags=regex.M), r"\g<fig>{}\2".format(tempfn)))                               #USFM3
                    else:
                        missingPics += [origfn]
                        if self.asBool("document/iffigskipmissing"):
                            # print("(?i)(\\fig .*?\|){}(\|.+?\\fig\*)".format(origfn), "--> Skipped!!!!")
                            self.localChanges.append((None, regex.compile(r"(?i)\\fig .*?\|{}\|.+?\\fig\*".format(origfn), flags=regex.M), ""))     #USFM2
                            self.localChanges.append((None, regex.compile(r'(?i)\\fig .*?src=\"{}\" .+?\\fig\*'.format(origfn), flags=regex.M), "")) #USFM3

            if self.asBool("document/iffighiderefs"): # del ch:vs from caption 
                self.localChanges.append((None, regex.compile(r"(\\fig [^\\]+?\|)([0-9:.\-,\u2013\u2014]+?)(\\fig\*)", \
                                          flags=regex.M), r"\1\3"))   # USFM2
                self.localChanges.append((None, regex.compile(r'(\\fig .+?)(ref=\"\d+[:.]\d+([-,\u2013\u2014]\d+)?\")(.*?\\fig\*)', \
                                          flags=regex.M), r"\1\4"))   # USFM3
        else:
            # Strip out all \figs from the USFM as an internally generated temp PicList will do the same job
            self.localChanges.append((None, regex.compile(r'\\fig [^\\]+?\\fig\*', flags=regex.M), ""))
        
        if not self.asBool("document/bookintro"): # Drop Introductory matter
            self.localChanges.append((None, regex.compile(r"\\i(s|m|mi|mt|p|pi|li\d?|pq|mq|pr|b|q\d?) .+?\r?\n", flags=regex.M), "")) 

        if not self.asBool("document/introoutline"): # Drop ALL Intro Outline matter & Intro Outline References
            # Wondering whether we should restrict this to just the GEN...REV books (as some xtra books only use \ixx markers for content)
            self.localChanges.append((None, regex.compile(r"\\(iot|io\d) [^\\]+", flags=regex.M), ""))
            self.localChanges.append((None, regex.compile(r"\\ior .+?\\ior\*\s?\r?\n", flags=regex.M), ""))

        if not self.asBool("document/sectionheads"): # Drop ALL Section Headings (which also drops the Parallel passage refs now)
            self.localChanges.append((None, regex.compile(r"\\[sr] .+", flags=regex.M), ""))

        if not self.asBool("document/parallelrefs"): # Drop ALL Parallel Passage References
            self.localChanges.append((None, regex.compile(r"\\r .+", flags=regex.M), ""))

        if self.asBool("document/preventorphans"): # Prevent orphans at end of *any* paragraph [anything that isn't followed by a \v]
            # self.localChanges.append((None, regex.compile(r" ([^\\ ]+?) ([^\\ ]+?\r?\n)(?!\\v)", flags=regex.S), r" \1\u00A0\2"))
            # OLD RegEx: Keep final two words of \q lines together [but doesn't work if there is an \f or \x at the end of the line] 
            self.localChanges.append((None, regex.compile(r"(\\q\d?(\s?\r?\n?\\v)?( \S+)+( (?!\\)[^\\\s]+)) (\S+\s*\n)", \
                                            flags=regex.M), r"\1\u2000\5"))
            self.localChanges.append((None, regex.compile(r"(\s+[^ 0-9\\\n\u2000\u00A0]+) ([^ 0-9\\\n\u2000\u00A0]+\n(?:\\[pmqsc]|$))", flags=regex.S), r"\1\u2000\2"))

        if self.asBool("document/preventwidows"):
            # Push the verse number onto the next line (using NBSP) if there is
            # a short widow word (3 characters or less) at the end of the line
            self.localChanges.append((None, regex.compile(r"(\\v \d+([-,]\d+)? [\w]{1,3}) ", flags=regex.M), r"\1\u2000")) 

        # By default, HIDE chapter numbers for all non-scripture (Peripheral) books (unless "Show... is checked)
        if not self.asBool("document/showxtrachapnums") and bk in TexModel._peripheralBooks:
            self.localChanges.append((None, regex.compile(r"(\\c \d+ ?\r?\n)", flags=regex.M), ""))

        if self.asBool("document/ch1pagebreak"):
            self.localChanges.append((None, regex.compile(r"(\\c 1 ?\r?\n)", flags=regex.M), r"\pagebreak\r\n\1"))

        if self.asBool("document/glueredupwords"): # keep reduplicated words together
            self.localChanges.append((None, regex.compile(r"(?<=[ ])(\w{3,}) \1(?=[\s,.!?])", flags=regex.M), r"\1\u2000\1")) 
        
        if self.asBool("notes/addcolon"): # Insert a colon between \fq (or \xq) and following \ft (or \xt)
            self.localChanges.append((None, regex.compile(r"(\\[fx]q .+?):* ?(\\[fx]t)", flags=regex.M), r"\1: \2")) 
        
        if self.asBool("notes/keepbookwithrefs"): # keep Booknames and ch:vs nums together within \xt and \xo 
            self.localChanges.append((regex.compile(r"(\\[xf]t [^\\]+)"), regex.compile(r"(?<!\\[fx][rto]) (\d+[:.]\d+([-,]\d+)?)"), r"\u00A0\1"))
            self.localChanges.append((regex.compile(r"(\\[xf]t [^\\]+)"), regex.compile(r"( .) "), r"\1\u00A0"))

        # keep \xo & \fr refs with whatever follows (i.e the bookname or footnote) so it doesn't break at end of line
        self.localChanges.append((None, regex.compile(r"(\\(xo|fr) (\d+[:.]\d+([-,]\d+)?)) "), r"\1\u2000"))

        for c in ("fn", "xr"):
            # Force all footnotes/x-refs to be either '+ ' or '- ' rather than '*/#'
            if self.asBool("notes/{}Override".format(c)):
                t = "+" if self.asBool("notes/if{}autocallers".format(c)) else "-"
                self.localChanges.append((None, regex.compile(r"\\{} .".format(c[0])), r"\\{} {}".format(c[0],t)))
            # Remove the [spare] space after a note caller if the caller is omitted AND if after a digit (verse number).
            if self.asBool("notes/{}omitcaller".format(c)):
                self.localChanges.append((None, regex.compile(r"(\d )(\\[{}] - .*?\\[{}]\*)\s+".format(c[0])), r"\1\2"))

        # Paratext marks no-break space as a tilde ~
        self.localChanges.append((None, regex.compile(r"~", flags=regex.M), r"\u00A0")) 

        # Remove the + of embedded markup (xetex handles it)
        self.localChanges.append((None, regex.compile(r"\\\+", flags=regex.M), r"\\"))  
            
        for c in range(1,4): # Remove any \toc lines that we don't want appearing in the Table of Contents
            if not self.asBool("document/usetoc{}".format(c)):
                self.localChanges.append((None, regex.compile(r"(\\toc{} .+)".format(c), flags=regex.M), ""))

        # Add End of Book decoration PDF to Scripture books only if FancyBorders is enabled and .PDF defined
        if self.asBool("fancy/enableborders") and self.asBool("fancy/endofbook") and bk not in self._peripheralBooks \
           and self.dict["fancy/endofbookpdf"].lower().endswith('.pdf'):
            self.localChanges.append((None, regex.compile(r"\Z", flags=regex.M), r"\r\n\z"))
        
        # Insert a rule between end of Introduction and start of body text (didn't work earlier, but might work now)
        # self.localChanges.append((None, regex.compile(r"(\\c\s1\s?\r?\n)", flags=regex.S), r"\\par\\vskip\\baselineskip\\hskip-\\columnshift\\hrule\\vskip 2\\baselineskip\n\1"))

        # Apply any changes specified in snippets
        for k, c in self._snippets.items():
            if self.printer is None:
                v = self.asBool(k)
            else:
                v = self.printer.get(c[0])
                self.dict[k] = "true" if v else "false"
            if v: # if the c_checkbox is true then extend the list with those changes
                if k == "snippets/fancyintro" and bk in self._peripheralBooks: # Only allow fancyIntros for scripture books
                    pass
                else:
                    self.localChanges.extend(c[1].regexes)

        ## Final tweaks
        # Strip out any spaces either side of an en-quad 
        self.localChanges.append((None, regex.compile(r"\s?\u2000\s?", flags=regex.M), r"\u2000")) 
        # Change double-spaces to singles
        self.localChanges.append((None, regex.compile(r"  ", flags=regex.M), r" ")) 
        # Escape special codes % and $ that could be in the text itself
        self.localChanges.append((None, regex.compile(r"([%$])", flags=regex.M), r"\\\1")) 

        if self.printer is not None and self.printer.get("c_tracing"):
            print("List of Local Changes:----------------------------------------------------------")
            report = "\n".join("{} -> {}".format(p[1].pattern, p[2]) for p in self.localChanges)
            if getattr(printer, "logger", None) is not None:
                printer.logger.insert_at_cursor(v)
            else:
                print(report)
        return self.localChanges

    def figNameChanges(self, printer, bk):
        # This method will probably disappear once we have a way to handle the peripheral books
        if printer is None:
            return([])
        figlist = []
        figchngs = []
        prjid = self.dict['project/id']
        prjdir = os.path.join(self.ptsettings.basedir, prjid)
        picdir = os.path.join(prjdir, 'PrintDraft', 'tmpPics') #.replace("\\","/")
        fname = printer.getBookFilename(bk, prjdir)
        infpath = os.path.join(prjdir, fname)
        extOrder = printer.getExtOrder()
        with universalopen(infpath) as inf:
            dat = inf.read()
            inf.close()
            figlist += re.findall(r"(?i)\\fig .*?\|(.+?\.(?=jpg|jpeg|tif|tiff|bmp|png|pdf)....?)\|.+?\\fig\*", dat)    # Finds USFM2-styled markup in text:
            figlist += re.findall(r'(?i)\\fig .+src="(.+?\.(?=jpg|jpeg|tif|tiff|bmp|png|pdf)....?)" .+?\\fig\*', dat)  # Finds USFM3-styled markup in text:
            for f in figlist:
                found = False
                for ext in extOrder:
                    if ext.lower().startswith("tif"):
                        ext = "jpg"
                    tmpf = self.newBase(f)+"."+ext
                    fname = os.path.join(picdir, tmpf)
                    if os.path.exists(fname):
                        figchngs.append((f,tmpf))
                        found = True
                        break
                if not found:
                    figchngs.append((f,"")) 
        return(figchngs)

    def base(self, fpath):
        doti = fpath.rfind(".")
        return os.path.basename(fpath[:doti])

    def codeLower(self, fpath):
        cl = re.findall(r"(?i)_?((?=ab|cn|co|hk|lb|bk|ba|dy|gt|dh|mh|mn|wa|dn|ib)..\d{5})[abc]?$", self.base(fpath))
        if cl:
            return cl[0].lower()
        else:
            return ""

    def newBase(self, fpath):
        clwr = self.codeLower(fpath)
        if len(clwr):
            return clwr
        else:
            return re.sub('[()&+,. ]', '_', self.base(fpath).lower())

    def generateNestedStyles(self, diglot=False):
        if diglot:
            pfx = "diglot"
            sfx = "R.sty"
        else:
            pfx = "notes"
            sfx = ".sty"
        rtl = self['document/ifrtl'] == "true"
        cfgname = self.printer.configName()
        nstyfname = os.path.join(self.printer.configPath(cfgname), "NestedStyles"+sfx)
        nstylist = []
        if self.dict["document/ifshowversenums"] == '':
            nstylist.append("##### Remove all verse numbers\n\\Marker v\n\\TextProperties nonpublishable\n\n")

        if not self.asBool(pfx+"/includefootnotes"):
            nstylist.append("##### Set Footnote Size and Line Spacing\n")
            nstylist.append("\\Marker {}\n\\FontSize {}\n".format("f", self.dict[pfx+'/fnfontsize']))
            nstylist.append("\\BaseLine {}pt plus 2pt\n".format(self.dict[pfx+'/fnlinespacing']))
            nstylist.append("\\Justification {}\n\n".format("Right" if rtl else "Left"))
        else:
            nstylist.append("##### Remove all footnotes\n\\Marker f\n\\TextProperties nonpublishable\n\n")

        if not self.asBool("notes/includexrefs"):
            nstylist.append("##### Set Cross-reference Size and Line Spacing\n")
            nstylist.append("\\Marker {}\n\\FontSize {}\n".format("x", self.dict[pfx+'/fnfontsize']))
            nstylist.append("\\BaseLine {}pt plus 2pt\n".format(self.dict[pfx+'/fnlinespacing']))
            nstylist.append("\\Justification {}\n\n".format("Right" if rtl else "Left"))
        else:
            nstylist.append("##### Remove all cross-references\n\\Marker x\n\\TextProperties nonpublishable\n\n")

        if self.dict[pfx+"/ifblendfnxr"]:
            nstylist.append("##### Treat x-refs as footnotes with their own caller\n\\Marker x\n\\NoteBlendInto f\n\n")

        # Adjust the amount of indent on \p according to the IndentUnit setting 2=default
        iu = float(self.dict["document/indentunit"])
        cols = int(self.dict["paper/columns"])
        nstylist.append("##### Adjust p-first-line-indent\n\\Marker p\n\\FirstLineIndent {:.3f}\n\n".format(0.250 * iu / cols))

        nstylist.append("##### Adjust poetic indents\n")
        m = ["\Marker", "\LeftMargin", "\FirstLineIndent"]
        if self.dict["paper/columns"] == "2" or self.dict["document/ifdiglot"] == "": # Double Column layout so use smaller indents
            v = [["q", "0.60", "-0.45"], ["q1", "0.60", "-0.45"], ["q2", "0.60", "-0.225"], 
                 ["q3", "0.60", "-0.112"], ["q4", "0.60", "-0.0"]]
        else: # Single column layout, so use larger (USFM.sty default) indents
            v = [["q", "1.25", "-1.00"], ["q1", "1.25", "-1.00"], ["q2", "1.25", "-0.75"],
                 ["q3", "1.25", "-0.5"], ["q4", "1.25", "-0.25"]]
        r = [list(zip(m, x)) for x in v]
        
        for mkr in r:
            for l in range(0,3):
                nstylist.append("{} {}\n".format(mkr[l][0],mkr[l][1]))
            nstylist.append("\\Justification {}\n\n".format("Right" if rtl else "Left"))

        if True: # Hack! We need to qualify this (look in USFM for a \cl and if it exists, then don't do this)
            nstylist.append("# The descriptive heading is typically considered VerseText, but then often formatted as a heading.\n")
            nstylist.append("# We need to change the TextType so that Print Draft will handle it correctly beside drop-caps.\n")
            nstylist.append("\\Marker d\n\\TextType Section\n\\SpaceBefore 0\n\n")

        for k, c in self._snippets.items():
            if self.printer is None:
                v = self.asBool(k)
            else:
                v = self.printer.get(c[0])
                self.dict[k] = "true" if v else "false"
            if v: # if the c_checkbox is true then add the stylesheet snippet for that option
                if isinstance(c[1].styleInfo, str):
                    nstylist.append(c[1].styleInfo+"\n")
                else:
                    nstylist.append(c[1].styleInfo(self)+"\n")

        if nstylist == []:
            if os.path.exists(nstyfname):
                os.remove(nstyfname)
            return []
        else:
            os.makedirs(self.printer.configPath(cfgname), exist_ok=True)
            with open(nstyfname, "w", encoding="utf-8") as outf:
                outf.write("".join(nstylist))
            return [nstyfname]

    def makeGlossaryFootnotes(self, printer, bk):
        # Glossary entries for the key terms appearing like footnotes
        prjid = self.dict['project/id']
        prjdir = os.path.join(self.ptsettings.basedir, prjid)
        fname = printer.getBookFilename("GLO", prjdir)
        infname = os.path.join(prjdir, fname)
        if os.path.exists(infname):
            with universalopen(infname, rewrite=True) as inf:
                dat = inf.read()
                ge = re.findall(r"\\p \\k (.+)\\k\* (.+)\r?\n", dat) # Finds all glossary entries in GLO book (may need to add \ili)
                if ge is not None:
                    for g in ge:
                        gdefn = regex.sub(r"\\xt (.+)\\xt\*", r"\1", g[1])
                        self.localChanges.append((None, regex.compile(r"(\\w (.+\|)?{} ?\\w\*)".format(g[0]), flags=regex.M), \
                                                                     r"\1\\f + \\fq {}: \\ft {}\\f* ".format(g[0],gdefn)))

    def filterGlossary(self, printer):
        # Only keep entries that have appeared in this collection of books
        glossentries = []
        prjid = self.dict['project/id']
        prjdir = os.path.join(self.dict["/ptxpath"], prjid)
        for bk in printer.getBooks():
            if bk not in TexModel._peripheralBooks:
                fname = printer.getBookFilename(bk, prjid)
                fpath = os.path.join(prjdir, fname)
                if os.path.exists(fpath):
                    with universalopen(fpath) as inf:
                        sfmtxt = inf.read()
                    glossentries += re.findall(r"\\w .*?\|?([^\|]+?)\\w\*", sfmtxt)
        fname = printer.getBookFilename("GLO", prjdir)
        infname = os.path.join(prjdir, fname)
        if os.path.exists(infname):
            with universalopen(infname, rewrite=True) as inf:
                dat = inf.read()
                ge = re.findall(r"\\p \\k (.+)\\k\* .+\r?\n", dat) # Finds all glossary entries in GLO book
        for delGloEntry in [x for x in ge if x not in list(set(glossentries))]:
            self.localChanges.append((None, regex.compile(r"\\p \\k {}\\k\* .+\r?\n".format(delGloEntry), flags=regex.M), ""))

