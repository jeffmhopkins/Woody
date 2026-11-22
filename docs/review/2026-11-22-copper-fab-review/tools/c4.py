from c1 import *
def parts(g): return list(g.geoms) if hasattr(g,'geoms') else ([g] if not g.is_empty else [])
def ang(a,b,c):
    v1=(a[0]-b[0],a[1]-b[1]); v2=(c[0]-b[0],c[1]-b[1])
    n1=math.hypot(*v1); n2=math.hypot(*v2)
    if n1<1e-6 or n2<1e-6: return None
    return math.degrees(math.acos(max(-1,min(1,(v1[0]*v2[0]+v1[1]*v2[1])/(n1*n2)))))
for b in BOARDS:
    G=L(b); print('=====',b)
    for layer in G['cu']:
        ts=[t for t in G['tracks'] if t['layer']==layer]
        if not ts: continue
        # acute junctions: endpoints coincident or endpoint on another segment
        res=[]
        for i,t in enumerate(ts):
            for u in ts[i+1:]:
                if t['net']!=u['net']: continue
                for pe,po in ((t['a'],t['b']),(t['b'],t['a'])):
                    for qe,qo in ((u['a'],u['b']),(u['b'],u['a'])):
                        if math.hypot(pe[0]-qe[0],pe[1]-qe[1])<1e-4:
                            a=ang(po,pe,qo)
                            if a is not None and a<89: res.append((round(a,1),t['net'],(round(pe[0],2),round(pe[1],2)),'end-end'))
                # T: endpoint of one on interior of other
                for (x,y,z) in ((t,u,0),(u,t,0)):
                    for pe,po in ((x['a'],x['b']),(x['b'],x['a'])):
                        ls=LineString([y['a'],y['b']])
                        if ls.length<1e-6: continue
                        if ls.distance(Point(pe))<1e-4 and min(math.hypot(pe[0]-y['a'][0],pe[1]-y['a'][1]),math.hypot(pe[0]-y['b'][0],pe[1]-y['b'][1]))>1e-3:
                            a1=ang(po,pe,y['a']); a2=ang(po,pe,y['b'])
                            a=min(a1,a2)
                            if a<89: res.append((round(a,1),t['net'],(round(pe[0],2),round(pe[1],2)),'T'))
        res=sorted(set(res)); print(' ',layer,'acute track junctions:',len(res),res[:12])
        # same-net narrow gaps (etch pockets) : closing of per-net copper
        it=copper_items(G,layer); bynet=collections.defaultdict(list)
        for g,n,lab in it:
            if n and not n.startswith('?'): bynet[n].append(g)
        gaps=[]
        for n,gs in bynet.items():
            u=unary_union(gs)
            for w in (0.2,):
                cl=u.buffer(w/2,8).buffer(-w/2,8).difference(u.buffer(0.002))
                for q in parts(cl):
                    if q.area>0.004: gaps.append((round(q.area,3),n,(round(q.centroid.x,2),round(q.centroid.y,2))))
        gaps.sort(reverse=True); print('    same-net pockets narrower than 0.2:',len(gaps),gaps[:14])
        # dangling track ends: endpoint not on any other same-net copper
        tree_it=[(g,n,lab) for g,n,lab in it]
        dang=[]
        for t in ts:
            for pe in (t['a'],t['b']):
                P=Point(pe); ok=False
                for g,n,lab in tree_it:
                    if n==t['net'] and not lab.startswith('track %.2f (%.2f,%.2f)-(%.2f,%.2f)'%(t['w'],*t['a'],*t['b'])) and g.distance(P)<1e-3: ok=True;break
                if not ok:
                    # via/pad on other layers
                    if any(Point(v['p']).distance(P)<v['d']/2 for v in G['vias']): continue
                    dang.append((t['net'],(round(pe[0],2),round(pe[1],2))))
        print('    dangling ends:',len(dang),dang[:8])
