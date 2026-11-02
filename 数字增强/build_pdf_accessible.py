#!/usr/bin/env python3
"""Non-destructive accessibility/navigation enhancement of the approved Aeneis PDF.
Preserves all page geometry, typography, art assets and visible content.
Does not assert PDF/UA or PDF/A conformance; requires assistive-tech testing.
"""
from pathlib import Path
from collections import defaultdict,Counter
from copy import deepcopy
import re,json,hashlib
import fitz
from pypdf import PdfReader, PdfWriter
from pypdf.generic import (NameObject as N, TextStringObject as T, NumberObject as I, FloatObject as F,
    DictionaryObject as D, ArrayObject as A, NullObject as Z, DecodedStreamObject as Stream,
    ContentStream, BooleanObject as B)

BASE=Path('/mnt/data')
SRC=BASE/'aeneis_pdf_repair/visual_color_fixed.pdf'
OUT=BASE/'Aeneid-zh_ed4_2026-10-08_PDF修订校验版.pdf'
REPORT=BASE/'aeneis_pdf_repair/report.json'
doc=fitz.open(SRC)
r=PdfReader(SRC)
w=PdfWriter(clone_from=r)
w.pdf_header="%PDF-1.7"
assert len(doc)==len(w.pages)==338
H=float(w.pages[0].mediabox.height)


# Independent, human-reviewed labels are derived from approved edition captions.
plate_titles=['狄多与埃涅阿斯','埃涅阿斯离开特洛伊','埃涅阿斯与安德罗玛刻相会','墨丘利催促埃涅阿斯',
 '埃涅阿斯与阿刻斯忒斯','埃涅阿斯与卡戎','阿玛塔与拉维尼娅在酒神女信徒之中',
 '维纳斯将武器交给埃涅阿斯','尼苏斯杀死沃尔肯斯','埃涅阿斯与墨泽提乌斯、劳苏斯之战',
 '卡米拉杀死奥努斯之子','埃涅阿斯与图尔努斯的最后决斗']
plate_pages=[7,32,58,82,106,133,164,191,215,242,271,300] # zero-based from edition bookmarks
# Additional context for useful Alt text, without speculative visual detail.
alt={0:'《埃涅阿斯纪》第四版封面：古典风景绘画中，黄昏天空下的河岸、石柱遗迹与树林；下方叠印中文书名。',
 5:'地图一：上下两幅古代世界地图的灰度复现图，示出地中海及周边地区，用于对照史诗发生地的古代地理观念。',
 6:'地图二：现代简化的地中海路线图，用蓝色线条示意埃涅阿斯从特洛伊向西航行至意大利拉提乌姆的路线，标注重要停靠地与海域。',
 163:'地图三：拉提乌姆与台伯河及其支流的示意图，以不同线条和标注展示河流、居住地与史诗后半部意大利战争有关的地点。',
 337:'版本记：深灰色超大竖排“版本记”标题位于左侧，右侧列出第四版、发布者及日期；下方提供可点击的主页二维码与文字链接。'}
for n,idx in enumerate(plate_pages):
 alt[idx]=f'第{n+1}卷卷首黑白蚀刻版画，描绘《{plate_titles[n]}》中的人物与场景；以人物、建筑和风景的明暗线条组成叙事画面。原版由 Wenceslaus Hollar 据 Francis Cleyn 设计制作。'

# --- Identify all existing body superscript citations; locate corresponding printed note numerals ---
forward={};note_boxes={};note_first_top={}
for pgnum,p in enumerate(doc):
 for l in p.get_links():
  nm=l.get('nameddest','')
  if re.fullmatch(r'Hfootnote\.\d+',nm):
   n=int(nm.split('.')[-1]);assert n not in forward,(n,pgnum)
   forward[n]=(pgnum,l)
