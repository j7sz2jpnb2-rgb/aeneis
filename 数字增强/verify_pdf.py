#!/usr/bin/env python3
"""Independent color, navigation, tag structure, font, text and visual regression QA; PDF only."""
from pathlib import Path
from collections import defaultdict,Counter
import fitz, re, json, subprocess, hashlib
from pypdf import PdfReader
from pypdf.generic import ContentStream
R=Path('/mnt/data/aeneis_pdf_repair')
corrected=R/'visual_color_fixed.pdf'
baseline=Path('/mnt/data/Aeneid-zh_ed4_2026-10-08_版本记对齐微调.pdf')
output=Path('/mnt/data/Aeneid-zh_ed4_2026-10-08_PDF修订校验版.pdf')
a=fitz.open(baseline);b=fitz.open(corrected);c=fitz.open(output)
r=PdfReader(output)
assert len(a)==len(b)==len(c)==len(r.pages)==338
forward={};backs={};gloss=0
for i,p in enumerate(c):
    for l in p.get_links():
        if re.fullmatch(r'Hfootnote\.\d+',l.get('nameddest','')):
            n=int(l['nameddest'].split('.')[-1]);assert n not in forward
            forward[n]=(i,l)
        if l['kind']==fitz.LINK_GOTO:backs.setdefault(i,[]).append(l)
assert set(forward)==set(range(1,535)),len(forward)

# Verify actual colored glyphs, not merely defined CSS or TeX colors.
all_note_marks={};colors=Counter();note_body_colors=Counter();bad_body=[];num_cross=0
for n,(src,l) in forward.items():
    pi=l['page'];num_cross+=(src!=pi)
    matches=[]
    for block in c[pi].get_text('dict')['blocks']:
        for line in block.get('lines',[]):
            for sp in line['spans']:
                if sp['text'].strip()==str(n) and 5<sp['size']<6.8 and sp['bbox'][0]<85:matches.append(sp)
    assert len(matches)==1,(n,pi,len(matches))
    sp=matches[0];all_note_marks[n]=(pi,sp['bbox']);colors[f'#{sp["color"]:06X}']+=1
assert colors=={'#596166':534},colors
# Complete note region: ignore decorative line rule, inspect every font-sized note glyph.
first_on_page=defaultdict(lambda:float('inf'))
for pi,rect in all_note_marks.values():first_on_page[pi]=min(first_on_page[pi],rect[1])
for pi,top in first_on_page.items():
    for block in c[pi].get_text('dict')['blocks']:
        for line in block.get('lines',[]):
            for sp in line['spans']:
                if sp['bbox'][1]>=top-1 and 5<sp['size']<9.6 and sp['bbox'][1]<c[pi].rect.height-28:
                    if sp['color']==0x697176 and sp['text'].strip().isdigit() and sp['bbox'][1]>c[pi].rect.height-55 and sp['size']<8.2:
                        continue  # printed page-number furniture, not a footnote
                    note_body_colors[f'#{sp["color"]:06X}']+=1
                    if sp['color']!=0x596166:bad_body.append((pi+1,sp['text'][:20],hex(sp['color'])))
assert not bad_body,bad_body[:50]

# Check every annotation-to-destination pair in both directions and presence of /StructParent.
back_annot_count=0; forwards_struct=[]; glossary_count=0; link_count=0; missing_struct=[]
for pi,page in enumerate(r.pages):
    for anref in page.get('/Annots',[]):
        an=anref.get_object()
        if an.get('/Subtype')!='/Link':continue
        link_count+=1
        if '/StructParent' not in an:missing_struct.append((pi,'link'))
        if str(an.get('/Contents','')).startswith('返回正文中脚注 '):
            n=int(str(an['/Contents']).split('脚注 ')[1].split(' ')[0])
            assert n in forward
            d=an.get('/A').get('/D')
            assert d is not None and str(an['/A']['/S'])=='/GoTo'
            assert d[0].idnum==r.pages[forward[n][0]].indirect_reference.idnum,(n,pi,d[0].idnum,r.pages[forward[n][0]].indirect_reference.idnum)
            back_annot_count+=1
        if str(an.get('/Contents','')).startswith('跳转到脚注 '):forwards_struct.append(pi)
        if str(an.get('/Contents','')).endswith('：前往专名与术语表对应条目'):glossary_count+=1
assert back_annot_count==534 and len(forwards_struct)==534
assert link_count==1275 and glossary_count==173,(link_count,glossary_count)
assert not missing_struct

