# -*- coding: utf-8 -*-
"""预测验证引擎 v2 — 快速模式，可配置期数"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from collections import Counter
from database import get_all_ssq, get_all_dlt
from analyzer import SSQAnalyzer, DLTAnalyzer, MultiStrategyPredictor

def verify_ssq(test_periods=10):
    data = get_all_ssq()
    total = len(data)
    if total < 150: return
    print("\n" + "=" * 55)
    print(f"  SSQ 倒退验证 ({total}期, 近{test_periods}期)")
    print("=" * 55)

    msp = MultiStrategyPredictor()
    results = {"red_hits": [], "blue_hit": 0, "total": 0}
    t_start = time.time()

    for i in range(total - test_periods, total):
        train = data[:i]
        actual = data[i]
        period = actual["period"]
        next_p = str(int(period))

        anl = SSQAnalyzer(train).comprehensive_analysis()
        # 快速模式：只生成1组，加时间熵防同号
        seed = next_p + str(int(time.time() * 1000) % 10000)
        preds = msp.select_best_ssq(anl, count=1, period_seed=seed)
        if not preds: continue

        pred = preds[0]
        pred_reds = set(pred["reds"])
        actual_reds = {actual["red%d" % j] for j in range(1, 7)}
        actual_blue = actual["blue"]

        red_hit = len(pred_reds & actual_reds)
        blue_hit = 1 if pred["blue"] == actual_blue else 0
        results["red_hits"].append(red_hit)
        results["blue_hit"] += blue_hit
        results["total"] += 1

        status = f"期{period}: 红{red_hit}/6" + ("=" if red_hit>=3 else("-" if red_hit>=1 else "X"))
        status += f" 蓝{'=OK' if blue_hit else 'X  '}"
        elapsed = time.time() - t_start
        eta = elapsed / (i - (total - test_periods) + 1) * (test_periods - (i - (total - test_periods)) - 1)
        print(f"  [{results['total']}/{test_periods}] {status}  (已用{elapsed:.0f}s, 预计剩余{eta:.0f}s)")

    elapsed = time.time() - t_start
    avg_red = sum(results["red_hits"]) / max(results["total"], 1)
    blue_rate = results["blue_hit"] / max(results["total"], 1) * 100
    g3 = sum(1 for h in results["red_hits"] if h >= 3)
    print("-" * 45)
    print(f"  红球均值: {avg_red:.2f}/6 (随机1.09) | >=3: {g3}/{results['total']}")
    print(f"  蓝球命中: {results['blue_hit']}/{results['total']} = {blue_rate:.1f}% (随机6.25%)")
    print(f"  耗时: {elapsed:.0f}s")
    return results

def verify_dlt(test_periods=10):
    data = get_all_dlt()
    total = len(data)
    if total < 150: return
    print("\n" + "=" * 55)
    print(f"  DLT 倒退验证 ({total}期, 近{test_periods}期)")
    print("=" * 55)

    msp = MultiStrategyPredictor()
    results = {"front_hits": [], "back_hits": [], "total": 0}
    t_start = time.time()

    for i in range(total - test_periods, total):
        train = data[:i]
        actual = data[i]
        period = actual["period"]
        next_p = str(int(period))

        anl = DLTAnalyzer(train).comprehensive_analysis()
        seed = next_p + str(int(time.time() * 1000) % 10000)
        preds = msp.select_best_dlt(anl, count=1, period_seed=seed)
        if not preds: continue

        pred = preds[0]
        pred_fronts = set(pred["fronts"])
        actual_fronts = {actual["front%d" % j] for j in range(1, 6)}
        pred_backs = set(pred["backs"])
        actual_backs = {actual["back1"], actual["back2"]}

        front_hit = len(pred_fronts & actual_fronts)
        back_hit = len(pred_backs & actual_backs)
        results["front_hits"].append(front_hit)
        results["back_hits"].append(back_hit)
        results["total"] += 1

        status = f"期{period}: 前{front_hit}/5" + ("=" if front_hit>=2 else("-" if front_hit>=1 else "X"))
        status += f" 后{back_hit}/2" + ("=OK" if back_hit>=1 else "X  ")
        elapsed = time.time() - t_start
        eta = elapsed / (i - (total - test_periods) + 1) * (test_periods - (i - (total - test_periods)) - 1)
        print(f"  [{results['total']}/{test_periods}] {status}  (已用{elapsed:.0f}s, 预计剩余{eta:.0f}s)")

    elapsed = time.time() - t_start
    avg_front = sum(results["front_hits"]) / max(results["total"], 1)
    avg_back = sum(results["back_hits"]) / max(results["total"], 1)
    g1_back = sum(1 for h in results["back_hits"] if h >= 1)
    g2_front = sum(1 for h in results["front_hits"] if h >= 2)
    print("-" * 45)
    print(f"  前区均值: {avg_front:.2f}/5 (随机0.71) | >=2: {g2_front}/{results['total']}")
    print(f"  后区均值: {avg_back:.2f}/2 (随机0.33) | >=1: {g1_back}/{results['total']}")
    print(f"  耗时: {elapsed:.0f}s")
    return results

if __name__ == "__main__":
    N = 10
    print(f"预测验证引擎 v2 — {N}期倒退测试")
    t0 = time.time()
    r1 = verify_ssq(N)
    r2 = verify_dlt(N)
    t1 = time.time()
    print(f"\n总耗时: {t1-t0:.0f}s")
