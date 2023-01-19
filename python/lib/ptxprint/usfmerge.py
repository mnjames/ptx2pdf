#!/usr/bin/python3
import sys, os, re
import ptxprint.sfm as sfm
from ptxprint.sfm import usfm
from ptxprint.sfm import style
import argparse, difflib, sys
from enum import Enum,Flag
from itertools import groupby
import logging

class MergeF(Flag):
    ChunkOnVerses=1
    NoSplitNB=2
    HeadWithText=4

settings=MergeF.ChunkOnVerses | MergeF.NoSplitNB
logger = logging.getLogger(__name__)
debugPrint = False
class ChunkType(Enum):
    DEFSCORE = 0        # Value for default scores
    CHAPTER = 1
    HEADING = 2
    TITLE = 3
    INTRO = 4
    BODY = 5
    ID = 6
    TABLE = 7
    VERSE = 8           # A verse chunk, inside a paragraph 
    PARVERSE = 9           # A verse chunk, inside a paragraph 
    MIDVERSEPAR = 10     # A verse immediately after a paragraph
    PREVERSEPAR = 11    # A paragrpah where the next content is a verse number
    NOVERSEPAR = 12     # A paragraph which is not in verse-text, e.g inside a side-bar, or book/chapter introduction
    NPARA = 13          # A nested paragraph 
    NB = 14             # A nobreak mark 
    NBCHAPTER = 15      # A chapter that is followed by an NB

splitpoints={
        ChunkType.VERSE:True
} 
_textype_map = {
    "ChapterNumber":   ChunkType.CHAPTER,
    "Section":   ChunkType.HEADING,
    "Title":     ChunkType.TITLE,
    "Other":     ChunkType.INTRO,
    "VerseText": ChunkType.BODY
}
_marker_modes = {
    'id': ChunkType.TITLE,
    'ide': ChunkType.TITLE,
    'h': ChunkType.TITLE,
    'toc1': ChunkType.TITLE,
    'toc2': ChunkType.TITLE,
    'toc3': ChunkType.TITLE,
    'v': ChunkType.VERSE,
    'cl': ChunkType.CHAPTER,
    'nb': ChunkType.NB
}

_canonical_order={
    ChunkType.ID:0,
    ChunkType.PREVERSEPAR:1,
    ChunkType.PARVERSE:1,
    ChunkType.VERSE:2,
    ChunkType.MIDVERSEPAR:3,
    ChunkType.HEADING:4,
}
    

class Chunk(list):
    def __init__(self, *a, mode=None, chap=0, verse=0, end=0, pnum=0):
        super(Chunk, self).__init__(a)
        self.type = mode
        self.chap = chap
        self.verse = verse
        self.end = verse
        self.pnum = pnum
        self.hasVerse = False
        if mode in (ChunkType.MIDVERSEPAR, ChunkType.VERSE, ChunkType.PARVERSE):
            self.verseText = True
        else:
            self.verseText = False
        self.labelled = False
        self.score = None

    def label(self, chap, verse, end, pnum):
        if self.labelled:
            self.end = end
            return
        self.chap = chap
        self.verse = verse
        self.end = end
        self.pnum = pnum
        self.labelled = True

    @property
    def position(self):
        return((self.chap,self.verse,self.pnum,_canonical_order[self.type] if self.type in _canonical_order else 9,self.type.name if self.type.name != 'VERSE' else '@VERSE'))
        #return("%03d:%03d:%04d:%s" % (self.chap,self.verse,self.pnum,self.type.name))

    @property
    def ident(self):
        if len(self) == 0:
            return ("", 0, 0,0) # , 0, 0)
        return (self.type.name, self.chap, self.verse, self.pnum) # , self.end, self.pnum)

    def __str__(self):
        #return "".join(repr(x) for x in self)
        #return "".join(sfm.generate(x) for x in self)
        return sfm.generate(self)


nestedparas = set(('io2', 'io3', 'io4', 'toc2', 'toc3', 'ili2', 'cp', 'cl' ))

