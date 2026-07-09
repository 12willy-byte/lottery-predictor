import os,time; os.chdir(r"C:\Users\Administrator\Documents\彩票选票机")
import sys; sys.path.insert(0,".")
from database import get_all_ssq, get_all_dlt
from analyzer import SSQAnalyzer, DLTAnalyzer, MultiStrategyPredictor

MIN_TRAIN=100; STEP=10
print("定位分析走回验证 (步长10)")

# SSQ
s=get_all_ssq()
s_draws=[[d["red%d"%j] for j in range(1,7)] for d in s]
freq_all=__import__('collections').Counter()
for d in s_draws:
    for n in d: freq_all[n]+=1

old_hits=[]; new_hits=[]
t0=time.time()
for i in range(MIN_TRAIN,len(s),STEP):
    train=s[:i]
    actual=set(s_draws[i])
    anl=SSQAnalyzer(train).comprehensive_analysis()
    m=MultiStrategyPredictor()
    preds=m.select_best_ssq(anl,count=1,period_seed=s[i]["period"])
    if preds:
        new_hits.append(len(set(preds[0]["reds"])&actual))
    # Baseline: all-time freq top6
    ranked=sorted(range(1,34),key=lambda x:-freq_all.get(x,0))
    old_hits.append(len(set(ranked[:6])&actual))
    if len(new_hits)%100==0:
        print(f"  SSQ {len(new_hits)}期 旧{sum(old_hits)/len(old_hits):.3f} 新{sum(new_hits)/len(new_hits):.3f}")

avg_old=sum(old_hits)/len(old_hits)
avg_new=sum(new_hits)/len(new_hits)
print(f"\nSSQ: 旧(全量频率) {avg_old:.3f}/6  新(v3.4定位) {avg_new:.3f}/6  {(avg_new-avg_old)/avg_old*100:+.1f}%")

# DLT
d=get_all_dlt()
d_draws=[[d["front%d"%j] for j in range(1,6)] for d in d]
freq_f=__import__('collections').Counter()
for dd in d_draws:
    for n in dd: freq_f[n]+=1

old_f=[]; new_f=[]
for i in range(MIN_TRAIN,len(d),STEP):
    train=d[:i]
    actual=set(d_draws[i])
    anl=DLTAnalyzer(train).comprehensive_analysis()
    m=MultiStrategyPredictor()
    preds=m.select_best_dlt(anl,count=1,period_seed=d[i]["period"])
    if preds:
        new_f.append(len(set(preds[0]["fronts"])&actual))
    ranked=sorted(range(1,36),key=lambda x:-freq_f.get(x,0))
    old_f.append(len(set(ranked[:5])&actual))

avg_of=sum(old_f)/len(old_f) if old_f else 0
avg_nf=sum(new_f)/len(new_f) if new_f else 0
print(f"DLT: 旧(全量频率) {avg_of:.3f}/5  新(v3.4定位) {avg_nf:.3f}/5  {(avg_nf-avg_of)/avg_of*100:+.1f}%")
print(f"\n{time.time()-t0:.0f}s")