# Full structural references, including exactly 534 distinct /Note nodes.
st=r.trailer['/Root']['/StructTreeRoot'].get_object();parents=st['/ParentTree'].get_object()['/Nums']
assert len(parents)%2==0
keys=[int(parents[k]) for k in range(0,len(parents),2)]
assert keys==list(range(len(keys)))
rolecounts=Counter();note_titles=[];figure_alts=[];duplicate_mcid=[];link_kids=0
seen=set()
def walk(ind):
    global link_kids
    node=ind.get_object()
    assert str(node.get('/Type'))=='/StructElem'
    key=(ind.idnum,ind.generation)
    assert key not in seen,('duplicate struct node',key)
    seen.add(key)
    role=str(node['/S']);rolecounts[role]+=1
    if role=='/Note':note_titles.append(str(node.get('/T','')))
    if role=='/Figure':figure_alts.append(str(node.get('/Alt','')))
    if role=='/Link':link_kids+=1
    for child in node.get('/K',[]):
        if hasattr(child,'get_object') and isinstance(child.get_object(),dict) and str(child.get_object().get('/Type'))=='/StructElem':walk(child)
for ch in st['/K']:walk(ch)
assert len(note_titles)==534 and len(set(note_titles))==534,Counter(note_titles).most_common(4)
assert {f'脚注 {i}' for i in range(1,535)}==set(note_titles)
assert len(figure_alts)==17 and all(figure_alts)
assert link_kids==link_count
assert rolecounts['/P']>10000 and rolecounts['/H1']>=12
for pi,p in enumerate(r.pages):
    assert '/StructParents' in p and int(p['/StructParents'])==pi
    parentarr=parents[pi*2+1].get_object()
    ops=ContentStream(p.get_contents(),r).operations
    idlist=[]
    for args,op in ops:
        if op==b'BDC' and args and len(args)>1 and '/MCID' in args[1]:idlist.append(int(args[1]['/MCID']))
    assert sorted(idlist)==list(range(len(idlist))) and len(idlist)==len(parentarr),(pi,len(idlist),len(parentarr))
    for item in parentarr:
        assert item.get_object().get('/Type')=='/StructElem'

# Exact textual integrity, including the repaired original colophon.
textdiff=[i+1 for i in range(338) if a[i].get_text()!=c[i].get_text()]
assert not textdiff,textdiff
# Render consistency: the accessibility layer must be invisible at every page.
renderdiff=[];original_visual_changes=[]
for i in range(338):
    after=c[i].get_pixmap(matrix=fitz.Matrix(.56,.56),alpha=False)
    fixed=b[i].get_pixmap(matrix=fitz.Matrix(.56,.56),alpha=False)
    orig=a[i].get_pixmap(matrix=fitz.Matrix(.56,.56),alpha=False)
    if after.samples!=fixed.samples:renderdiff.append(i+1)
    if after.samples!=orig.samples:original_visual_changes.append(i+1)
    if i%60==0:print('RENDER_PROGRESS',i+1,flush=True)
assert not renderdiff,renderdiff
assert len(original_visual_changes)==22,(len(original_visual_changes),original_visual_changes)

# All font instances embedded and relevant map glyphs Unicode-mappable.
f=subprocess.run(['pdffonts',str(output)],text=True,capture_output=True,check=True)
font_rows=f.stdout.splitlines()[2:]
unembedded=[];badunicode=[]
for line in font_rows:
    terms=line.split()
    if len(terms)<6:continue
    # last columns: emb sub uni object ID gen
    if terms[-5]=='no':unembedded.append(line)
    if 'LiberationSans' in terms[0] and terms[-3]=='no':badunicode.append(line)
assert not unembedded and not badunicode,(unembedded[:5],badunicode[:5])
info=subprocess.run(['pdfinfo',str(output)],text=True,capture_output=True,check=True)
assert 'Tagged:          yes' in info.stdout
assert output.stat().st_size<50_000_000
assert len(c.get_toc())==168

result={'pages':338,'size_bytes':output.stat().st_size,
 'footnotes':534,'cross_page_footnotes':num_cross,'note_marker_colors':dict(colors),
 'note_body_span_colors':dict(note_body_colors),'color_errors':len(bad_body),
 'forward_links':len(forward),'reverse_links':back_annot_count,
 'glossary_links':glossary_count,'all_structured_link_annotations':link_count,
 'individual_note_nodes':len(note_titles),'figure_alt_nodes':len(figure_alts),
 'structure_roles':dict(rolecounts),'reader_bookmarks':len(c.get_toc()),
 'all_pages_identical_text':len(textdiff)==0,'render_identical_to_color_fixed_pages':338,
 'visually_changed_pages_vs_original':original_visual_changes,'fonts_unembedded':len(unembedded),
 'map_liberation_font_unicode_mappings_present':not badunicode,
 'tagged_pdf':'True','pdf_ua_independently_validated':False,
 'assistive_technology_manual_testing':'NOT DONE',
 'pdf_a':'NOT ASSESSED','full_resolution_human_proofreading':'NOT DONE'}
(R/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
for k,v in result.items():print('QA',k,v,flush=True)