SyncPoints = {
    "chapter":{ChunkType.VERSE:0,ChunkType.PREVERSEPAR:0,ChunkType.NOVERSEPAR:0,ChunkType.MIDVERSEPAR:0,ChunkType.HEADING:0,ChunkType.CHAPTER:1,ChunkType.NBCHAPTER:1}, # Just split at chapters
    "normal":{ChunkType.VERSE:0,ChunkType.PREVERSEPAR:1,ChunkType.NOVERSEPAR:1,ChunkType.MIDVERSEPAR:1,ChunkType.HEADING:1,ChunkType.CHAPTER:1,ChunkType.NBCHAPTER:0}, 
    "verse":{ChunkType.VERSE:1,ChunkType.PREVERSEPAR:1,ChunkType.NOVERSEPAR:1,ChunkType.MIDVERSEPAR:1,ChunkType.HEADING:1,ChunkType.CHAPTER:1,ChunkType.NBCHAPTER:1} # split at every verse
}

def ispara(c):
    return 'paragraph' == str(c.meta.get('StyleType', 'none')).lower()
    
class Collector:
    """TODO: write more here
        synchronise : str
            This picks the ChunkTypes that will be contribute to scoring for this collection. 
        scores : int or {ChunkType.DEFSCORE:int, ...}
            Normally this takes a single value, which is promoted to the default score.
            For really interesting scoring, a mapping of ChunkType.*:score can
            be supplied, e.g. to force a chunk-break at all headings from one source)
             For any ChunkType  that is missing from the scores mapping (or for
            all ChunkTypes if a single value is supplied), then the default score is applied
            according to the rule-set chosen from synchronise
    """
    def __init__(self, doc=None, primary=True, fsecondary=False, stylesheet=None, colkey=None, scores=None, synchronise=None):
        self.acc = []
        self.loc = {} # Locations to turn position into offset into acc[] array 
        self.colkey=colkey
        self.fsecondary = fsecondary
        self.stylesheet = stylesheet
       
        self.chap = 0
        self.verse = 0
        self.end = 0
        self.waspar = False # Was the previous item an empty paragraph mark of some type?
        self.counts = {}
        self.scores = {}
        self.currChunk = None
        self.mode = ChunkType.INTRO
        self.oldmode= None
        if (scores==None):
            raise ValueError("Scores can be integer or ChunkType:Score values, but must be supplied!")
        if debugPrint:
            print("Scores supplied are: ",  type(scores), scores)
        if synchronise in SyncPoints:
            if debugPrint:
                print("Sync points:", synchronise.lower())
            syncpoints=SyncPoints[synchronise.lower()] 
        else:
            syncpoints=SyncPoints['normal'] 
            if debugPrint:
                print("Sync points are normal")

        if (type(scores)==int):
            tmp=scores
            scores={ChunkType.DEFSCORE:tmp}
            if debugPrint:
                print(f"Default score =  {scores[ChunkType.DEFSCORE]}")
        else:
            pass

        for st in ChunkType:
            if st.value==ChunkType.DEFSCORE:
                self.scores[st.value]=scores[st]
            else:
                self.scores[st.value]=scores[st] if (st in scores) else (scores[ChunkType.DEFSCORE] * (syncpoints[st] if (st in syncpoints) else 0))
            #if (self.scores[st.value]):
            #    splitpoints[st] = True
            #else:
            #    if (st not in splitpoints):
            #        splitpoints[st] = False
            if debugPrint:
                print(f"Score for {st} -> ",self.scores[st.value], splitpoints[st] if st in splitpoints else '-' )
        if doc is not None:
            self.collect(doc, primary=primary)
            self.reorder()

    def pnum(self, c):
        if c is None:
            return 0
        if hasattr(c,'name') :
            n=c.name
        else:
            n=c
        res = self.counts.get(n, 0)
        #if debugPrint:
             #print(n,res)
        self.counts[n] = res + 1
        return res

    def makeChunk(self, c=None):
        if c is None:
            currChunk = Chunk(mode=self.mode)
            self.waspar = False
        else:
            if c.name == "cl":
                mode = ChunkType.TITLE if self.chap == 0 else ChunkType.HEADING
            elif c.name == "id":
                mode = ChunkType.ID
            elif c.name == "nb":
                mode = ChunkType.NB
            elif c.name == "tr":
                mode = ChunkType.TABLE
            elif c.name in nestedparas:
                mode = ChunkType.NPARA
            elif c.name == "v":
                if self.waspar:
                    mode = ChunkType.PARVERSE
                else:
                    mode = ChunkType.VERSE
            else:
                mode = _marker_modes.get(c.name, _textype_map.get(str(c.meta.get('TextType')), self.mode))
                if mode == ChunkType.BODY and ispara(c):
                    if debugPrint:
                        print(f'Bodypar: vt?{self.currChunk.verseText} hv?{self.currChunk.hasVerse}:', len(self.acc))
                    if(len(c)==1 and isinstance(c[0],sfm.Text)):
                        if debugPrint:
                            print(f'Bodypar(simple): ',c.name,  c[0], type(c[0]))
                        if (len(c[0])>2 and self.currChunk.verseText):
                            mode = ChunkType.MIDVERSEPAR
                    elif (len(c)>1):
                        #Multi-component body paragraph
                        if debugPrint:
                            print('Bodypar:', c.name, type(c[0]),c[0], type(c[1]), c[1])
                        if (len(c[0])>2 and self.currChunk.verseText):
                            mode = ChunkType.MIDVERSEPAR
                        elif(isinstance(c[0],sfm.Element)):
                            if (c[0].name=="v" ):
                                mode = ChunkType.PREVERSEPAR
                        elif(isinstance(c[1],sfm.Element)):
                            if (c[1].name=="v" ):
                                mode = ChunkType.PREVERSEPAR
                        elif(isinstance(c[1],sfm.Text)):
                            if self.currChunk.verseText:
                                mode = ChunkType.MIDVERSEPAR
                    if debugPrint:
                        print(f"Conclusion: bodypar type is {mode}")
                        
            currChunk = Chunk(mode=mode, chap=self.chap, verse=self.verse, end=self.end, pnum=self.pnum(mode))
            self.waspar = ispara(c)
            self.mode = mode
        self.acc.append(currChunk)
        self.currChunk = currChunk
        return currChunk

    def collect(self, root, primary=True, depth=0):
        ischap = sfm.text_properties('chapter')
        isverse = sfm.text_properties('verse')
        currChunk = None
        if depth==0:
            self.type=None
        else:
            if debugPrint:
                print("{" * depth)
        elements = root[:]
        if len(self.acc) == 0:
            if isinstance(root[0], sfm.Element) and root[0].name == "id":
                # turn \id into a paragraph level and main children as siblings
                elements = root[0][1:]
                idel = sfm.Element(root[0].name, args=root[0].args[:], content=root[0][0], meta=root[0].meta)
                currChunk = self.makeChunk(idel)
                currChunk.append(idel)
        for c in elements:
            if not isinstance(c, sfm.Element): 
                if (isinstance(c,sfm.Text) and len(c)>3):
                    self.waspar=False
                if(currChunk): # It's a text node, make sure it's attached to the right place.
                    currChunk.append(c)
                    root.remove(c)
                continue
            if c.name == "fig":
                if self.fsecondary == primary:
                    root.remove(c)
                    continue
            newchunk = False
            if ispara(c):
                newmode = _marker_modes.get(c.name, _textype_map.get(str(c.meta.get('TextType')), self.mode))
                if c.name not in nestedparas and (newmode != self.mode \
                                                  or self.mode not in (ChunkType.HEADING, ChunkType.TITLE)):
                    newchunk = True
            if isverse(c):
                vc = re.sub(r"[^0-9\-]", "", c.args[0])
                try:
                    if "-" in c.args[0]:
                        v, e = map(int, vc.split('-'))
                    else:
                        v = int(vc)
                        e = v
                except (ValueError, TypeError):
                    v = 0
                    e = 0
                self.verse = v
                self.end = e
                self.counts = {}
                self.currChunk.hasVerse = True
                if MergeF.ChunkOnVerses in settings:
                    newchunk = True
                else:
                    self.currChunk.label(self.chap, self.verse, self.end, 0)
            if debugPrint:
                print(newchunk, c.name, "context:", self.oldmode,self.mode  if isinstance(c, sfm.Element) else '-' )
            if newchunk:
                self.oldmode=self.mode
                currChunk = self.makeChunk(c)
                if MergeF.ChunkOnVerses in settings:
                    if isverse(c):
                        currChunk.hasVerse = True # By definition!
                        self.currChunk.label(self.chap, self.verse, self.end, 0)
                        self.currChunk.hasVerse = True
                #elif (currChunk.type==ChunkType.BODY and ispara(c) and self.oldmode == ChunkType.MIDVERSEPAR): 
                    #currChunk.type=ChunkType.MIDVERSEPAR
            if currChunk is not None:
                currChunk.append(c)
                if c in root:
                    root.remove(c)      # now separate thing in a chunk, it can't be in the content of something
            if ischap(c):
                vc = re.sub(r"[^0-9\-]", "", c.args[0])
                try:
                    self.chap = int(vc)
                except (ValueError, TypeError):
                    self.chap = 0
                if currChunk is not None:
                    currChunk.chap = self.chap
                    currChunk.verse = 0
                newc = sfm.Element(c.name, pos=c.pos, parent=c.parent, args=c.args, meta=c.meta)
                currChunk[-1] = newc
            currChunk = self.collect(c, primary=primary,depth=1+depth) or currChunk
        if debugPrint:
            print("}" * depth)
        return currChunk

    def reorder(self):
        # Merge contiguous title and table chunks, Merge in nested paragraphs
        ti = None
        bi = None
        ni = None
        #for i in range(0, 10):
            #print(i,self.acc[i].ident if isinstance(self.acc[i],Chunk) else '-' ,self.acc[i].type,self.acc[i])
        for i in range(1, len(self.acc)):
            if self.acc[i].type == ChunkType.TITLE and self.acc[i-1].type == ChunkType.TITLE:
                if bi is None:
                    bi = i-1
                self.acc[bi].extend(self.acc[i])
                self.acc[i].deleteme = True
                ti = None
                ni = None
                if debug:
                    print('Merged.1:', 'deleteme' in self.acc[bi], self.acc[bi])
            elif self.acc[i].type == ChunkType.TABLE and self.acc[i-1].type == ChunkType.TABLE:
                if ti is None:
                    ti = i - 1
                self.acc[ti].extend(self.acc[i])
                self.acc[i].deleteme = True
                bi = None
                ni = None
                if debugPrint:
                    print('Merged.2:', 'deleteme' in self.acc[ti], self.acc[ti])
            elif self.acc[i].type == ChunkType.NPARA and self.acc[i-1].type != None:
                if ni is None:
                    ni = i - 1
                self.acc[ni].extend(self.acc[i])
                self.acc[i].deleteme = True
                bi = None
                ti = None
                if debugPrint:
                    print('Merged.3:', 'deleteme' in self.acc[ni], self.acc[ni])
        # Merge nb with chapter number and 1st verse.
        for i in range(1, len(self.acc) - 1):
            if self.acc[i].type is ChunkType.NB and self.acc[i-1].type is ChunkType.CHAPTER:
                self.acc[i-1].type=ChunkType.NBCHAPTER
                if MergeF.NoSplitNB in settings:
                    self.acc[i-1].extend(self.acc[i])
                    self.acc[i].deleteme = True
                    #print("NB met",self.acc[i-2].type ,self.acc[i-1].type ,self.acc[i].type )
                    if self.acc[i+1].type == ChunkType.PARVERSE:
                        self.acc[i-1].verse=self.acc[i+1].verse
                        self.acc[i-1].extend(self.acc[i+1])
                        self.acc[i+1].deleteme = True
                    if i>2 and self.acc[i-2].type in (ChunkType.VERSE, ChunkType.MIDVERSEPAR, ChunkType.PARVERSE, ChunkType.PREVERSEPAR):
                        self.acc[i-2].extend(self.acc[i-1])
                        self.acc[i-1].deleteme = True
                        

        # Merge pre-verse paragraph and verses.
        for i in range(1, len(self.acc) - 1):
            if self.acc[i].type == ChunkType.PARVERSE:
                if  self.acc[i-1].type in (ChunkType.PREVERSEPAR, ChunkType.NB):
                    # A PARVERSE gives its address and content up to the preceeding PREVERSEPAR, as the two may not be seperated
                    if bi is None:
                        bi=i-1
                    self.acc[bi].verse=self.acc[i].verse
                    self.acc[bi].pnum=self.acc[i].pnum
                    self.acc[bi].extend(self.acc[i])
                    self.acc[i].deleteme = True
                elif (self.acc[i-1].type in (ChunkType.CHAPTER, ChunkType.NBCHAPTER)):
                    pass 
                else:
                    print(F"Caught unexpected situtuation. Expected (PREVERSEPAR,PARVERSE), got: {self.acc[i-1].type} {self.acc[i].type}")
                    print(self.acc[i-1], self.acc[i])
                    #raise ValueError("Caught unexpected situtuation. Expected (PREVERSEPAR,PARVERSE), got: %,%" %  (self.acc[i-1].type, self.acc[i].type))
            else:
                bi=None
        # make headings in the intro into intro
        for i in range(1, len(self.acc) - 1):
            c = self.acc[i+1]
            if c.type in (ChunkType.CHAPTER, ChunkType.BODY, ChunkType.PREVERSEPAR):
                break
            c = self.acc[i]
            if c.type == ChunkType.HEADING:
                c.type == ChunkType.INTRO
        # Swap chapter and heading first
        for i in range(1, len(self.acc)):
            if self.acc[i].type == ChunkType.CHAPTER and self.acc[i-1].type == ChunkType.HEADING:
                self.acc[i].extend(self.acc[i-1])
                self.acc[i-1].deleteme = True
                if debugPrint:
                    print('Merged.4:', 'deleteme' in self.acc[i], self.acc[i])
            elif self.acc[i-1].type == ChunkType.CHAPTER and self.acc[i].type == ChunkType.HEADING:
                self.acc[i-1].extend(self.acc[i])
                self.acc[i].deleteme = True
                if debugPrint:
                    print('Merged.5:', 'deleteme' in self.acc[i-1], str(self.acc[i-1]))
        # Merge all chunks between \c and not including \v.
        if 0:
            for i in range(1, len(self.acc)):
                if self.acc[i-1].type == ChunkType.CHAPTER and not self.acc[i].hasVerse:
                    self.acc[i-1].extend(self.acc[i])
                    self.acc[i].deleteme = True
                    if debugPrint:
                        print('Merged.6:', 'deleteme' in self.acc[i-1], self.acc[i-1])
        # merge \c with body chunk following
        if 0:
            lastchunk = None
            prelastchunk = None
            for i in range(1, len(self.acc)):
                if getattr(self.acc[i], 'deleteme', False):
                    continue
                if lastchunk is not None and lastchunk.type == ChunkType.CHAPTER and self.acc[i].type == ChunkType.BODY:
                    tag = self.acc[i][0].name
                    lastchunk.extend(self.acc[i])
                    lastchunk.type = self.acc[i].type
                    self.acc[i].deleteme = True
                    if tag == "nb" and prelastchunk is not None:
                        prelastchunk.extend(lastchunk)
                        lastchunk.deleteme = True
                    elif tag.startswith("q") and i < len(self.acc) - 1 and self.acc[i+1][0].name.startswith("q"):
                        lastchunk.extend(self.acc[i+1])
                        self.acc[i+1].deleteme = True
                if not getattr(lastchunk, 'deleteme', False):
                    prelastchunk = lastchunk
                else:
                    lastchunk = prelastchunk
                    prelastchunk = None     # can't really move backwards
                if not getattr(self.acc[i], 'deleteme', False):
                    lastchunk = self.acc[i]
        logger.debug("Chunks before reordering: {}".format(len(self.acc)))
        self.acc = [x for x in self.acc if not getattr(x, 'deleteme', False)]
        logger.debug("Chunks after reordering: {}".format(len(self.acc)))
        if debugPrint:
            for i in range(0, len(self.acc)):
                print(i,self.acc[i].ident if isinstance(self.acc[i],Chunk) else '-' ,self.acc[i].type,self.acc[i])
    def score(self,results={}):
        """Calculate the scores for each chunk, returning an array of non-zero scores (potential break points)
        If the results parameter is given, then the return value is a summation
        """
        for i in range(0, len(self.acc)):
            t=self.acc[i].type.value
            scval=self.scores[t]
            self.acc[i].score=scval
            pos=self.acc[i].position
            self.loc[pos]=i
            if pos in results:
                results[pos]+=scval
                print("%s  + %d = %d" % (pos,scval, results[pos]))
            else:
                results[pos]=scval
                print(pos, "=", scval)
        return results
    def getofs(self,pos, incremental=True):
        """Return the index into acc[] of the (end-point) pos. If an exact match for pos cannot be found, return the index of the next highest point. If incremental is true, it assumes that calls to this are always done in increasing sequence.
        """
        if (pos in self.loc):
            self.lastloc=self.loc[pos]
        else:
            if (self.lastloc is None) or (not incremental):
                self.lastloc=0
            lim=len(self.acc)
            while self.lastloc< lim and self.acc[self.lastloc].position < pos:
                self.lastloc+=1
        return self.lastloc