assert sorted(forward)==list(range(1,535))
for n,(page_idx,l) in forward.items():
 dest_page=l['page'];assert 0<=dest_page<len(doc)
 matches=[]
 for b in doc[dest_page].get_text('dict')['blocks']:
  for ln in b.get('lines',[]):
   for sp in ln['spans']:
    if sp['text'].strip()==str(n) and 5<sp['size']<6.8 and sp['bbox'][0]<80:
     matches.append(sp['bbox'])
 assert len(matches)==1,(n,dest_page,matches)
 box=matches[0]
 note_boxes[n]=(dest_page,box)
 note_first_top[dest_page]=min(note_first_top.get(dest_page,float('inf')),box[1])

# --- Footnote annotations: internal destinations link exactly to source marker, not just the page ---
link_num=0
for n in sorted(forward):
 src,l=forward[n]
 dest,box=note_boxes[n]
 bp=w.pages[dest]
 x0,y0,x1,y1=box
 # Footnote number is accessible as a return target without drawing a new symbol.
 # Avoid covering body text: click region primarily lies in the number's indentation.
 a=A([F(max(0,x0-2.1)),F(H-min(H,y1+2.6)),F(x1+3.2),F(H-max(0,y0-2.6))])
 sx=l['from'];sx0,sy0,sx1,sy1=map(float,[sx.x0,sx.y0,sx.x1,sx.y1])
 to=A([w.pages[src].indirect_reference,N('/XYZ'),F(max(0,sx0-8)),F(H-max(0,sy0-5)),Z()])
 annot=D({N('/Type'):N('/Annot'),N('/Subtype'):N('/Link'),N('/Rect'):a,
  N('/Border'):A([I(0),I(0),I(0)]),N('/H'):N('/I'),
  N('/Contents'):T(f'返回正文中脚注 {n} 的引用位置'),
  N('/A'):D({N('/S'):N('/GoTo'),N('/D'):to})})
 ref=w._add_object(annot)
 if '/Annots' not in bp:bp[N('/Annots')]=A([])
 bp['/Annots'].append(ref)
 link_num+=1
 # Existing forward link hit box is increased for finger/stylus use, cautiously avoiding overlap.
 for old in w.pages[src]['/Annots']:
  obj=old.get_object()
  if obj.get('/Subtype')!='/Link': continue
  aa=obj.get('/A')
  if aa is None or str(aa.get('/D',''))!=f'Hfootnote.{n}':continue
  x0,y0,x1,y1=map(float,obj['/Rect'])
  obj[N('/Rect')]=A([F(max(0,x0-2)),F(max(0,y0-2.1)),F(x1+3),F(min(H,y1+2.1))])
  obj[N('/Contents')]=T(f'跳转到脚注 {n}；可点击脚注编号返回正文')
  break
 else:raise RuntimeError(f'Missing body link annotation for {n}')
print('FOOTNOTES',link_num,flush=True)

# --- Font preflight: embed metrically compatible Latin sans for sole unembedded Helvetica in imported map artwork ---
font_fixed=0
for ob in w._objects:
 if not isinstance(ob,D):continue
 if ob.get('/Type')=='/Font' and ob.get('/Subtype')=='/Type1' and ob.get('/BaseFont')=='/Helvetica':
  fp=Path('/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf')
  fdata=Stream();fdata.set_data(fp.read_bytes());fdata[N('/Length1')]=I(fp.stat().st_size)
  fref=w._add_object(fdata)
  descriptor=D({N('/Type'):N('/FontDescriptor'),N('/FontName'):N('/LiberationSans'),
   N('/Flags'):I(32),N('/FontBBox'):A([I(-543),I(-303),I(1300),I(1016)]),
   N('/ItalicAngle'):I(0),N('/Ascent'):I(905),N('/Descent'):I(-212),
   N('/CapHeight'):I(688),N('/StemV'):I(80),N('/FontFile2'):fref})
  dref=w._add_object(descriptor)
  # Keep Helvetica glyph advances to preserve the existing map label positioning.
  from reportlab.pdfbase import _fontdata_widths_helvetica as helv
  from reportlab.pdfbase import _fontdata_enc_winansi as encoding
  widths=[]
  for cp in range(32,256):
   glyph=encoding.WinAnsiEncoding[cp]
   widths.append(I(int(helv.widths.get(glyph, 0)) if glyph else 0))
  ob.update({N('/Subtype'):N('/TrueType'),N('/BaseFont'):N('/LiberationSans'),N('/FirstChar'):I(32),N('/LastChar'):I(255),
   N('/Widths'):A(widths),N('/FontDescriptor'):dref})
  font_fixed+=1

