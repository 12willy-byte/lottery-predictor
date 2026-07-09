import os, time, json
os.chdir(r"C:\Users\Administrator\Documents\彩票选票机")
import sys; sys.path.insert(0,".")

from database import get_all_ssq, get_all_dlt
from analyzer import SSQAnalyzer, DLTAnalyzer, MultiStrategyPredictor

# Verify DLT 26071
dlt = get_all_dlt()
train = [d for d in dlt if int(d["period"]) < 26071]
actual = [d for d in dlt if d["period"] == "26071"][0]
actual_f = {actual["front%d"%j] for j in range(1,6)}
actual_b = {actual["back1"], actual["back2"]}

print("DLT 26071 验证")
print(f"实际: 前{[actual['front%d'%j] for j in range(1,6)]} 后({actual['back1']},{actual['back2']})")
print()

t0 = time.time()
anl = DLTAnalyzer(train).comprehensive_analysis()
msp = MultiStrategyPredictor()
preds = msp.select_best_dlt(anl, count=3, period_seed="26071")
t1 = time.time()

for i, p in enumerate(preds):
    fh = len(set(p["fronts"]) & actual_f)
    bh = len(set(p["backs"]) & actual_b)
    mark = ""
    if fh >= 3: mark += " [前区大中!]"
    elif fh >= 2: mark += " [前区命中]"
    if bh >= 1: mark += " [后区命中]"
    print(f"  #{i+1}: 前{p['fronts']} 后{p['backs']} -> 前{fh}/5 后{bh}/2{mark}")

print(f"\n耗时: {t1-t0:.1f}s")

# Now generate next predictions
print(f"\n{'='*45}")
print(f"新一轮预测")
print(f"{'='*45}")

next_dlt = str(int(dlt[-1]["period"]) + 1)
full_anl = DLTAnalyzer(dlt).comprehensive_analysis()
msp2 = MultiStrategyPredictor()
dlt_preds = msp2.select_best_dlt(full_anl, count=3, period_seed=next_dlt)

print(f"\nDLT 第{next_dlt}期:")
for i, p in enumerate(dlt_preds):
    print(f"  #{i+1}: 前{sorted(p['fronts'])} 后{p['backs']} 分{p['score']:.0f}")

# SSQ
ssq = get_all_ssq()
next_ssq = str(int(ssq[-1]["period"]) + 1)
ssq_anl = SSQAnalyzer(ssq).comprehensive_analysis()
ssq_preds = msp2.select_best_ssq(ssq_anl, count=3, period_seed=next_ssq)

print(f"\nSSQ 第{next_ssq}期:")
for i, p in enumerate(ssq_preds):
    print(f"  #{i+1}: 红{sorted(p['reds'])} 蓝{p['blue']} 分{p['score']:.0f}")

# Update cache
cache = {
    "ssq": {"weights": msp2.weights, "bonus": msp2.bonus, "version": "3.3", "updated": time.strftime("%Y-%m-%d")},
    "dlt": {"weights": msp2.weights, "bonus": msp2.bonus, "version": "3.3", "updated": time.strftime("%Y-%m-%d")},
}
with open("data/weights_cache.json", "w") as f:
    json.dump(cache, f, indent=2, ensure_ascii=False)

print(f"\n缓存v3.3已更新 | SSQ{len(ssq)}期 DLT{len(dlt)}期")