def appendpair(pairs, ind, chunks):
    if len(pairs) and pairs[-1][ind] is not None:
        lastp = pairs[-1][ind]
        lastt = lastp.type
        end = None
        found = False
        for i, c in enumerate(chunks):
            if c.type == lastt:
                found = True
                end = i
            elif found:
                break
        if end is not None:
            for c in chunks[:end+1]:
                lastp.extend(c)
            chunks = chunks[end+1:]
    if ind == 1:
        pairs.extend([[None, c] for c in chunks])
    else:
        pairs.extend([[c, None] for c in chunks])

def appendpairs(pairs, pchunks, schunks):
    if len(pairs) and pairs[-1][0] is not None and pairs[-1][1] is not None:
        lastp = pairs[-1][0]
        lasts = pairs[-1][1]
        lastt = lastp.type
        if lasts.type == lastt:
            while len(pchunks) and pchunks[0].type == lastt:
                lastp.extend(pchunks.pop(0))
            while len(schunks) and schunks[0].type == lastt:
                lasts.extend(schunks.pop(0))
    if len(pchunks):
        pc = pchunks[0]
        for c in pchunks[1:]:
            pc.extend(c)
    else:
        pc = None
    if len(schunks):
        sc = schunks[0]
        for c in schunks[1:]:
            sc.extend(c)
    else:
        sc = None
    pairs.append([pc, sc])

