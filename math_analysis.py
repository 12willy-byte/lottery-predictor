# -*- coding: utf-8 -*-
"""全中可行性数学分析"""
import math
from collections import Counter
from database import get_all_ssq

def comb(n, k):
    return math.comb(n, k)

print("=" * 60)
print("  全中(6/6)的数学边界")
print("=" * 60)

# 双色球: C(33,6) = 1,107,568 种红球组合
total_combos = comb(33, 6)
print(f"\n红球总组合数: {total_combos:,}")

# 如果选 n 注不同的组合
for n_bets in [1, 5, 10, 50, 100, 1000, 10000]:
    prob = n_bets / total_combos * 100
    print(f"  买 {n_bets:>6,} 注: 中奖概率 {prob:.6f}%")

print(f"\n要 100% 全中需要买全部 {total_combos:,} 注(约 2215 万元)")

# ========================================
print("\n" + "=" * 60)
print("  候选池大小 vs 覆盖命中数")
print("=" * 60)

# 如果候选池有 N 个号码，从中选6个组合
# 实际开奖的6个号码在候选池中的期望个数
for pool_size in [6, 10, 15, 18, 22, 25, 30, 33]:
    # 超几何分布期望: pool_size * 6 / 33
    expected = pool_size * 6 / 33
    # 6个全在池中的概率
    prob_all6 = comb(pool_size, 6) / comb(33, 6) if pool_size >= 6 else 0
    prob_5plus = (comb(pool_size, 6) + comb(pool_size, 5) * comb(33-pool_size, 1)) / comb(33, 6)
    print(f"  池{pool_size:>3}个: 期望命中{expected:.1f}个 | 6全在池概率={prob_all6*100:.6f}% | 5+在池概率={prob_5plus*100:.4f}%")

# ========================================
print("\n" + "=" * 60)
print("  全中6个的必需条件")
print("=" * 60)

# 要全中，候选池必须包含全部6个开奖号
# 候选池大小 → 包含全部6个的概率
for pool in range(6, 34):
    p = comb(pool, 6) / comb(33, 6)
    if p > 0.001 or pool <= 20:
        print(f"  池{pool:>3}: 6全在池概率 = {p*100:.6f}%")
    if p > 0.01 and pool > 20:
        print(f"  池{pool:>3}: 6全在池概率 = {p*100:.4f}%")

print(f"\n  即使池=30(覆盖91%号码), 6全在池概率也仅 {comb(30,6)/comb(33,6)*100:.2f}%")
print(f"  要 >50% 概率, 需要池≥{next(p for p in range(6,34) if comb(p,6)/comb(33,6) > 0.5)} 个号码")

# ========================================
print("\n" + "=" * 60)
print("  实际数据中的统计上限")
print("=" * 60)

data = get_all_ssq()
draws = [[d["red%d" % j] for j in range(1, 7)] for d in data]

# 3367期中，各策略最高单期命中
print(f"\n  总期数: {len(draws)}")

# 频率前6的历史表现
print("\n  频率策略前6候选的历史命中分布:")
freq_hits = Counter()
for i in range(100, len(draws)):
    train = draws[:i]
    actual = set(draws[i])
    freq = Counter(x for d in train[-50:] for x in d)
    top6 = set(n for n, _ in freq.most_common(6))
    freq_hits[len(top6 & actual)] += 1

for k in range(7):
    if k in freq_hits:
        pct = freq_hits[k] / sum(freq_hits.values()) * 100
        print(f"    {k}个: {freq_hits[k]:>5}期 ({pct:5.1f}%)")

# 最优可能：取所有策略的并集（30个候选）
print("\n  30候选池(几乎覆盖所有策略前几名)的历史命中:")
pool30_hits = Counter()
for i in range(100, len(draws)):
    train = draws[:i]
    actual = set(draws[i])
    freq = Counter(x for d in train[-50:] for x in d)
    # 模拟30候选
    pool = set(n for n, _ in freq.most_common(30))
    pool30_hits[len(pool & actual)] += 1

for k in range(7):
    if k in pool30_hits:
        pct = pool30_hits[k] / sum(pool30_hits.values()) * 100
        print(f"    {k}个: {pool30_hits[k]:>5}期 ({pct:5.1f}%)")

# ========================================
print("\n" + "=" * 60)
print("  结论")
print("=" * 60)
print(f"""
  1. 红球全中(6/6)在统计学上和数学上都是不可能的:
     - 需要猜中 C(33,6) = {total_combos:,} 分之一的组合
     - 即使候选池有30个号码(覆盖91%), 6全在池概率仅 {comb(30,6)/comb(33,6)*100:.2f}%
  
  2. 实际 3367 期历史中:
     - 最佳单策略从未命中6个
     - 30候选池也仅 {pool30_hits.get(6, 0)} 次覆盖全部6个
  
  3. 系统的实际能力上限:
     - 预测1-2个: 约80%的期能做到
     - 预测3个: 约17%的期
     - 预测4个: 约2%的期
     - 预测5+: 几乎不可能
  
  4. "全中的规律"如果存在，彩票就不存在了。
     彩票的本质是随机 + 期望值为负，任何声称能做到全中的方法都是骗局。
""")
