import sys, os
os.chdir(r"C:\Users\Administrator\Documents\彩票选票机")
sys.path.insert(0, ".")
from database import get_all_dlt
from analyzer import DLTAnalyzer, MultiStrategyPredictor

dlt = get_all_dlt()
nd = str(int(dlt[-1]["period"]) + 1)
anl = DLTAnalyzer(dlt).comprehensive_analysis()

m1 = MultiStrategyPredictor()
p1 = m1.select_best_dlt(anl, count=1, period_seed=nd)

m2 = MultiStrategyPredictor()
p2 = m2.select_best_dlt(anl, count=1, period_seed=nd)

same = p1[0]["fronts"] == p2[0]["fronts"] and p1[0]["backs"] == p2[0]["backs"]
print(f"Run1: {p1[0]['fronts']} {p1[0]['backs']}")
print(f"Run2: {p2[0]['fronts']} {p2[0]['backs']}")
print(f"Stable: {'YES' if same else 'NO - BUG'}")
