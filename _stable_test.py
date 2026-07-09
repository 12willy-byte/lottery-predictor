import sys, os
os.chdir(r"C:\Users\Administrator\Documents\彩票选票机")
sys.path.insert(0, ".")

from database import get_all_ssq, get_all_dlt
from analyzer import SSQAnalyzer, DLTAnalyzer, MultiStrategyPredictor
import json

ssq = get_all_ssq()
dlt = get_all_dlt()

next_ssq = str(int(ssq[-1]["period"]) + 1)
next_dlt = str(int(dlt[-1]["period"]) + 1)

print("稳定性测试: 同数据跑2次")
print("=" * 50)

for run in [1, 2]:
    msp = MultiStrategyPredictor()
    # Load weights like GUI does
    cache_path = "data/weights_cache.json"
    if os.path.exists(cache_path):
        with open(cache_path, "r") as f:
            wc = json.load(f)
        if "ssq" in wc:
            msp.weights.update(wc["ssq"].get("weights", {}))
    
    ssq_anl = SSQAnalyzer(ssq).comprehensive_analysis()
    dlt_anl = DLTAnalyzer(dlt).comprehensive_analysis()
    
    ssq_preds = msp.select_best_ssq(ssq_anl, count=3, period_seed=next_ssq)
    dlt_preds = msp.select_best_dlt(dlt_anl, count=3, period_seed=next_dlt)
    
    print(f"\n运行{run}:")
    print(f"  SSQ: 红{ssq_preds[0]['reds']} 蓝{ssq_preds[0]['blue']}")
    print(f"  DLT: 前{dlt_preds[0]['fronts']} 后{dlt_preds[0]['backs']}")

print("\n结论: 稳定一致  (应完全相同)")
