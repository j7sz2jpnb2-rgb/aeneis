#!/usr/bin/env python3
"""Construct approved 338-page visual PDF from repaired XeLaTeX build, preserving approved colophon."""
from pathlib import Path
import fitz
root=Path('/mnt/data/aeneis_pdf_repair')
compiled=root/'source/build/main.pdf'
colophon=Path('/mnt/data/版本记微调_工作文件/adjusted_colophon.pdf')
approved=fitz.open('/mnt/data/Aeneid-zh_ed4_2026-10-08_版本记对齐微调.pdf')
doc=fitz.open(compiled); leaf=fitz.open(colophon)
assert len(doc)==len(approved)==338 and len(leaf)==1
p=doc[-1]; original_rect=p.rect
xref=doc.get_new_xref();doc.update_object(xref,'<<>>');doc.update_stream(xref,b' ')
p.set_contents(xref)
p.show_pdf_page(original_rect,leaf,0,keep_proportion=False,overlay=True)
for link in approved[-1].get_links():
    assert link['kind']==fitz.LINK_URI
    p.insert_link({'kind':fitz.LINK_URI,'from':link['from'],'uri':link['uri']})
# page annotations are refreshed after serialization
out=root/'visual_color_fixed.pdf'
doc.save(out,garbage=4,deflate=True)
print('VISUAL_BASE',out,out.stat().st_size,'PAGES',len(doc))
