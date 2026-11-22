from c1 import *
import re
for b in BOARDS:
    G=L(b); print('=====',b)
    fps=collections.defaultdict(list)
    for p in G['pads']: fps[p['ref']].append(p)
    print(' footprints',sorted(collections.Counter(v[0]['fpname'] for v in fps.values()).items()))
    rows=[]
    for ref,pads in fps.items():
        if len(pads)!=2 or any(p['drill'][0]>0 for p in pads): continue
        m=re.search(r'_(0402|0603|0805|1206|1210)_',pads[0]['fpname'])
        if not m: continue
        info=[]
        for p in pads:
            ly=next(iter(p['cu'])); pg=p['cu'][ly]
            ws=[]
            for t in G['tracks']:
                if t['layer']==ly and t['net']==p['net'] and t['poly'].intersects(pg):
                    # count only tracks that leave the pad
                    if not pg.buffer(0.01).contains(t['poly']): ws.append(t['w'])
            nv=sum(1 for v in G['vias'] if v['net']==p['net'] and pg.distance(Point(v['p']))<v['d']/2+0.3)
            zs=sum(1 for z in G['zones'] if not z['rule'] and z['layer']==ly and z['net']==p['net'] and z['poly'].intersects(pg.buffer(0.05)))
            info.append((p['num'],p['net'],sorted(ws),nv,zs))
        s=[sum(i[2])+0.7*i[3]*0 for i in info]
        rows.append((m.group(1),ref,info,s))
    c=collections.Counter(r[0] for r in rows); print(' 2-pad chips',dict(c))
    bad=[]
    for size,ref,info,s in rows:
        lo,hi=min(s),max(s)
        nearvia=[i[3] for i in info]
        if lo==0 or hi/lo>=2.0 or (nearvia[0]>0)!=(nearvia[1]>0) and False:
            bad.append((round(hi/lo,1) if lo else 99,size,ref,[(i[0],i[1].split('/')[-1],i[2],'v%d'%i[3]) for i in info]))
    bad.sort(reverse=True)
    print(' copper imbalance >=2x (sum of track widths leaving each pad):',len(bad))
    for r in bad: print('   ',r)
