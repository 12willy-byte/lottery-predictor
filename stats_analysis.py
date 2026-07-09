# -*- coding: utf-8 -*-
"""
统计学全中规律发现引擎
- 条件概率矩阵
- 多维命中条件分析
- 统计显著性检验
- 特征回归建模
- 周期分解
"""
import sys, os, json, time, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collections import Counter, defaultdict
from database import get_all_ssq, get_all_dlt
from strategy_discovery import fast_extract_features


def analyze_conditional_hits(lottery_type="ssq"):
    """条件概率分析：当某个特征命中时，其他特征命中的概率"""
    if lottery_type == "ssq":
        raw = get_all_ssq()
        num_range, pick_cnt = 33, 6
        draws = [[d["red%d" % j] for j in range(1, 7)] for d in raw]
    else:
        raw = get_all_dlt()
        num_range, pick_cnt = 35, 5
        draws = [[d["front%d" % j] for j in range(1, 6)] for d in raw]
    
    total = len(draws)
    min_train = 100
    
    # 收集每期的预测命中情况
    records = []
    for i in range(min_train, total):
        train = draws[:i]
        actual = set(draws[i])
        feats = fast_extract_features(train, num_range, pick_cnt)
        if feats is None:
            continue
        
        rec = {
            "period": raw[i]["period"],
            "freq_hit": len(set(feats["sorted_by_freq"][:pick_cnt]) & actual),
            "om_hit": len(set(feats["sorted_by_om"][:pick_cnt]) & actual),
            "edge_hit": len(set(feats["sorted_by_edge"][:pick_cnt]) & actual),
            "comb_hit": len(set(feats["combined_top"][:pick_cnt]) & actual),
            "repeat_hit": len(set(draws[i-1]) & actual) if i > 0 else 0,
            "prime_hit": len(feats["prime_set"] & actual),
            "actual_span": max(draws[i]) - min(draws[i]),
            "actual_sum": sum(draws[i]),
            "actual_odd": sum(1 for x in draws[i] if x % 2 == 1),
            "actual_seq": sum(1 for j in range(len(draws[i])-1) if sorted(draws[i])[j+1] == sorted(draws[i])[j] + 1),
        }
        records.append(rec)
    
    print(f"\n  {'='*60}")
    print(f"  {lottery_type.upper()} 条件概率分析 ({len(records)}期)")
    print(f"  {'='*60}")
    
    # 1) 多维命中分布
    print(f"\n  命中数分布:")
    hit_counts = Counter()
    for r in records:
        total_hits = r["freq_hit"] + r["om_hit"] + r["edge_hit"] + r["comb_hit"]
        # 用最好的单策略命中数
        best = max(r["freq_hit"], r["om_hit"], r["edge_hit"], r["comb_hit"])
        hit_counts[best] += 1
    
    for k in sorted(hit_counts):
        pct = hit_counts[k] / len(records) * 100
        bar = "#" * int(pct / 2)
        print(f"    {k}个命中: {hit_counts[k]:>5}期 ({pct:5.1f}%) {bar}")
    
    # 2) 条件概率：当A命中≥2时，B也命中≥1的概率
    print(f"\n  条件概率矩阵 (行=条件, 列=结果, 值=条件满足时结果≥1命中的概率%):")
    strategies = ["freq", "om", "edge", "comb"]
    labels = ["频率", "遗漏", "边码", "综合"]
    
    # Header
    print(f"    {'':>8}", end="")
    for l in labels:
        print(f" {l:>8}", end="")
    print()
    
    for si, (s1, l1) in enumerate(zip(strategies, labels)):
        print(f"    {l1:>8}", end="")
        cond_true = [r for r in records if r[f"{s1}_hit"] >= 1]
        for s2, l2 in zip(strategies, labels):
            if s1 == s2:
                print(f" {'---':>8}", end="")
            else:
                both = sum(1 for r in cond_true if r[f"{s2}_hit"] >= 1)
                pct = both / max(len(cond_true), 1) * 100
                print(f" {pct:>7.1f}%", end="")
        print()
    
    # 3) 多命中(≥3)的条件分析
    print(f"\n  多命中(≥3)的触发条件:")
    high_hit = [r for r in records if max(r["freq_hit"], r["om_hit"], r["edge_hit"], r["comb_hit"]) >= 3]
    low_hit = [r for r in records if max(r["freq_hit"], r["om_hit"], r["edge_hit"], r["comb_hit"]) <= 1]
    
    print(f"    高命中期(≥3): {len(high_hit)}期 ({len(high_hit)/len(records)*100:.1f}%)")
    print(f"    低命中期(≤1): {len(low_hit)}期 ({len(low_hit)/len(records)*100:.1f}%)")
    
    # 4) 重号与命中的关系
    print(f"\n  重号数 vs 预测命中率:")
    for rp in range(pick_cnt + 1):
        subset = [r for r in records if r["repeat_hit"] == rp]
        if subset:
            avg_hit = sum(max(r["freq_hit"], r["om_hit"], r["comb_hit"]) for r in subset) / len(subset)
            print(f"    重号{rp}个: {len(subset)}期, 均命中{avg_hit:.2f}")
    
    # 5) 跨度与命中
    print(f"\n  跨度 vs 命中率:")
    span_bins = [(0, 10), (11, 15), (16, 20), (21, 25), (26, 32), (33, 99)]
    for lo, hi in span_bins:
        subset = [r for r in records if lo <= r["actual_span"] <= hi]
        if subset:
            avg = sum(max(r["freq_hit"], r["om_hit"], r["comb_hit"]) for r in subset) / len(subset)
            print(f"    跨度{lo}-{hi}: {len(subset)}期, 均命中{avg:.2f}")
    
    return records