# Every substituted WinAnsi character needs an explicit copy/search mapping.
# Metric data is retained to prevent shifts in the approved cartographic labels.
from pypdf.generic import create_string_object
cmap_lines=[
    '/CIDInit /ProcSet findresource begin', '12 dict begin','begincmap',
    '/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def',
    '/CMapName /Adobe-WinAnsi-UCS def', '/CMapType 2 def',
    '1 begincodespacerange','<00> <FF>','endcodespacerange']
pairs=[]
for cp in range(32,256):
    try: ch=bytes([cp]).decode('cp1252')
    except UnicodeDecodeError: continue
    pairs.append(f'<{cp:02X}> <{ord(ch):04X}>')
for i in range(0,len(pairs),95):
    subset=pairs[i:i+95]
    cmap_lines.append(f'{len(subset)} beginbfchar')
    cmap_lines.extend(subset)
    cmap_lines.append('endbfchar')
cmap_lines += ['endcmap','CMapName currentdict /CMap defineresource pop','end','end']
cmap_stream=Stream();cmap_stream.set_data(('\n'.join(cmap_lines)+'\n').encode('ascii'))
cmap_ref=w._add_object(cmap_stream)
for ob in w._objects:
    if isinstance(ob,D) and ob.get('/Type')=='/Font' and ob.get('/BaseFont')=='/LiberationSans':
        ob[N('/ToUnicode')]=cmap_ref

assert font_fixed==1,font_fixed
print('FONT EMBED',font_fixed,flush=True)

# --- Selected glossary cross-references, once per book/term to avoid noisy hyperlinks ---
# All destinations are the actual displayed Chinese entry heads (not merely a glossary page).
important_names=['埃涅阿斯','狄多','安喀塞斯','朱诺','维纳斯','图尔努斯',
 '赫克托耳','拉维尼娅','卡米拉','尼苏斯','欧律阿卢斯','普里阿摩斯',
 '厄万德','帕拉斯','狄俄墨得斯','拉提努斯','墨泽提乌斯','劳苏斯',
 '安德罗玛刻','阿喀琉斯','拉奥孔','俄里翁','朱庇特','墨丘利',
 '克瑞乌萨','帕利努鲁斯','阿玛塔','安娜','阿卡忒斯','赫勒努斯']
glossary_targets={}
for pi in range(331,337):
 for block in doc[pi].get_text('dict')['blocks']:
  for line in block.get('lines',[]):
   for sp in line['spans']:
    if 8.75<sp['size']<9.16 and sp['color']==4412506:
     normalized=sp['text'].strip()
     for term in important_names:
      if normalized==term and term not in glossary_targets:
       glossary_targets[term]=(pi,sp['bbox'])
glossary_link_count=0
ranges=[(8,32),(33,58),(59,82),(83,106),(107,133),(134,163),
 (165,191),(192,215),(216,242),(243,271),(272,300),(301,330)]
