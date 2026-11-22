import pickle,sys,collections,math,itertools
from shapely.geometry import Point,LineString,Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree
sys.path.insert(0,'/tmp/copper-fab-review'); from geo import BOARDS
def L(b): return pickle.load(open(f'/tmp/copper-fab-review/{b}.pkl','rb'))
def copper_items(G,layer):
    """every copper feature on a layer: (geom, net, label)"""
    it=[]
    for t in G['tracks']:
        if t['layer']==layer: it.append((t['poly'],t['net'],'track %.2f (%.2f,%.2f)-(%.2f,%.2f)'%(t['w'],*t['a'],*t['b'])))
    for v in G['vias']: it.append((Point(v['p']).buffer(v['d']/2,32),v['net'],'via (%.2f,%.2f)'%v['p']))
    for p in G['pads']:
        if layer in p['cu'] and not p['cu'][layer].is_empty: it.append((p['cu'][layer],p['net'],'pad %s.%s'%(p['ref'],p['num'])))
    for z in G['zones']:
        if not z['rule'] and z['layer']==layer and not z['poly'].is_empty: it.append((z['poly'],z['net'],'zone '+z['net']))
    for s in G['silk']:
        if s['layer']==layer and not s['poly'].is_empty: it.append((s['poly'],'?gfx','gfx '+s['owner']))
    for s in G['texts']:
        if s['layer']==layer and not s['poly'].is_empty: it.append((s['poly'],'?txt','cutext '+s['owner']))
    return it
def holes(G):
    h=[]
    for v in G['vias']: h.append((Point(v['p']).buffer(v['drill']/2,32),v['net'],'viahole (%.2f,%.2f)'%v['p'],'via',v['drill']))
    for p in G['pads']:
        dx,dy=p['drill']
        if dx>0:
            if abs(dx-dy)<1e-6: g=Point(p['pos']).buffer(dx/2,32)
            else:
                # slot: orientation from pad copper bbox
                any_cu=next(iter(p['cu'].values()),None)
                horiz = dx>dy
                # pad rotation unknown here; use copper bounds aspect to decide
                if any_cu is not None and not any_cu.is_empty:
                    bx=any_cu.bounds; cw,ch=bx[2]-bx[0],bx[3]-bx[1]
                    if (cw>ch)!=(dx>dy): horiz=not horiz
                r=min(dx,dy)/2; l=(max(dx,dy)-min(dx,dy))/2
                x,y=p['pos']
                g=(LineString([(x-l,y),(x+l,y)]) if horiz else LineString([(x,y-l),(x,y+l)])).buffer(r,32)
            h.append((g,p['net'],'hole %s.%s'%(p['ref'],p['num']),'npth' if p['attr']==3 else 'pth',(dx,dy)))
    return h
if __name__=='__main__':
  for b in BOARDS:
    G=L(b); print('=====',b,G['cu'])
    print(' track widths',sorted(collections.Counter(round(t['w'],3) for t in G['tracks']).items()),'arcs',sum(t['arc'] for t in G['tracks']))
    print(' vias',collections.Counter((round(v['d'],2),round(v['drill'],2),v['tentF'],v['tentB']) for v in G['vias']))
    hs=holes(G)
    print(' holes',sorted(collections.Counter((h[3],tuple(round(x,2) for x in h[4]) if isinstance(h[4],tuple) else round(h[4],2)) for h in hs).items(),key=str))
    # annular rings for PTH pads
    rings=collections.Counter()
    for p in G['pads']:
        if p['drill'][0]>0 and p['attr']!=3:
            hole=[h for h in hs if h[2]=='hole %s.%s'%(p['ref'],p['num'])][0][0]
            for ly,g in p['cu'].items():
                r=g.exterior.distance(hole) if g.geom_type=='Polygon' else None
                rings[(p['fpname'],ly,round(r,3) if r is not None else None)]+=1
    print(' PTH rings',sorted(rings.items(),key=lambda x:x[0][2] or 0)[:14])
    # clearances
    for layer in G['cu']:
        it=copper_items(G,layer); geoms=[i[0] for i in it]; tree=STRtree(geoms)
        res=[]
        for i,(g,n,lab) in enumerate(it):
            for j in tree.query(g.buffer(0.26)):
                if j<=i: continue
                g2,n2,lab2=it[j]
                if n==n2 and n!='' : continue
                d=g.distance(g2)
                if d<0.25: res.append((round(d,4),lab,n,lab2,n2))
        res.sort()
        print(' ',layer,'items',len(it),'pairs<0.25:',len(res),'min',res[:6])
        hist=collections.Counter(round(r[0],2) for r in res); print('    hist',sorted(hist.items()))
        # edge clearance
        edge=G['outline'].boundary
        er=sorted((round(g.distance(edge),3),lab,n) for g,n,lab in it if g.distance(edge)<0.5)
        print('    edge<0.5:',len(er),er[:8])
        # hole to copper other net
        hr=[]
        for hg,hn,hl,hk,hd in hs:
            for j in tree.query(hg.buffer(0.5)):
                g2,n2,lab2=it[j]
                if lab2.split(' ',1)[1]==hl.split(' ',1)[1]: continue
                if hk!='npth' and n2==hn and n2!='': continue
                d=hg.distance(g2)
                lim={'via':0.2,'pth':0.35,'npth':0.2}[hk]
                if d<lim+0.1: hr.append((round(d,3),hk,hl,lab2,n2))
        hr.sort(); print('    hole-to-copper near limit:',len(hr),hr[:10])
    # hole to hole
    hh=[]
    tree=STRtree([h[0] for h in hs])
    for i,h in enumerate(hs):
        for j in tree.query(h[0].buffer(0.6)):
            if j<=i: continue
            d=h[0].distance(hs[j][0])
            if d<0.5: hh.append((round(d,3),h[2],hs[j][2]))
    hh.sort(); print(' hole-hole<0.5',len(hh),hh[:8])
    edge=G['outline'].boundary
    he=sorted((round(h[0].distance(edge),3),h[2],h[3]) for h in hs if h[0].distance(edge)<1.0)
    print(' hole-edge<1.0',he[:10])
