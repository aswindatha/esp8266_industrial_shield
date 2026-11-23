import numpy as np, os
D=os.path.dirname(os.path.abspath(__file__))
def load(n):
    a=np.loadtxt(os.path.join(D,n))
    return a[:,0], a[:,1::2]   # wrdata emits time before each vector

print("=== SIM1 POWER-UP / LOAD STEP ===")
t,a=load("sim1_out.txt"); v1,vp,v5,v3=a[:,0],a[:,1],a[:,2],a[:,3]
def tc(t,v,th):
    i=np.where(v>=th)[0]; return t[i[0]]*1000 if len(i) else float('nan')
print(f"  12V reaches 11.4V at {tc(t,vp,11.4):.1f} ms ; reaches 12V at {tc(t,vp,11.99):.1f} ms")
print(f"  5V reaches 4.75V at {tc(t,v5,4.75):.1f} ms ; 3V3 reaches 3.135V at {tc(t,v3,3.135):.1f} ms")
m=(t>0.18)&(t<0.45)
print(f"  Load step: 5V min={v5[m].min():.3f} V (droop {5-v5[m].min():.3f} V); 3V3 min={v3[m].min():.3f} V (droop {3.3-v3[m].min():.3f} V)")
print(f"  Steady: 5V={np.mean(v5[t>0.6]):.3f} V, 3V3={np.mean(v3[t>0.6]):.3f} V, Vprot={np.mean(vp[t>0.6]):.3f} V")

print("\n=== SIM2 RESET RC ===")
t2,b=load("sim2_out.txt"); v33,en=b[:,0],b[:,1]
for th,name in [(0.825,"VIL 0.825V"),(2.475,"VIH 2.475V"),(2.97,"90% 2.97V")]:
    i=np.where(en>=th)[0]
    print(f"  EN crosses {name:12} at {t2[i[0]]*1000:.1f} ms" if len(i) else f"  EN never reached {name}")
i=np.where(en>=0.632*3.3)[0]
print(f"  measured tau(63.2%) = {t2[i[0]]*1000:.1f} ms (design 100 ms)")

print("\n=== SIM3 MOTOR CHANNEL ===")
t3,c=load("sim3_out.txt"); gpio,ledc,drv,mot=c[:,0],c[:,1],c[:,2],c[:,3]
on=(t3>0.135)&(t3<0.19); off=(t3>0.26)&(t3<0.29)   # LED active when GPIO is LOW (active-low drive)
IF=(3.3-ledc[on].mean())/330*1000
print(f"  LED cathode {ledc[on].mean():.3f} V -> IF={IF:.2f} mA")
print(f"  ULN input V(drv)={drv[on].mean():.3f} V -> Iin={(drv[on].mean()-1.4)/2700*1000:.2f} mA")
print(f"  ULN input CTR required >= {(drv[on].mean()-1.4)/2700*1000/IF*100:.0f}% (LTV-827S min CTR 50%)")
print(f"  ON: V(mot)={mot[on].mean():.3f} V ; OFF: V(mot)={mot[off].mean():.3f} V ; peak={mot.max():.2f} V")

print("\n=== SIM4 SENSOR SWEEP ===")
vsx,d=load("sim4_out.txt"); vs,va,vc=d[:,0],d[:,1],d[:,2]
for th in [0.5,1.65,2.0]:
    i=np.where(vc<=th)[0]
    print(f"  collector < {th:.2f} V at Vsens={vs[i[0]]:.2f} V" if len(i) else f"  never < {th}")
j=np.argmin(abs(vs-12)); print(f"  @12V: anode={va[j]:.3f} V, IF={(12-va[j])/2200*1000:.2f} mA, collector={vc[j]:.3f} V")
print(f"  @24V: anode={va[-1]:.3f} V, IF={(24-va[-1])/2200*1000:.2f} mA")
