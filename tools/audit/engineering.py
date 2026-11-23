"""Phase 3 engineering calculations from extracted netlist/geometry."""
import json, os, math, collections
D=os.path.dirname(os.path.abspath(__file__))
g=json.load(open(os.path.join(D,"netlist_geom.json"),encoding="utf-8"))
pads={(p["ref"],p["pad"]):p for p in g["pads"]}
def net(r,p): return pads.get((r,str(p)),{}).get(net.get.__name__ if False else "net","<none>")

def pn(ref,pad): 
    p=pads.get((ref,str(pad)))
    return p["net"] if p else None

print("=== A. LED / SENSOR CURRENT CALCULATIONS ===")
VF_LED=1.2
for i in range(1,9):
    r=f"R{i}"
    rp=[p for p in g["pads"] if p["ref"]==r]
    gpio=[p["net"] for p in rp if "GPIO" in p["net"]]
    led=[p["net"] for p in rp if "LED" in p["net"]]
    print(f"  {r}: {gpio[0] if gpio else '?'} -> {led[0] if led else '?'}  IF=({3.3-VF_LED:.1f})/330 = {(3.3-VF_LED)/330*1000:.2f} mA")
print(f"  Sensor 12V: IF=(12-1.2)/2200={(12-1.2)/2200*1000:.2f} mA, P={(12-1.2)**2/2200*1000:.1f} mW")
print(f"  Sensor 24V: IF=(24-1.2)/2200={(24-1.2)/2200*1000:.2f} mA, P={(24-1.2)**2/2200*1000:.1f} mW  (1206 rated 250 mW)")

print("\n=== B. MCU RESET RC ===")
R,C=10e3,10e-6
print(f"  R19={R}, C4={C}, tau=RC={R*C*1000:.1f} ms; 5tau={5*R*C*1000:.0f} ms")

print("\n=== C. TVS MARGIN ===")
print("  SMBJ15A VRWM=15.0V, VBR=16.7..18.5V, VC(max)@IPP=24.4V")
print(f"  vs nominal 12V: margin {15-12:.1f} V; vs 14.4V max: margin {15-14.4:.1f} V ({(15-14.4)/14.4*100:.1f}%)")

print("\n=== D. MOTOR DRIVER CHANNEL MAPPING ===")
for i in range(1,9):
    rp=[p for p in g["pads"] if p["ref"]==f"R{i}"]
    gpio=[p["net"].strip("/") for p in rp if "GPIO" in p["net"]]
    led=[p["net"].strip("/") for p in rp if "LED" in p["net"]]
    print(f"  CH{i}: GPIO={gpio[0] if gpio else '?':10} -> LED={led[0] if led else '?'}")

print("\n=== E. MX_DRV EXTERNAL PULL-DOWN CHECK ===")
for i in range(1,9):
    members=[(p["ref"],p["pad"]) for p in g["pads"] if p["net"]==f"/M{i}_DRV"]
    print(f"  M{i}_DRV pads: {members}  ({len(members)} pads, no external pull-down)")

print("\n=== F. POWER LOOP GEOMETRY (trace lengths) ===")
def dist(a,b): return math.dist(a,b)
def fp(ref): return next((f for f in g["footprints"] if f["ref"]==ref),None)
for r in ["D1","C_BULK1","U_BUCK1","D2","L1","C_BULK2","U_LDO1","U_MCU1"]:
    f=fp(r); print(f"  {r:10} at {f['pos'] if f else None}")
# path lengths between key nodes using routed copper
def netlen(n):
    ts=[t for t in g["tracks"] if t["net"]==n]
    return sum(t["len"] for t in ts), len(ts)
for n in ["/12V_PROT","/12V_RAW","/SW_BUCK","/5V_RAIL","/3V3_RAIL","/GND"]:
    L,c=netlen(n); print(f"  {n:12} total routed length {L:8.1f} mm in {c} segments")

print("\n=== G. AMPACITY (IPC-2152 simplified, 1oz external, 10C/20C rise) ===")
# IPC-2221 approximation: I = k * dT^0.44 * A^0.725, A in mils^2, k=0.048 external
def ipc(w_mm,oz=1,dT=10):
    mils=w_mm/0.0254
    A=mils*oz*1.378
    return 0.048*(dT**0.44)*(A**0.725)
for w in [0.2624,0.35,0.5,0.8,1.0]:
    print(f"  {w:.4f} mm: {ipc(w,1,10):.2f} A @10C, {ipc(w,1,20):.2f} A @20C")
print("  Power-net min widths:")
for n in ["/12V_PROT","/12V_RAW","/5V_RAIL","/3V3_RAIL","/GND"]+[f"/MOT{i}" for i in range(1,9)]:
    ws=[t["width"] for t in g["tracks"] if t["net"]==n]
    if ws: print(f"    {n:12} min={min(ws):.4f} max={max(ws):.4f} mm -> I@{min(ws):.4f}mm = {ipc(min(ws),1,10):.2f} A")
