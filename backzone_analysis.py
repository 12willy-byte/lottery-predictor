# -*- coding: utf-8 -*-
"""后区深度分析 - SSQ蓝球 + DLT后区 命中率最大化"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collections import Counter, defaultdict
from database import get_all_ssq, get_all_dlt


def analyze_ssq_blue():
    """SSQ 蓝球 (1-16) 深度分析"""
    data = get_all_ssq()
    blues = [d["blue"] for d in data]
    total = len(blues)
    
    print("\n" + "=" * 60)
    print("  SSQ 蓝球深度分析 (%d期)" % total)
    print("=" * 60)
    
    # 1) 频率分布
    print("\n[1] 频率分布:")
    freq = Counter(blues)
    for n in range(1, 17):
        cnt = freq.get(n, 0)
        pct = cnt / total * 100
        bar = "#" * int(pct * 4)
        print("    蓝%2d: %4d期 (%5.1f%%) %s" % (n, cnt, pct, bar))
    
    # 2) 遗漏分析
    print("\n[2] 当前遗漏 + 历史回补:")
    latest_blue = blues[-1]
    omission = {}
    for n in range(1, 17):
        if n == latest_blue:
            omission[n] = 0
        else:
            c = 0
            for b in reversed(blues[:-1]):
                if b == n: break
                c += 1
            omission[n] = c + 1
    
    # 历史最大遗漏
    max_omission = {}
    for n in range(1, 17):
        max_o = 0
        cur = 0
        for b in blues:
            if b == n:
                max_o = max(max_o, cur)
                cur = 0
            else:
                cur += 1
        max_omission[n] = max(max_o, cur)
    
    for n in range(1, 17):
        cur = omission[n]
        mx = max_omission[n]
        ratio = cur / max(mx, 1) * 100
        alert = " <<< 接近历史最大!" if ratio > 90 else ""
        print("    蓝%2d: 遗漏%3d期 | 历史最大%3d | %.0f%%%s" % (n, cur, mx, ratio, alert))
    
    # 3) 奇偶/大小模式
    print("\n[3] 奇偶/大小模式:")
    odd_even = Counter()
    big_small = Counter()
    for b in blues:
        oe = "奇" if b % 2 == 1 else "偶"
        bs = "大" if b >= 9 else "小"
        odd_even[oe] += 1
        big_small[bs] += 1
    print("    奇数: %d (%.1f%%)  偶数: %d (%.1f%%)" % (
        odd_even.get("奇",0), odd_even.get("奇",0)/total*100,
        odd_even.get("偶",0), odd_even.get("偶",0)/total*100))
    print("    大数(9-16): %d (%.1f%%)  小数(1-8): %d (%.1f%%)" % (
        big_small.get("大",0), big_small.get("大",0)/total*100,
        big_small.get("小",0), big_small.get("小",0)/total*100))
    
    # 4) 跟随模式
    print("\n[4] 蓝球跟随 (上期出X后, 下期出Y的概率):")
    follow = defaultdict(Counter)
    for i in range(1, len(blues)):
        follow[blues[i-1]][blues[i]] += 1
    
    # 显示当前上期蓝球的跟随分布
    prev = blues[-1]
    print("    上期蓝球=%d, 历史跟随分布:" % prev)
    for next_b, cnt in follow[prev].most_common(5):
        total_follow = sum(follow[prev].values())
        print("      -> %2d: %3d次 (%.1f%%)" % (next_b, cnt, cnt/total_follow*100))
    
    # 5) 连续出现模式
    print("\n[5] 连续出现分析:")
    streaks = []
    cur_streak = 1
    for i in range(1, len(blues)):
        if blues[i] == blues[i-1]:
            cur_streak += 1
        else:
            if cur_streak > 1:
                streaks.append(cur_streak)
            cur_streak = 1
    streak_counter = Counter(streaks)
    print("    历史连出: %s" % dict(sorted(streak_counter.items())))
    
    # 6) 全量倒退验证
    print("\n[6] 全量倒退验证 (min_train=100):")
    strategies = {
        "频率前1": lambda h: Counter(h).most_common(1)[0][0],
        "遗漏前1": lambda h: max(range(1,17), key=lambda n: sum(1 for b in reversed(h) if b != n)),
        "跟随前1": lambda h: follow.get(h[-1], Counter()).most_common(1)[0][0] if follow.get(h[-1]) else 1,
    }
    
    # 更好的遗漏计算
    def top_omission(history):
        om = {}
        latest = history[-1]
        for n in range(1, 17):
            if n == latest: om[n] = 0
            else:
                c = 0
                for b in reversed(history[:-1]):
                    if b == n: break
                    c += 1
                om[n] = c + 1
        return max(om, key=om.get)
    
    # 频率+遗漏混合
    def hybrid_predict(history):
        freq = Counter(history[-50:])
        om = {}
        latest = history[-1]
        for n in range(1, 17):
            if n == latest: om[n] = 0
            else:
                c = 0
                for b in reversed(history[:-1]):
                    if b == n: break
                    c += 1
                om[n] = c + 1
        scores = {}
        for n in range(1, 17):
            scores[n] = freq.get(n, 0) * 0.6 + om.get(n, 0) * 0.4
        return max(scores, key=scores.get)
    
    results = {}
    for name, fn in [
        ("频率", lambda h: Counter(h[-50:]).most_common(1)[0][0]),
        ("遗漏", top_omission),
        ("跟随", lambda h: follow.get(h[-1], Counter()).most_common(1)[0][0] if follow.get(h[-1]) and sum(follow[h[-1]].values()) >= 3 else Counter(h[-50:]).most_common(1)[0][0]),
        ("混合(频+遗)", hybrid_predict),
    ]:
        hits = 0
        tests = 0
        for i in range(100, len(blues)):
            pred = fn(blues[:i])
            if pred == blues[i]:
                hits += 1
            tests += 1
        rate = hits / tests * 100
        results[name] = {"hits": hits, "tests": tests, "rate": round(rate, 1)}
        bar = "#" * int(rate / 2)
        print("    %-12s: %d/%d = %.1f%% %s" % (name, hits, tests, rate, bar))
    
    # 7) 推荐
    print("\n[7] 本期蓝球推荐:")
    # 频率
    freq_top = Counter(blues[-100:]).most_common(3)
    print("    频率: %s" % [n for n, _ in freq_top])
    # 遗漏
    top_om = sorted(range(1,17), key=lambda n: -omission[n])
    print("    遗漏前3: %s" % top_om[:3])
    # 跟随
    if sum(follow[prev].values()) >= 3:
        print("    跟随(上期=%d): %s" % (prev, [n for n, _ in follow[prev].most_common(3)]))
    # 混合
    mixed = {}
    for n in range(1, 17):
        mixed[n] = freq.get(n, 0) * 0.5 + omission[n] * 0.3
        if sum(follow[prev].values()) > 0:
            mixed[n] += follow[prev].get(n, 0) / sum(follow[prev].values()) * 20
    top_mixed = sorted(mixed, key=lambda n: -mixed[n])
    print("    综合推荐前3: %s" % top_mixed[:3])
    
    return results, top_mixed[:5]


def analyze_dlt_back():
    """DLT 后区 (2个号码, 1-12) 深度分析"""
    data = get_all_dlt()
    backs = [(d["back1"], d["back2"]) for d in data]
    total = len(backs)
    
    print("\n" + "=" * 60)
    print("  DLT 后区深度分析 (%d期)" % total)
    print("=" * 60)
    
    # 1) 单号频率
    print("\n[1] 单号频率分布:")
    flat = [b for pair in backs for b in pair]
    freq = Counter(flat)
    for n in range(1, 13):
        cnt = freq.get(n, 0)
        pct = cnt / len(flat) * 100
        bar = "#" * int(pct * 2)
        print("    号%2d: %4d次 (%5.1f%%) %s" % (n, cnt, pct, bar))
    
    # 2) 对子频率 (C(12,2)=66种)
    print("\n[2] 对子频率 Top 10:")
    pair_freq = Counter(backs)
    for (a, b), cnt in pair_freq.most_common(10):
        pct = cnt / total * 100
        print("    (%2d,%2d): %4d次 (%.1f%%)" % (a, b, cnt, pct))
    
    # 3) 遗漏
    print("\n[3] 当前遗漏:")
    latest = backs[-1]
    omission = {}
    for n in range(1, 13):
        if n in latest: omission[n] = 0
        else:
            c = 0
            for pair in reversed(backs[:-1]):
                if n in pair: break
                c += 1
            omission[n] = c + 1
    
    for n in range(1, 13):
        cur = omission[n]
        alert = " <<< 超30期!" if cur > 30 else ""
        print("    号%2d: 遗漏%3d期%s" % (n, cur, alert))
    
    # 4) 和值分布
    print("\n[4] 后区和值分布:")
    sums = [a + b for a, b in backs]
    sum_counter = Counter(sums)
    avg_sum = sum(sums) / len(sums)
    print("    平均和值: %.1f (范围2-23)" % avg_sum)
    for s in range(3, 22):
        cnt = sum_counter.get(s, 0)
        if cnt > 0:
            bar = "#" * (cnt // 10)
            print("    和%2d: %4d %s" % (s, cnt, bar))
    
    # 5) 奇偶组合
    print("\n[5] 奇偶组合分布:")
    oe_counter = Counter()
    for a, b in backs:
        oa = a % 2; ob = b % 2
        oe_counter[(oa, ob)] += 1
    labels = {(1,1):"奇奇", (0,0):"偶偶", (1,0):"奇偶", (0,1):"奇偶"}
    for (oa, ob), cnt in oe_counter.most_common():
        label = labels.get((oa, ob), "??")
        pct = cnt / total * 100
        print("    %s: %d (%.1f%%)" % (label, cnt, pct))
    
    # 6) 全量倒退验证
    print("\n[6] 全量倒退验证 (min_train=100):")
    
    def predict_freq(history):
        flat_h = [b for p in history for b in p]
        top = [n for n, _ in Counter(flat_h[-100:]).most_common(2)]
        return (min(top), max(top))
    
    def predict_omission(history):
        latest_h = history[-1]
        om = {}
        for n in range(1, 13):
            if n in latest_h: om[n] = 0
            else:
                c = 0
                for pair in reversed(history[:-1]):
                    if n in pair: break
                    c += 1
                om[n] = c + 1
        top = sorted(om, key=lambda n: -om[n])[:2]
        return (min(top), max(top))
    
    def predict_hybrid(history):
        flat_h = [b for p in history for b in p]
        freq = Counter(flat_h[-100:])
        latest_h = history[-1]
        om = {}
        for n in range(1, 13):
            if n in latest_h: om[n] = 0
            else:
                c = 0
                for pair in reversed(history[:-1]):
                    if n in pair: break
                    c += 1
                om[n] = c + 1
        scores = {}
        for n in range(1, 13):
            scores[n] = freq.get(n, 0) * 0.5 + om.get(n, 0) * 0.5
        top = sorted(scores, key=lambda n: -scores[n])[:2]
        return (min(top), max(top))
    
    for name, fn in [
        ("频率", predict_freq),
        ("遗漏", predict_omission),
        ("混合", predict_hybrid),
    ]:
        hits_0 = 0; hits_1 = 0; hits_2 = 0
        tests = 0
        for i in range(100, len(backs)):
            pred = fn(backs[:i])
            actual = backs[i]
            h = (1 if pred[0] in actual else 0) + (1 if pred[1] in actual else 0)
            if h == 0: hits_0 += 1
            elif h == 1: hits_1 += 1
            else: hits_2 += 1
            tests += 1
        avg = (hits_1 + 2*hits_2) / tests
        print("    %-6s: 0中=%d(%.0f%%) 1中=%d(%.0f%%) 2中=%d(%.0f%%) 均=%.2f" % (
            name, hits_0, hits_0/tests*100, hits_1, hits_1/tests*100, hits_2, hits_2/tests*100, avg))
    
    # 7) 推荐
    print("\n[7] 本期后区推荐:")
    scores = {}
    for n in range(1, 13):
        scores[n] = freq.get(n, 0) * 0.5 + omission.get(n, 0) * 0.5
    top5 = sorted(scores, key=lambda n: -scores[n])[:5]
    print("    单号推荐: %s" % top5)
    
    # 推荐具体对子
    best_pairs = []
    for a in top5:
        for b in top5:
            if a < b:
                score = scores[a] + scores[b]
                # 罚分: 避免同奇偶
                if a % 2 == b % 2:
                    score *= 0.9
                # 和值在7-17之间加分
                s = a + b
                if 7 <= s <= 17:
                    score *= 1.05
                best_pairs.append(((a, b), round(score, 1)))
    best_pairs.sort(key=lambda x: -x[1])
    
    print("    推荐对子 Top 5:")
    for (a, b), score in best_pairs[:5]:
        print("      (%2d,%2d) 得分=%.1f" % (a, b, score))
    
    return top5, best_pairs[:5]


print("=" * 60)
print("  后区深度分析引擎")
print("  SSQ蓝球(1/16) + DLT后区(2/12)")
print("=" * 60)

ssq_result, ssq_top = analyze_ssq_blue()
dlt_nums, dlt_pairs = analyze_dlt_back()