def alignChunks(primary, secondary):
    pchunks, pkeys = primary
    schunks, skeys = secondary
    pairs = []
    diff = difflib.SequenceMatcher(None, pkeys, skeys)
    for op in diff.get_opcodes():
        (action, ab, ae, bb, be) = op
        if debugPrint:
            print(op, debstr(pkeys[ab:ae]), debstr(skeys[bb:be]))
        if action == "equal":
            pairs.extend([[pchunks[ab+i], schunks[bb+i]] for i in range(ae-ab)])
        elif action == "delete":
            appendpair(pairs, 0, pchunks[ab:ae])
        elif action == "insert":
            appendpair(pairs, 1, schunks[bb:be])
        elif action == "replace":
            pgk, pgg = zip(*[(k, list(g)) for k, g in groupby(pchunks[ab:ae], key=lambda c:c.type)])
            sgk, sgg = zip(*[(k, list(g)) for k, g in groupby(schunks[bb:be], key=lambda c:c.type)])
            diffg = difflib.SequenceMatcher(a=pgk, b=sgk)
            for opg in diffg.get_opcodes():
                (actiong, abg, aeg, bbg, beg) = opg
                if debugPrint:
                    print("--- ", opg, debstr(pgk[abg:aeg]), debstr(sgk[bbg:beg]))
                if actiong == "equal":
                    appendpairs(pairs, sum(pgg[abg:aeg], []), sum(sgg[bbg:beg], []))
                elif action == "delete":
                    appendpair(pairs, 0, sum(pgg[abg:aeg], []))
                elif action == "insert":
                    appendpair(pairs, 0, sum(sgg[bbg:beg], []))
                elif action == "replace":
                    for zp in zip(range(abg, aeg), range(bbg, beg)):
                        appendpairs(pairs, pgg[zp[0]], sgg[zp[1]])
                    sg = bbg + aeg - abg
                    if sg < beg:
                        appendpair(pairs, 1, sum(sgg[sg:beg], []))
                    sg = abg + beg - bbg
                    if sg < aeg:
                        appendpair(pairs, 0, sum(pgg[sg:aeg], []))
    return pairs

