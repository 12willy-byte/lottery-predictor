import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, get_ssq_count, get_dlt_count, get_last_update_time
import os;os.makedirs("data", exist_ok=True);init_db()
ssq = get_ssq_count()
dlt = get_dlt_count()

print("=" * 50)
print("  彩票智能选号系统 v3.1")
print("  " + "=" * 40)
print("  双色球(SSQ): %d 期" % ssq)
print("  大乐透(DLT): %d 期" % dlt)
print("  总计: %d 期开奖数据" % (ssq + dlt))
print()

# 加载回测缓存
try:
    import json
    cache_file = os.path.join("data", "backtest_cache.json")
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            cache = json.load(f)
        if "correction" in cache.get("ssq", {}):
            c = cache["ssq"]["correction"]["values"]
            print("  双色球修正规则: %s" % " ".join(["%+d" % v for v in c]))
        if "correction" in cache.get("dlt", {}):
            c = cache["dlt"]["correction"]["values"]
            print("  大乐透修正规则: %s" % " ".join(["%+d" % v for v in c]))
except:
    pass

print("=" * 50)
print()

import tkinter as tk
from gui import LotteryGUI
root = tk.Tk()
app = LotteryGUI(root)
root.mainloop()