for b,(start,stop) in enumerate(ranges):
 remaining=set(glossary_targets)
 for pi in range(start,stop):
  if not remaining:break
  for block in doc[pi].get_text('dict')['blocks']:
   for line in block.get('lines',[]):
    for sp in line['spans']:
     if not (9.9<sp['size']<10.4 and 52<sp['bbox'][1]<700):continue
     for term in sorted(remaining,key=len,reverse=True):
      if term not in sp['text']:continue
      matches=doc[pi].search_for(term)
      matches=[m for m in matches if abs(m.y0-sp['bbox'][1])<3 and m.x0>=sp['bbox'][0]-2 and m.x1<=sp['bbox'][2]+2]
      if not matches:continue
      rect=matches[0]
      gi,gb=glossary_targets[term]
      a=A([F(rect.x0),F(H-rect.y1),F(rect.x1),F(H-rect.y0)])
      to=A([w.pages[gi].indirect_reference,N('/XYZ'),F(max(0,gb[0]-15)),F(H-max(0,gb[1]-22)),Z()])
      obj=D({N('/Type'):N('/Annot'),N('/Subtype'):N('/Link'),N('/Rect'):a,
        N('/Border'):A([I(0),I(0),I(0)]),N('/Contents'):T(f'{term}：前往专名与术语表对应条目'),
        N('/A'):D({N('/S'):N('/GoTo'),N('/D'):to})})
      if '/Annots' not in w.pages[pi]:w.pages[pi][N('/Annots')]=A([])
      w.pages[pi]['/Annots'].append(w._add_object(obj))
      remaining.remove(term);glossary_link_count+=1
print('GLOSSARY',glossary_link_count,'terms',len(glossary_targets),flush=True)


# Actual marked-content and reading-order semantic structure.
# Footnotes use one /Note element per individual numbered note (not one per page).
# Link objects are placed under the text paragraph containing the clickable marker.
import bisect, math
root=D({N('/Type'):N('/StructTreeRoot'),N('/K'):A([])})
rootref=w._add_object(root)
w._root_object[N('/StructTreeRoot')]=rootref
w._root_object[N('/MarkInfo')]=D({N('/Marked'):B(True),N('/Suspects'):B(True)})
w._root_object[N('/Lang')]=T('zh-CN')
parent_numbers=A([])

def make_elem(role,parent,page_ref=None,alt_text=None):
    obj=D({N('/Type'):N('/StructElem'),N('/S'):N('/'+role),N('/P'):parent,N('/K'):A([])})
    if page_ref is not None:obj[N('/Pg')]=page_ref
    if alt_text:obj[N('/Alt')]=T(alt_text)
    ref=w._add_object(obj)
    parent.get_object()['/K'].append(ref)
    return ref

def mul(m,n):
    a,b,c,d,e,f=m; A_,B_,C_,D_,E_,F_=n
    return (a*A_+c*B_,b*A_+d*B_,a*C_+c*D_,b*C_+d*D_,a*E_+c*F_+e,b*E_+d*F_+f)

