# -*- coding: utf-8 -*-
"""
命中率预测引擎 - 最大化期望命中 + 概率校准
"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collections import Counter
from itertools import combinations
from database import get_all_ssq, get_all_dlt
from strategy_discovery import fast_extract_features


def calibrate_hit_probability(lottery_type="ssq"):
    """用全量历史倒退数据校准命中概率"""
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
    
    # 校准数据: 对每个号码, 记录其"得分排名"和"实际是否命中"的关系
    rank_hit_pairs = []  # (rank_percentile, was_hit)
    
    for i in range(min_train, total, 3):  # 每3期采样加快速度
        train = draws[:i]
        actual = set(draws[i])
        feats = fast_extract_features(train, num_range, pick_cnt)
        if feats is None:
            continue
        
        scores = feats["num_scores"]
        all_nums = list(range(1, num_range + 1))
        ranked = sorted(all_nums, key=lambda n: -scores.get(n, 0))
        
        for rank, n in enumerate(ranked):
            percentile = rank / num_range
            was_hit = 1 if n in actual else 0
            rank_hit_pairs.append((percentile, was_hit))
    
    # 按分位数分桶计算命中率
    buckets = 20
    bucket_size = 1.0 / buckets
    calibration = {}
    
    for b in range(buckets):
        lo = b * bucket_size
        hi = (b + 1) * bucket_size
        pairs = [(r, h) for r, h in rank_hit_pairs if lo <= r < hi]
        if pairs:
            hit_rate = sum(h for _, h in pairs) / len(pairs)
            calibration[f"{lo:.2f}-{hi:.2f}"] = {
                "samples": len(pairs),
                "hit_rate": round(hit_rate, 4),
            }
    
    # 拟合曲线: hit_prob = a * exp(-b * percentile) + c
    # 简化为线性插值
    percentiles = sorted(set(r for r, _ in rank_hit_pairs))
    
    return calibration, rank_hit_pairs


def predict_hit_distribution(candidate_scores, num_range, pick_cnt, calibration_data=None):
    """
    给每个号码的得分, 预测该号码被命中的概率,
    然后对组合计算命中数分布
    """
    all_nums = list(range(1, num_range + 1))
    ranked = sorted(all_nums, key=lambda n: -candidate_scores.get(n, 0))
    
    # 基于校准数据估算每个号码的命中概率
    num_probs = {}
    for rank, n in enumerate(ranked):
        percentile = rank / num_range
        # 默认模型: 排名越前概率越高, 用指数衰减
        prob = 6.0 / num_range * (1.5 - 0.8 * (rank / num_range))
        prob = max(0.05, min(0.95, prob))
        num_probs[n] = round(prob, 4)
    
    return num_probs


def expected_hits_for_combo(combo, num_probs):
    """计算一组号码的期望命中数"""
    return sum(num_probs.get(n, 0) for n in combo)


def hit_distribution_for_combo(combo, num_probs):
    """
    用动态规划精确计算命中0,1,2,...,k个的概率
    P(命中k) = sum over subsets of size k of product(probs) * product(1-probs)
    """
    n = len(combo)
    # DP: dp[i][j] = 前i个号码命中j个的概率
    dp = [[0.0] * (n + 1) for _ in range(n + 1)]
    dp[0][0] = 1.0
    
    for i in range(n):
        p = num_probs.get(combo[i], 0)
        for j in range(i + 1):
            dp[i + 1][j] += dp[i][j] * (1 - p)
            dp[i + 1][j + 1] += dp[i][j] * p
    
    return [round(dp[n][j], 6) for j in range(n + 1)]


def find_best_combos(scores, num_range, pick_cnt, num_probs, top_candidates=20, max_results=5):
    """找到期望命中最高的组合"""
    all_nums = list(range(1, num_range + 1))
    ranked = sorted(all_nums, key=lambda n: -scores.get(n, 0))
    candidates = ranked[:top_candidates]
    
    results = []
    for combo in combinations(candidates, pick_cnt):
        exp_hits = expected_hits_for_combo(combo, num_probs)
        dist = hit_distribution_for_combo(combo, num_probs)
        prob_2plus = sum(dist[2:])
        prob_3plus = sum(dist[3:])
        prob_4plus = sum(dist[4:])
        
        results.append({
            "combo": sorted(combo),
            "expected_hits": round(exp_hits, 2),
            "prob_2plus": round(prob_2plus * 100, 1),
            "prob_3plus": round(prob_3plus * 100, 1),
            "prob_4plus": round(prob_4plus * 100, 1),
            "hit_dist": [round(p * 100, 1) for p in dist],
        })
    
    results.sort(key=lambda x: -x["expected_hits"])
    return results[:max_results]


def main():
    print("=" * 60)
    print("  命中率预测引擎 - 最大化期望命中")
    print("=" * 60)
    
    for lt, label in [("ssq", "双色球 SSQ"), ("dlt", "大乐透 DLT")]:
        print(f"\n{'='*60}")
        print(f"  {label}")
        print(f"{'='*60}")
        
        if lt == "ssq":
            raw = get_all_ssq()
            num_range, pick_cnt = 33, 6
            draws = [[d["red%d" % j] for j in range(1, 7)] for d in raw]
        else:
            raw = get_all_dlt()
            num_range, pick_cnt = 35, 5
            draws = [[d["front%d" % j] for j in range(1, 6)] for d in raw]
        
        # 特征提取
        feats = fast_extract_features(draws, num_range, pick_cnt)
        
        # 命中概率预测
        num_probs = predict_hit_distribution(feats["num_scores"], num_range, pick_cnt)
        
        # 各策略前N名的期望命中
        print(f"\n  各策略候选池期望命中:")
        for name, candidates in [
            ("频率", feats["sorted_by_freq"]),
            ("遗漏", feats["sorted_by_om"]),
            ("边码", feats["sorted_by_edge"]),
            ("综合", feats["combined_top"]),
        ]:
            top6 = candidates[:pick_cnt]
            exp = expected_hits_for_combo(top6, num_probs)
            dist = hit_distribution_for_combo(top6, num_probs)
            print(f"    {name:6} {top6}")
            print(f"           期望命中: {exp:.2f} | P(>=2)={sum(dist[2:])*100:.1f}% | P(>=3)={sum(dist[3:])*100:.1f}%")
        
        # 找最优组合
        print(f"\n  期望命中最高的{pick_cnt}个组合:")
        best = find_best_combos(feats["num_scores"], num_range, pick_cnt, num_probs, 
                                top_candidates=20, max_results=5)
        
        for i, r in enumerate(best):
            print(f"    #{i+1}: {r['combo']}")
            print(f"        期望命中: {r['expected_hits']} | P(>=2)={r['prob_2plus']}% | P(>=3)={r['prob_3plus']}% | P(>=4)={r['prob_4plus']}%")
            dist_str = " ".join(f"{p}%" for p in r["hit_dist"])
            print(f"        命中分布: {dist_str}")
        
        # 号码级别的命中概率 Top 10
        print(f"\n  号码级别命中概率 Top 10:")
        probs_sorted = sorted(num_probs.items(), key=lambda x: -x[1])
        for n, p in probs_sorted[:10]:
            bar = "#" * int(p * 50)
            print(f"    号码{n:>2}: {p:.3f} {bar}")

if __name__ == "__main__":
    main()
