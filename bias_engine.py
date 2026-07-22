# -*- coding: utf-8 -*-
"""物理偏差检测引擎 — 贝叶斯+滑动窗口 z-score"""

import math
from collections import Counter

class BiasDetector:
    """检测彩票号码的物理偏差 (非随机性)"""
    
    def __init__(self, data, num_range=33, pick_cnt=6):
        self.data = data
        self.num_range = num_range
        self.pick_cnt = pick_cnt
        self.total = len(data)
    
    def compute_z_scores(self, window=None, recency_weight=False):
        """计算每个号码的z-score
        window: None=全部, int=最近N期
        recency_weight: True=近期加权
        """
        if window:
            draws = self.data[-window:]
        else:
            draws = self.data
        
        cnt = Counter()
        if recency_weight:
            for i, d in enumerate(draws):
                w = (i + 1) / len(draws)  # linear recency weight
                for j in range(1, self.pick_cnt + 1):
                    k = "red%d" % j if self.num_range == 33 else "front%d" % j
                    cnt[d[k]] += w
            total_weighted = sum(cnt.values())
            expected = total_weighted / self.num_range
            # Approximate std for weighted counts
            std = math.sqrt(expected * (1 - self.pick_cnt / self.num_range))
        else:
            for d in draws:
                for j in range(1, self.pick_cnt + 1):
                    k = "red%d" % j if self.num_range == 33 else "front%d" % j
                    cnt[d[k]] += 1
            total = len(draws) * self.pick_cnt
            expected = total / self.num_range
            std = math.sqrt(expected * (1 - self.pick_cnt / self.num_range))
        
        z_scores = {}
        for n in range(1, self.num_range + 1):
            obs = cnt.get(n, 0)
            if std > 0:
                z_scores[n] = (obs - expected) / std
            else:
                z_scores[n] = 0
        
        return z_scores, dict(cnt), expected, std
    
    def multi_window_analysis(self, windows=[100, 300, 1000]):
        """多窗口综合分析, 检测偏差漂移"""
        results = {}
        for w in windows:
            if w <= self.total:
                z, cnt, exp, std = self.compute_z_scores(window=w)
                results[w] = {"z": z, "cnt": cnt, "expected": exp, "std": std}
        return results
    
    def consensus_bias(self, windows=[100, 300, 1000]):
        """多窗口共识: 在所有窗口中都同向偏差的号码"""
        mw = self.multi_window_analysis(windows)
        
        scores = {}
        for n in range(1, self.num_range + 1):
            zs = []
            for w in windows:
                if w in mw:
                    zs.append(mw[w]["z"].get(n, 0))
            
            if zs:
                # Consensus score: mean z * sign consistency
                mean_z = sum(zs) / len(zs)
                signs = [1 if z > 0 else (-1 if z < 0 else 0) for z in zs]
                consistency = abs(sum(signs)) / len(signs)  # 0-1, how consistent
                scores[n] = mean_z * consistency
        
        return scores
    
    def hot_cold_classify(self, threshold=1.5):
        """分类: hot(>thresholdσ), cold(<-thresholdσ), neutral"""
        z, _, _, _ = self.compute_z_scores()
        hot = [n for n, z in z.items() if z > threshold]
        cold = [n for n, z in z.items() if z < -threshold]
        neutral = [n for n, z in z.items() if abs(z) <= threshold]
        return {"hot": sorted(hot, key=lambda n: -z[n]),
                "cold": sorted(cold, key=lambda n: z[n]),
                "neutral": neutral,
                "z_scores": z}


if __name__ == "__main__":
    from database import get_all_ssq
    ssq = get_all_ssq()
    bd = BiasDetector(ssq, 33, 6)
    
    print("=== SSQ 物理偏差检测 ===")
    hc = bd.hot_cold_classify(1.5)
    print("热号(>1.5σ):", hc["hot"])
    print("冷号(<-1.5σ):", hc["cold"])
    
    print()
    print("=== 多窗口共识 ===")
    consensus = bd.consensus_bias([100, 300, 1000])
    top = sorted(consensus.items(), key=lambda x: -x[1])[:8]
    bottom = sorted(consensus.items(), key=lambda x: x[1])[:8]
    print("最热:", [(n, round(s,2)) for n,s in top])
    print("最冷:", [(n, round(s,2)) for n,s in bottom])