document_elem=make_elem('Document',rootref)
current=make_elem('Sect',document_elem)
plate_pages_set=set(plate_pages)
first_body=set([8,33,59,83,107,134,165,192,216,243,272,301])
notes_by_page=defaultdict(list)
for n,(pi,b) in note_boxes.items(): notes_by_page[pi].append((b[1],n))
for pi in notes_by_page:notes_by_page[pi].sort()
page_structs=[]; page_records=[]; page_parent_arrays=[]
note_elems={}; num_figures=0;count_mcid=0;num_headings=0;pages_with_text=0
for pi,page in enumerate(w.pages):
    if pi in plate_pages_set or pi in (330,331,337):current=make_elem('Sect',document_elem)
    page_ref=page.indirect_reference
    page_structs.append(current)
    ops=ContentStream(page.get_contents(),w).operations
    output=[]; mcids=[]; records=[]
    state=(1.,0.,0.,1.,0.,0.);stack=[];bt_seen=0;figure_seen=0
    start_notes=notes_by_page.get(pi,[])
    start_ys=[s[0] for s in start_notes]
    def addmarked(parent,body):
        global count_mcid
        mcid=len(mcids)
        mcids.append(parent)
        parent.get_object()['/K'].append(I(mcid))
        output.append((A([N('/Span'),D({N('/MCID'):I(mcid)})]),b'BDC'))
        output.extend(body)
        output.append((A([]),b'EMC'))
        count_mcid+=1
        return mcid
    j=0
    while j<len(ops):
        args,op=ops[j]
        if op==b'q':stack.append(state)
        elif op==b'Q':
            if stack:state=stack.pop()
        elif op==b'cm' and len(args)==6:state=mul(state,tuple(float(x) for x in args))
        if op==b'BT':
            body=[(args,op)];j+=1
            textbase=None; fsize=0
            while j<len(ops):
                a,o=ops[j];body.append((a,o))
                if o==b'Tf' and len(a)>1:fsize=float(a[1])
                if o in (b'Td',b'Tm') and len(a)>=2 and textbase is None:
                    textbase=(float(a[0]),float(a[1])) if o==b'Td' else (float(a[4]),float(a[5]))
                if o==b'ET':break
                j+=1
            x=y=0;role='P'; n=None
            if textbase:
                x=state[0]*textbase[0]+state[2]*textbase[1]+state[4]
                y=H-(state[1]*textbase[0]+state[3]*textbase[1]+state[5])
                if start_notes and y >= start_ys[0]-7 and fsize<=9.6:
                    k=bisect.bisect_right(start_ys,y)-1
                    if k>=0:
                        n=start_notes[k][1]
                        role='Note'
                elif (y<40 or y>H-33) and fsize<9.2:
                    role='Artifact'
                elif ((pi in first_body and fsize>=20) or (pi in (330,331) and fsize>=19)):
                    role='H1'
            if role=='Artifact':
                output.append((A([N('/Artifact')]),b'BMC'))
                output.extend(body);output.append((A([]),b'EMC'))
            else:
                if role=='Note':
                    if n not in note_elems:
                        note_elems[n]=make_elem('Note',current,page_ref)
                        note_elems[n].get_object()[N('/T')]=T(f'脚注 {n}')
                    par=make_elem('P',note_elems[n],page_ref)
                else:
                    par=make_elem(role,current,page_ref)
                    if role=='H1':num_headings+=1
                mcid=addmarked(par,body)
                records.append({'x':x,'y':y,'size':fsize,'parent':par,'mcid':mcid,'note_n':n})
            bt_seen+=1
        elif op==b'Do':
            figure_seen+=1
            if pi in alt:
                fig=make_elem('Figure',current,page_ref,alt[pi] if figure_seen==1 else alt[pi]+'（补充图形）')
                addmarked(fig,[(args,op)])
                num_figures+=1
            else:
                output.append((A([N('/Artifact')]),b'BMC'))
                output.append((args,op));output.append((A([]),b'EMC'))
        else:output.append((args,op))
        j+=1
    if bt_seen:pages_with_text+=1
    if start_notes and not all(note_num in note_elems for _,note_num in start_notes): print('DEBUG_NOTES',pi+1,'expected',start_notes,'seen',list(note_elems)[-12:],'recs',[(round(t['y'],1),t['size'],t['note_n']) for t in records[-20:]],flush=True)
    assert all(note_num in note_elems for _,note_num in start_notes),(pi,start_notes)
    page_stream=ContentStream(None,w)
    page_stream.operations=output
    page[N('/Contents')]=w._add_object(page_stream)
    page[N('/StructParents')]=I(pi)
    parref=w._add_object(A(mcids))
    page_parent_arrays.append(parref)
    parent_numbers.extend([I(pi),parref])
    page_records.append(records)
    if pi%60==0:print('TAG_PROGRESS',pi+1,'MCID',len(mcids),'NOTES',len(start_notes),'FIG',figure_seen,flush=True)
assert set(note_elems)==set(note_boxes),(len(note_elems),len(note_boxes),set(note_boxes)-set(note_elems))

