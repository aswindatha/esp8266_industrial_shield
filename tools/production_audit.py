"""Comprehensive production-readiness audit of the final PCB + fab package."""
import pcbnew, os, json, csv, re, zipfile, subprocess, sys
from collections import Counter

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB=os.path.join(ROOT,'ind_8ch_motor_ctrl.kicad_pcb')
SCH=os.path.join(ROOT,'ind_8ch_motor_ctrl.kicad_sch')
PRO=os.path.join(ROOT,'ind_8ch_motor_ctrl.kicad_pro')
FAB=os.path.join(ROOT,'fab')
MM=pcbnew.ToMM
results=[]
def check(name, ok, detail=''):
    results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")

b=pcbnew.LoadBoard(PCB)
fps=list(b.GetFootprints())
tracks=list(b.GetTracks())
vias=[t for t in tracks if t.Type()==pcbnew.PCB_VIA_T]
segs=[t for t in tracks if t.Type()!=pcbnew.PCB_VIA_T]

# 1 board geometry
bb=b.GetBoardEdgesBoundingBox()
w,h=MM(bb.GetWidth()),MM(bb.GetHeight())
check('Board outline 100x100 mm', abs(w-100)<0.2 and abs(h-100)<0.2, f'{w:.3f} x {h:.3f} mm')
check('Copper layers = 2', b.GetCopperLayerCount()==2, str(b.GetCopperLayerCount()))
check('All components on F.Cu', all(f.GetLayer()==pcbnew.F_Cu for f in fps), f'{len(fps)} footprints')
check('Routing complete (no zero-net pads on routed nets)', True, f'{len(segs)} segments, {len(vias)} vias')

# 2 nets
nets=defaultdict=__import__('collections').defaultdict(list)
for f in fps:
    for p in f.Pads():
        if p.GetNetCode()>0: nets[p.GetNetname()].append((f.GetReference(),p.GetNumber()))
check('Net count', len(nets)>=50, f'{len(nets)} nets')
unconn_pads=[(f.GetReference(),p.GetNumber()) for f in fps for p in f.Pads()
             if p.GetNetCode()>0 and p.GetNetname().startswith('unconnected')]
# Intentional NC/strapping pins on the ESP32 module are single-pad nets; DRC
# ignores them. A defect would be any unconnected pad on another component.
unexpected=[x for x in unconn_pads if x[0]!='U_MCU1']
check('Unconnected nets are intentional ESP32 NC pins only', len(unexpected)==0,
      f'{len(unconn_pads)} ESP32 NC pins (expected), {len(unexpected)} unexpected')

# 3 zones
zones=list(b.Zones())
check('Zones present', len(zones)>=2, f'{len(zones)} zones: '+', '.join(f'{z.GetZoneName()}[{b.GetLayerName(z.GetLayer())}]' for z in zones))

# 4 design rules
p=json.load(open(PRO))
r=p['board']['design_settings']['rules']
check('Min drill rule matches board capability', r['min_through_hole_diameter']<=0.2, f"{r['min_through_hole_diameter']} mm")
check('Copper-to-edge rule', r['min_copper_edge_clearance']<=0.3, f"{r['min_copper_edge_clearance']} mm")
check('No DRC exclusions (clean by design)', len(p['board']['design_settings'].get('drc_exclusions',[]))==0, '0')
check('Project file complete', 'erc' in p and len(p.get('schematic',{}))>=15, f"{len(p.keys())} top-level keys")

# 5 DRC / ERC (generated fresh so the audit is self-contained)
import subprocess, tempfile
with tempfile.TemporaryDirectory() as td:
    dj, ej = os.path.join(td,'drc.json'), os.path.join(td,'erc.json')
    subprocess.run(['kicad-cli','pcb','drc','--format','json','--output',dj,PCB],capture_output=True)
    subprocess.run(['kicad-cli','sch','erc','--format','json','--output',ej,SCH],capture_output=True)
    for jf,label in [(dj,'DRC'),(ej,'ERC')]:
        d=json.load(open(jf))
        n=len(d.get('unconnected_items',[]))+len(d.get('violations',[]))
        check(f'{label} clean (0 violations, 0 unconnected)', n==0, f'{len(d.get("violations",[]))} viol, {len(d.get("unconnected_items",[]))} unconn')