def alignSimple(primary, *others):
    # import pdb; pdb.set_trace()
    pchunks, pkeys = primary
    if isinstance(pchunks, Collector):
        pchunks=pchunks.acc
    numkeys = len(pkeys)
    runs = [[[x, x]] for x in range(numkeys)]
    runindices = list(range(numkeys))
    for ochunks, okeys in others:
        if isinstance(pchunks, Collector):
            ochunks=ochunks.acc
        runs = [x + [None] for x in runs]
        diff = difflib.SequenceMatcher(None, pkeys, okeys)
        for op in diff.get_opcodes():
            (action, ab, ae, bb, be) = op
            if debugPrint:
                print(op, debstr(pkeys[ab:ae]), debstr(okeys[bb:be]))
            if action == "equal":
                for i in range(ae-ab):
                    ri = runindices[ab+i]
                    if runs[ri][-1] is None:
                        runs[ri][-1] = [bb+i, bb+i]
                    else:
                        runs[ri][-1][1] = bb+i
            if action in ("delete", "replace"):
                ai = runindices[ab]
                for c in range(ab, ae):
                    ri = runindices[c]
                    if ri > ai:
                        for j in len(runs[0]):
                            runs[ai][j][1] = runs[ri][j][1]
                    for j in range(c, numkeys):
                        runindices[j] -= 1
                    runs = runs[:ri] + runs[ri+1:]
            if action in ("insert", "replace"):
                ai = runindices[ab]
                runs[ai][-1] = [bb, be-1]
    results = []
    for r in runs:
        res = [Chunk(*sum(pchunks[r[0][0]:r[0][1]+1], []), mode=pchunks[r[0][1]].type)]
        for i, (ochunks, okeys) in enumerate(others, 1):
            res.append(Chunk(*sum(ochunks[r[i][0]:r[i][1]+1], []), mode=ochunks[r[i][1]].type))
        results.append(res)
    return results