# Associate every link annotation with its actual reading position. Short note
# reference glyphs are linked as marked content AND as annotation OBJRs.
linked_annotation_count=0
used_glyphs=set(); marker_anchored=0
for pi,page in enumerate(w.pages):
    records=page_records[pi]
    page_arr=page_parent_arrays[pi].get_object()
    for anref in page.get('/Annots',[]):
        annot=anref.get_object()
        if annot.get('/Subtype')!='/Link':continue
        x0,y0,x1,y1=map(float,annot['/Rect'])
        cx=(x0+x1)/2;cy=H-(y0+y1)/2
        lbl=str(annot.get('/Contents',''))
        is_back=lbl.startswith('返回正文中脚注 ')
        is_forward=lbl.startswith('跳转到脚注 ')
        n=None
        if is_back or is_forward:
            m=re.search(r'脚注 (\d+)',lbl)
            if m:n=int(m.group(1))
        candidates=records
        if is_back and n:
            qualified=[r for r in candidates if r['note_n']==n and r['size']<7.5]
            if qualified:candidates=qualified
        elif is_forward:
            qualified=[r for r in candidates if r['note_n'] is None and r['size']<8.0]
            if qualified:candidates=qualified
        if candidates:
            anchor=min(candidates,key=lambda r:abs(r['y']-cy)*12 + abs(r['x']-cx)*.22)
            parent=anchor['parent']
        else:
            anchor=None;parent=page_structs[pi]
        elem=make_elem('Link',parent,page.indirect_reference)
        objr=D({N('/Type'):N('/OBJR'),N('/Obj'):anref,N('/Pg'):page.indirect_reference})
        elem.get_object()['/K'].append(objr)
        if n and is_forward and n in note_elems:elem.get_object()[N('/Ref')]=A([note_elems[n]])
        key=len(doc)+linked_annotation_count
        annot[N('/StructParent')]=I(key)
        if '/Contents' not in annot:
            text=doc[pi].get_textbox(fitz.Rect(x0,H-y1,x1,H-y0)).strip()
            annot[N('/Contents')]=T((text or '打开内部或外部链接')[:140])
        parent_numbers.extend([I(key),elem])
        if (is_back or is_forward) and anchor is not None and anchor['size']<8 and (pi,anchor['mcid']) not in used_glyphs:
            # Place the short clickable superscript inside the Link structure.
            # It was a direct child of the preceding P; replace that MCID with Link.
            kids=parent.get_object()['/K']
            try:
                pos=next(k for k,v in enumerate(kids) if isinstance(v,I) and int(v)==anchor['mcid'])
                kids.pop(pos)
                kids.insert(pos,elem)
                # make_elem already appended elem at the end: remove duplicate occurrence
                for k in range(len(kids)-1,pos,-1):
                    if kids[k]==elem:kids.pop(k);break
                elem.get_object()['/K'].insert(0,I(anchor['mcid']))
                page_arr[anchor['mcid']]=elem
                used_glyphs.add((pi,anchor['mcid']))
                marker_anchored+=1
            except StopIteration:pass
        linked_annotation_count+=1
root[N('/ParentTree')]=w._add_object(D({N('/Nums'):parent_numbers}))
root[N('/ParentTreeNextKey')]=I(len(doc)+linked_annotation_count)
print('STRUCT_DONE',len(note_elems),'unique notes;',count_mcid,'MCIDs;',linked_annotation_count,'linked annots;',marker_anchored,'glyph links',flush=True)

# Add ordered print-format friendly thumbnail/illustration bookmarks; no new printed pages.
nav=w.add_outline_item('图版与地图快捷索引',5)
for page,title in [(5,'地图一：斯特拉波所述的世界'),(6,'地图二：从特洛伊到拉提乌姆'),(163,'地图三：拉提乌姆与台伯河')]+[(p,'第%s卷：%s'%(i+1,t)) for i,(p,t) in enumerate(zip(plate_pages,plate_titles))]:
 w.add_outline_item(title,page,parent=nav)

