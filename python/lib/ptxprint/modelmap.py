import re
from ptxprint.utils import f2s, coltoonemax, asfloat
from dataclasses import dataclass
from typing import Callable, Optional

@dataclass
class ModelInfo:
    texname: str
    widget: str
    category: str
    process: Optional[Callable]

def get(k): return k

_map = {
    "L_":                       ("c_diglot", "diglot", lambda w,v: "L" if v else ""),
    "R_":                       ("c_diglot", "diglot", lambda w,v: "R" if v else ""),
    "date_":                    ("_date", "meta", None),
    "pdfdate_":                 ("_pdfdate", "meta", None),
    "xmpdate_":                 ("_xmpdate", "meta", None),
    "ifusediglotcustomsty_":    ("_diglotcustomsty", "diglot", lambda w,v: "%" if not v else ""),
    "ifusediglotmodsty_":       ("_diglotmodsty", "diglot", lambda w,v: "%" if not v else ""),
    "ifdiglotincludefootnotes_":("_diglotincludefn", "diglot", lambda w,v: "%" if v else ""),
    "ifdiglotincludexrefs_":    ("_diglotincludexr", "diglot", lambda w,v: "%" if v else ""),
    "transparency_":            ("fcb_outputFormat", "finish", lambda w,v: "false" if v in (None, "None", "PDF/X-4") else "true"),

    "config/notes":             ("t_configNotes", "meta", lambda w,v: v or ""),
    "config/pwd":               ("t_invisiblePassword", "meta", lambda w,v: v or ""),
    "config/version":           ("_version", "meta", None),
    "config/gitversion":        ("_gitversion", "meta", None),
    "config/name":              ("_cfgid", "meta", None),
    "config/filterpics":        ("c_filterPicList", "meta", None),
    "config/autosave":          ("c_autoSave", "uiprefs", None),
    "config/displayfontsize":   ("s_viewEditFontSize", "uiprefs", None),
    "config/texperthacks":      ("c_showTeXpertHacks", "uiprefs", None),

    "project/id":               ("_prjid", "meta", None),
    "project/bookscope":        ("r_book", "meta", None),
    "project/uilevel":          ("fcb_uiLevel", "uiprefs", None),
    "project/book":             ("ecb_book", "meta", None),
    "project/modulefile":       ("btn_chooseBibleModule", "meta", lambda w,v: v.replace("\\","/") if v is not None else ""),
    "project/booklist":         ("ecb_booklist", "meta", lambda w,v: v or ""),
    "project/ifinclfrontpdf":   ("c_inclFrontMatter", "front", None),
    "project/frontincludes":    ("btn_selectFrontPDFs", "front", lambda w,v: "\n".join('\\includepdf{{{}}}'.format(s.as_posix()) \
                                 for s in w.FrontPDFs) if (w.get("c_inclFrontMatter") and w.FrontPDFs is not None
                                                                                      and w.FrontPDFs != 'None') else ""),
    "project/ifinclbackpdf":    ("c_inclBackMatter", "peripherals", None),
    "project/backincludes":     ("btn_selectBackPDFs", "peripherals", lambda w,v: "\n".join('\\includepdf{{{}}}'.format(s.as_posix()) \
                                 for s in w.BackPDFs) if (w.get("c_inclBackMatter") and w.BackPDFs is not None
                                                                                    and w.BackPDFs != 'None') else ""),
    "project/processscript":    ("c_processScript", "advanced", None),
    "project/when2processscript": ("r_when2processScript", "advanced", None),
    "project/selectscript":     ("btn_selectScript", "advanced", lambda w,v: w.customScript.as_posix() if w.customScript is not None else ""),
    "project/selectxrfile":     ("btn_selectXrFile", "noteref", None),
    "project/usechangesfile":   ("c_usePrintDraftChanges", "advanced", lambda w,v :"true" if v else "false"),
    "project/ifusemodstex":     ("c_useModsTex", "advanced", lambda w,v: "" if v else "%"),
    "project/ifusepremodstex":  ("c_usePreModsTex", "advanced", lambda w,v: "" if v else "%"),
    "project/ifusecustomsty":   ("c_useCustomSty", "advanced", lambda w,v: "" if v else "%"),
    "project/ifusemodssty":     ("c_useModsSty", "advanced", lambda w,v: "" if v else "%"),
    "project/ifstarthalfpage":  ("c_startOnHalfPage", "layout", lambda w,v :"true" if v else "false"),
    "project/randompicposn":    ("c_randomPicPosn", "uiprefs", None),
    "project/canonicalise":     ("c_canonicalise", "advanced", None),
    "project/autotaghebgrk":    ("c_autoTagHebGrk", "advanced", None),
    "project/interlinear":      ("c_interlinear", "advanced", lambda w,v: "" if v else "%"),
    "project/interlang":        ("t_interlinearLang", "advanced", None),
    "project/ruby":             ("c_ruby", "advanced", lambda w,v : "t" if v else "b"),
    "project/plugins":          ("t_plugins", "advanced", lambda w,v: v or ""),
    "project/license":          ("ecb_licenseText", "meta", None),
    "project/copyright":        ("t_copyrightStatement", "meta", lambda w,v: re.sub(r"\\u([0-9a-fA-F]{4})",
                                                                   lambda m: chr(int(m.group(1), 16)), v).replace("//", "\u2028") if v is not None else ""),
    "project/iffrontmatter":    ("c_frontmatter", "front", lambda w,v: "" if v else "%"),
    "project/inclcoverperiphs": ("c_includeCoverSections", "cover", None),
    "project/periphpagebreak":  ("c_periphPageBreak", "front", None),
    "project/colophontext":     ("txbf_colophon", "meta", lambda w,v: re.sub(r"\\u([0-9a-fA-F]{4})",
                                                                   lambda m: chr(int(m.group(1), 16)), v) if v is not None else ""),
    "project/ifcolophon":       ("c_colophon", "meta", lambda w,v: "" if v else "%"),
    "project/pgbreakcolophon":  ("c_standAloneColophon", "peripherals", lambda w,v: "" if v else "%"),
    "project/sectintros":       ("c_useSectIntros", "peripherals", None),

    "paper/height":             ("ecb_pagesize", "layout", lambda w,v: re.sub(r"^.*?[,xX]\s*(.+?)\s*(?:\(.*|$)", r"\1", v or "210mm")),
    "paper/width":              ("ecb_pagesize", "layout", lambda w,v: re.sub(r"^(.*?)\s*[,xX].*$", r"\1", v or "148mm")),
    "paper/pagesize":           ("ecb_pagesize", "layout", None),
    "paper/ifwatermark":        ("c_applyWatermark", "finish", lambda w,v: "" if v else "%"),
    "paper/watermarkpdf":       ("btn_selectWatermarkPDF", "finish", lambda w,v: w.watermarks.as_posix() \
                                 if (w.get("c_applyWatermark") and w.watermarks is not None and w.watermarks != 'None') else ""),
    "paper/cropmarks":          ("c_cropmarks", "finish", None),  
    "paper/ifgrid":             ("c_grid", "finish", lambda w,v :"" if v else "%"),
    "paper/ifverticalrule":     ("c_verticalrule", "layout", lambda w,v :"true" if v else "false"),
    "paper/margins":            ("s_margins", "layout", lambda w,v: round(float(v)) if v else "12"),
    "paper/topmargin":          ("s_topmargin", "layout", None),
    "paper/bottommargin":       ("s_bottommargin", "layout", None),
    "paper/headerpos":          ("s_headerposition", "headfoot", None),
    "paper/footerpos":          ("s_footerposition", "headfoot", None),
    "paper/rulegap":            ("s_rhruleposition", "headfoot", None),

    "paper/ifaddgutter":        ("c_pagegutter", "layout", lambda w,v :"true" if v else "false"),
    "paper/ifoutergutter":      ("c_outerGutter", "layout", lambda w,v :"true" if v else "false"),
    "paper/gutter":             ("s_pagegutter", "layout", lambda w,v: round(float(v)) if v else "0"),
    "paper/colgutteroffset":    ("s_colgutteroffset", "layout", lambda w,v: "{:.1f}".format(float(v)) if v else "0.0"),
    "paper/columns":            ("c_doublecolumn", "layout", lambda w,v: "2" if v else "1"),
    "paper/bottomrag":          ("s_bottomRag", "layout", None),
    "paper/fontfactor":         ("s_fontsize", "fontscript", lambda w,v: f2s(float(v) / 12, dp=8) if v else "1.000"),
    "paper/lockfont2baseline":  ("c_lockFontSize2Baseline", "fontscript", None),

    "grid/gridlines":           ("c_gridLines", "finish", lambda w,v: "\doGridLines" if v else ""),
    "grid/gridgraph":           ("c_gridGraph", "finish", lambda w,v: "\doGraphPaper" if v else ""),
    "grid/majorcolor":          ("col_gridMajor", "finish", None),
    "majorcolor_":              ("col_gridMajor", "finish", lambda w,v: "{:.2f} {:.2f} {:.2f}".format(*coltoonemax(v)) if v else "0.8 0.8 0.8"),
    "grid/minorcolor":          ("col_gridMinor", "finish", None),
    "minorcolor_":              ("col_gridMinor", "finish", lambda w,v: "{:.2f} {:.2f} {:.2f}".format(*coltoonemax(v)) if v else "0.8 1.0 1.0"),
    "grid/majorthickness":      ("s_gridMajorThick", "finish", None),
    "grid/minorthickness":      ("s_gridMinorThick", "finish", None),
    "grid/units":               ("fcb_gridUnits", "finish", None),
    "grid/divisions":           ("s_gridMinorDivisions", "finish", lambda w,v: int(float(v)) if v else "10"),
    "grid/xyadvance":           ("s_gridMinorDivisions", "finish", lambda w,v: (1 / max(asfloat(v, 4), 1)) if v else "0.25"),
    "grid/xyoffset":            ("fcb_gridOffset", "finish", None),
    
    "fancy/enableornaments":    ("c_useOrnaments", "decorate", lambda w,v: "" if v else "%"),
    "fancy/enableborders":      ("c_borders", "decorate", lambda w,v: "" if v else "%"),
    "fancy/pageborder":         ("c_inclPageBorder", "decorate", lambda w,v: "" if v else "%"),
    "fancy/pageborderfullpage": ("c_borderPageWide", "decorate", lambda w,v: "" if v else "%"),
    "fancy/pagebordernfullpage_": ("c_borderPageWide", "decorate", lambda w,v: "%" if v else ""),
    "fancy/pageborderpdf":      ("btn_selectPageBorderPDF", "decorate", lambda w,v: w.pageborder.as_posix() \
                                            if (w.pageborder is not None and w.pageborder != 'None') \
                                            else get("/ptxprintlibpath")+"/A5 page border.pdf"),
    "fancy/sectionheader":      ("c_inclSectionHeader", "decorate", lambda w,v: "" if v else "%"),
    "fancy/sectionheaderpdf":   ("btn_selectSectionHeaderPDF", "decorate", lambda w,v: w.sectionheader.as_posix() \
                                            if (w.sectionheader is not None and w.sectionheader != 'None') \
                                            else get("/ptxprintlibpath")+"/A5 section head border.pdf"),
    "fancy/sectionheadershift": ("s_inclSectionShift", "decorate", lambda w,v: float(v or "0")),
    "fancy/sectionheaderscale": ("s_inclSectionScale", "decorate", lambda w,v: int(float(v or "1.0")*1000)),
    "fancy/endofbook":          ("c_inclEndOfBook", "decorate", lambda w,v: "" if v else "%"),
    "fancy/endofbookpdf":       ("btn_selectEndOfBookPDF", "decorate", lambda w,v: w.endofbook.as_posix() \
                                            if (w.endofbook is not None and w.endofbook != 'None') \
                                            else get("/ptxprintlibpath")+"/decoration.pdf"),
    "fancy/versedecorator":     ("c_inclVerseDecorator", "decorate", lambda w,v: "" if v else "%"),
    "fancy/versedecoratortype": ("r_decorator", "decorate", None),
    "fancy/versedecoratorpdf":  ("btn_selectVerseDecorator", "decorate", lambda w,v: w.versedecorator.as_posix() \
                                            if (w.versedecorator is not None and w.versedecorator != 'None') \
                                            else get("/ptxprintlibpath")+"/Verse number star.pdf"),
    "fancy/versedecoratorshift":   ("s_verseDecoratorShift", "decorate", lambda w,v: float(v or "0")),
    "fancy/versedecoratorscale":   ("s_verseDecoratorScale", "decorate", lambda w,v: int(float(v or "1.0")*1000)),
    "fancy/endayah":            ("c_decorator_endayah", "decorate", lambda w,v: "" if v else "%"), # In the UI this is "Move Ayah"

    "paragraph/linespacing":       ("s_linespacing", "layout", lambda w,v: f2s(float(v), dp=8) if v else "15"),
    "paragraph/linespacebase":     ("c_AdvCompatLineSpacing", "layout", lambda w,v: 14 if v else 12),
    "paragraph/useglyphmetrics":   ("c_AdvCompatGlyphMetrics", "layout", lambda w,v: "%" if v else ""),
    "paragraph/ifjustify":      ("c_justify", "body", lambda w,v: "true" if v else "false"),
    "paragraph/ifhyphenate":    ("c_hyphenate", "body", lambda w,v: "" if v else "%"),
    "paragraph/ifomithyphen":   ("c_omitHyphen", "body", lambda w,v: "" if v else "%"),
    "paragraph/ifhyphlimitbks": ("c_hyphenLimitBooks", "body", None),
    "paragraph/ifsylhyphens":   ("c_addSyllableBasedHyphens", "body", None),
    "paragraph/ifnothyphenate": ("c_hyphenate", "body", lambda w,v: "%" if v else ""),
    "paragraph/ifusefallback":  ("c_useFallbackFont", "fontscript", None),
    "paragraph/missingchars":   ("t_missingChars", "fontscript", lambda w,v: v or ""),

    "document/sensitive":       ("c_sensitive", "meta", None),
    "document/title":           (None, "meta", lambda w,v: "[Unknown]" if w.get("c_sensitive") else w.ptsettings.get('FullName', "[Unknown]")),
    "document/subject":         ("ecb_booklist", "meta", lambda w,v: v if w.get("r_book") == "multiple" else w.get("ecb_book")),
    "document/author":          (None, "meta", lambda w,v: "" if w.get("c_sensitive") else w.ptsettings.get('Copyright', "")),

    "document/startpagenum":    ("s_startPageNum", "front", lambda w,v: int(float(v)) if v else "1"),
    "document/multibook":       ("r_book_multiple", "meta", lambda w,v: "" if v else "%"),
    "document/toc":             ("c_autoToC", "front", lambda w,v: "" if v else "%"),
    "document/toctitle":        ("t_tocTitle", "front", lambda w,v: v or ""),
    "document/usetoc1":         ("c_usetoc1", "front", lambda w,v: "true" if v else "false"),
    "document/usetoc2":         ("c_usetoc2", "front", lambda w,v: "true" if v else "false"),
    "document/usetoc3":         ("c_usetoc3", "front", lambda w,v: "true" if v else "false"),
    "document/tocleaders":      ("fcb_leaderStyle", "front", None),
    "document/chapfrom":        ("t_chapfrom", "meta", lambda w,v: str(round(float(v))) if v else "1"),
    "document/chapto":          ("t_chapto", "meta", lambda w,v: str(round(float(v))) if v else "999"),
    "document/colgutterfactor": ("s_colgutterfactor", "layout", lambda w,v: round(float(v or 4)*3)), # Hack to be fixed
    "document/ifrtl":           ("fcb_textDirection", "fontscript", lambda w,v:"true" if v == "rtl" else "false"),
    "document/toptobottom":     ("fcb_textDirection", "fontscript", lambda w,v: "" if v == "ttb" else "%"),
    "document/iflinebreakon":   ("c_linebreakon", "fontscript", lambda w,v: "" if v else "%"),
    "document/linebreaklocale": ("t_linebreaklocale", "fontscript", lambda w,v: v or ""),
    "document/script":          ("fcb_script", "fontscript", lambda w,v: ":script="+v.lower() if v and v != "Zyyy" else ""),
    "document/ch1pagebreak":    ("c_ch1pagebreak", "body", lambda w,v: "true" if v else "false"),
    "document/marginalverses":  ("c_marginalverses", "body", lambda w,v: "" if v else "%"),
    "document/marginalposn":    ("fcb_marginVrsPosn", "body", None),
    "document/columnshift":     ("s_columnShift", "layout", lambda w,v: v or "16"),
    "document/ifshowchapternums": ("c_chapterNumber", "body", lambda w,v: "%" if v else ""),
    "document/showxtrachapnums":  ("c_showNonScriptureChapters", "peripherals", None),
    "document/ifshow1chbooknum": ("c_show1chBookNum", "body", None),
    "document/ifomitverseone":  ("c_omitverseone", "body", lambda w,v: "true" if v else "false"),
    "document/ifshowversenums": ("c_verseNumbers", "body", lambda w,v: "" if v else "%"),
    "document/afterchapterspace": ("s_afterChapterSpace", "body", lambda w,v: f2s(asfloat(v, 0.25) * 12)),
    "document/afterversespace": ("s_afterVerseSpace", "body", lambda w,v: f2s(asfloat(v, 0.15) * 12)),
    "document/ifmainbodytext":  ("c_mainBodyText", "body", None),
    "document/glueredupwords":  ("c_glueredupwords", "body", None),
    "document/ifinclfigs":      ("c_includeillustrations", "pictures", lambda w,v: "true" if v else "false"),
    "document/ifusepiclist":    ("c_includeillustrations", "pictures", lambda w,v :"" if v else "%"),
    "document/iffigexclwebapp": ("c_figexclwebapp", "pictures", None),
    "document/iffigskipmissing": ("c_skipmissingimages", "pictures", None),
    "document/iffigcrop":       ("c_cropborders", "pictures", None),
    "document/iffigplaceholders": ("c_figplaceholders", "pictures", lambda w,v: "true" if v else "false"),
    "document/iffigshowcaptions": ("c_fighidecaptions", "pictures", lambda w,v: "false" if v else "true"),
    "document/iffighiderefs":   ("c_fighiderefs", "pictures", None),
    "document/picresolution":   ("r_pictureRes", "pictures", None),
    "document/customfiglocn":   ("c_useCustomFolder", "pictures", lambda w,v :"" if v else "%"),
    "document/exclusivefolder": ("c_exclusiveFiguresFolder", "pictures", None),
    "document/customfigfolder": ("btn_selectFigureFolder", "pictures", lambda w,v: w.customFigFolder.as_posix() \
                                                                       if w.customFigFolder is not None else ""),
    "document/imagetypepref":   ("t_imageTypeOrder", "pictures", None),
    "document/glossarymarkupstyle":  ("fcb_glossaryMarkupStyle", "body", None),
    "document/filterglossary":  ("c_filterGlossary", "body", None),
    "document/hangpoetry":      ("c_hangpoetry", "body", lambda w,v: "" if v else "%"),
    "document/preventorphans":  ("c_preventorphans", "body", None),
    "document/preventwidows":   ("c_preventwidows", "body", None),
    "document/sectionheads":    ("c_sectionHeads", "body", None),
    "document/parallelrefs":    ("c_parallelRefs", "body", None),
    "document/bookintro":       ("c_bookIntro", "body", None),
    "document/introoutline":    ("c_introOutline", "body", None),
    "document/indentunit":      ("s_indentUnit", "body", lambda w,v: round(float(v or "1.0"), 1)),
    "document/firstparaindent": ("c_firstParaIndent", "body", lambda w,v: "true" if v else "false"),
    "document/ifhidehboxerrors": ("c_showHboxErrorBars", "finish", lambda w,v :"%" if v else ""),
    "document/hidemptyverses":  ("c_hideEmptyVerses", "body", None),
    "document/elipsizemptyvs":  ("c_elipsizeMissingVerses", "body", None),
    "document/ifspacing":       ("c_spacing", "fontscript", lambda w,v :"" if v else "%"),
    "document/spacestretch":    ("s_maxSpace", "fontscript", lambda w,v : str((int(float(v or 150)) - 100) / 100.)),
    "document/spaceshrink":     ("s_minSpace", "fontscript", lambda w,v : str((100 - int(float(v or 66))) / 100.)),
    "document/ifletter":        ("c_letterSpacing", "fontscript", lambda w,v: "" if v else "%"),
    "document/letterstretch":   ("s_letterStretch", "fontscript", lambda w,v: float(v or "5.0") / 100.),
    "document/lettershrink":    ("s_letterShrink", "fontscript", lambda w,v: float(v or "1.0") / 100.),
    "document/ifcolorfonts":    ("c_colorfonts", "fontscript", lambda w,v: "%" if v else ""),

    "document/ifchaplabels":    ("c_useChapterLabel", "body", lambda w,v: "%" if v else ""),
    "document/clabelbooks":     ("t_clBookList", "body", lambda w,v: v.upper() if v else ""),
    "document/clabel":          ("t_clHeading", "body", None),
    "document/diffcolayout":        ("c_differentColLayout", "body", None),
    "document/diffcolayoutbooks":   ("t_differentColBookList", "body", None),
    "document/cloptimizepoetry":    ("c_optimizePoetryLayout", "body", None),

    "document/ifdiglot":            ("c_diglot", "diglot", lambda w,v : "" if v else "%"),
    "document/ifndiglot":           ("c_diglot", "diglot", lambda w,v : "%" if v else ""),
    "document/diglotprifraction":   ("s_diglotPriFraction", "diglot", lambda w,v : round((float(v)/100), 3) if v is not None else "0.550"),
    "document/diglotsecfraction":   ("s_diglotPriFraction", "diglot", lambda w,v : round(1 - (float(v)/100), 3) if v is not None else "0.450"),
    "document/diglotsecprj":        ("fcb_diglotSecProject", "diglot", None),
    "document/diglotpicsources":    ("fcb_diglotPicListSources", "diglot", None),
    "document/diglot2captions": ("c_diglot2captions", "diglot", None),
    "document/diglotswapside":  ("c_diglotSwapSide", "diglot", lambda w,v: "true" if v else "false"),
    "document/diglotsepnotes":  ("c_diglotSeparateNotes", "diglot", lambda w,v: "true" if v else "false"),
    "document/diglotsecconfig": ("ecb_diglotSecConfig", "diglot", None),
    "document/diglotmergemode": ("c_diglotMerge", "diglot", lambda w,v: "simple" if v else "doc"),
    "document/diglotadjcenter": ("c_diglotAdjCenter", "diglot", None),
    "document/diglotheaders":   ("c_diglotHeaders", "diglot", None),
    "document/diglotnotesrule": ("c_diglotNotesRule", "diglot", lambda w,v: "true" if v else "false"),
    "document/diglotjoinvrule": ("c_diglotJoinVrule", "diglot", lambda w,v: "true" if v else "false"),

    "document/hasnofront_":        ("c_frontmatter", "front", lambda w,v: "%" if v else ""),
    "document/noblankpage":        ("c_periphSuppressPage", "layout", None),
    "document/cutouterpadding":    ("s_cutouterpadding", "layout", None),
    "document/underlinethickness": ("s_underlineThickness", "body", lambda w,v: float(v or "0.05")),
    "document/rulethickness":      ("s_ruleThickness", "body", lambda w,v: float(v or "0.40")),
    "document/underlineposition":  ("s_underlinePosition", "body", lambda w,v: float(v or "-0.1")),
    "document/pagefullfactor":     ("s_pageFullFactor", "layout", lambda w,v: float(v or "0.65")),
    
    "document/onlyshowdiffs":   ("c_onlyDiffs", "finish", None),
    "document/ndiffcolor":      ("col_ndiffColor", "finish", None),
    "document/odiffcolor":      ("col_odiffColor", "finish", None),
    "document/diffpdf":         ("btn_selectDiffPDF", "finish", lambda w,v: w.diffPDF.as_posix() \
                                 if (w.diffPDF is not None and w.diffPDF != 'None') else ""),
    "document/printarchive":    ("c_printArchive", "finish", None),

    "cover/makecoverpage":      ("c_makeCoverPage", "cover", lambda w,v: "" if v else "%"),
    "cover/rtlbookbinding":     ("c_RTLbookBinding", "cover", lambda w,v: "true" if v else "false"),
    "cover/includespine":       ("c_inclSpine", "cover", None),
    "cover/rotatespine":        ("fcb_rotateSpineText", "cover", None),
    "cover/overridepagecount":  ("c_overridePageCount", "cover", None),
    "cover/totalpages":         ("s_totalPages", "cover", None),
    "cover/coveradjust":        ("s_coverAdjust", "cover", None),
    "cover/weightorthick":      ("s_paperWidthOrThick", "cover", None),
    "cover/spineoverlapback":   ("s_spineOverlapBack", "cover", None),
    "cover/spineoverlapfront":  ("s_spineOverlapFront", "cover", None),
    "cover/papercalcunits":     ("r_paperCalc", "cover", None),
    "cover/covercropmarks":     ("c_coverCropMarks", "cover", None),
    "cover/coverbleed":         ("s_coverBleed", "cover", None),
    "cover/coverartbleed":      ("s_coverArtBleed", "cover", None),
    "cover/makeseparatePDF":    ("c_coverSeparatePDF", "cover", None),

    "covergen/covertype":       ("r_cover", "cover", None),
    "covergen/textscale":       ("s_coverTextScale", "cover", None),
    "covergen/textcolor":       ("col_coverText", "cover", None),
    "covergen/useborder":       ("c_coverBorder", "cover", None),
    "covergen/borderstyle":     ("fcb_coverBorder", "cover", None),
    "covergen/bordercolor":     ("col_coverBorder", "cover", None),
    "covergen/useshading":      ("c_coverShading", "cover", None),
    "covergen/shadingcolor":    ("col_coverShading", "cover", None),
    "covergen/useimage":        ("c_coverSelectImage", "cover", None),
    "covergen/imagefront":      ("c_coverImageFront", "cover", None),
    "covergen/imagefile":       ("btn_coverSelectImage", "cover", lambda w,v: w.coverImage.as_posix() if w.coverImage is not None else ""),
    # "covergen/imgfname":       ("lb_coverImageFilename", "cover", None),

    "document/keepversions":    ("s_keepVersions", "finish", None),
    "document/settingsinpdf":   ("c_inclSettingsInPDF", "finish", None),
    
    "finishing/pgsperspread":   ("fcb_pagesPerSpread", "finish", None),
    "finishing/rtlpagination":  ("c_RTLpagination", "finish", None),
    "finishing/foldfirst":      ("c_foldFirst", "finish", None),
    "finishing/scaletofit":     ("c_scaleToFit", "finish", None),
    "finishing/sheetsize":      ("ecb_sheetSize", "finish", None),
    "finishing/sheetsinsigntr": ("s_sheetsPerSignature", "finish", None),
    "finishing/foldcutmargin":  ("s_foldCutMargin", "finish", None),
    "finishing/inclsettings":   ("c_inclSettingsInPDF", "finish", None),
    "finishing/spotcolor":      ("col_spotColor", "finish", None),
    "finishing/spottolerance":  ("s_spotColorTolerance", "finish", None),
    # The next line is redundant (I think) - check and remove
    "color/spotcolrange":       ("s_spotColorTolerance", "finish", None),
    
    "header/ifshowbook":        ("c_rangeShowBook", "headfoot", lambda w,v :"false" if v else "true"),
    "header/ifshowchapter":     ("c_rangeShowChapter", "headfoot", lambda w,v :"false" if v else "true"),
    "header/ifshowverse":       ("c_rangeShowVerse", "headfoot", lambda w,v :"true" if v else "false"),
    "header/chvseparator":      ("r_CVsep", "headfoot", lambda w,v : ":" if v == "colon" else "."),
    "header/ifrhrule":          ("c_rhrule", "headfoot", lambda w,v: "" if v else "%"),
    "header/hdrleftside":       ("r_hdrLeft", "headfoot", None),
    "header/hdrleft":           ("ecb_hdrleft", "headfoot", lambda w,v: v or "-empty-"),
    "header/hdrcenterside":     ("r_hdrCenter", "headfoot", None),
    "header/hdrcenter":         ("ecb_hdrcenter", "headfoot", lambda w,v: v or "-empty-"),
    "header/hdrrightside":      ("r_hdrRight", "headfoot", None),
    "header/hdrright":          ("ecb_hdrright", "headfoot", lambda w,v: v or "-empty-"),
    "header/mirrorlayout":      ("c_mirrorpages", "headfoot", lambda w,v: "true" if v else "false"),
    
    "footer/ftrcenterside":     ("r_ftrCenter", "headfoot", None),
    "footer/ftrcenter":         ("ecb_ftrcenter", "headfoot", lambda w,v: v or "-empty-"),
    "footer/ifftrtitlepagenum": ("c_pageNumTitlePage", "headfoot", lambda w,v: "" if v else "%"),
    "footer/ifprintconfigname": ("c_printConfigName", "headfoot", lambda w,v: "" if v else "%"),
    "footer/noinkinmargin":     ("c_noinkinmargin", "layout", lambda w,v :"true" if v else "false"),

    "notes/frverseonly":        ("c_frVerseOnly", "noteref", None),
    "notes/includefootnotes":   ("c_includeFootnotes", "noteref", lambda w,v: "%" if v else ""),
    "notes/fneachnewline":      ("c_fneachnewline", "noteref", lambda w,v: "%" if v else ""),
    "notes/fnoverride":         ("c_fnOverride", "noteref", None),
    "notes/iffnautocallers":    ("c_fnautocallers", "noteref", lambda w,v :"true" if v else "false"),
    "notes/fncallers":          ("t_fncallers", "noteref", lambda w,v: v if w.get("c_fnautocallers") else ""),
    "notes/fnresetcallers":     ("c_fnpageresetcallers", "noteref", lambda w,v: "" if v else "%"),
    "notes/fnomitcaller":       ("c_fnomitcaller", "noteref", lambda w,v: "%" if v else ""),

    "notes/includexrefs":       ("c_includeXrefs", "noteref", lambda w,v: "%" if v else ""),
    "notes/showextxrefs":       ("c_extendedXrefs", "noteref", None),
    "notes/xreachnewline":      ("c_xreachnewline", "noteref", lambda w,v: "%" if v else ""),
    "notes/xroverride":         ("c_xrOverride", "noteref", None),
    "notes/ifxrautocallers":    ("c_xrautocallers", "noteref", lambda w,v :"true" if v else "false"),
    "notes/xrcallers":          ("t_xrcallers", "noteref", lambda w,v: v if w.get("c_xrautocallers") else ""),
    "notes/xrresetcallers":     ("c_xrpageresetcallers", "noteref", lambda w,v: "" if v else "%"),
    "notes/xromitcaller":       ("c_xromitcaller", "noteref", lambda w,v: "%" if v else ""),

    "notes/xrlocation":         ("r_xrpos", "noteref", lambda w,v: r"" if v == "centre" else "%"),
    "notes/xrpos":              ("r_xrpos", "noteref", None),
    "notes/xrcolside":          ("fcb_colXRside", "noteref", None),
    "notes/xrcentrecolwidth":   ("s_centreColWidth", "noteref", lambda w,v: int(float(v)) if v else "60"),
    "notes/xrguttermargin":     ("s_xrGutterWidth", "noteref", lambda w,v: "{:.1f}".format(float(v)) if v else "2.0"),
    "notes/xrcolrule":          ("c_xrColumnRule", "noteref", lambda w,v: "true" if v else "false"),
    "notes/xrcolbottom":        ("c_xrColumnBottom", "noteref", lambda w,v: "true" if v else "false"),
    "notes/xrcolalign":         ("c_xrSideAlign", "noteref", lambda w,v: "true" if v else "false"),
    "notes/ifxrexternalist":    ("c_useXrefList", "noteref", lambda w,v: "%" if v else ""),
    "notes/xrlistsource":       ("fcb_xRefExtListSource", "noteref", None),
    "notes/xrextlistsource":    ("fcb_xRefExtListSource", "noteref", None),
    "notes/xrfilterbooks":      ("fcb_filterXrefs", "noteref", None),
    "notes/xrverseonly":        ("c_xoVerseOnly", "noteref", None),
    "notes/addcolon":           ("c_addColon", "noteref", None),
    "notes/keepbookwithrefs":   ("c_keepBookWithRefs", "noteref", None),
    "notes/glossaryfootnotes":  ("c_glossaryFootnotes", "noteref", None),
    "notes/fnpos":              ("r_fnpos", "noteref", None),
    "notes/columnnotes_":       ("r_fnpos", "noteref", lambda w,v: "true" if v == "column" else "false"),
    "notes/endnotes_":          ("r_fnpos", "noteref", lambda w,v: "" if v == "endnotes" else "%"),

    "notes/iffootnoterule":     ("c_footnoterule", "noteref", lambda w,v: "%" if v else ""),
    "notes/ifxrefrule":         ("c_xrefrule", "noteref", lambda w,v: "%" if v else ""),
    "notes/ifstudynoterule":    ("c_studynoterule", "noteref", lambda w,v: "%" if v else ""),

    "notes/abovenotespace":     ("s_fnAboveSpace", "noteref", None),
    "notes/belownoterulespace": ("s_fnBelowSpace", "noteref", None),
    "notes/fnruleposn":         ("fcb_fnHorizPosn", "noteref", None),
    "notes/fnruleindent":       ("s_fnIndent", "noteref", None),
    "notes/fnrulelength":       ("s_fnLength", "noteref", None),
    "notes/fnrulethick":        ("s_fnThick", "noteref", None),
    
    "notes/abovexrefspace":     ("s_xrAboveSpace", "noteref", None),
    "notes/belowxrefrulespace": ("s_xrBelowSpace", "noteref", None),
    "notes/xrruleposn":         ("fcb_xrHorizPosn", "noteref", None),
    "notes/xrruleindent":       ("s_xrIndent", "noteref", None),
    "notes/xrrulelength":       ("s_xrLength", "noteref", None),
    "notes/xrrulethick":        ("s_xrThick", "noteref", None),

    "notes/abovestudyspace":    ("s_snAboveSpace", "noteref", None),
    "notes/belowstudyrulespace": ("s_snBelowSpace", "noteref", None),
    "notes/snruleposn":         ("fcb_snHorizPosn", "noteref", None),
    "notes/snruleindent":       ("s_snIndent", "noteref", None),
    "notes/snrulelength":       ("s_snLength", "noteref", None),
    "notes/snrulethick":        ("s_snThick", "noteref", None),
    
    "notes/internotespace":     ("s_internote", "noteref", lambda w,v: f2s(float(v or 3))),

    "notes/horiznotespacemin":  ("s_notespacingmin", "noteref", lambda w,v: f2s(float(v)) if v is not None else "7"),
    "notes/horiznotespacemax":  ("s_notespacingmax", "noteref", lambda w,v: f2s(float(v)) if v is not None else "27"),

    "studynotes/includextfn":     ("c_extendedFnotes", "noteref", lambda w,v: "" if v else "%"),
    "studynotes/showcallers":     ("c_ef_showCallers", "noteref", lambda w,v: "%" if v else ""),
    "studynotes/colgutterfactor": ("s_ef_colgutterfactor", "noteref", lambda w,v: round(float(v or 4)*3)), # Hack to be fixed?
    "studynotes/ifverticalrule":  ("c_ef_verticalrule", "noteref", lambda w,v :"true" if v else "false"),
    "studynotes/internote":       ("s_ef_internote", "noteref", lambda w,v: "{:.1f}".format(float(v)) if v else "0.0"),
    "studynotes/colgutteroffset": ("s_ef_colgutteroffset", "noteref", lambda w,v: "{:.1f}".format(float(v)) if v else "0.0"),
  # "studynotes/bottomrag":       ("s_ef_bottomRag", "noteref", lambda w,v: str(int(v or 0)+0.95)),
    "studynotes/includesidebar":  ("c_sidebars", "noteref", None),
    "studynotes/txlinclquestions":("c_txlQuestionsInclude", "noteref", None),
    "studynotes/txloverview":     ("c_txlQuestionsOverview", "noteref", None),
    # "studynotes/txlboldover":     ("c_txlBoldOverview", "noteref", None),
    "studynotes/txlnumbered":     ("c_txlQuestionsNumbered", "noteref", None),
    "studynotes/txlshowrefs":     ("c_txlQuestionsRefs", "noteref", None),
    "studynotes/txllangtag":      ("t_txlQuestionsLang", "noteref", None), 
    "studynotes/filtercats":      ("c_filterCats", "noteref", None),

    "document/fontregular":     ("bl_fontR", "fontscript", lambda w,v,s: v.asTeXFont(s.inArchive) if v else ""),
    "document/fontbold":        ("bl_fontB", "fontscript", lambda w,v,s: v.asTeXFont(s.inArchive) if v else ""),
    "document/fontitalic":      ("bl_fontI", "fontscript", lambda w,v,s: v.asTeXFont(s.inArchive) if v else ""),
    "document/fontbolditalic":  ("bl_fontBI", "fontscript", lambda w,v,s: v.asTeXFont(s.inArchive) if v else ""),
    "document/fontextraregular":("bl_fontExtraR", "fontscript", lambda w,v,s: v.asTeXFont(s.inArchive) if v else ""),

    "snippets/fancyintro":      ("c_prettyIntroOutline", "body", None),
    "snippets/pdfoutput":       ("fcb_outputFormat", "finish", None),
    "snippets/diglot":          ("c_diglot", "diglot", lambda w,v: True if v else False),
    "snippets/fancyborders":    ("c_borders", "decorate", None),

    "document/includeimg":      ("c_includeillustrations", "pictures", None),
    
    "thumbtabs/ifthumbtabs":    ("c_thumbtabs", "tabsborders", None),
    "thumbtabs/numtabs":        ("s_thumbtabs", "tabsborders", None),
    "thumbtabs/length":         ("s_thumblength", "tabsborders", None),
    "thumbtabs/height":         ("s_thumbheight", "tabsborders", None),
    "thumbtabs/background":     ("col_thumbback", "tabsborders", None),
    "thumbtabs/background":     ("col_thumbback", "tabsborders", None),
    "thumbtabs/rotate":         ("c_thumbrotate", "tabsborders", None),
    "thumbtabs/rotatetype":     ("fcb_rotateTabs", "tabsborders", None),
    "thumbtabs/thumbtextmkr":   ("r_thumbText", "tabsborders", None),
    "thumbtabs/restart":        ("c_thumbrestart", "tabsborders", None),
    "thumbtabs/groups":         ("t_thumbgroups", "tabsborders", None),

    "scripts/mymr/syllables":   ("c_scrmymrSyllable", "fontscript", None),
    "scripts/arab/lrcolon":     ("c_scrarabrefs", "fontscript", None),
    "scripts/indic/syllables":  ("c_scrindicSyllable", "fontscript", None),
    "scripts/indic/showhyphen": ("c_scrindicshowhyphen", "fontscript", None),

    "strongsndx/showintext":    ("c_strongsShowInText", "strongs", None),
    "strongsndx/showall":       ("c_strongsShowAll", "strongs", None),
    "strongsndx/shownums":      ("c_strongsShowNums", "strongs", None),
    "strongsndx/showhebrew":    ("c_strongsHeb", "strongs", None),
    "strongsndx/showgreek":     ("c_strongsGrk", "strongs", None),
    "strongsndx/showindex":     ("c_strongsNdx", "strongs", None),
    "strongsndx/sourcelang":    ("c_strongsSrcLg", "strongs", None),
    "strongsndx/transliterate": ("c_strongsTranslit", "strongs", None),
    "strongsndx/renderings":    ("c_strongsRenderings", "strongs", None),
    "strongsndx/definitions":   ("c_strongsDefn", "strongs", None),
    "strongsndx/keyvrsrefs":    ("c_strongsKeyVref", "strongs", None),
    "strongsndx/fallbackprj":   ("fcb_strongsFallbackProj", "strongs", None),
    "strongsndx/majorlang":     ("fcb_strongsMajorLg", "strongs", None),
    "strongsndx/nocomments":    ("c_strongsNoComments", "strongs", None),
    "strongsndx/wildcards":     ("fcb_strongswildcards", "strongs", None),
    "strongsndx/raglines":      ("s_strongRag", "strongs", None),
    "strongsndx/ndxbookid":     ("fcb_strongsNdxBookId", "strongs", None),
    "strongsndx/twocols":       ("c_strongs2cols", "strongs", None),
    "strongsndx/openineditor":  ("c_strongsOpenIndex", "strongs", None),
    
    "import/impsource":         ("r_impSource", "import", None),
    "import/impsourcepdf":      ("btn_selectImpSource_pdf", "import", lambda w,v: w.impSourcePDF.as_posix() if w.impSourcePDF is not None else ""),
    "import/project":           ("fcb_impProject", "import", None),
    "import/config":            ("ecb_impConfig", "import", None),
    "import/resetconfig":       ("c_imp_ResetConfig", "import", None),
    "import/layout":            ("c_impLayout", "import", None),
    "import/fontsscript":       ("c_impFontsScript", "import", None),
    "import/styles":            ("c_impStyles", "import", None),
    "import/pictures":          ("c_impPictures", "import", None),
    "import/addnewpics":        ("c_impPicsAddNew", "import", None),
    "import/deloldpics":        ("c_impPicsDelOld", "import", None),
    "import/imppics":           ("r_impPics", "import", None),
    "import/captions":          ("c_pic_Captions", "import", None),
    "import/sizeposn":          ("c_pic_SizePosn", "import", None),
    "import/copyright":         ("c_pic_Copyright", "import", None),
    "import/other":             ("c_impOther", "import", None),
    "import/body":              ("c_oth_Body", "import", None),
    "import/notesrefs":         ("c_oth_NotesRefs", "noteref", None),
    "import/headerfooter":      ("c_oth_HeaderFooter", "import", None),
    "import/tabsborders":       ("c_oth_TabsBorders", "import", None),
    "import/peripherals":       ("c_oth_Peripherals", "import", None),
    "import/advanced":          ("c_oth_Advanced", "import", None),
    "import/frontmatter":       ("c_oth_FrontMatter", "import", None),
    "import/cover":             ("c_oth_Cover", "import", None),
    
}

ModelMap = {k: ModelInfo(k, *v) for k, v in _map.items()}

ImportCategories = {
    'c_oth_Body': 'body',
    'c_oth_NotesRefs': 'noteref',
    'c_oth_HeaderFooter': 'headfoot',
    'c_oth_TabsBorders': 'tabsborders',
    'c_oth_Advanced': 'advanced',
    'c_oth_FrontMatter': 'front',
    'c_oth_Cover': 'cover',
    'c_impLayout': 'layout'
}
