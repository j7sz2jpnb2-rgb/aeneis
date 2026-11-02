"""Synchronize current TeX from the current authoritative TXT, then validate."""
from pathlib import Path
import csv, json, subprocess, sys
from build_matrix import parse_full_text
from build_draft import verse_order, TEX_LINE_RE, poem_to_tex
ROOT=Path(__file__).resolve().parent
D=ROOT/'拼合工程_工作稿'
T=D/'正文与注释权威源/埃涅阿斯纪_最新全文_附注释_20261006.txt'
body,notes=parse_full_text(T);order=verse_order(T)
assert len(body)==9888 and sorted(notes)==list(range(1,535))
with (ROOT/'注释新旧编号.tsv').open(encoding='utf-8-sig',newline='') as f:
 for row in csv.DictReader(f,delimiter='\t'):
  old=row['旧注号或新注ID'];notes[int(row['新注号'])]['old_number']=int(old) if old.isdigit() else None
for book in range(1,13):
 p=D/f'制版源文件/content/book{book:02d}_current.tex';out=[];index=0
 for line in p.read_text(encoding='utf-8-sig').splitlines():
  m=TEX_LINE_RE.match(line)
  if m:
   key=order[book][index];index+=1
   line='\\verseline{'+m[1]+'}{'+poem_to_tex(body[key],notes)+'}'
  out.append(line)
 assert index==len(order[book])
 p.write_text('\n'.join(out)+'\n',encoding='utf-8')
p=D/'制版源文件/CONTENT_AUTHORITY.json';a=json.loads(p.read_text(encoding='utf-8'));a.update(notes=len(notes),per_book_notes={str(b):sum(x['book']==b for x in notes.values()) for b in range(1,13)});p.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
subprocess.run([sys.executable,str(ROOT/'validate_draft.py')],check=True)