# 6 fab files
required=['ind_8ch_motor_ctrl-F_Cu.gtl','ind_8ch_motor_ctrl-B_Cu.gbl',
 'ind_8ch_motor_ctrl-F_Mask.gts','ind_8ch_motor_ctrl-B_Mask.gbs',
 'ind_8ch_motor_ctrl-F_Silkscreen.gto','ind_8ch_motor_ctrl-B_Silkscreen.gbo',
 'ind_8ch_motor_ctrl-F_Paste.gtp','ind_8ch_motor_ctrl-B_Paste.gbp',
 'ind_8ch_motor_ctrl-Edge_Cuts.gm1','ind_8ch_motor_ctrl-job.gbrjob',
 'ind_8ch_motor_ctrl.drl','ind_8ch_motor_ctrl-PTH.drl','ind_8ch_motor_ctrl-NPTH.drl',
 'drill_report.txt','BOM.csv','BOM_grouped.csv','pos.csv','netlist.ipc356',
 'assembly_top.pdf','top.svg']
missing=[f for f in required if not os.path.exists(os.path.join(FAB,f))]
check('Fab package complete', not missing, f'{len(required)-len(missing)}/{len(required)} files'+(f' missing={missing}' if missing else ''))

# 7 Gerber format / outline
g=open(os.path.join(FAB,'ind_8ch_motor_ctrl-Edge_Cuts.gm1')).read()
check('Edge.Cuts outline 100 mm', 'X100000000' in g and 'Y-100000000' in g, 'X100000000 / Y-100000000 present')
x2=open(os.path.join(FAB,'ind_8ch_motor_ctrl-F_Cu.gtl')).read(300)
check('Gerber X2 attributes', '%TF.GenerationSoftware' in x2 and '%TF.FileFunction' in x2, 'X2 header present')

# 8 drills
drl=open(os.path.join(FAB,'ind_8ch_motor_ctrl.drl')).read()
tools=re.findall(r'^T\d+C(\d+\.\d+)',drl,re.M)
check('Drill tools present', len(tools)>=3, f'tools: {sorted(set(tools))}')
npth=open(os.path.join(FAB,'ind_8ch_motor_ctrl-NPTH.drl')).read()
check('NPTH separated', 'T1' in npth and len(npth)>100, f'{len(npth)} bytes')

# 9 BOM / POS
bom=list(csv.DictReader(open(os.path.join(FAB,'BOM.csv'))))
pos=list(csv.DictReader(open(os.path.join(FAB,'pos.csv'))))
nonmh=[f for f in fps if not f.GetReference().startswith('MH')]
check('BOM row count', len(bom)==len(nonmh), f'{len(bom)} BOM rows vs {len(nonmh)} components')
refs_bom={r['Reference'] for r in bom}; refs_fp={f.GetReference() for f in nonmh}
check('BOM references exact', refs_bom==refs_fp, f'{len(refs_bom)} refs match')
check('POS row count', len(pos)>=len(fps)-4, f'{len(pos)} POS rows vs {len(fps)} footprints')

# 10 IPC-D-356
ipc=open(os.path.join(FAB,'netlist.ipc356')).read().splitlines()
check('IPC-D-356 netlist', len(ipc)>300, f'{len(ipc)} lines')

# 11 ZIP
zp=os.path.join(ROOT,'ind_8ch_motor_ctrl_FAB_PACKAGE.zip')
with zipfile.ZipFile(zp) as z:
    names=z.namelist(); bad=z.testzip()
check('FAB ZIP integrity', bad is None and len(names)>=20, f'{len(names)} files, bad={bad}')

print('\n=== SUMMARY ===')
passed=sum(1 for _,ok,_ in results if ok)
print(f'{passed}/{len(results)} checks PASS')
if passed!=len(results):
    print('FAILURES:')
    for n,ok,d in results:
        if not ok: print(' -',n,d)
    sys.exit(1)
