"""Add F.Silkscreen function labels for every terminal-block pin.

Compact labels centered in the free strip beside each TB body:
  J_IN  -> x = 12.2 (right of TB body)
  J_OUT -> x = 87.8 (left of TB body)
"""
import pcbnew, os

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

JIN={1:'12VIN',2:'GND',3:'12VP',4:'SENS1',5:'SENS2',6:'SENS3',7:'SENS4',
     8:'3V3',9:'SDA',10:'SCL',11:'TX',12:'RX'}
JOUT={1:'MOT1',2:'MOT2',3:'MOT3',4:'MOT4',5:'MOT5',6:'MOT6',7:'MOT7',8:'MOT8',9:'12VP'}

def label(ref,n):
    m=JIN if ref=='J_IN' else JOUT
    return m.get(n,f'{n}:NC')

def process(path, xin=12.2, xout=87.8):
    b=pcbnew.LoadBoard(path)
    # remove previous pin labels (board-level PCB_TEXT on F.SilkS containing ':' or known tokens)
    tokens=('12VIN','12VP','SENS','MOT','GND','3V3','SDA','SCL','TX','RX','NC')
    for d in list(b.GetDrawings()):
        if isinstance(d,pcbnew.PCB_TEXT) and d.GetLayer()==pcbnew.F_SilkS:
            t=d.GetText().strip()
            if any(tok in t for tok in tokens):
                b.RemoveNative(d)
    for ref,anchor in (('J_IN',xin),('J_OUT',xout)):
        f=b.FindFootprintByReference(ref)
        if not f: continue
        for p in sorted(f.Pads(),key=lambda p:p.GetPosition().y):
            n=int(p.GetNumber()); q=p.GetPosition()
            t=pcbnew.PCB_TEXT(b)
            t.SetText(label(ref,n))
            t.SetLayer(pcbnew.F_SilkS)
            t.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(anchor),q.y))
            t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.8),pcbnew.FromMM(0.8)))
            t.SetTextThickness(pcbnew.FromMM(0.12))
            t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
            t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
            b.Add(t)
    pcbnew.SaveBoard(path,b)

if __name__=='__main__':
    import sys
    xin=float(sys.argv[1]) if len(sys.argv)>1 else 12.2
    xout=float(sys.argv[2]) if len(sys.argv)>2 else 87.8
    for sub in ('2layer_production','1layer_prototype'):
        process(os.path.join(ROOT,sub,'ind_8ch_motor_ctrl.kicad_pcb'),xin,xout)
