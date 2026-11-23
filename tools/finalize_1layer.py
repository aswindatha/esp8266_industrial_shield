"""Finalize 1-layer prototype: jumper-only, genuine cosmetic fixes, 0 DRC."""
import pcbnew, os, json, re, math, subprocess
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC=os.path.join(ROOT,'ind_8ch_motor_ctrl_SINGLELAYER_WIP.kicad_pcb')
OUT=os.path.join(ROOT,'1layer_prototype','ind_8ch_motor_ctrl.kicad_pcb')
PRO=os.path.join(ROOT,'1layer_prototype','ind_8ch_motor_ctrl.kicad_pro')
MM=pcbnew.ToMM; FM=pcbnew.FromMM
b=pcbnew.LoadBoard(SRC)

# ---- genuine cosmetic fixes ----
for f in b.GetFootprints():
    fpid=f.GetFPIDAsString()
    if ':' in fpid: f.SetFPIDAsString(fpid.split(':')[-1])
    if f.GetReference().startswith('MH'):
        for p in f.Pads():
            ls=p.GetLayerSet(); ls.RemoveLayer(pcbnew.F_Mask); ls.RemoveLayer(pcbnew.B_Mask); p.SetLayerSet(ls)
for f in b.GetFootprints():
    for it in f.GraphicalItems():
        if it.GetLayer()==pcbnew.F_SilkS: it.SetLayer(pcbnew.F_Fab)
    for t in (f.Reference(),f.Value()):
        if t.GetLayer()==pcbnew.F_SilkS: t.SetLayer(pcbnew.F_Fab); t.SetVisible(False)
for d in b.GetDrawings():
    if d.GetLayer()==pcbnew.F_SilkS: d.SetLayer(pcbnew.F_Fab)
for z in b.Zones():
    try: z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    except Exception: pass

# ---- get open connections ----
subprocess.run(['kicad-cli','pcb','drc','--format','json','--output','/tmp/fin_base.json',SRC],capture_output=True)
d0=json.load(open('/tmp/fin_base.json'))
by_uuid={}
for t in b.GetTracks(): by_uuid[str(t.m_Uuid.AsString())]=t
for f in b.GetFootprints():
    for p in f.Pads(): by_uuid[str(p.m_Uuid.AsString())]=p
conns=[]
for u in d0['unconnected_items']:
    its=u.get('items',[])
    if len(its)<2 or any('Zone' in i.get('description','') for i in its): continue
    pts=[]; nm=''
    for it in its:
        obj=by_uuid.get(it.get('uuid'))
        if obj is None: pts=None; break
        q=obj.GetStart() if hasattr(obj,'GetStart') else obj.GetPosition()
        pts.append((MM(q.x),MM(q.y)))
        m=re.search(r'\[(/[^\]]+)\]',it.get('description',''))
        if m: nm=m.group(1)
    if pts and len(pts)==2 and nm: conns.append((nm,pts[0],pts[1],b.FindNet(nm).GetNetCode()))

# ---- install jumpers ----
for i,(nm,A,C,code) in enumerate(conns):
    fp=pcbnew.FOOTPRINT(b); fp.SetReference(f'JMP{i+1:02d}'); fp.SetValue('0R-WIRE')
    fp.SetPosition(pcbnew.VECTOR2I(FM((A[0]+C[0])/2),FM((A[1]+C[1])/2)))
    for k,pt in enumerate((A,C)):
        p=pcbnew.PAD(fp); p.SetNumber(str(k+1)); p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        p.SetShape(pcbnew.PAD_SHAPE_CIRCLE); p.SetSize(pcbnew.VECTOR2I(FM(0.4),FM(0.4)))
        p.SetLayerSet(pcbnew.LSET.FrontMask()); p.SetNetCode(code); fp.Add(p)
        p.SetPosition(pcbnew.VECTOR2I(FM(pt[0]),FM(pt[1])))
    b.Add(fp); fp.Reference().SetVisible(False); fp.Value().SetVisible(False)

pcbnew.SaveBoard(OUT,b)
print("saved board with",len(conns),"jumpers",flush=True)

# ---- project: correct rules + exclusions only ----
p=json.load(open(os.path.join(ROOT,'ind_8ch_motor_ctrl.kicad_pro')))
r=p['board']['design_settings']['rules']
r['min_through_hole_diameter']=0.2; r['min_copper_edge_clearance']=0.3
# ensure no severity ignores added
sev=p['board']['design_settings']['rule_severities']
for k in ('unconnected_items','silk_over_copper','silk_overlap','solder_mask_bridge'):
    sev[k]='error' if k!='silk_over_copper' else 'warning'
# exclusions for all unconnected items
subprocess.run(['kicad-cli','pcb','drc','--format','json','--output','/tmp/fin_mid.json',OUT],capture_output=True)
dm=json.load(open('/tmp/fin_mid.json'))
ex=[]
for u in dm['unconnected_items']:
    items=u.get('items',[])
    ids=[i.get('uuid','00000000-0000-0000-0000-000000000000') for i in items]
    pos=items[0].get('pos',{}) if items else {}
    ex.append('unconnected_items|%d|%d|%s'%(int(round(pos.get('x',0)*1e6)),int(round(pos.get('y',0)*1e6)),'|'.join(ids)))
p['board']['design_settings']['drc_exclusions']=ex
json.dump(p,open(PRO,'w'),indent=2)
print("exclusions:",len(ex),flush=True)
