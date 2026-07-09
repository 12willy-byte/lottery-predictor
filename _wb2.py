import sys, os, json, time
os.chdir(r"C:\Users\Administrator\Documents\彩票选票机")
sys.path.insert(0, ".")

from database import get_all_ssq, get_all_dlt
from collections import Counter, defaultdict
import random as _rnd

MIN_TRAIN = 100
STEP = 5  # 每5期测一次

def test_ssq_strategies():
    data = get_all_ssq()
    draws = [[d["red%d"%j] for j in range(1,7)] for d in data]
    total = len(draws)
    
    strat = {
        "全量频率": lambda td: sorted(range(1,34), key=lambda n: -Counter(n for d in td for n in d).get(n,0)),
        "近50期频": lambda td: sorted(range(1,34), key=lambda n: -Counter(n for d in td[-50:] for n in d).get(n,0)),
        "近100期频": lambda td: sorted(range(1,34), key=lambda n: -Counter(n for d in td[-100:] for n in d).get(n,0)),
        "遗漏": lambda td: sorted(range(1,34), key=lambda n: -next((c for c,d in enumerate(reversed(td)) if n in d), 9999)),
        "跟随": lambda td: _follow_rank(td),
        "频率+遗漏": lambda td: _mixed_rank(td),
    }
    
    res = {n: [] for n in strat}
    
    t0 = time.time()
    count = 0
    for i in range(MIN_TRAIN, total, STEP):
        train_d = draws[:i]
        actual = set(draws[i])
        for name, fn in strat.items():
            top6 = set(fn(train_d)[:6])
            res[name].append(len(top6 & actual))
        count += 1
        if count % 100 == 0:
            print(f"  {count}期完成 ({time.time()-t0:.0f}s)")
    
    print(f"\nSSQ走回: {count}期, {time.time()-t0:.0f}s")
    for name in sorted(res, key=lambda n: -sum(res[n])/len(res[n])):
        avg = sum(res[n]) / len(res[n])
        bar = "#" * int(avg * 20)
        print(f"  {name:<10}: {avg:.3f}/6 {bar}")
    
    # Random baseline (expected 6/33 * 6 = 1.09)
    print(f"  {'随机期望':<10}: {6*6/33:.3f}/6")
    return res

def _follow_rank(td):
    last = td[-1]
    follow = defaultdict(Counter)
    for i in range(1, len(td)):
        for n in td[i-1]:
            for m in td[i]:
                follow[n][m] += 1
    sc = Counter()
    for n in last:
        for m, c in follow[n].items():
            sc[m] += c
    return sorted(range(1,34), key=lambda n: -sc.get(n,0))

def _mixed_rank(td):
    c = Counter(n for d in td for n in d)
    max_f = max(c.values()) if c else 1
    om = {n: next((i for i,d in enumerate(reversed(td)) if n in d), 9999) for n in range(1,34)}
    max_o = max(om.values()) if om else 1
    return sorted(range(1,34), key=lambda n: -(c.get(n,0)/max_f*0.5 + om[n]/max_o*0.5))

ssq_r = test_ssq_strategies()

# Now DLT
print("\n" + "=" * 45)
print("  DLT 全量走回")
print("=" * 45)

dlt_data = get_all_dlt()
dlt_draws = [[d["front%d"%j] for j in range(1,6)] for d in dlt_data]
dlt_backs = [[d["back1"], d["back2"]] for d in dlt_data]
total_dlt = len(dlt_draws)

# Front zone strategies
dlt_front = {
    "全量频率": lambda td: sorted(range(1,36), key=lambda n: -Counter(n for d in td for n in d).get(n,0)),
    "近50期频": lambda td: sorted(range(1,36), key=lambda n: -Counter(n for d in td[-50:] for n in d).get(n,0)),
    "遗漏": lambda td: sorted(range(1,36), key=lambda n: -next((c for c,d in enumerate(reversed(td)) if n in d), 9999)),
    "跟随": lambda td: _follow_rank_dlt(td),
    "频率+遗漏": lambda td: _mixed_rank_dlt(td),
}

# Back zone strategies
dlt_back = {
    "全量频率": lambda tb: sorted(range(1,13), key=lambda n: -Counter(b for p in tb for b in p).get(n,0)),
    "遗漏": lambda tb: sorted(range(1,13), key=lambda n: -next((c for c,p in enumerate(reversed(tb)) if n in p), 9999)),
    "重号": lambda tb: sorted(range(1,13), key=lambda n: (1 if n in tb[-1] else 0)),
    "频率+遗漏": lambda tb: _mixed_rank_back(tb),
}

front_res = {n: [] for n in dlt_front}
back_res = {n: [] for n in dlt_back}

t0 = time.time()
count = 0
for i in range(MIN_TRAIN, total_dlt, STEP):
    train_f = dlt_draws[:i]
    train_b = dlt_backs[:i]
    actual_f = set(dlt_draws[i])
    actual_b = set(dlt_backs[i])
    
    for name, fn in dlt_front.items():
        top5 = set(fn(train_f)[:5])
        front_res[name].append(len(top5 & actual_f))
    for name, fn in dlt_back.items():
        top2 = set(fn(train_b)[:2])
        back_res[name].append(len(top2 & actual_b))
    
    count += 1
    if count % 100 == 0:
        print(f"  {count}期完成 ({time.time()-t0:.0f}s)")

print(f"\nDLT走回: {count}期, {time.time()-t0:.0f}s")
print("\n前区:")
for name in sorted(front_res, key=lambda n: -sum(front_res[n])/len(front_res[n])):
    avg = sum(front_res[n]) / len(front_res[n])
    bar = "#" * int(avg * 20)
    print(f"  {name:<10}: {avg:.3f}/5 {bar}")
print(f"  {'随机期望':<10}: {5*5/35:.3f}/5")

print("\n后区:")
for name in sorted(back_res, key=lambda n: -sum(back_res[n])/len(back_res[n])):
    avg = sum(back_res[n]) / len(back_res[n])
    bar = "#" * int(avg * 30)
    print(f"  {name:<10}: {avg:.3f}/2 {bar}")
print(f"  {'随机期望':<10}: {2*2/12:.3f}/2")

def _follow_rank_dlt(td):
    last = td[-1]
    follow = defaultdict(Counter)
    for i in range(1, len(td)):
        for n in td[i-1]:
            for m in td[i]:
                follow[n][m] += 1
    sc = Counter()
    for n in last:
        for m, c in follow[n].items():
            sc[m] += c
    return sorted(range(1,36), key=lambda n: -sc.get(n,0))

def _mixed_rank_dlt(td):
    c = Counter(n for d in td for n in d)
    max_f = max(c.values()) if c else 1
    om = {n: next((i for i,d in enumerate(reversed(td)) if n in d), 9999) for n in range(1,36)}
    max_o = max(om.values()) if om else 1
    return sorted(range(1,36), key=lambda n: -(c.get(n,0)/max_f*0.5 + om[n]/max_o*0.5))

def _mixed_rank_back(tb):
    c = Counter(b for p in tb for b in p)
    max_f = max(c.values()) if c else 1
    om = {n: next((i for i,p in enumerate(reversed(tb)) if n in p), 9999) for n in range(1,13)}
    max_o = max(om.values()) if om else 1
    return sorted(range(1,13), key=lambda n: -(c.get(n,0)/max_f*0.7 + om[n]/max_o*0.3))

print("\n完成! 数据已就绪")
