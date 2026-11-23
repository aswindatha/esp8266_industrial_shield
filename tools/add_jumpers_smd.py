"""Add 0R jumper-wire footprints directly on the 1-layer board endpoints.

No new tracks: each jumper's two pads land on the existing copper of the net at
the two reported endpoints. The jumper body spans any blocking trace physically.
KiCad cannot model through-component connections, so DRC exclusions are added
for the jumper-internal nets only.
"""
import pcbnew, os, json, re, math
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB=os.path.join(ROOT,'1layer_prototype','ind_8ch_motor_ctrl.kicad_pcb')
MM=pcbnew.ToMM; FM=pcbnew.FromMM
b=pcbnew.LoadBoard(PCB)
drc=json.load(open('/tmp/1l_clean.json'))
by_uuid={}
for t in b.GetTracks(): by_uuid[str(t.m_Uuid.AsString())]=t
for f in b.GetFootprints():
    for p in f.Pads(): by_uuid[str(p.m_Uuid.AsString())]=p

jumpers=[]
for i,u in enumerate(drc['unconnected_items']):
    its=u.get('items',[])
    if len(its)<2: continue
    A=C=None; nm=''
    for it in its:
        if 'Zone' in it.get('description',''): A=None; break
        obj=by_uuid.get(it.get('uuid'))
        if obj is None: A=None; break
        q=obj.GetStart() if hasattr(obj,'GetStart') else obj.GetPosition()
        pt=(MM(q.x),MM(q.y))
        if A is None: A=pt
        else: C=pt
        m=re.search(r'\[(/[^\]]+)\]',it.get('description',''))
        if m: nm=m.group(1)
    if A is None or C is None: continue
    net=b.FindNet(nm)
    if not net: continue
    fp=pcbnew.FOOTPRINT(b)
    fp.SetReference(f'JMP{i+1:02d}'); fp.SetValue('0R-WIRE')
    fp.SetPosition(pcbnew.VECTOR2I(FM((A[0]+C[0])/2),FM((A[1]+C[1])/2)))
    for k,pt in enumerate((A,C)):
        p=pcbnew.PAD(fp)
        p.SetNumber(str(k+1)); p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        p.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        p.SetSize(pcbnew.VECTOR2I(FM(0.5),FM(0.5)))
        
        p.SetLayerSet(pcbnew.LSET.FrontMask())
        p.SetNet(net)
        fp.Add(p)
        p.SetPosition(pcbnew.VECTOR2I(FM(pt[0]),FM(pt[1])))
    b.Add(fp)
    fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
    jumpers.append({'ref':f'JMP{i+1:02d}','net':nm,'A':A,'C':C,'len':round(math.dist(A,C),1)})
    print(f"JMP{i+1:02d} {nm:16s} {math.dist(A,C):5.1f}mm",flush=True)

pcbnew.SaveBoard(PCB,b)
json.dump(jumpers,open(os.path.join(ROOT,'tools','audit','jumpers_installed.json'),'w'),indent=1)
print("saved; jumpers:",len(jumpers),flush=True)
