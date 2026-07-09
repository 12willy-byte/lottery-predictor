import sys, os
os.chdir(r"C:\Users\Administrator\Documents\彩票选票机")
sys.path.insert(0, ".")
from database import get_all_ssq
from collections import Counter

ssq = get_all_ssq()
draws = [[d["red%d"%j] for j in range(1,7)] for d in ssq]

# Debug: check omission ranking at a few periods
omission = {n: -1 for n in range(1,34)}
for i in [200, 500, 1000, 2000, 3000]:
    # Build omission up to period i
    for j in range(i):
        d = draws[j]
        for n in range(1,34):
            if n in d:
                omission[n] = j
    
    actual = set(draws[i])
    ranked = sorted(range(1,34), key=lambda x: i - omission.get(x, -1), reverse=True)
    top6 = set(ranked[:6])
    hits = len(top6 & actual)
    
    om_vals = {x: i - omission.get(x, -1) for x in range(1,34)}
    print(f"\n期{i}: 实际{actual}")
    print(f"  Top6遗漏: {sorted(top6)} (遗漏值: {[om_vals[x] for x in sorted(top6)]})")
    print(f"  命中: {hits}")
    print(f"  遗漏分布: min={min(om_vals.values())} max={max(om_vals.values())}")

# Check: what is the actual omission distribution?
omission = {n: -1 for n in range(1,34)}
for j in range(len(draws)):
    d = draws[j]
    for n in range(1,34):
        if n in d:
            omission[n] = j

print(f"\n最终遗漏(i={len(draws)-1}):")
for n in sorted(range(1,34), key=lambda x: len(draws)-1 - omission.get(x,-1), reverse=True)[:10]:
    print(f"  {n}: {len(draws)-1 - omission.get(n,-1)}期未出")
