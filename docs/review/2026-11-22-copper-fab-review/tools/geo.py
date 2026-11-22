"""Extract a board's fabricated geometry into shapely, straight from the .kicad_pcb via pcbnew.
Independent of tools/pcb.py. Units mm, y as in the file."""
import pcbnew, sys, pickle
from shapely.geometry import Polygon, LineString, Point, MultiPolygon
from shapely.ops import unary_union
MM=1e-6
BOARDS=['main-board','key-board-lh','key-board-rh','matrix-carrier','umb-adapter']
def path(b): return f'/home/user/Woody/hardware/boards/{b}/{b}.kicad_pcb'
def sps(ps):
    """SHAPE_POLY_SET -> shapely geometry"""
    out=[]
    for i in range(ps.OutlineCount()):
        o=ps.Outline(i); ext=[(o.CPoint(k).x*MM,o.CPoint(k).y*MM) for k in range(o.PointCount())]
        holes=[]
        for h in range(ps.HoleCount(i)):
            ho=ps.Hole(i,h); holes.append([(ho.CPoint(k).x*MM,ho.CPoint(k).y*MM) for k in range(ho.PointCount())])
        if len(ext)>=3:
            p=Polygon(ext,holes)
            if not p.is_valid: p=p.buffer(0)
            out.append(p)
    return unary_union(out) if out else Polygon()
def load(b):
    bd=pcbnew.LoadBoard(path(b))
    G=dict(name=b,tracks=[],vias=[],pads=[],zones=[],silk=[],texts=[])
    cu=[l for l in bd.GetEnabledLayers().CuStack()]
    G['cu']=[bd.GetLayerName(l) for l in cu]
    ERR=2000
    for t in bd.GetTracks():
        if t.Type()==pcbnew.PCB_VIA_T:
            v=t
            G['vias'].append(dict(p=(v.GetPosition().x*MM,v.GetPosition().y*MM),d=v.GetWidth(pcbnew.F_Cu)*MM,drill=v.GetDrillValue()*MM,net=v.GetNetname(),
                tentF=v.IsTented(pcbnew.F_Mask),tentB=v.IsTented(pcbnew.B_Mask)))
        else:
            ps=pcbnew.SHAPE_POLY_SET(); t.TransformShapeToPolygon(ps,t.GetLayer(),0,ERR,pcbnew.ERROR_INSIDE)
            G['tracks'].append(dict(layer=bd.GetLayerName(t.GetLayer()),net=t.GetNetname(),a=(t.GetStart().x*MM,t.GetStart().y*MM),b=(t.GetEnd().x*MM,t.GetEnd().y*MM),w=t.GetWidth()*MM,arc=t.Type()==pcbnew.PCB_ARC_T,poly=sps(ps)))
    for fp in bd.GetFootprints():
        for pad in fp.Pads():
            d=dict(ref=fp.GetReference(),num=pad.GetNumber(),net=pad.GetNetname(),fpname=str(fp.GetFPID().GetLibItemName()),
                   attr=pad.GetAttribute(),pos=(pad.GetPosition().x*MM,pad.GetPosition().y*MM),
                   drill=(pad.GetDrillSize().x*MM,pad.GetDrillSize().y*MM),side='B' if fp.IsFlipped() else 'F',cu={},mask={},paste={},
                   zc={})
            for l in cu:
                if pad.IsOnLayer(l):
                    ps=pcbnew.SHAPE_POLY_SET(); pad.TransformShapeToPolygon(ps,l,0,ERR,pcbnew.ERROR_INSIDE)
                    d['cu'][bd.GetLayerName(l)]=sps(ps)
            for ml,cl,key in ((pcbnew.F_Mask,pcbnew.F_Cu,'F'),(pcbnew.B_Mask,pcbnew.B_Cu,'B')):
                if pad.IsOnLayer(ml):
                    ps=pcbnew.SHAPE_POLY_SET(); pad.TransformShapeToPolygon(ps,ml,0,ERR,pcbnew.ERROR_INSIDE)
                    g=sps(ps)
                    if g.is_empty:
                        ps=pcbnew.SHAPE_POLY_SET(); pad.TransformShapeToPolygon(ps,cl,pad.GetSolderMaskExpansion(ml),ERR,pcbnew.ERROR_INSIDE); g=sps(ps)
                    d['mask'][key]=g; d['maskexp']=pad.GetSolderMaskExpansion(ml)*MM
            for pl,key in ((pcbnew.F_Paste,'F'),(pcbnew.B_Paste,'B')):
                if pad.IsOnLayer(pl): d['paste'][key]=True
            G['pads'].append(d)
        for it in list(fp.GraphicalItems())+list(fp.GetFields()):
            add_gfx(bd,G,it,fp.GetReference())
    for it in bd.GetDrawings(): add_gfx(bd,G,it,'board')
    for z in bd.Zones():
        if z.GetIsRuleArea():
            G['zones'].append(dict(rule=True,name=z.GetZoneName(),layers=[bd.GetLayerName(l) for l in z.GetLayerSet().Seq()],outline=sps(z.Outline()))); continue
        for l in z.GetLayerSet().Seq():
            G['zones'].append(dict(rule=False,net=z.GetNetname(),layer=bd.GetLayerName(l),poly=sps(z.GetFilledPolysList(l)),outline=sps(z.Outline()),
                clearance=z.GetLocalClearance().value()*MM if hasattr(z.GetLocalClearance(),'value') else z.GetLocalClearance(),minw=z.GetMinThickness()*MM,
                conn=z.GetPadConnection(),tgap=z.GetThermalReliefGap()*MM,tspoke=z.GetThermalReliefSpokeWidth()*MM,prio=z.GetAssignedPriority(),
                island=z.GetIslandRemovalMode(),filled=z.IsFilled()))
    ps=pcbnew.SHAPE_POLY_SET(); ok=bd.GetBoardPolygonOutlines(ps)
    G['outline']=sps(ps); G['outline_ok']=ok
    ds=bd.GetDesignSettings()
    G['mask_exp']=ds.m_SolderMaskExpansion*MM; G['mask_minw']=ds.m_SolderMaskMinWidth*MM
    try: G['tent']=(ds.m_TentViasFront,ds.m_TentViasBack)
    except Exception as e: G['tent']=str(e)
    G['thick']=ds.GetBoardThickness()*MM
    return G