def correlation_analysis(records, lottery_type):
    """相关性分析 + 特征回归"""
    print(f"\n  {'='*60}")
    print(f"  {lottery_type.upper()} 特征相关性分析")
    print(f"  {'='*60}")
    
    # 特征向量
    features = []
    targets = []
    
    for r in records:
        feat_vec = [
            r["freq_hit"],
            r["om_hit"],
            r["edge_hit"],
            r["comb_hit"],
            r["repeat_hit"],
            r["prime_hit"],
            r["actual_span"],
            r["actual_sum"],
            r["actual_odd"],
            r["actual_seq"],
        ]
        features.append(feat_vec)
        targets.append(max(r["freq_hit"], r["om_hit"], r["edge_hit"], r["comb_hit"]))
    
    n = len(records)
    feat_names = ["频率命中", "遗漏命中", "边码命中", "综合命中", "重号数", "质数数", "跨度", "和值", "奇数数", "连号数"]
    
    # Pearson 相关系数矩阵
    print(f"\n  Pearson 相关系数 (特征 vs 最佳命中数):")
    for i, name in enumerate(feat_names):
        x = [f[i] for f in features]
        y = targets
        # Pearson r
        mx = sum(x) / n
        my = sum(y) / n
        sx = math.sqrt(sum((xi - mx)**2 for xi in x) / n)
        sy = math.sqrt(sum((yi - my)**2 for yi in y) / n)
        if sx > 0 and sy > 0:
            r = sum((x[j] - mx) * (y[j] - my) for j in range(n)) / (n * sx * sy)
            sig = "***" if abs(r) > 0.3 else ("**" if abs(r) > 0.2 else ("*" if abs(r) > 0.1 else ""))
            bar = "#" * int(abs(r) * 40) if r > 0 else "." * int(abs(r) * 40)
            direction = "正相关" if r > 0 else "负相关"
            print(f"    {name:<8} r={r:+.3f} {sig:<3} {direction} {bar}")
    
    # 多元回归近似（简化为加权平均）
    print(f"\n  线性回归权重 (标准化):")
    reg_weights = {}
    all_x = []
    for i, name in enumerate(feat_names):
        x = [f[i] for f in features]
        mx = sum(x) / n
        sx = math.sqrt(sum((xi - mx)**2 for xi in x) / n)
        if sx > 0:
            x_std = [(xi - mx) / sx for xi in x]
            # 简单OLS: beta = corr(x, y) * std(y) / std(x) ≈ corr(x, y) since we normalize
            my = sum(targets) / n
            sy2 = math.sqrt(sum((t - my)**2 for t in targets) / n)
            cov = sum(x_std[j] * (targets[j] - my) for j in range(n)) / n
            beta = cov / sy2 if sy2 > 0 else 0
            reg_weights[name] = round(beta, 3)
        all_x.append(x)
    
    for name, w in sorted(reg_weights.items(), key=lambda x: -abs(x[1])):
        bar = "#" * int(abs(w) * 100) if w > 0 else "." * int(abs(w) * 100)
        print(f"    {name:<8} β={w:+.3f} {bar}")
    
    return reg_weights


