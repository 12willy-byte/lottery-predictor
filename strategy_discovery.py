# -*- coding: utf-8 -*-
"""
策略全量倒退分析引擎
逐期回滚：对每一期，用该期之前的所有历史数据训练，预测当期，对比实际开奖
汇总所有期的结果，自动发现最优策略维度组合
"""
import sys, os, json, time, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collections import Counter, defaultdict
from database import get_all_ssq, get_all_dlt


def fast_extract_features(draws, num_range, pick_cnt):
    """从历史序列中快速提取所有策略维度的特征"""
    n = len(draws)
    if n < 30:
        return None
    
    recent_n = min(50, n)
    recent = draws[-recent_n:]
    all_nums = list(range(1, num_range + 1))
    latest = draws[-1]
    latest_set = set(latest)
    
    # ---- 频率统计 ----
    freq = Counter()
    for d in recent:
        for x in d: freq[x] += 1
    sorted_by_freq = sorted(all_nums, key=lambda x: -freq.get(x, 0))
    
    # ---- 遗漏值 ----
    omission = {}
    for x in all_nums:
        if x in latest_set:
            omission[x] = 0
        else:
            c = 0
            for d in reversed(draws[:-1]):
                if x in d: break
                c += 1
            omission[x] = c + 1
    sorted_by_om = sorted(all_nums, key=lambda x: -omission[x])
    
    # ---- 尾数分布 ----
    tail_freq = Counter()
    for d in recent:
        for x in d: tail_freq[x % 10] += 1
    
    # ---- 跨度 ----
    spans = [max(d) - min(d) for d in recent]
    span_counter = Counter(spans)
    common_span = span_counter.most_common(3)
    
    # ---- 奇偶 ----
    odd_ratios = Counter()
    for d in recent:
        odd_ratios[sum(1 for x in d if x % 2 == 1)] += 1
    
    # ---- 大小 ----
    mid = num_range // 2 + 1
    big_ratios = Counter()
    for d in recent:
        big_ratios[sum(1 for x in d if x >= mid)] += 1
    
    # ---- 重号 ----
    repeats = []
    for i in range(1, len(recent)):
        repeats.append(len(set(recent[i-1]) & set(recent[i])))
    avg_repeat = sum(repeats) / max(len(repeats), 1) if repeats else 0
    
    # ---- 012路 ----
    mod3_total = Counter()
    for d in recent:
        for x in d: mod3_total[x % 3] += 1
    t = sum(mod3_total.values()) or 1
    mod3_ratios = {k: v/t for k, v in mod3_total.items()}
    cold_mod = min(mod3_ratios, key=mod3_ratios.get) if mod3_ratios else 0
    
    # ---- 质数 ----
    prime_set = {p for p in [2,3,5,7,11,13,17,19,23,29,31] if p <= num_range}
    prime_ratios = []
    for d in recent:
        prime_ratios.append(sum(1 for x in d if x in prime_set))
    avg_prime = sum(prime_ratios) / max(len(prime_ratios), 1)
    
    # ---- 和值 ----
    sums = [sum(d) for d in recent]
    avg_sum = sum(sums) / max(len(sums), 1)
    sum_std = math.sqrt(sum((s - avg_sum)**2 for s in sums) / max(len(sums), 1))
    
    # ---- AC值 ----
    ac_vals = []
    for d in recent[-30:]:
        s = sorted(d)
        diffs = set()
        for i in range(len(s)):
            for j in range(i+1, len(s)):
                diffs.add(s[j] - s[i])
        ac_vals.append(len(diffs) - (len(s) - 1))
    avg_ac = sum(ac_vals) / max(len(ac_vals), 1) if ac_vals else 0
    
    # ---- 边码 ----
    edge_hits = Counter()
    for i in range(1, len(recent)):
        prev_set = set(recent[i-1])
        curr_set = set(recent[i])
        for x in prev_set:
            for dx in [-1, 1]:
                nx = x + dx
                if 1 <= nx <= num_range and nx not in prev_set and nx in curr_set:
                    edge_hits[nx] += 1
    sorted_by_edge = sorted(all_nums, key=lambda n: -edge_hits.get(n, 0))
    
    # ---- 连号 ----
    cons_vals = []
    for d in recent:
        s = sorted(d)
        cons_vals.append(sum(1 for i in range(len(s)-1) if s[i+1] == s[i] + 1))
    avg_cons = sum(cons_vals) / max(len(cons_vals), 1)
    
    # ---- 位置频次 ----
    pos_freqs = [Counter() for _ in range(pick_cnt)]
    for d in recent:
        sd = sorted(d)
        for j in range(pick_cnt):
            pos_freqs[j][sd[j]] += 1
    
    # ---- 振幅 ----
    amp_counter = Counter()
    for i in range(1, len(recent)):
        s_prev = sorted(recent[i-1])
        s_curr = sorted(recent[i])
        for j in range(pick_cnt):
            amp_counter[s_curr[j] - s_prev[j]] += 1
    
    # ---- 综合评分 ----
    num_scores = {n: 0.0 for n in all_nums}
    for rank, n in enumerate(sorted_by_freq):
        num_scores[n] += max(0, 20 - rank * 0.6)
    for rank, n in enumerate(sorted_by_om):
        num_scores[n] += max(0, 15 - rank * 0.45)
    for rank, n in enumerate(sorted_by_edge):
        num_scores[n] += max(0, 8 - rank * 0.6)
    for n in all_nums:
        if n % 3 == cold_mod:
            num_scores[n] += 4
        if n in prime_set:
            num_scores[n] += avg_prime * 1.5
    combined_top = sorted(all_nums, key=lambda n: -num_scores[n])
    
    # ---- 区间覆盖 ----
    zone_size = max(5, num_range // 4)
    zones = [(i, min(i+zone_size-1, num_range)) for i in range(1, num_range+1, zone_size)]
    zone_counts = []
    for d in recent[-20:]:
        zc = [0] * len(zones)
        for x in d:
            for zi, (lo, hi) in enumerate(zones):
                if lo <= x <= hi:
                    zc[zi] += 1
                    break
        zone_counts.append(zc)
    
    return {
        "sorted_by_freq": sorted_by_freq,
        "sorted_by_om": sorted_by_om,
        "sorted_by_edge": sorted_by_edge,
        "combined_top": combined_top,
        "mod3_ratios": mod3_ratios,
        "cold_mod": cold_mod,
        "prime_set": prime_set,
        "avg_prime": avg_prime,
        "avg_repeat": avg_repeat,
        "avg_cons": avg_cons,
        "avg_sum": avg_sum,
        "sum_std": sum_std,
        "avg_ac": avg_ac,
        "common_span": common_span,
        "odd_ratios": dict(odd_ratios),
        "big_ratios": dict(big_ratios),
        "num_scores": num_scores,
        "pos_freqs": pos_freqs,
        "amp_counter": dict(amp_counter),
        "zone_counts": zone_counts,
        "zones": zones,
    }


def evaluate_topk(candidates, actual_set, k):
    """评估前k个候选命中几个"""
    return len(set(candidates[:k]) & actual_set)


def walkback_full(lottery_type="ssq", min_train=100, checkpoint_every=100):
    """
    全量逐期倒退分析 - 不采样
    对每一期: 训练→预测→对比→累积
    """
    if lottery_type == "ssq":
        raw = get_all_ssq()
        num_range, pick_cnt = 33, 6
        bonus_range = 16
        draws = [[d["red%d" % j] for j in range(1, 7)] for d in raw]
        blues = [d["blue"] for d in raw]
    else:
        raw = get_all_dlt()
        num_range, pick_cnt = 35, 5
        bonus_range = 12
        draws = [[d["front%d" % j] for j in range(1, 6)] for d in raw]
        backs = [[d["back1"], d["back2"]] for d in raw]
    
    total = len(draws)
    periods = [d["period"] for d in raw]
    
    print(f"\n{'='*60}")
    print(f"  {lottery_type.upper()} 全量逐期倒退分析")
    print(f"  总期数: {total}  训练起点: {min_train}  测试期数: {total - min_train}")
    print(f"{'='*60}\n")
    
    # 累积器：对每个维度，记录每期命中数
    accum = defaultdict(list)
    # 额外：记录位置偏差、遗漏模式等
    extra_accum = defaultdict(list)
    
    t_start = time.time()
    test_count = 0
    
    for i in range(min_train, total):
        train_draws = draws[:i]
        actual = draws[i]
        actual_set = set(actual)
        actual_sorted = sorted(actual)
        period = periods[i]
        
        feats = fast_extract_features(train_draws, num_range, pick_cnt)
        if feats is None:
            continue
        
        # ---- 12个维度逐一评估 ----
        
        # 1) 频率前k
        hits = evaluate_topk(feats["sorted_by_freq"], actual_set, pick_cnt)
        accum["freq"].append(hits)
        
        # 2) 遗漏前k
        hits = evaluate_topk(feats["sorted_by_om"], actual_set, pick_cnt)
        accum["omission"].append(hits)
        
        # 3) 边码前k
        hits = evaluate_topk(feats["sorted_by_edge"], actual_set, pick_cnt)
        accum["edge"].append(hits)
        
        # 4) 综合评分前k
        hits = evaluate_topk(feats["combined_top"], actual_set, pick_cnt)
        accum["combined"].append(hits)
        
        # 5) 频率前2k（宽池）
        hits = evaluate_topk(feats["sorted_by_freq"], actual_set, pick_cnt*2)
        accum["freq_wide"].append(hits)
        
        # 6) 遗漏前2k
        hits = evaluate_topk(feats["sorted_by_om"], actual_set, pick_cnt*2)
        accum["omission_wide"].append(hits)
        
        # 7) 综合前2k
        hits = evaluate_topk(feats["combined_top"], actual_set, pick_cnt*2)
        accum["combined_wide"].append(hits)
        
        # 8) 质数命中
        prime_set = feats["prime_set"]
        prime_hits = len(prime_set & actual_set)
        accum["prime"].append(prime_hits)
        
        # 9) 012路冷路命中
        cold_mod = feats["cold_mod"]
        cold_nums = [n for n in range(1, num_range+1) if n % 3 == cold_mod]
        accum["mod3_cold"].append(len(set(cold_nums) & actual_set))
        
        # 10) 重号
        prev_set = set(train_draws[-1]) if train_draws else set()
        accum["repeat"].append(len(prev_set & actual_set))
        
        # 11) 连号
        s = sorted(actual)
        cons = sum(1 for j in range(len(s)-1) if s[j+1] == s[j] + 1)
        accum["consecutive"].append(cons)
        
        # 12) 位置相关 - 每个位置中高频号
        pos_freqs = feats["pos_freqs"]
        for j in range(pick_cnt):
            if j < len(pos_freqs):
                top3 = set(n for n, _ in pos_freqs[j].most_common(3))
                accum[f"pos{j}_top3"].append(1 if actual_sorted[j] in top3 else 0)
        
        # ---- 额外：模式分析 ----
        # 跨度是否在常见跨度中
        actual_span = max(actual) - min(actual)
        common_spans = [s for s, _ in feats["common_span"]]
        accum["span_match"].append(1 if actual_span in common_spans else 0)
        
        # 奇偶比是否常见
        odd_cnt = sum(1 for x in actual if x % 2 == 1)
        odd_total = sum(feats["odd_ratios"].values())
        if odd_total > 0:
            accum["odd_ratio_score"].append(feats["odd_ratios"].get(odd_cnt, 0) / odd_total)
        
        # 和值偏离度
        if feats["sum_std"] > 0:
            z_score = abs(sum(actual) - feats["avg_sum"]) / feats["sum_std"]
            accum["sum_zscore"].append(z_score)
        
        test_count += 1
        
        # 断点保存
        if test_count % checkpoint_every == 0:
            elapsed = time.time() - t_start
            rate = test_count / max(elapsed, 1)
            remaining = (total - min_train - test_count) / max(rate, 0.001)
            print(f"  [{period}] {test_count}/{total-min_train} ({test_count/(total-min_train)*100:.1f}%) "
                  f"| {rate:.1f}期/s | 预计剩余 {remaining:.0f}s")
            _save_checkpoint(lottery_type, accum, extra_accum, test_count, i)
    
    # 最终汇总
    elapsed = time.time() - t_start
    print(f"\n  完成! {test_count} 次测试, 耗时 {elapsed:.0f}s ({elapsed/60:.1f}min)")
    
    return _summarize(accum, lottery_type, test_count, total, periods)


def _save_checkpoint(lottery_type, accum, extra_accum, count, idx):
    """断点保存"""
    cp = {
        "lottery_type": lottery_type,
        "tests_done": count,
        "last_idx": idx,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    # 只保存汇总统计，不保存原始数据
    summary = {}
    for k, v in accum.items():
        if v:
            summary[k] = {
                "count": len(v),
                "sum": sum(v),
                "avg": round(sum(v)/len(v), 4),
            }
    cp["summary"] = summary
    
    os.makedirs("data", exist_ok=True)
    with open(f"data/walkback_{lottery_type}_cp.json", "w", encoding="utf-8") as f:
        json.dump(cp, f, ensure_ascii=False)


def _summarize(accum, lottery_type, test_count, total, periods):
    """汇总分析结果"""
    results = {}
    
    dim_labels = {
        "freq": "频率前N", "omission": "遗漏前N", "edge": "边码前N",
        "combined": "综合前N", "freq_wide": "频率前2N", "omission_wide": "遗漏前2N",
        "combined_wide": "综合前2N", "prime": "质数命中", "mod3_cold": "012路冷路",
        "repeat": "重号命中", "consecutive": "连号数",
    }
    
    print(f"\n{'='*60}")
    print(f"  {lottery_type.upper()} 策略发现结果")
    print(f"  总期数: {total}  测试期数: {test_count}")
    print(f"{'='*60}")
    
    # 各维度统计
    print(f"\n  {'维度':<16} {'测试数':>7} {'均命中':>8} {'≥1命中%':>10} {'≥2命中%':>10}")
    print(f"  {'-'*55}")
    
    dim_results = {}
    for dim, hits in sorted(accum.items()):
        if not hits or dim.startswith("pos") or dim in ("span_match", "odd_ratio_score", "sum_zscore"):
            continue
        n = len(hits)
        avg = sum(hits) / n
        hit1 = sum(1 for h in hits if h >= 1) / n * 100
        hit2 = sum(1 for h in hits if h >= 2) / n * 100
        label = dim_labels.get(dim, dim)
        print(f"  {label:<16} {n:>7} {avg:>8.3f} {hit1:>9.1f}% {hit2:>9.1f}%")
        dim_results[dim] = {"avg": round(avg, 3), "hit1%": round(hit1, 1), "hit2%": round(hit2, 1)}
    
    # 位置分析
    print(f"\n  位置命中率（前3高频号命中当期该位置）:")
    pos_summary = {}
    for j in range(10):
        key = f"pos{j}_top3"
        if key in accum:
            rate = sum(accum[key]) / len(accum[key]) * 100
            print(f"    位置{j+1}: {rate:.1f}%")
            pos_summary[f"pos{j+1}"] = round(rate, 1)
    
    # 跨度匹配
    if "span_match" in accum:
        rate = sum(accum["span_match"]) / len(accum["span_match"]) * 100
        print(f"\n  跨度匹配率: {rate:.1f}%")
        dim_results["span_match"] = round(rate, 1)
    
    # 奇偶比相关性
    if "odd_ratio_score" in accum:
        avg_score = sum(accum["odd_ratio_score"]) / len(accum["odd_ratio_score"])
        print(f"  奇偶比匹配度: {avg_score:.3f}")
    
    # 和值偏离
    if "sum_zscore" in accum:
        avg_z = sum(accum["sum_zscore"]) / len(accum["sum_zscore"])
        print(f"  和值平均Z-score: {avg_z:.3f} (越小越可预测)")
    
    # ---- 规律总结 ----
    discoveries = []
    
    # 比较频率 vs 遗漏
    if "freq" in dim_results and "omission" in dim_results:
        f_avg = dim_results["freq"]["avg"]
        o_avg = dim_results["omission"]["avg"]
        if o_avg > f_avg + 0.05:
            discoveries.append(f"遗漏策略(均{o_avg})优于频率策略(均{f_avg})→冷号回补更有效")
        elif f_avg > o_avg + 0.05:
            discoveries.append(f"频率策略(均{f_avg})优于遗漏策略(均{o_avg})→热号追踪更有效")
        else:
            discoveries.append(f"频率({f_avg})与遗漏({o_avg})效果相当→需综合使用")
    
    # 宽池效果
    if "freq_wide" in dim_results and "freq" in dim_results:
        gain = dim_results["freq_wide"]["hit1%"] - dim_results["freq"]["hit1%"]
        discoveries.append(f"候选池翻倍：命中率+{gain:.1f}% →候选池越大越好")
    
    # 综合 vs 单维度
    if "combined" in dim_results:
        best_single = max(
            dim_results.get("freq", {}).get("avg", 0),
            dim_results.get("omission", {}).get("avg", 0),
        )
        if dim_results["combined"]["avg"] > best_single:
            discoveries.append(f"综合评分优于单一维度：{dim_results['combined']['avg']:.3f} vs {best_single:.3f}")
    
    # 边码效果
    if "edge" in dim_results:
        discoveries.append(f"边码平均命中{dim_results['edge']['avg']:.3f}个 → {'有效' if dim_results['edge']['avg'] > 0.3 else '效果一般'}")
    
    # 重号
    if "repeat" in dim_results:
        discoveries.append(f"平均重号{dim_results['repeat']['avg']:.2f}个/期 → {'重号是重要因子' if dim_results['repeat']['avg'] > 0.8 else '重号影响有限'}")
    
    print(f"\n  发现的规律:")
    for d in discoveries:
        print(f"    - {d}")
    
    results["dimensions"] = dim_results
    results["positions"] = pos_summary
    results["discoveries"] = discoveries
    results["tests"] = test_count
    results["total_periods"] = total
    
    return results


def derive_optimal_weights(dim_results):
    """从维度命中率推导最优权重"""
    # 取核心维度的平均命中率
    core_dims = {
        "cold_hot": dim_results.get("freq", {}).get("avg", 0),
        "omission": dim_results.get("omission", {}).get("avg", 0),
        "tail": dim_results.get("combined", {}).get("avg", 0) * 0.8,
        "span": dim_results.get("span_match", 0) / 100 * dim_results.get("freq", {}).get("avg", 0),
        "odd_even": dim_results.get("freq", {}).get("avg", 0) * 0.5,
        "big_small": dim_results.get("freq", {}).get("avg", 0) * 0.5,
        "follow": dim_results.get("edge", {}).get("avg", 0),
        "rna": dim_results.get("repeat", {}).get("avg", 0),
    }
    
    # 确保有值
    for k in core_dims:
        if core_dims[k] == 0:
            core_dims[k] = 0.3
    
    # 归一化到 3-25
    min_v = min(core_dims.values())
    max_v = max(core_dims.values())
    weights = {}
    for k, v in core_dims.items():
        if max_v > min_v:
            normalized = (v - min_v) / (max_v - min_v)
        else:
            normalized = 0.5
        weights[k] = max(3, min(25, round(3 + normalized * 22)))
    
    return weights


def main():
    print("=" * 60)
    print("  策略全量倒退发现引擎 v1.0")
    print("  逐期回滚 · 不采样 · 全维度评估")
    print("=" * 60)
    
    # SSQ
    ssq_result = walkback_full("ssq", min_train=100, checkpoint_every=100)
    
    # DLT
    dlt_result = walkback_full("dlt", min_train=100, checkpoint_every=100)
    
    # 汇总输出
    print("\n" + "=" * 60)
    print("  最终策略权重推荐")
    print("=" * 60)
    
    ssq_weights = derive_optimal_weights(ssq_result.get("dimensions", {}))
    dlt_weights = derive_optimal_weights(dlt_result.get("dimensions", {}))
    
    print(f"\n  双色球 SSQ 推荐权重:")
    for k, v in sorted(ssq_weights.items(), key=lambda x: -x[1]):
        print(f"    {k}: {v}")
    
    print(f"\n  大乐透 DLT 推荐权重:")
    for k, v in sorted(dlt_weights.items(), key=lambda x: -x[1]):
        print(f"    {k}: {v}")
    
    # 保存全部结果
    output = {
        "ssq": {
            "dimensions": ssq_result.get("dimensions", {}),
            "positions": ssq_result.get("positions", {}),
            "discoveries": ssq_result.get("discoveries", []),
            "weights": ssq_weights,
        },
        "dlt": {
            "dimensions": dlt_result.get("dimensions", {}),
            "positions": dlt_result.get("positions", {}),
            "discoveries": dlt_result.get("discoveries", []),
            "weights": dlt_weights,
        },
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    os.makedirs("data", exist_ok=True)
    with open("data/strategy_full_discovery.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    # 同时更新权重缓存
    weights_cache = {}
    weights_cache["ssq"] = ssq_weights
    weights_cache["dlt"] = dlt_weights
    with open("data/weights_cache.json", "w", encoding="utf-8") as f:
        json.dump(weights_cache, f, ensure_ascii=False, indent=2)
    
    print(f"\n  结果已保存:")
    print(f"    data/strategy_full_discovery.json")
    print(f"    data/weights_cache.json (权重已自动更新)")
    print("\n  完成!")


if __name__ == "__main__":
    main()