def alignScores(*columns):
    # get the basic scores.
    merged={}
    for ochunks, okeys in columns:
        merged=ochunks.score(merged)
    positions=[k for k,v in merged.items()]
    positions.sort()
    # Ensure headings get split from preceding text if there's a coming break
    for i in range (0,len(positions)-1):
        if(positions[i][3]=='HEADING') and (merged[positions[i+1]]>99):
            a=0
            while positions[i-a-1][3]=='HEADING':
                a+=1
            print(f"Spliting between positions {positions[i-a]} and {positions[i+1]}")
            merged[positions[i-a]]=100
            if MergeF.HeadWithText in settings:
                merged[positions[i+1]]=0
    del positions
    syncpositions=[k for k,v in merged.items() if v>=100]
    syncpositions.sort()
    print(syncpositions, sep=" ")
    results=[]
    colkeys={}
    for i in range(0,len(columns)):
        colkeys[columns[i][0].colkey]=i
    print("colkeys:", colkeys)
    ofs={}
    blank={}
    lim={}
    acc={}
    coln={}
    for c,i in colkeys.items():
        ofs[c]=0
        blank[c]=None
        lim[c]=len(columns[i][0].acc)
        coln[c]=columns[i][0]
        acc[c]=coln[c].acc
    syncpositions.append((999,999,999))
    for posn in syncpositions:
        chunks=blank.copy()
        for c,i in colkeys.items():
            nxt=coln[c].getofs(posn) # Get the next offset.
            if debugPrint:
                print ("CHUNK:\n",posn, c,ofs[c],nxt, lim[c])
                if (ofs[c]==nxt):
                    print (nxt,'=',acc[c][nxt].position)
            if (nxt>lim[c]):
                raise ValueError(f"This shouldn't happen, {nxt} > {lim[c]}!")
            p=merged
            while (ofs[c]<lim[c]) and (ofs[c]<nxt): 
                thispos=acc[c][ofs[c]].position
                print(ofs[c], thispos, merged[thispos] if thispos in merged else '0' ,  sep='=', end=" ",flush=True)
                if chunks[c]:
                    chunks[c].append(acc[c][ofs[c]])
                else:
                    chunks[c]=[acc[c][ofs[c]]]
                ofs[c]+=1
            print()
            if (chunks[c]):
                print(*chunks[c], sep="")
        results.append({c:chunks[c] for c in colkeys})
    return results

