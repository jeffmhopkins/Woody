from c1 import *
def parts(g): return list(g.geoms) if hasattr(g,'geoms') else ([g] if not g.is_empty else [])
for b in BOARDS:
    G=L(b); print('=====',b)
    hs=holes(G)
    # (a) vias near SMD pads: mask dam between pad opening and via HOLE
    res=[]
    for p in G['pads']:
        for side in p['mask']:
            if p['drill'][0]>0: continue
            for v in G['vias']:
                d=p['mask'][side].distance(Point(v['p']))-v['drill']/2
                if d<0.45: res.append((round(d,3),p['ref']+'.'+p['num'],p['net'],v['net'],'(%.2f,%.2f)'%v['p'],side))
    res.sort(); print(' via hole to SMD mask opening <0.45:',len(res),collections.Counter(round(r[0],2) for r in res).most_common(12)); print('   ',res[:12])
    print('    diff-net:',[r for r in res if r[2]!=r[3]][:5])
    # (b) zone-to-pad connections
    for z in G['zones']:
        if z['rule']: continue
        print(' zone',z['net'],z['layer'],'clr',z['clearance'],'minw',z['minw'],'conn',z['conn'],'tgap',z['tgap'],'spoke',z['tspoke'],'parts',len(parts(z['poly'])),'areas',sorted([round(q.area,1) for q in parts(z['poly'])],reverse=True)[:6])
        st=collections.Counter(); det=[]
        for p in G['pads']:
            if p['net']!=z['net'] or z['layer'] not in p['cu']: continue
            pg=p['cu'][z['layer']]
            ring=pg.buffer(0.08).difference(pg.buffer(0.01))
            cov=ring.intersection(z['poly']).area/ring.area
            band=pg.buffer(z['tgap']*0.5 if z['tgap'] else 0.1).exterior
            sp=band.intersection(z['poly'])
            n=len(parts(sp)) if not sp.is_empty else 0
            kind='solid' if cov>0.9 else ('none' if n==0 else f'{n} spokes')
            typ='TH' if p['drill'][0]>0 else 'SMD'
            st[(typ,kind)]+=1
            if kind!='solid' and n<2 or kind=='solid': det.append((p['ref']+'.'+p['num'],typ,kind,round(cov,2)))
        print('   pad connections',dict(st)); print('   notable',det[:40])
        # vias on net: connection kind
        vs=collections.Counter()
        for v in G['vias']:
            if v['net']==z['net']:
                c=Point(v['p']).buffer(v['d']/2+0.05).exterior
                vs['solid' if z['poly'].contains(c) else ('none' if not z['poly'].intersects(c) else 'partial')]+=1
        print('   vias',dict(vs))
        # (c) necks / slivers
        for w in (0.2,0.3,0.5):
            op=z['poly'].buffer(-w/2).buffer(w/2+0.001)
            lost=z['poly'].difference(op)
            big=[q for q in parts(lost) if q.area>0.02]
            print(f'   open by {w}: components {len(parts(z["poly"]))}->{len([q for q in parts(op) if q.area>0.05])}, thin bits(area>0.02): {len(big)}', [ (round(q.centroid.x,1),round(q.centroid.y,1),round(q.area,2)) for q in sorted(big,key=lambda q:-q.area)[:8]])
