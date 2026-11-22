import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from c1 import *
COL={'F.Cu':'#c83232','In1.Cu':'#3a9a3a','In2.Cu':'#c8a020','B.Cu':'#3250c8'}
def patch(ax,g,**kw):
    if g.is_empty: return
    gs=list(g.geoms) if hasattr(g,'geoms') else [g]
    for p in gs:
        if p.geom_type!='Polygon': continue
        verts=list(p.exterior.coords); codes=[Path.MOVETO]+[Path.LINETO]*(len(verts)-2)+[Path.CLOSEPOLY]
        for r in p.interiors:
            v=list(r.coords); verts+=v; codes+=[Path.MOVETO]+[Path.LINETO]*(len(v)-2)+[Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(verts,codes),**kw))
def render(G,box,layers,fn,title='',marks=(),mask=None,silk=None,labels=True,scale=None,notes=()):
    x0,y0,x1,y1=box; w=x1-x0; h=y1-y0
    s=scale or min(60,16/max(w,h)*2.2)
    fig,ax=plt.subplots(figsize=(max(6,w*s/2.54*0.4),max(4,h*s/2.54*0.4)),dpi=200)
    from shapely.geometry import box as sbox
    bx=sbox(*box)
    patch(ax,G['outline'],fc='#f4f1e8',ec='k',lw=1.2,zorder=0)
    for i,ly in enumerate(layers):
        for g,n,lab in copper_items(G,ly):
            if not g.intersects(bx): continue
            z=lab.startswith('zone')
            patch(ax,g,fc=COL[ly],ec='none',alpha=0.28 if z else 0.75,zorder=1+i+(0 if z else 5))
    if mask:
        for p in G['pads']:
            if mask in p['mask'] and p['mask'][mask].intersects(bx): patch(ax,p['mask'][mask],fc='none',ec='#00a0a0',lw=0.8,zorder=20)
    if silk:
        for s in G['silk']+G['texts']:
            if s['layer']==silk and s['poly'].intersects(bx): patch(ax,s['poly'],fc='k',ec='none',alpha=.8,zorder=21)
    for hg,hn,hl,hk,hd in holes(G):
        if hg.intersects(bx): patch(ax,hg,fc='white' if hk!='npth' else '#bbbbbb',ec='k',lw=0.5,zorder=30)
    if labels:
        seen=set()
        for p in G['pads']:
            if bx.contains(Point(p['pos'])) and any(l in p['cu'] for l in layers):
                ax.text(p['pos'][0],p['pos'][1],p['num'],fontsize=4,ha='center',va='center',zorder=40,color='k')
                if p['ref'] not in seen:
                    seen.add(p['ref'])
        refs=collections.defaultdict(list)
        for p in G['pads']:
            if any(l in p['cu'] for l in layers): refs[p['ref']].append(p['pos'])
        for r,ps in refs.items():
            cx=sum(a for a,_ in ps)/len(ps); cy=sum(b for _,b in ps)/len(ps)
            if bx.contains(Point(cx,cy)): ax.text(cx,cy-0.0,r,fontsize=6,ha='center',va='bottom',zorder=41,color='#101010',weight='bold',bbox=dict(fc='white',ec='none',alpha=.6,pad=0.5))
    for m in marks:
        x,y,r=m[:3]; ax.add_patch(plt.Circle((x,y),r,fc='none',ec='#ff00ff',lw=1.8,zorder=50))
        if len(m)>3: ax.text(x,y-r-0.05*h*0.2,m[3],fontsize=7,color='#b000b0',ha='center',va='bottom',zorder=51,weight='bold',bbox=dict(fc='white',ec='none',alpha=.8,pad=0.6))
    ax.set_xlim(x0,x1); ax.set_ylim(y1,y0); ax.set_aspect('equal'); ax.set_title(title,fontsize=9)
    ax.tick_params(labelsize=6)
    hnd=[plt.Rectangle((0,0),1,1,fc=COL[l],alpha=.75) for l in layers]
    ax.legend(hnd,layers,fontsize=6,loc='lower right',framealpha=.9)
    fig.tight_layout(); fig.savefig(fn); plt.close(fig)
if __name__=='__main__':
    for b in BOARDS:
        G=L(b); bb=G['outline'].bounds
        for ly in G['cu']:
            render(G,(bb[0]-1,bb[1]-1,bb[2]+1,bb[3]+1),[ly],f'/tmp/copper-fab-review/ov-{b}-{ly}.png',title=f'{b} {ly}',labels=ly in('F.Cu','B.Cu'),scale=60/max(bb[2]-bb[0],1)*1.0 if False else None)
