"""
回测引擎 - 通过对历史数据的反复预测-验证，总结预测偏差规律
用发现的规律修正后续预测，实现"在预测中学习"
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collections import Counter
from itertools import combinations
from database import get_all_ssq, get_all_dlt
from analyzer import MultiStrategyPredictor, SSQAnalyzer, DLTAnalyzer


def fast_analysis(train_data, lottery_type="ssq"):
    n = len(train_data)
    recent_n = min(50, n)
    if lottery_type == "ssq":
        max_num, pick_cnt, bonus_range = 33, 6, 16
        nums_list = [[d["red%d" % i] for i in range(1, 7)] for d in train_data]
        blist = [d["blue"] for d in train_data]
    else:
        max_num, pick_cnt, bonus_range = 35, 5, 12
        nums_list = [[d["front%d" % i] for i in range(1, 6)] for d in train_data]
        bpairs = [(d["back1"], d["back2"]) for d in train_data]
        flat_bonus = [x for d in train_data for x in (d["back1"], d["back2"])]
    freq = Counter(x for r in nums_list for x in r)
    rn = [x for r in nums_list[-recent_n:] for x in r]
    rc = Counter(rn)
    th_h = recent_n * pick_cnt / max_num * 1.5
    th_c = recent_n * pick_cnt / max_num * 0.5
    all_n = list(range(1, max_num + 1))
    hot = [x for x in all_n if rc.get(x, 0) >= th_h]
    warm = [x for x in all_n if th_c < rc.get(x, 0) < th_h]
    cold = [x for x in all_n if rc.get(x, 0) <= th_c]
    ls = set(nums_list[-1]) if nums_list else set()
    om = {}
    for x in range(1, max_num + 1):
        if x in ls:
            om[x] = 0
        else:
            c = 0
            for r in reversed(nums_list[:-1]):
                if x in r: break
                c += 1
            om[x] = c + 1 if nums_list else 0
    if lottery_type == "ssq":
        bf = Counter(blist)
        lb = blist[-1] if blist else 0
        bom = {}
        for x in range(1, bonus_range + 1):
            if x == lb: bom[x] = 0
            else:
                c = 0
                for b in reversed(blist[:-1]):
                    if b == x: break
                    c += 1
                bom[x] = c + 1 if blist else 0
    else:
        bf = Counter(flat_bonus)
        lbs = set(bpairs[-1]) if bpairs else set()
        bom = {}
        for x in range(1, bonus_range + 1):
            if x in lbs: bom[x] = 0
            else:
                c = 0
                for bp in reversed(bpairs[:-1]):
                    if x in bp: break
                    c += 1
                bom[x] = c + 1 if bpairs else 0
    return {
        "hot": hot, "warm": warm, "cold": cold,
        "freqs": {x: rc.get(x, 0) for x in all_n},
        "all_freqs": {x: freq.get(x, 0) for x in all_n},
        "omission": om,
        "bonus_freq": {x: bf.get(x, 0) for x in range(1, bonus_range + 1)},
        "bonus_omission": bom,
    }


def predict_main(analysis, max_num, pick_cnt, bonus_range, bonus_pick):
    sc = {}
    for n in range(1, max_num + 1):
        s = 0
        if n in analysis["hot"]: s += 50
        elif n in analysis["warm"]: s += 30
        else: s += 10
        s += analysis["omission"].get(n, 0) * 2.0
        s += analysis["all_freqs"].get(n, 0) * 3.0
        sc[n] = s
    cand = sorted(sc.keys(), key=lambda n: -sc[n])[:15]
    bs, bbest = -1, None
    for combo in combinations(cand, pick_cnt):
        s = sum(sc[n] for n in combo)
        odd = sum(1 for n in combo if n % 2 == 1)
        big = sum(1 for n in combo if n >= (max_num // 2 + 1))
        tgt = pick_cnt // 2 + pick_cnt % 2
        s += 30 if odd == tgt else 15 if abs(odd - tgt) == 1 else 0
        s += 30 if big == tgt else 15 if abs(big - tgt) == 1 else 0
        if s > bs: bs, bbest = s, combo
    main_nums = sorted(bbest) if bbest else cand[:pick_cnt]
    bsc = {n: analysis["bonus_freq"].get(n, 0) * 1.5 + analysis["bonus_omission"].get(n, 0) * 0.5
           for n in range(1, bonus_range + 1)}
    bonus_nums = sorted(sorted(bsc, key=lambda n: -bsc[n])[:bonus_pick])
    return main_nums, bonus_nums


class BacktestEngine:
    def __init__(self, all_data, lottery_type="ssq", max_test=100):
        self.all_data = all_data
        self.lottery_type = lottery_type
        self.test_data = all_data[-(max_test + 51):]
        self.results = []

    def run(self, callback=None):
        self.results = []
        td = self.test_data
        for i in range(50, len(td) - 1):
            train, actual = td[:i + 1], td[i + 1]
            try:
                analysis = fast_analysis(train, self.lottery_type)
                if self.lottery_type == "ssq":
                    pn, pb = predict_main(analysis, 33, 6, 16, 1)
                    an = {actual["red%d" % j] for j in range(1, 7)}
                    hit = len(set(pn) & an)
                    bh = 1 if pb[0] == actual["blue"] else 0
                    aso = sorted([actual["red%d" % j] for j in range(1, 7)])
                    pbias = [aso[k] - pn[k] for k in range(6)]
                else:
                    pn, pb = predict_main(analysis, 35, 5, 12, 2)
                    an = {actual["front%d" % j] for j in range(1, 6)}
                    ab = {actual["back%d" % j] for j in range(1, 3)}
                    hit = len(set(pn) & an)
                    bh = len(set(pb) & ab)
                    aso = sorted([actual["front%d" % j] for j in range(1, 6)])
                    pbias = [aso[k] - pn[k] for k in range(5)]
                self.results.append({"hit": hit, "bonus_hit": bh, "pos_biases": pbias})
            except:
                continue
            if callback and (i - 49) % 10 == 0:
                callback(i - 49, len(td) - 51)
        return self.get_statistics()

    def get_statistics(self):
        if not self.results:
            return {"error": "无数据"}
        n = len(self.results)
        hd = Counter(r["hit"] for r in self.results)
        bhd = Counter(r["bonus_hit"] for r in self.results)
        np_ = len(self.results[0]["pos_biases"])
        ab = [sum(r["pos_biases"][j] for r in self.results) / n for j in range(np_)]
        ab = [round(b, 2) for b in ab]
        stats = {
            "total_tests": n,
            "hit_dist": {str(k): round(v / n * 100, 1) for k, v in sorted(hd.items())},
            "bonus_hit_dist": {str(k): round(v / n * 100, 1) for k, v in sorted(bhd.items())},
            "avg_position_bias": ab,
        }
        corr = [round(b) for b in ab]
        if max(abs(b) for b in ab) >= 0.7:
            stats["correction"] = {
                "type": "position_shift",
                "values": corr,
                "desc": "位置修正: " + " ".join(["%+d" % c for c in corr])
            }
        else:
            stats["correction"] = {"type": "none", "desc": "无需修正"}
        return stats

    def get_prediction(self):
        analysis = fast_analysis(self.all_data, self.lottery_type)
        if self.lottery_type == "ssq":
            nums, bonus = predict_main(analysis, 33, 6, 16, 1)
            max_n = 33
        else:
            nums, bonus = predict_main(analysis, 35, 5, 12, 2)
            max_n = 35
        stats = self.get_statistics()
        corr = stats.get("correction", {}).get("values", None)
        result = {"original": nums, "bonus": bonus}
        if corr and max(abs(c) for c in corr) >= 1:
            cr = sorted([max(1, min(max_n, nums[j] + corr[j])) for j in range(len(nums))])
            if len(set(cr)) == len(nums):
                result["corrected"] = cr
        return result


def run_ssq_backtest(max_test=100):
    data = get_all_ssq()
    eng = BacktestEngine(data, "ssq", max_test)
    stats = eng.run()
    pred = eng.get_prediction()
    msp = MultiStrategyPredictor()
    anl = SSQAnalyzer(data).comprehensive_analysis()
    multi = msp.select_best_ssq(anl, count=3)
    return {"stats": stats, "prediction": pred, "multi_prediction": multi}

def run_dlt_backtest(max_test=100):
    data = get_all_dlt()
    eng = BacktestEngine(data, "dlt", max_test)
    stats = eng.run()
    pred = eng.get_prediction()
    msp = MultiStrategyPredictor()
    anl = DLTAnalyzer(data).comprehensive_analysis()
    multi = msp.select_best_dlt(anl, count=3)
    return {"stats": stats, "prediction": pred, "multi_prediction": multi}


if __name__ == "__main__":
    print("=" * 60)
    print("双色球回测")
    print("=" * 60)
    t0 = time.time()
    r1 = run_ssq_backtest()
    s = r1["stats"]
    print("回测 %d 次 (%.1fs)" % (s["total_tests"], time.time() - t0))
    print("红球命中分布: %s" % s["hit_dist"])
    print("蓝球命中: %s" % s["bonus_hit_dist"])
    print("位置偏差: %s" % s["avg_position_bias"])
    print("修正: %s" % s.get("correction", {}).get("desc", "无"))
    p = r1["prediction"]
    print("预测: %s + 蓝球%s" % (p["original"], p["bonus"]))
    if "corrected" in p:
        print("修正: %s" % p["corrected"])

    print()
    print("=" * 60)
    print("大乐透回测")
    print("=" * 60)
    t0 = time.time()
    r2 = run_dlt_backtest()
    s2 = r2["stats"]
    print("回测 %d 次 (%.1fs)" % (s2["total_tests"], time.time() - t0))
    print("前区命中: %s" % s2["hit_dist"])
    print("后区命中: %s" % s2["bonus_hit_dist"])
    print("位置偏差: %s" % s2["avg_position_bias"])
    print("修正: %s" % s2.get("correction", {}).get("desc", "无"))
    p2 = r2["prediction"]
    print("预测: %s + %s" % (p2["original"], p2["bonus"]))
    if "corrected" in p2:
        print("修正: %s" % p2["corrected"])