def add_gfx(bd,G,it,owner):
    l=it.GetLayer(); ln=bd.GetLayerName(l)
    if ln not in ('F.Silkscreen','B.Silkscreen','F.SilkS','B.SilkS','F.Cu','B.Cu','In1.Cu','In2.Cu','Edge.Cuts','F.Mask','B.Mask','F.Paste','B.Paste'): return
    cls=it.GetClass()
    if cls in ('PCB_TEXT','PCB_FIELD','PCB_TEXTBOX'):
        if hasattr(it,'IsVisible') and not it.IsVisible(): return
        ps=pcbnew.SHAPE_POLY_SET()
        try: it.TransformTextToPolySet(ps,0,2000,pcbnew.ERROR_INSIDE)
        except Exception as e: return
        G['texts'].append(dict(owner=owner,layer=ln,text=it.GetText() if cls!='PCB_FIELD' else it.GetShownText(False),h=it.GetTextHeight()*MM,w=it.GetTextWidth()*MM,th=it.GetTextThickness()*MM,poly=sps(ps),knock=it.IsKnockout() if hasattr(it,'IsKnockout') else False))
    else:
        ps=pcbnew.SHAPE_POLY_SET()
        try: it.TransformShapeToPolygon(ps,l,0,2000,pcbnew.ERROR_INSIDE)
        except Exception as e: return
        w=it.GetWidth()*MM if hasattr(it,'GetWidth') else None
        G['silk'].append(dict(owner=owner,layer=ln,w=w,poly=sps(ps),cls=cls,filled=it.IsFilled() if hasattr(it,'IsFilled') else None))
if __name__=='__main__':
    for b in BOARDS:
        G=load(b); pickle.dump(G,open(f'/tmp/copper-fab-review/{b}.pkl','wb'))
        print(b,G['cu'],'tracks',len(G['tracks']),'vias',len(G['vias']),'pads',len(G['pads']),'zones',[(z.get('net'),z.get('layer'),round(z['poly'].area,1),z['filled']) if not z['rule'] else ('rule',z['name'],z['layers']) for z in G['zones']],'outline',G['outline_ok'],round(G['outline'].area,1),G['outline'].bounds,'mask',G['mask_exp'],G['mask_minw'],G['tent'],G['thick'])
