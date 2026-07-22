import sqlite3, json, math, random, os
from collections import Counter
from datetime import datetime

DB = r"C:\Users\Administrator\Documents\彩票选票机\data\lottery.db"

def main():
    conn = sqlite3.connect(DB)
    c = conn.execute("SELECT red1,red2,red3,red4,red5,red6,blue FROM ssq ORDER BY period")
    ssq = [(sorted([int(r[i]) for i in range(6)]), int(r[6])) for r in c.fetchall()]
    conn.close()
    N = len(ssq)
    
    freq = Counter()
    for reds, _ in ssq:
        for n in reds: freq[n] += 1
    exp_r = N * 6.0 / 33
    std_r = math.sqrt(N * 6.0 / 33 * 27.0 / 33)
    weights = {n: 1.0 / (1.0 + math.exp(-((freq[n] - exp_r) / std_r) * 0.7)) for n in range(1, 34)}
    
    pos = [[] for _ in range(6)]
    for reds, _ in ssq:
        for i, r in enumerate(reds): pos[i].append(r)
    pm = [(sum(v) / N, math.sqrt(sum((x - sum(v)/N) ** 2 for x in v) / N)) for v in pos]
    
    bfreq = Counter(b for _, b in ssq)
    
    rng = random.Random(42)
    last = ssq[-1][0]
    pool = set()
    for n in last:
        for d in [-2, -1, 0, 1, 2]:
            v = n + d
            if 1 <= v <= 33: pool.add(v)
    plist = sorted(pool)
    
    cans = []
    for _ in range(500):
        if len(plist) >= 6:
            cans.append(sorted(rng.sample(plist, 6)))
    for _ in range(500):
        combo = [max(1, min(33, int(rng.gauss(pm[i][0], max(pm[i][1], 2))))) for i in range(6)]
        fixed = []
        for v in sorted(combo):
            while v in fixed: v = min(v + 1, 33)
            if v <= 33: fixed.append(v)
        if len(set(fixed)) == 6:
            cans.append(fixed)
    
    scored = []
    for c in cans:
        sc = sorted(c)
        s = sum(weights.get(n, 1) for n in c) / 6 * 0.5
        ps = sum(-0.5 * ((sc[i] - pm[i][0]) / max(pm[i][1], 0.01)) ** 2 for i in range(6))
        s += max(0, 1 + ps / 10) * 0.25
        ds = sum(-0.5 * ((sc[i+1] - sc[i] - 5) / 3.8) ** 2 for i in range(5)) / 5
        s += max(0, 1 + ds) * 0.15
        s += sum(1 for n in c if any(abs(n - ln) <= 2 for ln in last)) / 6 * 0.1
        scored.append((s, tuple(c)))
    
    scored.sort(reverse=True)
    seen = set()
    res = []
    for s, c in scored:
        if c not in seen:
            seen.add(c)
            res.append((s, list(c)))
        if len(res) >= 5: break
    
    top_b = sorted(range(1, 17), key=lambda b: bfreq.get(b, 0), reverse=True)[:3]
    preds = [{"rank": i+1, "reds": res[i][1], "blue": top_b[i%3], "score": round(res[i][0], 3)} for i in range(min(5, len(res)))]
    
    print("=" * 50)
    print("V5.2 SSQ PREDICTIONS")
    print("=" * 50)
    for p in preds:
        print("Rank #%d: %s + Blue:%d (Score:%.3f)" % (p["rank"], p["reds"], p["blue"], p["score"]))
    
    wb = []
    for idx in range(max(0, N-11), N-1):
        rng2 = random.Random(idx)
        past = ssq[:idx+1]
        actual = ssq[idx+1]
        last2 = past[-1][0]
        p2 = set()
        for n2 in last2:
            for d2 in [-2, -1, 0, 1, 2]:
                v2 = n2 + d2
                if 1 <= v2 <= 33: p2.add(v2)
        pl2 = sorted(p2)
        if len(pl2) >= 6:
            best = sorted(rng2.sample(pl2, 6))
        else:
            best = sorted(rng2.sample(range(1, 34), 6))
        pbf = Counter(b for _, b in past)
        pb = max(range(1, 17), key=lambda b: pbf.get(b, 0))
        wb.append((len(set(best) & set(actual[0])), int(pb == actual[1])))
    
    if wb:
        th = sum(r[0] for r in wb)
        tb = sum(r[1] for r in wb)
        nw = len(wb)
        print("\nWalkback %d: avg_red=%.1f/6 blue=%.0f%%" % (nw, th/nw, tb/nw*100))
    
    pf = r"C:\Users\Administrator\Documents\彩票选票机\data\pred_history.json"
    ex = json.load(open(pf, encoding="utf-8")) if os.path.exists(pf) else []
    ex.append({
        "timestamp": datetime.now().isoformat(),
        "version": "5.2",
        "ssq_predictions": preds,
        "walkback": {"n": len(wb) if wb else 0, "avg_red": round(th/nw if wb and nw>0 else 0, 2), "blue_acc": round(tb/nw if wb and nw>0 else 0, 3)} if wb else {}
    })
    with open(pf, "w", encoding="utf-8") as f:
        json.dump(ex, f, indent=2, ensure_ascii=False)
    print("Saved!")

if __name__ == "__main__":
    main()
