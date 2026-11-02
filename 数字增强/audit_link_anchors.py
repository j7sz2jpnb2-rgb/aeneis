from pypdf import PdfReader
from pypdf.generic import ContentStream
from collections import defaultdict,Counter
import math,re,statistics,json
pdf='/mnt/data/Aeneid-zh_ed4_2026-10-08_PDF修订校验版.pdf'
r=PdfReader(pdf)
st=r.trailer['/Root']['/StructTreeRoot'].get_object(); nums=st['/ParentTree'].get_object()['/Nums']
H=float(r.pages[0].mediabox.height)
def mul(m,n):
 a,b,c,d,e,f=m; A,B,C,D,E,F=n
 return(a*A+c*B,b*A+d*B,a*C+c*D,b*C+d*D,a*E+c*F+e,b*E+d*F+f)
samples=[];bad=[];bytype=Counter()
for pi,p in enumerate(r.pages):
 ops=ContentStream(p.get_contents(),r).operations
 state=(1.,0.,0.,1.,0.,0.);stack=[];cur=None;recs={}
 for ii,(args,op) in enumerate(ops):
  if op==b'q':stack.append(state)
  if op==b'Q' and stack:state=stack.pop()
  if op==b'cm' and len(args)==6:state=mul(state,tuple(map(float,args)))
  if op==b'BDC' and len(args)>1 and '/MCID' in args[1]:cur=int(args[1]['/MCID'])
  if op==b'EMC':cur=None
  if op==b'BT' and cur is not None:
   base=None;fz=0
   for sub,o in ops[ii+1:]:
    if o==b'Tf':fz=float(sub[1])
    if o in (b'Td',b'Tm') and base is None:base=(float(sub[0]),float(sub[1])) if o==b'Td' else (float(sub[4]),float(sub[5]))
    if o==b'ET':break
   if base:
    x=state[0]*base[0]+state[2]*base[1]+state[4]
    y=H-(state[1]*base[0]+state[3]*base[1]+state[5])
    recs[cur]=(x,y,fz)
 for ar in p.get('/Annots',[]):
  obj=ar.get_object()
  if obj.get('/Subtype')!='/Link':continue
  txt=str(obj.get('/Contents',''))
  kind='forward' if txt.startswith('跳转到脚注 ') else 'back' if txt.startswith('返回正文中脚注 ') else 'other'
  if kind=='other':continue
  structkey=int(obj['/StructParent']);link=nums[2*structkey+1].get_object()
  kids=link['/K']
  idkids=[int(k) for k in kids if isinstance(k,int)]
  if len(idkids)!=1:bad.append((kind,pi,'no single glyph MCID',idkids));continue
  mcid=idkids[0]
  if mcid not in recs:bad.append((kind,pi,'no BT record',mcid));continue
  x,y,fz=recs[mcid]
  ax0,ay0,ax1,ay1=map(float,obj['/Rect']);cx=(ax0+ax1)/2;cy=H-(ay0+ay1)/2
  dx=x-cx;dy=y-cy
  bytype[kind]+=1
  samples.append((abs(dx),abs(dy),kind,pi+1,txt,round(fz,2)))
  if abs(dx)>22 or abs(dy)>9:bad.append((kind,pi+1,txt,round(dx,2),round(dy,2),fz))
  if kind=='back':
   par=link['/P'].get_object();note=par['/P'].get_object()
   n=int(re.search('脚注 (\\d+)',txt).group(1))
   if note['/S']!='/Note' or note['/T']!=f'脚注 {n}':bad.append(('wrong note parent',pi,n,str(note.get('/T'))))
  else:
   ref=link.get('/Ref')
   n=int(re.search('脚注 (\\d+)',txt).group(1))
   if not ref or len(ref)!=1 or ref[0].get_object().get('/T')!=f'脚注 {n}':bad.append(('wrong note ref',pi,n))
print('TYPES',bytype)
print('MAX_DEVIATIONS',sorted(samples,reverse=True)[:12])
print('BAD',len(bad),bad[:30])
assert bytype=={'forward':534,'back':534},bytype
assert not bad,bad[:15]
