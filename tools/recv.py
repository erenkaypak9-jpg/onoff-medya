import json,re,glob,base64,sys,os
import time
MINT=time.time()-float(sys.argv[3]) if len(sys.argv)>3 else 0
def texts():
    for f in glob.glob('/tmp/claude-tool-results/b0318284-9775-5329-8424-856f2addfd15/*.txt'):
        if os.path.getmtime(f)<MINT: continue
        s=open(f).read()
        try:
            o,_=json.JSONDecoder().raw_decode(s); t=o[0]['text']
            if t.startswith('"'): t,_=json.JSONDecoder().raw_decode(t)
            yield os.path.getmtime(f),t
        except Exception: pass
SLN=int(sys.argv[2]) if len(sys.argv)>2 else 240000
sl={}
for mt,t in texts():
    for m in re.finditer(r'SL\[(\d+)\]',t):
        body=t[m.end():m.end()+SLN]
        k=body.rfind('/SL')
        if len(body)<SLN: body=body[:k]
        j=body.find('/SL---')
        if j>=0: body=body[:j]
        i=int(m.group(1))
        if i not in sl or mt>sl[i][0]: sl[i]=(mt,body)
# keep only the newest batch per index
allt=''.join(sl[i][1] for i in sorted(sl))
out=sys.argv[1]; os.makedirs(out,exist_ok=True); n=0
for m in re.finditer(r'CH\[(\w+),0\]([A-Za-z0-9+/=]+?)/CH(?:\n|$)',allt):
    open(f"{out}/{m.group(1)}.jpg",'wb').write(base64.b64decode(m.group(2))); n+=1
print('files',n,'slices',sorted(sl))