def regime_analysis(records, lottery_type):
    """体制分析：是否存在某些条件下策略更有效"""
    print(f"\n  {'='*60}")
    print(f"  {lottery_type.upper()} 体制分析")
    print(f"  {'='*60}")
    
    n = len(records)
    
    # 按时期分段
    segments = [
        ("早期 (03001-10000)", lambda r: int(r["period"]) < 10000),
        ("中期 (10001-15000)", lambda r: 10000 <= int(r["period"]) < 15000),
        ("后期1 (15001-20000)", lambda r: 15000 <= int(r["period"]) < 20000),
        ("后期2 (20001-25000)", lambda r: 20000 <= int(r["period"]) < 25000),
        ("近期 (25001+)", lambda r: int(r["period"]) >= 25000),
    ]
    
    print(f"\n  不同时期的策略效果:")
    print(f"  {'时期':<25} {'期数':>6} {'频率均命中':>10} {'遗漏均命中':>10} {'综合均命中':>10}")
    
    for seg_name, seg_fn in segments:
        subset = [r for r in records if seg_fn(r)]
        if subset:
            avg_f = sum(r["freq_hit"] for r in subset) / len(subset)
            avg_o = sum(r["om_hit"] for r in subset) / len(subset)
            avg_c = sum(r["comb_hit"] for r in subset) / len(subset)
            print(f"  {seg_name:<25} {len(subset):>6} {avg_f:>10.3f} {avg_o:>10.3f} {avg_c:>10.3f}")
    
    # 滚动窗口分析
    window = 200
    print(f"\n  滚动窗口分析 (窗口={window}期):")
    print(f"  {'窗口':>8} {'频率均命中':>12} {'遗漏均命中':>12} {'趋势':>20}")
    
    rolling = []
    for i in range(window, n):
        subset = records[i-window:i]
        avg_f = sum(r["freq_hit"] for r in subset) / window
        avg_o = sum(r["om_hit"] for r in subset) / window
        rolling.append((i, avg_f, avg_o))
    
    # 找最好和最差的窗口
    rolling.sort(key=lambda x: -x[1])
    for label, idx in [("最佳窗口", 0), ("最差窗口", 1), ("最近窗口", -1)]:
        i, af, ao = rolling[idx]
        period = records[i]["period"]
        trend = "频率优" if af > ao else ("遗漏优" if ao > af else "持平")
        print(f"    {label}: 期号{period} 频率{af:.3f} 遗漏{ao:.3f} {trend}")


def main():
    print("=" * 60)
    print("  统计学全中规律发现引擎")
    print("  条件概率 · 相关性 · 回归 · 体制分析")
    print("=" * 60)
    
    for lt in ["ssq", "dlt"]:
        records = analyze_conditional_hits(lt)
        reg = correlation_analysis(records, lt)
        regime_analysis(records, lt)
    
    print("\n" + "=" * 60)
    print("  分析完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