def appendsheet(fname, sheet):
    if os.path.exists(fname):
        with open(fname) as s:
            sheet = style.update_sheet(sheet, style.parse(s))
    return sheet

modes = {
    "doc": alignChunks,
    "simple": alignSimple,
    "scores" : alignScores
}

def usfmerge2(infilearr, keyarr, outfile, stylesheets=[],stylesheetsa=[], stylesheetsb=[], fsecondary=False, mode="doc", debug=False, scorearr={}, synchronise="normal"):
    global debugPrint, debstr,settings
    debugPrint = debug
    # print(f"{stylesheetsa=}, {stylesheetsb=}, {fsecondary=}, {mode=}, {debug=}")
    tag_escapes = r"[^a-zA-Z0-9]"
    # Check input
    if (len(keyarr) != len(infilearr)):
        raise ValueError("Cannot have %d keys and %d files!" % (len(keyarr),len(infilearr)) )
        
    if type(scorearr)==list:
        tmp=zip(keyarr,scorearr)
        scorearr={}
        for k,v in tmp:
            if k in scorearr:
                raise ValueError("Cannot have reapeated entries in key array! (%c already seen)" %(k))
            scorearr[k]=int(v)
        del tmp
    print(type(scorearr),scorearr)
    if debugPrint:
        print(stylesheetsa, stylesheetsb)
    
    # load stylesheets
    sheets={}
    for k in keyarr:
        if debugPrint:
            print(f"defining stylesheet {k}")
        sheets[k]=usfm._load_cached_stylesheet('usfm_sb.sty')
    for s in stylesheetsa:
        if debugPrint:
            print(f"Appending {s} to stylesheet {k}")
        sheets['L']=appendsheet(s, sheets['L'])
    for s in stylesheetsb:
        if debugPrint:
            print(f"Appending {s} to stylesheet {k}")
        sheets['R']=appendsheet(s, sheets['R'])
    for k,s in stylesheets:
        if debugPrint:
            print(f"Appending {s} to stylesheet {k}")
        sheets[k] = appendsheet(s,sheet[k])
    # Set-up potential synch points
    tmp=synchronise.split(",")
    if len(tmp)==1:
        syncarr={k:synchronise for k in keyarr}
    else:
        if len(tmp)!=len(keyarr):
            raise ValueError("Cannot have %d keys and %d synchronisation modes!" % (len(keyarr),len(tmp)) )
        else:
            syncarr=tmp


    if len(scorearr)==0:
        s=int(1+100/len(keyarr))
        scorearr={k:s for k in keyarr}
    elif len(scorearr)!=len(keyarr) :
        raise ValueError("Cannot have %d keys and %d scores!" % (len(keyarr),len(scorearr)) )

    def texttype(m):
        res = stylesheet.get(m, {'TextType': 'other'}).get('TextType').lower()
        #if res in ('chapternumber', 'versenumber'):
        #   res = 'versetext'
        return res

    debstr = lambda s: s

    def myGroupChunks(*a, **kw):
        return groupChunks(*a, texttype, **kw)
    chunks={}
    chunklocs={}
    colls={}
    if (mode == "scores") or ("verse"  in syncarr) or ("chapter" in syncarr) : #Score-based splitting may force the break-up of an NB, the others certainly will.
        settings =  settings & (~MergeF.NoSplitNB)
    for colkey,infile in zip(keyarr,infilearr):
        if debugPrint:
            print(f"Reading {colkey}: {infile}")
        with open(infile, encoding="utf-8") as inf:
            doc = list(usfm.parser(inf, stylesheet=sheets[colkey],
                                   canonicalise_footnotes=False, tag_escapes=tag_escapes))
            while len(doc) > 1:
                if isinstance(doc[0], sfm.Text):
                    doc.pop(0)
                else:
                    break
            colls[colkey] = Collector(doc=doc, colkey=colkey, fsecondary=fsecondary, stylesheet=sheets[colkey], scores=scorearr[colkey],synchronise=syncarr[colkey])
        chunks[colkey] = {c.ident: c for c in colls[colkey].acc}
        chunklocs[colkey] = ["_".join(str(x) for x in c.ident) for c in colls[colkey].acc]

    f = modes[mode]
    pairs = f(*((colls[k], chunklocs[k]) for k in keyarr))

    if mode=="scores":
        if outfile is not None:
            outf = open(outfile, "w", encoding="utf-8")
        else:
            outf = sys.stdout
        for i, p in enumerate(pairs):
            for col,data in p.items():
                if data is not None:
                    outf.write("\\polyglotcolumn %c\n" % col)
                    for d in data:
                        outf.write(str(d))
            outf.write("\n\\polyglotendcols\n")
    else:
        isright = True
        for i, p in enumerate(pairs):
            if p[0] is not None and len(p[0]):
                if isright:
                    outf.write("\\lefttext\n")
                    isright = False
                outf.write(str(p[0]))
                if p[0].type != ChunkType.HEADING and p[0].type != ChunkType.TITLE:
                    outf.write("\\p\n")
            elif i != 0 and isright and p[1] is not None and len(p[1]):
                outf.write("\\nolefttext\n")
                isright = False
            if p[1] is not None and len(p[1]):
                if not isright:
                    outf.write("\\righttext\n")
                    isright = True
                outf.write(str(p[1]))
                if p[1].type != ChunkType.HEADING and p[1].type != ChunkType.TITLE:
                    outf.write("\\p\n")
            elif not isright:
                outf.write("\\norighttext\n")

