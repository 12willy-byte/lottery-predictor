import sys, os, time
os.chdir(r"C:\Users\Administrator\Documents\彩票选票机")
sys.path.insert(0, ".")

from database import get_all_ssq, get_all_dlt
from analyzer import SSQAnalyzer, DLTAnalyzer, MultiStrategyPredictor

N = 5
print(f"快速验证 — SSQ+DLT 各{N}期")
print("=" * 55)

# === SSQ ===
ssq = get_all_ssq()
print(f"\nSSQ ({len(ssq)}期, 测近{N}期):")
msp = MultiStrategyPredictor()
rh = []; bh = []
t0 = time.time()

for i in range(len(ssq) - N, len(ssq)):
    train = ssq[:i]
    actual = ssq[i]
    period = actual["period"]
    
    anl = SSQAnalyzer(train).comprehensive_analysis()
    preds = msp.select_best_ssq(anl, count=1, period_seed=str(period)+str(i))
    
    if preds:
        p = preds[0]
        fh = len(set(p["reds"]) & {actual["red%d"%j] for j in range(1,7)})
        bh_now = 1 if p["blue"] == actual["blue"] else 0
    else:
        fh = bh_now = 0
    rh.append(fh); bh.append(bh_now)
    print(f"  期{period}: 红{fh}/6 蓝{'=OK' if bh_now else 'X'}  (已用{time.time()-t0:.0f}s)")

print(f"  SSQ: 红{sum(rh)/N:.1f}/6  蓝{sum(bh)}/{N}  耗时{time.time()-t0:.0f}s")

# === DLT ===
dlt = get_all_dlt()
print(f"\nDLT ({len(dlt)}期, 测近{N}期):")
fh_list = []; bh_list = []
t0 = time.time()

for i in range(len(dlt) - N, len(dlt)):
    train = dlt[:i]
    actual = dlt[i]
    period = actual["period"]
    
    anl = DLTAnalyzer(train).comprehensive_analysis()
    preds = msp.select_best_dlt(anl, count=1, period_seed=str(period)+str(i))
    
    if preds:
        p = preds[0]
        fh = len(set(p["fronts"]) & {actual["front%d"%j] for j in range(1,6)})
        bh_now = len(set(p["backs"]) & {actual["back1"], actual["back2"]})
    else:
        fh = bh_now = 0
    fh_list.append(fh); bh_list.append(bh_now)
    print(f"  期{period}: 前{fh}/5 后{bh_now}/2  (已用{time.time()-t0:.0f}s)")

print(f"  DLT: 前{sum(fh_list)/N:.1f}/5  后{sum(bh_list)/N:.1f}/2  耗时{time.time()-t0:.0f}s")

print(f"\n总耗时: {time.time()-t0:.0f}s")
