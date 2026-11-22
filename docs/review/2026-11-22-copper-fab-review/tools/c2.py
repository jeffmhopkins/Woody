from c1 import *
for b in BOARDS:
    G=L(b); print('=====',b)
    hs=holes(G)
    for side,sl in (('F','F.Silkscreen'),('B','B.Silkscreen')):
        ops=[(p['mask'][side],p['net'],'%s.%s'%(p['ref'],p['num']),p) for p in G['pads'] if side in p['mask'] and not p['mask'][side].is_empty]
        # board-level mask graphics
        for s in G['silk']:
            if s['layer']==side+'.Mask': ops.append((s['poly'],'?','gfx '+s['owner'],None))
        tree=STRtree([o[0] for o in ops]); res=[]
        for i,o in enumerate(ops):
            for j in tree.query(o[0].buffer(0.3)):
                if j<=i: continue
                d=o[0].distance(ops[j][0])
                if 0<d<0.25: res.append((round(d,3),o[2],ops[j][2],o[1]==ops[j][1]))
        res.sort()
        print(' mask',side,'openings',len(ops),'webs<0.25:',len(res),collections.Counter(r[0] for r in res).most_common(8),res[:6])
        # mask opening vs foreign copper on that side
        layer=side+'.Cu'; it=copper_items(G,layer); ct=STRtree([i[0] for i in it]); ex=[]
        for o in ops:
            for j in ct.query(o[0].buffer(0.15)):
                g,n,lab=it[j]
                if lab=='pad '+o[2]: continue
                d=o[0].distance(g)
                if d<0.09 and n!=o[1]: ex.append((round(d,3),o[2],o[1],lab,n))
        ex.sort(); print('   foreign copper within 0.09 of opening:',len(ex),ex[:8])
        # same-net copper exposed? via inside opening
        vi=[(o[2],'via (%.2f,%.2f)'%v['p'],round(o[0].distance(Point(v['p']).buffer(v['d']/2)),3)) for o in ops for v in G['vias'] if o[0].distance(Point(v['p']))<1.0]
        vi=[x for x in vi if x[2]<0.2]; print('   vias within 0.2 of a mask opening:',len(vi),sorted(vi,key=lambda x:x[2])[:8])
        # silk
        sk=[(s['poly'],s) for s in G['silk'] if s['layer']==sl and not s['poly'].is_empty]
        tx=[(s['poly'],s) for s in G['texts'] if s['layer']==sl and not s['poly'].is_empty]
        print(' silk',side,'gfx',len(sk),'texts',len(tx),'line widths',sorted(collections.Counter(round(s['w'],2) for _,s in sk if s['w'] is not None).items()),
              'text h/th',sorted(collections.Counter((round(s['h'],2),round(s['w'],2),round(s['th'],2)) for _,s in tx).items()))
        allmask=unary_union([o[0] for o in ops]) if ops else Polygon()
        allholes=unary_union([h[0] for h in hs])
        near=[];over=[];hole=[];out=[]
        inside=G['outline']
        for g,s in sk+tx:
            lab=(s.get('text') or s['cls'])+'@'+s['owner']
            d=g.distance(allmask)
            if g.intersects(allmask): over.append((round(g.intersection(allmask).area,3),lab,[round(v,1) for v in g.bounds[:2]]))
            elif d<0.15: near.append((round(d,3),lab,[round(v,1) for v in g.bounds[:2]]))
            if g.intersects(allholes): hole.append((lab,[round(v,1) for v in g.bounds[:2]]))
            if not inside.buffer(-0.2).contains(g): out.append((lab,[round(v,1) for v in g.bounds[:2]]))
        print('   silk overlapping mask openings:',len(over),sorted(over,reverse=True)[:10])
        print('   silk within 0.15 of opening:',len(near),sorted(near)[:10])
        print('   silk over drilled holes:',len(hole),hole[:10])
        print('   silk within 0.2 of edge/outside:',len(out),out[:10])