# Bookmark navigation every hundred lines, without a visible change to poem layout.
poem_bookmarks=0
verse_root=w.add_outline_item('按原诗行定位（每100行）',8)
body_start=[8,33,59,83,107,134,165,192,216,243,272,301]
body_end=[32,58,82,106,133,163,191,215,242,271,300,330]
for b,(start,end) in enumerate(zip(body_start,body_end)):
 parent=w.add_outline_item(f'第{b+1}卷',start,parent=verse_root)
 found={}
 for pi in range(start,end):
  if pi in plate_pages:continue
  for bl in doc[pi].get_text('dict')['blocks']:
   for ln in bl.get('lines',[]):
    for sp in ln['spans']:
     t=sp['text'].strip()
     if t.isdigit() and len(t)<=4 and int(t)%100==0 and int(t)>0 and 7<sp['size']<8 and sp['bbox'][0]<90 and 45<sp['bbox'][1]<700:
      k=int(t)
      if k not in found:found[k]=(pi,sp['bbox'][1])
 for v,(pi,y) in sorted(found.items()):
  # Fit bookmarks to exact vertical position instead of opening at page top.
  try:
   from pypdf.generic import Fit
   w.add_outline_item(f'第 {v} 行',pi,parent=parent,fit=Fit.xyz(left=0,top=H-max(0,y-14),zoom=Z()))
  except Exception:
   w.add_outline_item(f'第 {v} 行',pi,parent=parent)
  poem_bookmarks+=1

# PDF metadata and links inherited from the visually adjusted reference.
w.add_metadata({'/Title':'埃涅阿斯纪 · 第四版','/Author':'Novelist',
 '/Subject':'中文自由体诗译本与注释；含双向脚注导航及标记内容结构',
 '/Creator':'XeLaTeX, pypdf; accessibility and navigation edition',
 '/Keywords':'Aeneis; 中文译本; 第四版; Tagged PDF; 双向脚注; 数字阅读'})

# Machine-readable descriptive metadata, without claiming PDF/UA or PDF/A certification.
from xml.sax.saxutils import escape as xml_escape
xmp='''<?xpacket begin="\ufeff" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
<rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:pdf="http://ns.adobe.com/pdf/1.3/" xmlns:xmp="http://ns.adobe.com/xap/1.0/">
<dc:title><rdf:Alt><rdf:li xml:lang="x-default">埃涅阿斯纪 · 第四版</rdf:li><rdf:li xml:lang="zh-CN">埃涅阿斯纪 · 第四版</rdf:li></rdf:Alt></dc:title>
<dc:creator><rdf:Seq><rdf:li>Novelist</rdf:li></rdf:Seq></dc:creator>
<dc:language><rdf:Bag><rdf:li>zh-CN</rdf:li></rdf:Bag></dc:language>
<dc:description><rdf:Alt><rdf:li xml:lang="zh-CN">中文自由体诗译本与注释，含脚注往返链接与 PDF 结构标签</rdf:li></rdf:Alt></dc:description>
<pdf:Keywords>Aeneis; 中文译本; 维吉尔; 注释; 第四版</pdf:Keywords>
<pdf:Producer>XeLaTeX, pypdf</pdf:Producer>
</rdf:Description></rdf:RDF></x:xmpmeta>
<?xpacket end="w"?>'''
xmpobj=Stream();xmpobj.set_data(xmp.encode('utf-8'))
xmpobj[N('/Type')]=N('/Metadata');xmpobj[N('/Subtype')]=N('/XML')
w._root_object[N('/Metadata')]=w._add_object(xmpobj)
w._root_object[N('/ViewerPreferences')]=D({N('/DisplayDocTitle'):B(True)})

with OUT.open('wb') as f:w.write(f)
print('OUTPUT',OUT,OUT.stat().st_size,'TAGGED',count_mcid,'FIGURES',num_figures,'LINE_BOOKMARKS',poem_bookmarks,flush=True)
summary={'pages':len(doc),'backlinks':link_num,'forward_citations':len(forward),'embedded_font_fixed':font_fixed,
 'marked_content_sections':count_mcid, 'individual_note_nodes':len(note_elems),'figures_with_alt':num_figures,'tagged_link_annotations':linked_annotation_count,'glossary_crosslinks':glossary_link_count,'glossary_distinct_terms':len(glossary_targets),'verse_bookmarks':poem_bookmarks,'file_size':OUT.stat().st_size,
 'figure_page_list':sorted(alt.keys())}
(BASE/'aeneis_pdf_repair/rebuild_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
