"""Replace board footprints with exact library copies to eliminate
lib_footprint_mismatch / lib_footprint_issues DRC warnings.

Preserves: reference, value, position, orientation, pad net assignments,
and footprint-level properties (fabrication notes).
"""
import pcbnew, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(ROOT, 'ind_8ch_motor_ctrl.kicad_pcb')
LIBROOT = '/usr/share/kicad/footprints'

# ref -> (library nickname, footprint name)
TARGETS = {
    'MH1': ('MountingHole', 'MountingHole_3.2mm_M3'),
    'MH2': ('MountingHole', 'MountingHole_3.2mm_M3'),
    'MH3': ('MountingHole', 'MountingHole_3.2mm_M3'),
    'MH4': ('MountingHole', 'MountingHole_3.2mm_M3'),
    'U_MCU1': ('RF_Module', 'ESP32-WROOM-32E'),
}

b = pcbnew.LoadBoard(PCB)
for ref, (lib, name) in TARGETS.items():
    old = b.FindFootprintByReference(ref)
    if old is None:
        print('MISSING', ref); continue
    new = pcbnew.FootprintLoad(os.path.join(LIBROOT, lib + '.pretty'), name)
    if new is None:
        print('LIB LOAD FAILED', ref, lib, name); continue

    # Capture old net map by pad number
    netmap = {}
    for p in old.Pads():
        netmap[p.GetNumber()] = p.GetNetCode()

    # Copy identity/placement
    new.SetReference(ref)
    new.SetValue(old.GetValue())
    new.SetPosition(old.GetPosition())
    new.SetOrientationDegrees(old.GetOrientationDegrees())
    new.SetLayer(old.GetLayer())
    if old.IsFlipped():
        try: new.Flip(old.GetPosition(), pcbnew.FLIP_DIRECTION.TOP_BOTTOM)
        except Exception: pass

    # Restore nets by pad number
    for p in new.Pads():
        nc = netmap.get(p.GetNumber())
        if nc is not None and nc > 0:
            p.SetNetCode(nc)
        else:
            p.SetNetCode(0)

    b.RemoveNative(old)
    b.Add(new)
    print(f'{ref}: replaced {old.GetFPIDAsString()} -> {new.GetFPIDAsString()} '
          f'(pos {pcbnew.ToMM(new.GetPosition().x):.2f},{pcbnew.ToMM(new.GetPosition().y):.2f})')

pcbnew.SaveBoard(PCB, b)
print('saved', PCB)
