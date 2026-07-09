# -*- coding: utf-8 -*-
"""全量走回引擎 — 对每一期用之前所有历史训练，记录所有策略命中率"""
import sys, os, json, time
os.chdir(r"C:\Users\Administrator\Documents\彩票选票机")
sys.path.insert(0, ".")

from database import get_all_ssq, get_all_dlt
from collections import Counter, defaultdict

MIN_TRAIN = 100  # 至少100期训练数据才预测

def run_ssq_walkback():
    data = get_all_ssq()
    draws = [[d["red%d"%j] for j in range(1,7)] for d in data]
    blues = [d["blue"] for d in data]
    total = len(data)
    
    # 策略定义: name -> function(train_draws, train_blues) -> ranked_numbers
    strategies = {}
    
    # 1. 全量频率
    def s_alltime_freq(train_d, train_b):
        c = Counter(n for d in train_d for n in d)
        return sorted(range(1,34), key=lambda n: -c.get(n,0))
    strategies["全量频率"] = s_alltime_freq
    
    # 2. 近50期频率
    def s_recent50(train_d, train_b):
        c = Counter(n for d in train_d[-50:] for n in d)
        return sorted(range(1,34), key=lambda n: -c.get(n,0))
    strategies["近50期频率"] = s_recent50
    
    # 3. 近100期频率
    def s_recent100(train_d, train_b):
        c = Counter(n for d in train_d[-100:] for n in d)
        return sorted(range(1,34), key=lambda n: -c.get(n,0))
    strategies["近100期频率"] = s_recent100
    
    # 4. 遗漏(最久未出)
    def s_omission(train_d, train_b):
        om = {}
        for n in range(1, 34):
            cnt = 0
            for d in reversed(train_d):
                if n in d: break
                cnt += 1
            om[n] = cnt
        return sorted(range(1,34), key=lambda n: -om[n])
    strategies["遗漏"] = s_omission
    
    # 5. 跟随
    def s_follow(train_d, train_b):
        last = train_d[-1]
        follow = defaultdict(Counter)
        for i in range(1, len(train_d)):
            for n in train_d[i-1]:
                for m in train_d[i]:
                    follow[n][m] += 1
        scores = Counter()
        for n in last:
            for m, c in follow[n].items():
                scores[m] += c
        ranked = sorted(range(1,34), key=lambda n: -scores.get(n,0))
        return ranked if ranked else list(range(1,34))
    strategies["跟随"] = s_follow
    
    # 6. 重号
    def s_repeat(train_d, train_b):
        last_set = set(train_d[-1])
        ranked = sorted(range(1,34), key=lambda n: (1 if n in last_set else 0))
        return ranked
    strategies["重号"] = s_repeat
    
    # 7. 邻号
    def s_adjacent(train_d, train_b):
        last = train_d[-1]
        adj = set()
        for n in last:
            if n > 1: adj.add(n-1)
            if n < 33: adj.add(n+1)
        adj -= set(last)
        ranked = sorted(range(1,34), key=lambda n: (1 if n in adj else 0))
        return ranked
    strategies["邻号"] = s_adjacent
    
    # 8. 混合: 频率0.5+遗漏0.5
    def s_mixed(train_d, train_b):
        c = Counter(n for d in train_d for n in d)
        om = {}
        for n in range(1, 34):
            cnt = 0
            for d in reversed(train_d):
                if n in d: break
                cnt += 1
            om[n] = cnt
        max_f = max(c.values()) if c else 1
        max_o = max(om.values()) if om else 1
        scores = {n: c.get(n,0)/max_f*0.5 + om.get(n,0)/max_o*0.5 for n in range(1,34)}
        return sorted(range(1,34), key=lambda n: -scores[n])
    strategies["频率+遗漏"] = s_mixed
    
    # 9. 随机基线
    import random as _r
    strategies["随机基线"] = lambda td, tb: _r.sample(range(1,34), 33)
    
    results = {name: {"red_hits": [], "blue_hits": 0, "blue_total": 0, "periods": 0} for name in strategies}
    
    t0 = time.time()
    for i in range(MIN_TRAIN, total):
        train_d = draws[:i]
        train_b = blues[:i]
        actual_d = set(draws[i])
        actual_b = blues[i]
        
        for name, fn in strategies.items():
            ranked = fn(train_d, train_b)
            top6 = set(ranked[:6])
            hits = len(top6 & actual_d)
            results[name]["red_hits"].append(hits)
            results[name]["periods"] += 1
        
        if (i - MIN_TRAIN) % 500 == 0:
            elapsed = time.time() - t0
            eta = elapsed / max(i - MIN_TRAIN, 1) * (total - i)
            print(f"  SSQ {i}/{total} ({i-MIN_TRAIN}期完成) 已用{elapsed:.0f}s 预计剩余{eta:.0f}s")
    
    print(f"\nSSQ走回完成 ({total-MIN_TRAIN}期, {time.time()-t0:.0f}s)")
    return {name: {
        "avg_hits": sum(r["red_hits"])/max(r["periods"],1),
        "periods": r["periods"],
        "hits_dist": dict(Counter(r["red_hits"]))
    } for name, r in results.items()}

# Run SSQ
print("=" * 55)
print("  SSQ 全量走回 — 10种策略 (至少100期训练)")
print("=" * 55)
ssq_results = run_ssq_walkback()

print("\n排名 (按平均命中/6排序):")
print("-" * 45)
for name, r in sorted(ssq_results.items(), key=lambda x: -x[1]["avg_hits"]):
    bar = "#" * int(r["avg_hits"] * 15)
    print(f"  {name:<12}: {r['avg_hits']:.3f}/6  {bar}")
    # Show distribution
    d = r["hits_dist"]
    dist_str = "  ".join(f"{k}球:{d.get(k,0)}" for k in sorted(d))
    print(f"  {'':>12}  分布: {dist_str}")

# Save results
with open("data/walkback_ssq.json", "w", encoding="utf-8") as f:
    # Convert to serializable
    out = {k: {"avg_hits": v["avg_hits"], "periods": v["periods"], "hits_dist": {str(kk): vv for kk, vv in v["hits_dist"].items()}} for k, v in ssq_results.items()}
    json.dump(out, f, ensure_ascii=False, indent=2)
print("\n已保存: data/walkback_ssq.json")
