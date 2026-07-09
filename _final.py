import os,time,json; os.chdir(r"C:\Users\Administrator\Documents\彩票选票机")
import sys; sys.path.insert(0,".")
from database import get_all_ssq, get_all_dlt
from analyzer import SSQAnalyzer, DLTAnalyzer, MultiStrategyPredictor

s=get_all_ssq(); d=get_all_dlt()
ns=str(int(s[-1]["period"])+1); nd=str(int(d[-1]["period"])+1)

sa=SSQAnalyzer(s).comprehensive_analysis()
da=DLTAnalyzer(d).comprehensive_analysis()
m=MultiStrategyPredictor()
sp=m.select_best_ssq(sa,count=3,period_seed=ns)
dp=m.select_best_dlt(da,count=3,period_seed=nd)

print(f"SSQ{ns}期 (v3.4 定位评分):")
for i,p in enumerate(sp):
    print(f"  #{i+1}: 红{sorted(p['reds'])} 蓝{p['blue']} 分{p['score']:.0f}")
print(f"\nDLT{nd}期 (v3.4 定位评分):")
for i,p in enumerate(dp):
    print(f"  #{i+1}: 前{sorted(p['fronts'])} 后{p['backs']} 分{p['score']:.0f}")

# Save prediction history
hist_file="data/pred_history.json"
hist=[]
if os.path.exists(hist_file):
    with open(hist_file) as f: hist=json.load(f)
hist.append({
    "time": time.strftime("%Y-%m-%d %H:%M"),
    "ssq_period": ns, "dlt_period": nd,
    "ssq_data": len(s), "dlt_data": len(d),
    "ssq_preds": [{"reds":p["reds"],"blue":p["blue"],"score":p["score"]} for p in sp],
    "dlt_preds": [{"fronts":p["fronts"],"backs":p["backs"],"score":p["score"]} for p in dp],
})
with open(hist_file,"w") as f: json.dump(hist,f,indent=2,ensure_ascii=False)
print(f"\n预测历史已保存 ({len(hist)}条)")

# Update cache
cache={"ssq":{"weights":m.weights,"bonus":m.bonus,"version":"3.4"},"dlt":{"weights":m.weights,"bonus":m.bonus,"version":"3.4"}}
with open("data/weights_cache.json","w") as f: json.dump(cache,f)
print("缓存v3.4已更新")
print(f"\n数据: SSQ{len(s)}期 DLT{len(d)}期")
