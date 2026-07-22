"""
分析引擎 - 多策略统计分析引擎
包含：冷热号、遗漏值、奇偶比、大小比、区间分布、连号、和值、AC值、重号、质数分析
"""
import random
import math
from collections import Counter, defaultdict

class LotteryAnalyzer:
    """彩票分析引擎基类"""

    def __init__(self, history_data):
        self.data = history_data
        self.total = len(history_data)

    def get_frequency(self, num_range):
        """号码频率统计"""
        counter = Counter()
        return counter

    def analyze_hot_cold(self, num_range, recent_n=50):
        """冷热号分析: 热号=高频, 冷号=低频, 温号=中间"""
        counter = Counter()
        for draw in self.data[-recent_n:]:
            for n in draw:
                counter[n] += 1
        all_nums = list(range(1, num_range + 1))
        freqs = {n: counter.get(n, 0) for n in all_nums}
        sorted_nums = sorted(all_nums, key=lambda x: freqs[x], reverse=True)
        threshold_hot = recent_n * 0.18
        threshold_cold = recent_n * 0.08
        hot = [n for n in all_nums if freqs[n] >= threshold_hot]
        cold = [n for n in all_nums if freqs[n] <= threshold_cold]
        warm = [n for n in all_nums if threshold_cold < freqs[n] < threshold_hot]
        return {"hot": hot, "warm": warm, "cold": cold, "freqs": freqs}

    def analyze_omission(self, num_range):
        """遗漏值分析: 计算每个号码当前遗漏期数"""
        latest_nums = set()
        if self.data:
            latest_nums = set(self.data[-1])
        omission = {}
        for n in range(1, num_range + 1):
            if n in latest_nums:
                omission[n] = 0
            else:
                count = 0
                for draw in reversed(self.data[:-1]):
                    if n in draw:
                        break
                    count += 1
                omission[n] = count + 1 if self.data else 0
        return omission

    def analyze_odd_even(self, nums):
        """奇偶比分析"""
        odd = sum(1 for n in nums if n % 2 == 1)
        even = len(nums) - odd
        return {"odd": odd, "even": even, "ratio": f"{odd}:{even}"}

    def analyze_big_small(self, nums, mid_point):
        """大小比分析"""
        big = sum(1 for n in nums if n >= mid_point)
        small = len(nums) - big
        return {"big": big, "small": small, "ratio": f"{big}:{small}"}

    def analyze_range_dist(self, nums, ranges):
        """区间分布分析"""
        dist = {f"{r[0]}-{r[1]}": 0 for r in ranges}
        for n in nums:
            for r in ranges:
                if r[0] <= n <= r[1]:
                    dist[f"{r[0]}-{r[1]}"] += 1
                    break
        return dist

    def analyze_consecutive(self, nums):
        """连号分析"""
        sorted_nums = sorted(nums)
        consecutives = []
        temp = [sorted_nums[0]]
        for i in range(1, len(sorted_nums)):
            if sorted_nums[i] == sorted_nums[i - 1] + 1:
                temp.append(sorted_nums[i])
            else:
                if len(temp) >= 2:
                    consecutives.append(list(temp))
                temp = [sorted_nums[i]]
        if len(temp) >= 2:
            consecutives.append(list(temp))
        return consecutives

    def analyze_sum(self, nums):
        """和值分析"""
        return sum(nums)

    def analyze_ac(self, nums):
        """AC值计算 - 号码复杂度指标"""
        sorted_nums = sorted(nums)
        diffs = set()
        for i in range(len(sorted_nums)):
            for j in range(i + 1, len(sorted_nums)):
                diffs.add(sorted_nums[j] - sorted_nums[i])
        return len(diffs) - (len(nums) - 1)

    def analyze_repeat(self, nums, last_draw):
        """重号分析 - 与上期重复的号码"""
        if not last_draw:
            return []
        return [n for n in nums if n in last_draw]

    def _compute_follow_stats(self, draws, num_range, top_n=5):
        """计算跟随号统计 - 每个号码最常见的后续号码"""
        from collections import Counter, defaultdict
        follow = defaultdict(list)
        for i in range(len(draws) - 1):
            curr = draws[i]
            nxt = draws[i + 1]
            for c in curr:
                follow[c].extend(nxt)
        result = {}
        for num, next_nums in follow.items():
            cnt = Counter(next_nums)
            result[num] = cnt.most_common(top_n)
        return result

    def _compute_blue_streak(self, blues):
        """分析蓝球冷热连出规律 - 返回每号连出统计和冷号回补概率"""
        from collections import Counter
        streaks = {}  # {num: {max_hot_streak, avg_cold_gap, recent_hot}}
        for n in range(1, 17):
            positions = [i for i, b in enumerate(blues) if b[0] == n]
            gaps = [positions[i+1] - positions[i] for i in range(len(positions)-1)] if len(positions) > 1 else []
            streaks[n] = {
                'total_appear': len(positions),
                'avg_gap': round(sum(gaps) / len(gaps), 1) if gaps else 99,
                'last_gap': len(blues) - 1 - positions[-1] if positions else 99,
                'recent_3': sum(1 for p in positions if p >= len(blues) - 3),
            }
        return streaks

    def _compute_back_pair_freq(self, backs):
        """分析后区两号组合频率 + 近期权重 - v4.0"""
        from collections import Counter
        pair_counter = Counter()
        pair_recent = Counter()  # 近50期加权
        total = len(backs)
        for i, draw in enumerate(backs):
            if len(draw) >= 2:
                pair = tuple(sorted(draw[:2]))
                pair_counter[pair] += 1
                # 近期权重: 越近越高
                recency = min(1.0, (i - max(0, total - 50)) / 50) if i >= total - 50 else 0
                if recency > 0:
                    pair_recent[pair] += 1 + recency
        # 合并: 全量0.4 + 近期0.6
        merged = {}
        all_pairs = set(list(pair_counter.keys()) + list(pair_recent.keys()))
        for p in all_pairs:
            merged[p] = pair_counter.get(p, 0) * 0.4 + pair_recent.get(p, 0) * 0.6
        top = sorted(merged.items(), key=lambda x: -x[1])[:20]
        return {
            'top_pairs': [(p, round(c, 1)) for p, c in top],
            'total_draws': total,
            'pair_rate': {p: round(c/total, 4) for p, c in top},
            'recent_weighted': True
        }

    def _compute_recent_hits(self, draws, n=5):
        """计算近N期每个号码的出现次数"""
        from collections import Counter
        cnt = Counter()
        for draw in draws[-n:]:
            for num in draw:
                cnt[num] += 1
        return dict(cnt)

    def get_primes(self, limit):
        """获取质数列表"""
        primes = []
        for n in range(2, limit + 1):
            is_prime = True
            for i in range(2, int(n ** 0.5) + 1):
                if n % i == 0:
                    is_prime = False
                    break
            if is_prime:
                primes.append(n)
        return primes

    def analyze_tails(self, nums):
        """\u5c3e\u6570\u5206\u6790"""
        tails = [n % 10 for n in nums]
        return {"tails": sorted(tails), "unique_tails": len(set(tails)), "tail_count": __import__("collections").Counter(tails)}

    def analyze_span(self, nums):
        """\u8de8\u5ea6\u5206\u6790"""
        return max(nums) - min(nums)

    def get_tail_distribution(self, num_range, pick_count):
        """\u5c3e\u6570\u5206\u5e03\u7edf\u8ba1"""
        from collections import Counter
        total_unique = 0
        for draw in self.data:
            total_unique += len(set(n % 10 for n in draw))
        avg = round(total_unique / max(len(self.data), 1), 1)
        tail_freq = Counter()
        for draw in self.data:
            for n in draw:
                tail_freq[n % 10] += 1
        return {"avg_unique_tails": avg, "tail_freq": {t: tail_freq.get(t, 0) for t in range(10)}}

    def get_span_distribution(self, num_range, pick_count):
        """\u8de8\u5ea6\u5206\u5e03"""
        from collections import Counter
        span_counter = Counter()
        for draw in self.data:
            s = max(draw) - min(draw)
            span_counter[s] += 1
        mc = span_counter.most_common(1)
        return {"most_common_span": mc[0][0] if mc else num_range // 2,
                "avg_span": round(sum(k*v for k,v in span_counter.items()) / max(len(self.data), 1), 1)}

    def get_follow_stats(self, num_range):
        """\u8ddf\u968f\u53f7\u7edf\u8ba1"""
        from collections import Counter, defaultdict
        follows = defaultdict(Counter)
        for i in range(len(self.data) - 1):
            for n1 in self.data[i]:
                for n2 in self.data[i + 1]:
                    follows[n1][n2] += 1
        result = {}
        for n in range(1, num_range + 1):
            if follows[n]:
                result[n] = [(num, cnt) for num, cnt in follows[n].most_common(5)]
        return result

    def get_repeat_neighbor_stats(self, num_range):
        """\u91cd\u90bb\u5b64\u7edf\u8ba1"""
        if len(self.data) < 2:
            return {"avg_repeat": 0}
        total_r = 0
        for i in range(1, len(self.data)):
            total_r += len(set(self.data[i]) & set(self.data[i-1]))
        return {"avg_repeat": round(total_r / (len(self.data) - 1), 2)}

    def analyze_prime_count(self, nums):
        """质数数量分析"""
        primes = self.get_primes(max(nums))
        return sum(1 for n in nums if n in primes)

    def get_position_stats(self, num_range, pick_count):
        """\u4f4d\u7f6e\u7edf\u8ba1 - \u6bcf\u4e2a\u4f4d\u7f6e\u7684\u5386\u53f2\u8303\u56f4\u548c\u5e38\u89c1\u533a\u95f4"""
        if not self.data:
            return {"ranges": [{"min":1, "max":num_range, "p10":1, "p90":num_range} for _ in range(pick_count)]}
        positions = [[] for _ in range(pick_count)]
        for draw in self.data:
            s = sorted(draw)
            for j in range(pick_count):
                positions[j].append(s[j])
        stats = []
        for j in range(pick_count):
            vals = sorted(positions[j])
            n = len(vals)
            stats.append({
                "min": vals[0], "max": vals[-1],
                "avg": round(sum(vals)/n, 1),
                "p10": vals[n//10] if n >= 10 else vals[0],
                "p25": vals[n//4] if n >= 4 else vals[0],
                "p75": vals[3*n//4] if n >= 4 else vals[-1],
                "p90": vals[9*n//10] if n >= 10 else vals[-1],
                "common_range": "%d-%d" % (vals[n//10] if n>=10 else vals[0], vals[9*n//10] if n>=10 else vals[-1])
            })
        return stats

    def get_amplitude_stats(self, num_range, pick_count):
        """\u632f\u5e45\u7edf\u8ba1 - \u5404\u4f4d\u7f6e\u76f8\u6bd4\u4e0a\u671f\u7684\u53d8\u5316\u5e45\u5ea6"""
        if len(self.data) < 2:
            return {"avg_amps": [0]*pick_count, "common_amps": [[0] for _ in range(pick_count)]}
        amps = [[] for _ in range(pick_count)]
        for i in range(1, len(self.data)):
            prev = sorted(self.data[i-1])
            curr = sorted(self.data[i])
            for j in range(pick_count):
                amps[j].append(curr[j] - prev[j])
        from collections import Counter
        stats = {"avg_amps": [], "common_amps": []}
        for j in range(pick_count):
            if amps[j]:
                stats["avg_amps"].append(round(sum(amps[j])/len(amps[j]), 1))
                c = Counter(amps[j])
                stats["common_amps"].append([a for a,_ in c.most_common(4)])
            else:
                stats["avg_amps"].append(0)
                stats["common_amps"].append([0])
        return stats

    def get_historical_pattern(self, num_range, pick_count):
        """历史模式统计"""
        patterns = {
            "odd_even": Counter(),
            "big_small": Counter(),
            "sum_range": Counter(),
            "ac_range": Counter(),
        }
        mid = num_range // 2 + 1
        for draw in self.data:
            oe = self.analyze_odd_even(draw)
            bs = self.analyze_big_small(draw, mid)
            s = self.analyze_sum(draw)
            ac = self.analyze_ac(draw)
            patterns["odd_even"][oe["ratio"]] += 1
            patterns["big_small"][bs["ratio"]] += 1
            sum_key = f"{s // 10 * 10}-{s // 10 * 10 + 9}"
            patterns["sum_range"][sum_key] += 1
            ac_key = f"{ac}-{ac}"
            if ac <= 3: ac_key = "0-3"
            elif ac <= 6: ac_key = "4-6"
            elif ac <= 9: ac_key = "7-9"
            else: ac_key = "10+"
            patterns["ac_range"][ac_key] += 1
        return patterns


class SSQAnalyzer(LotteryAnalyzer):
    """双色球分析器: 红球1-33选6, 蓝球1-16选1"""

    def __init__(self, data):
        super().__init__(data)
        self.red_range = 33
        self.blue_range = 16
        self.red_count = 6
        self.blue_count = 1

    def get_reds_from_data(self):
        """从数据中提取红球列表"""
        reds = []
        for d in self.data:
            reds.append([d["red1"], d["red2"], d["red3"], d["red4"], d["red5"], d["red6"]])
        return reds

    def get_blues_from_data(self):
        """从数据中提取蓝球列表"""
        return [[d["blue"]] for d in self.data]

    def get_red_frequency(self):
        """红球频率统计"""
        counter = Counter()
        for d in self.data:
            for key in ["red1", "red2", "red3", "red4", "red5", "red6"]:
                counter[d[key]] += 1
        return counter

    def get_blue_frequency(self):
        """蓝球频率统计"""
        counter = Counter()
        for d in self.data:
            counter[d["blue"]] += 1
        return counter

    def comprehensive_analysis(self, recent_n=50):
        """综合分析 - 返回完整分析结果"""
        reds = self.get_reds_from_data()
        blues = self.get_blues_from_data()
        red_freq = self.get_red_frequency()
        blue_freq = self.get_blue_frequency()

        # 1. 红球冷热号
        hot_cold = self.analyze_hot_cold(self.red_range, recent_n)
        # 替换为从实际数据计算
        counter = Counter()
        recent_reds = [d for draw in reds[-recent_n:] for d in draw]
        for n in recent_reds:
            counter[n] += 1
        threshold_hot = recent_n * 6 / 33 * 1.5
        threshold_cold = recent_n * 6 / 33 * 0.5
        all_nums = list(range(1, 34))
        hot_cold = {
            "hot": [n for n in all_nums if counter.get(n, 0) >= threshold_hot],
            "warm": [n for n in all_nums if threshold_cold < counter.get(n, 0) < threshold_hot],
            "cold": [n for n in all_nums if counter.get(n, 0) <= threshold_cold],
            "freqs": {n: counter.get(n, 0) for n in all_nums}
        }

        # 2. 红球遗漏分析
        latest_reds = set(reds[-1]) if reds else set()
        red_omission = {}
        for n in range(1, 34):
            if n in latest_reds:
                red_omission[n] = 0
            else:
                cnt = 0
                for draw in reversed(reds[:-1]):
                    if n in draw:
                        break
                    cnt += 1
                red_omission[n] = cnt + 1 if reds else 0

        # 3. 蓝球冷热
        blue_counter = Counter()
        for b in blues[-recent_n:]:
            blue_counter[b[0]] += 1
        blue_hot = [n for n in range(1, 17) if blue_counter.get(n, 0) >= 3]
        blue_cold = [n for n in range(1, 17) if blue_counter.get(n, 0) == 0]

        # 4. 蓝球遗漏
        latest_blue = blues[-1][0] if blues else 0
        blue_omission = {}
        for n in range(1, 17):
            if n == latest_blue:
                blue_omission[n] = 0
            else:
                cnt = 0
                for b in reversed(blues[:-1]):
                    if b[0] == n:
                        break
                    cnt += 1
                blue_omission[n] = cnt + 1 if blues else 0

        # 5. 历史奇偶比
        oe_counter = Counter()
        for draw in reds:
            oe = self.analyze_odd_even(draw)
            oe_counter[oe["ratio"]] += 1

        # 6. 历史大小比
        bs_counter = Counter()
        for draw in reds:
            bs = self.analyze_big_small(draw, 17)
            bs_counter[bs["ratio"]] += 1

        # 7. 区间分布 (1-11, 12-22, 23-33)
        range_counter = {f"{r[0]}-{r[1]}": Counter() for r in [(1,11),(12,22),(23,33)]}
        for draw in reds:
            rd = self.analyze_range_dist(draw, [(1,11),(12,22),(23,33)])
            for k, v in rd.items():
                range_counter[k][v] += 1

        # 8. 红球和值范围
        sum_counter = Counter()
        for draw in reds:
            s = sum(draw)
            key = f"{s//20*20}-{s//20*20+19}"
            sum_counter[key] += 1

        # 9. 连号概率
        consecutive_count = sum(1 for draw in reds if self.analyze_consecutive(draw))
        return {
            "total": self.total,
            "recent_n": min(recent_n, self.total),
            "red_frequency": {n: red_freq.get(n, 0) for n in range(1, 34)},
            "blue_frequency": {n: blue_freq.get(n, 0) for n in range(1, 17)},
            "red_hot_cold": hot_cold,
            "blue_hot": blue_hot,
            "blue_cold": blue_cold,
            "red_omission": red_omission,
            "blue_omission": blue_omission,
            "odd_even_pattern": dict(oe_counter.most_common()),
            "big_small_pattern": dict(bs_counter.most_common()),
            "range_pattern": {k: dict(v.most_common()) for k, v in range_counter.items()},
            "sum_pattern": dict(sum_counter.most_common(10)),
            "consecutive_prob": consecutive_count / max(self.total, 1),
        # 10-13. 新维度: 尾数/跨度/跟随号/重邻孤 (computed inline from reds)
        "tail_stats": {"avg_unique_tails": round(sum(len(set(n % 10 for n in d)) for d in reds) / max(len(reds), 1), 1),
                       "tail_freq": {t: sum(1 for d in reds for n in d if n % 10 == t) for t in range(10)}},
        "span_stats": {"most_common_span": max(set(max(d)-min(d) for d in reds), key=lambda s: sum(1 for d in reds if max(d)-min(d)==s)) if reds else 0,
                       "avg_span": round(sum(max(d)-min(d) for d in reds) / max(len(reds), 1), 1)},
        "follow_stats": self._compute_follow_stats(reds, 33),
        "rn_stats": {"avg_repeat": round(sum(len(set(reds[i]) & set(reds[i-1])) for i in range(1, len(reds))) / max(len(reds)-1, 1), 2)},
        "pos_stats": [{"min":min(p),"max":max(p),"avg":round(sum(p)/len(p),1),"p10":sorted(p)[len(p)//10]if len(p)>=10 else 1,"p90":sorted(p)[9*len(p)//10]if len(p)>=10 else 33} for p in [[sorted(d)[j] for d in reds] for j in range(6)]],
        "amp_stats": {"common_amps": [[sorted(reds[i])[j]-sorted(reds[i-1])[j] for i in range(1,len(reds))] for j in range(6)]},
            # 定位频率 (每位置独立统计)
        "_pos_freq": [{n: sum(1 for d in reds if sorted(d)[j]==n) for n in range(1,34)} for j in range(6)],
        "_last_blue": blues[-1][0] if blues else None,
            "blue_follow_stats": self._compute_follow_stats(blues, 16),
            "blue_streak": self._compute_blue_streak(blues),
            "_recent_hits": self._compute_recent_hits(reds, 5),
        "_last_draw": reds[-1] if reds else []
        }


class DLTAnalyzer(LotteryAnalyzer):
    """大乐透分析器: 前区1-35选5, 后区1-12选2"""

    def __init__(self, data):
        super().__init__(data)
        self.front_range = 35
        self.back_range = 12
        self.front_count = 5
        self.back_count = 2

    def get_fronts_from_data(self):
        fronts = []
        for d in self.data:
            fronts.append([d["front1"], d["front2"], d["front3"], d["front4"], d["front5"]])
        return fronts

    def get_backs_from_data(self):
        return [[d["back1"], d["back2"]] for d in self.data]

    def comprehensive_analysis(self, recent_n=50):
        """大乐透综合分析"""
        fronts = self.get_fronts_from_data()
        backs = self.get_backs_from_data()

        # 前区频率
        front_freq = Counter()
        for draw in fronts:
            for n in draw:
                front_freq[n] += 1

        # 后区频率
        back_freq = Counter()
        for draw in backs:
            for n in draw:
                back_freq[n] += 1

        # 前区冷热
        counter = Counter()
        for draw in fronts[-recent_n:]:
            for n in draw:
                counter[n] += 1
        th_hot = recent_n * 5 / 35 * 1.5
        th_cold = recent_n * 5 / 35 * 0.5
        hot = {"hot": [n for n in range(1,36) if counter.get(n,0) >= th_hot],
               "warm": [n for n in range(1,36) if th_cold < counter.get(n,0) < th_hot],
               "cold": [n for n in range(1,36) if counter.get(n,0) <= th_cold]}

        # 前区遗漏
        latest = set(fronts[-1]) if fronts else set()
        front_omission = {}
        for n in range(1, 36):
            if n in latest: front_omission[n] = 0
            else:
                cnt = 0
                for draw in reversed(fronts[:-1]):
                    if n in draw: break
                    cnt += 1
                front_omission[n] = cnt + 1 if fronts else 0

        # 后区遗漏
        latest_backs = set(backs[-1]) if backs else set()
        back_omission = {}
        for n in range(1, 13):
            if n in latest_backs: back_omission[n] = 0
            else:
                cnt = 0
                for draw in reversed(backs[:-1]):
                    if n in draw: break
                    cnt += 1
                back_omission[n] = cnt + 1 if backs else 0

                from collections import Counter as _DC
        
        # DLT additional stats
        _front_tails = [n % 10 for draw in fronts for n in draw]
        _tail_counter = _DC(_front_tails)
        _avg_ut = round(sum(len(set(n % 10 for n in d)) for d in fronts) / max(len(fronts), 1), 1)
        _spans = [max(d) - min(d) for d in fronts]
        _common_span = max(set(_spans), key=lambda s: _spans.count(s)) if _spans else 0
        _avg_span = round(sum(_spans) / max(len(_spans), 1), 1) if _spans else 0
        _repeats = []
        for _i in range(1, len(fronts)):
            _repeats.append(len(set(fronts[_i]) & set(fronts[_i-1])))
        _avg_rep = round(sum(_repeats) / max(len(_repeats), 1), 2) if _repeats else 0
        
        return {
            "total": self.total,
            "recent_n": min(recent_n, self.total),
            "front_frequency": {n: front_freq.get(n,0) for n in range(1,36)},
            "back_frequency": {n: back_freq.get(n,0) for n in range(1,13)},
            "front_hot_cold": hot,
            "front_omission": front_omission,
            "back_omission": back_omission,
            "tail_stats": {"avg_unique_tails": _avg_ut,
                           "tail_freq": dict(_tail_counter)},
            "span_stats": {"most_common_span": _common_span,
                           "avg_span": _avg_span},
            "follow_stats": self._compute_follow_stats(fronts, 35),
            "rn_stats": {"avg_repeat": _avg_rep},
            "pos_stats": [{"min":min(p),"max":max(p),"avg":round(sum(p)/len(p),1),"p10":sorted(p)[len(p)//10]if len(p)>=10 else 1,"p90":sorted(p)[9*len(p)//10]if len(p)>=10 else 35} for p in [[sorted(d)[j] for d in fronts] for j in range(5)]],
            "amp_stats": {"common_amps": [[sorted(fronts[i])[j]-sorted(fronts[i-1])[j] for i in range(1,len(fronts))] for j in range(5)]},
            "_last_backs": backs[-1] if backs else [],
            "back_follow_stats": self._compute_follow_stats(backs, 12),
            "_pos_freq": [{n: sum(1 for d in fronts if sorted(d)[j]==n) for n in range(1,36)} for j in range(5)],
        # 动态调权: 近5期重号率
        "_regime": "hot" if sum(len(set(fronts[i])&set(fronts[i-1])) for i in range(max(1,len(fronts)-5), len(fronts))) >= 6 else "normal",
        "back_repeat_rate": round(sum(1 for i in range(1, len(backs)) if set(backs[i]) & set(backs[i-1])) / max(len(backs)-1, 1), 3),
            "back_pair_freq": self._compute_back_pair_freq(backs),
            "_last_draw": fronts[-1] if fronts else []
        }


class LotteryPredictor:
    """选号预测器 - 基于综合分析生成推荐号码"""

    @staticmethod
    def weighted_choice(items, weights, k=1):
        """加权随机选择"""
        if not items: return []
        total = sum(weights)
        if total == 0: return random.sample(items, min(k, len(items)))
        chosen = []
        pool = list(zip(items, weights))
        for _ in range(k):
            if not pool: break
            r = random.random() * sum(w for _, w in pool)
            cumsum = 0
            for i, (item, w) in enumerate(pool):
                cumsum += w
                if r <= cumsum:
                    chosen.append(item)
                    pool.pop(i)
                    break
        return chosen

    def predict_best_ssq(self, analysis):
        data = analysis
        red_freq = data['red_frequency']
        red_omission = data['red_omission']
        hot = data['red_hot_cold']['hot']
        warm = data['red_hot_cold']['warm']
        oe_pat = data.get('odd_even_pattern', {})
        common_oe = '3:3'
        if oe_pat: common_oe = list(oe_pat.keys())[0]
        target_odd = int(common_oe.split(':')[0])
        bs_pat = data.get('big_small_pattern', {})
        common_bs = '3:3'
        if bs_pat: common_bs = list(bs_pat.keys())[0]
        target_big = int(common_bs.split(':')[0])
        sum_pat = data.get('sum_pattern', {})
        common_sum = '100-119'
        if sum_pat: common_sum = list(sum_pat.keys())[0]
        smin, smax = [int(x) for x in common_sum.split('-')]
        range_pat = data.get('range_pattern', {})
        common_dist = {}
        for k, v in range_pat.items():
            if v: common_dist[k] = int(list(v.keys())[0])
            else: common_dist[k] = 2
        has_cons = data.get('consecutive_prob', 0.5) > 0.4
        from itertools import combinations
        pool = hot + [n for n in warm if n not in hot]
        if len(pool) < 12:
            cold_sorted = sorted([n for n in range(1,34) if n not in pool], key=lambda n: -red_omission.get(n,0))
            pool.extend(cold_sorted)
        pool = pool[:18]
        best_combo = None
        best_score = -999
        for combo in combinations(pool, 6):
            reds = list(combo)
            odd = sum(1 for n in reds if n%2==1)
            big = sum(1 for n in reds if n>=17)
            total = sum(reds)
            score = 0
            if odd==target_odd: score+=30
            elif abs(odd-target_odd)==1: score+=15
            if big==target_big: score+=30
            elif abs(big-target_big)==1: score+=15
            if smin<=total<=smax: score+=20
            elif abs(total-(smin+smax)//2)<=15: score+=10
            r1=sum(1 for n in reds if 1<=n<=11)
            r2=sum(1 for n in reds if 12<=n<=22)
            r3=sum(1 for n in reds if 23<=n<=33)
            dscore=0
            for k,target in common_dist.items():
                actual={'1-11':r1,'12-22':r2,'23-33':r3}.get(k,0)
                if actual==target: dscore+=15
                elif abs(actual-target)==1: dscore+=8
            score+=dscore
            sr=sorted(reds)
            hc=any(sr[i+1]-sr[i]==1 for i in range(5))
            if has_cons and hc: score+=10
            if not has_cons and not hc: score+=10
            score+=sum(1 for n in reds if n in hot)*8
            score+=sum(red_freq.get(n,0) for n in reds)*0.5
            if score>best_score:
                best_score=score
                best_combo=sorted(reds)
        if not best_combo: best_combo=sorted(list(pool[:6]))
        blue_freq=data.get('blue_frequency',{})
        blue_omission=data['blue_omission']
        blue_scores={}
        for n in range(1,17):
            s=blue_freq.get(n,0)*1.5+blue_omission.get(n,0)*0.5
            if n in data.get('blue_hot',[]): s+=20
            blue_scores[n]=s
        best_blue=max(blue_scores,key=blue_scores.get)
        return {'reds':best_combo,'blue':best_blue}

    def predict_best_dlt(self, analysis):
        """生成最大机率的一注大乐透"""
        hot = analysis["front_hot_cold"]["hot"]
        warm = analysis["front_hot_cold"]["warm"]
        cold = analysis["front_hot_cold"]["cold"]
        freqs = analysis["front_frequency"]
        omission = analysis["front_omission"]

        scores = {}
        for n in range(1, 36):
            s = 0
            if n in hot: s += 50
            elif n in warm: s += 30
            else: s += 10
            s += omission.get(n, 0) * 2.0
            s += freqs.get(n, 0) * 3.0
            scores[n] = s

        from itertools import combinations
        candidates = sorted(scores.items(), key=lambda x: -x[1])
        best = None
        best_score = -1
        for combo in combinations([c[0] for c in candidates[:12]], 5):
            reds = list(combo)
            score = sum(scores[n] for n in reds)
            if score > best_score:
                best_score = score
                best = sorted(reds)
        if not best:
            best = sorted([c[0] for c in candidates[:5]])

        # 后区
        back_scores = {}
        for n in range(1, 13):
            s = 10 + analysis["back_omission"].get(n, 0) * 3
            back_scores[n] = s
        best_backs = sorted([max(back_scores, key=back_scores.get)])
        remaining = [n for n in range(1,13) if n != best_backs[0]]
        best_backs.append(max(remaining, key=lambda n: back_scores[n]))
        best_backs.sort()

        return {"fronts": best, "backs": best_backs}

    def predict_ssq(self, analysis, count=5):
        """生成双色球推荐号码"""
        results = []
        hot = analysis["red_hot_cold"]["hot"]
        warm = analysis["red_hot_cold"]["warm"]
        cold = analysis["red_hot_cold"]["cold"]
        freqs = analysis["red_hot_cold"]["freqs"]
        omission = analysis["red_omission"]
        oe_pattern = analysis.get("odd_even_pattern", {})
        bs_pattern = analysis.get("big_small_pattern", {})

        # 获取最常见的奇偶比和大小比
        common_oe = "3:3"
        common_bs = "3:3"
        if oe_pattern: common_oe = list(oe_pattern.keys())[0]
        if bs_pattern: common_bs = list(bs_pattern.keys())[0]

        target_odd = int(common_oe.split(":")[0])
        target_big = int(common_bs.split(":")[0])

        for _ in range(count):
            selected = set()
            # 混合策略: 40%热号 + 35%温号 + 25%冷号
            pool_weights = {}
            for n in range(1, 34):
                w = 0
                if n in hot: w += 40
                elif n in warm: w += 35
                else: w += 25
                # 加成: 遗漏值越大权重略增
                w += omission.get(n, 0) * 1.5
                # 加成: 频率加成
                w += freqs.get(n, 0) * 2
                pool_weights[n] = w

            # 加权选择6个红球
            items = list(pool_weights.keys())
            weights = [pool_weights[n] for n in items]
            
            # 先选3个主要号码
            main = self.weighted_choice(items, weights, 4)
            selected.update(main)
            
            # 补充剩余号码
            remaining = [n for n in items if n not in selected]
            remaining_weights = [pool_weights[n] for n in remaining]
            extra = self.weighted_choice(remaining, remaining_weights, 6 - len(selected))
            selected.update(extra)

            # 如果不够6个，随机补充
            while len(selected) < 6:
                n = random.randint(1, 33)
                if n not in selected:
                    selected.add(n)

            reds = sorted(list(selected))[:6]

            # 蓝球选择: 冷热结合
            blue_candidates = []
            blue_weights = []
            for n in range(1, 17):
                w = 10
                if n in analysis.get("blue_hot", []): w += 30
                if n in analysis.get("blue_cold", []): w += 20
                w += analysis["blue_omission"].get(n, 0) * 3
                blue_candidates.append(n)
                blue_weights.append(w)
            blue = self.weighted_choice(blue_candidates, blue_weights, 1)[0]

            results.append({"reds": reds, "blue": blue})

        return results

    def predict_dlt(self, analysis, count=5):
        """生成大乐透推荐号码"""
        results = []
        hot = analysis["front_hot_cold"]["hot"]
        warm = analysis["front_hot_cold"]["warm"]
        cold = analysis["front_hot_cold"]["cold"]
        freqs = analysis["front_frequency"]
        omission = analysis["front_omission"]

        for _ in range(count):
            selected = set()
            pool_weights = {}
            for n in range(1, 36):
                w = 0
                if n in hot: w += 40
                elif n in warm: w += 35
                else: w += 25
                w += omission.get(n, 0) * 1.5
                w += freqs.get(n, 0) * 2
                pool_weights[n] = w

            items = list(pool_weights.keys())
            weights = [pool_weights[n] for n in items]
            main = self.weighted_choice(items, weights, 3)
            selected.update(main)
            remaining = [n for n in items if n not in selected]
            remaining_weights = [pool_weights[n] for n in remaining]
            extra = self.weighted_choice(remaining, remaining_weights, 5 - len(selected))
            selected.update(extra)
            while len(selected) < 5:
                n = random.randint(1, 35)
                if n not in selected:
                    selected.add(n)
            fronts = sorted(list(selected))[:5]

            # 后区选择
            back_candidates = []
            back_weights = []
            for n in range(1, 13):
                w = 10
                w += analysis["back_omission"].get(n, 0) * 3
                back_candidates.append(n)
                back_weights.append(w)
            backs = sorted(self.weighted_choice(back_candidates, back_weights, 2))

            results.append({"fronts": fronts, "backs": backs})

        return results
        # 10-13. 新维度: 尾数/跨度/跟随号/重邻孤
        # 10-13. 新维度: 尾数/跨度/跟随号/重邻孤
        from collections import Counter
        _reds_data = reds  # use already-extracted reds lists
        _total_unique = sum(len(set(n % 10 for n in draw)) for draw in _reds_data)
        _avg_tails = round(_total_unique / max(len(_reds_data), 1), 1)
        _tail_freq = Counter()
        for draw in _reds_data:
            for n in draw:
                _tail_freq[n % 10] += 1
        analysis["tail_stats"] = {"avg_unique_tails": _avg_tails, "tail_freq": {t: _tail_freq.get(t, 0) for t in range(10)}}
        
        _span_counter = Counter(max(d) - min(d) for d in _reds_data)
        _mc_span = _span_counter.most_common(1)
        analysis["span_stats"] = {"most_common_span": _mc_span[0][0] if _mc_span else 16,
                                  "avg_span": round(sum(k*v for k,v in _span_counter.items())/max(len(_reds_data),1), 1)}
        
        _follows = defaultdict(lambda: Counter())
        for i in range(len(_reds_data)-1):
            for n1 in _reds_data[i]:
                for n2 in _reds_data[i+1]:
                    _follows[n1][n2] += 1
        analysis["follow_stats"] = {n: [(num, cnt) for num, cnt in _follows[n].most_common(5)] 
                                     for n in range(1, 34) if _follows[n]}
        
        _total_r = 0
        for i in range(1, len(_reds_data)):
            _total_r += len(set(_reds_data[i]) & set(_reds_data[i-1]))
        analysis["rn_stats"] = {"avg_repeat": round(_total_r / max(len(_reds_data)-1, 1), 2)}
        
        # 10-13. 新维度: 尾数/跨度/跟随号/重邻孤
        # 10-13. 新维度: 尾数/跨度/跟随号/重邻孤
        from collections import Counter, defaultdict
        _fronts_data = fronts  # use already-extracted fronts lists
        _total_unique = sum(len(set(n % 10 for n in draw)) for draw in _fronts_data)
        _avg_tails = round(_total_unique / max(len(_fronts_data), 1), 1)
        _tail_freq = Counter()
        for draw in _fronts_data:
            for n in draw:
                _tail_freq[n % 10] += 1
        analysis["tail_stats"] = {"avg_unique_tails": _avg_tails, "tail_freq": {t: _tail_freq.get(t, 0) for t in range(10)}}
        
        _span_counter = Counter(max(d) - min(d) for d in _fronts_data)
        _mc_span = _span_counter.most_common(1)
        analysis["span_stats"] = {"most_common_span": _mc_span[0][0] if _mc_span else 17,
                                  "avg_span": round(sum(k*v for k,v in _span_counter.items())/max(len(_fronts_data),1), 1)}
        
        _follows = defaultdict(lambda: Counter())
        for i in range(len(_fronts_data)-1):
            for n1 in _fronts_data[i]:
                for n2 in _fronts_data[i+1]:
                    _follows[n1][n2] += 1
        analysis["follow_stats"] = {n: [(num, cnt) for num, cnt in _follows[n].most_common(5)] 
                                     for n in range(1, 36) if _follows[n]}
        
        _total_r = 0
        for i in range(1, len(_fronts_data)):
            _total_r += len(set(_fronts_data[i]) & set(_fronts_data[i-1]))
        analysis["rn_stats"] = {"avg_repeat": round(_total_r / max(len(_fronts_data)-1, 1), 2)}
        analysis["_last_draw"] = fronts[-1] if fronts else []
        






class MultiStrategyPredictor:
    """多策略加权投票预测器 v3
    8维基础评分体系 (满分~100):
      冷热号20 + 遗漏值15 + 尾数15 + 跨度10 + 奇偶比10 + 大小比10 + 跟随号10 + 重邻孤10
    加分项 (~80):
      质数+AC值+和值范围+位置频次+振幅 ≈ 80
    总分满分约180
    """
    
    # 8维基础权重 (用户指定比例)
    STRATEGY_WEIGHTS = {
        'cold_hot': 25,
        'omission': 25,
        'tail': 19,
        'span': 3,
        'odd_even': 12,
        'big_small': 12,
        'follow': 25,
        'rna': 25,
    }
    BONUS_WEIGHTS = {
        'prime': 8,
        'ac_value': 6,
        'sum_range': 6,
        'position': 8,
        'amplitude': 5,
    }

    def __init__(self):
        self.weights = dict(self.STRATEGY_WEIGHTS)
        self.bonus = dict(self.BONUS_WEIGHTS)
        self.scores_detail = {}

    def _sync_weights_from_cache(self, lottery_type):
        """从缓存加载权重，与GUI保持一致"""
        try:
            import json, os
            cache_path = os.path.join("data", "weights_cache.json")
            if os.path.exists(cache_path):
                with open(cache_path, "r", encoding="utf-8") as f:
                    c = json.load(f)
                if lottery_type in c:
                    self.weights.update(c[lottery_type])
        except:
            pass

    def score_numbers(self, analysis, num_range, pick_cnt):
        """个号评分 - 冷热号 + 遗漏值 + 尾数 + 重邻孤 + 质数加分"""
        scores = {}
        hc_key = 'red_hot_cold' if num_range == 33 else 'front_hot_cold'
        om_key = 'red_omission' if num_range == 33 else 'front_omission'
        hc = analysis.get(hc_key, {})
        hot_set = set(hc.get('hot', []))
        warm_set = set(hc.get('warm', []))
        om = analysis.get(om_key, {})
        last = analysis.get('_last_draw', [])
        last_set = set(last)
        adj_set = set()
        for ln in last:
            if ln > 1: adj_set.add(ln - 1)
            if ln < num_range: adj_set.add(ln + 1)
        adj_set -= last_set
        prime_set = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31}
        w = self.weights
        b = self.bonus
        is_dlt = (num_range == 35)
        for n in range(1, num_range + 1):
            s = 0.0
            if is_dlt:
                # DLT v3.5: 全量频率主导 + 动态调权(热号连出时遗漏提权)
                alltime_freq = analysis.get('front_frequency', {}).get(n, 0)
                alltime_max = max(analysis.get('front_frequency', {}).values()) if analysis.get('front_frequency') else 1
                alltime_f = alltime_freq / max(alltime_max, 1)
                recent_f = (1.2 if n in hot_set else (1.0 if n in warm_set else 0.5))
                # 动态: 近5期重号率高时降低频率权重
                regime = analysis.get('_regime', 'normal')
                if regime == 'hot':
                    freq_factor = alltime_f * 0.5 + recent_f * 0.2
                    s += w['cold_hot'] / pick_cnt * freq_factor * 0.7
                else:
                    freq_factor = alltime_f * 0.7 + recent_f * 0.3
                    s += w['cold_hot'] / pick_cnt * freq_factor
                ov = om.get(n, 0)
                if ov <= 2: f2 = 0.5
                elif ov <= 8: f2 = 0.8
                elif ov <= 15: f2 = 1.0
                else: f2 = 1.1
                s += w['omission'] / pick_cnt * f2 * 0.6
                s += w['tail'] / pick_cnt * 0.3
                if n in last_set:
                    s += w['rna'] / pick_cnt * 1.2
                elif n in adj_set:
                    s += w['rna'] / pick_cnt * 0.8
                else:
                    s += w['rna'] / pick_cnt * 0.3
            else:
                f = 1.2 if n in hot_set else (1.0 if n in warm_set else 0.3)
                s += w['cold_hot'] / pick_cnt * f
                ov = om.get(n, 0)
                if ov <= 2: f2 = 0.3
                elif ov <= 5: f2 = 0.6
                elif ov <= 10: f2 = 1.0
                elif ov <= 20: f2 = 1.3
                else: f2 = 1.5
                s += w['omission'] / pick_cnt * f2
                s += w['tail'] / pick_cnt * 0.6
                if n in last_set:
                    s += w['rna'] / pick_cnt * 1.5
                elif n in adj_set:
                    s += w['rna'] / pick_cnt
                else:
                    s += w['rna'] / pick_cnt * 0.3
                # v3.8: 近期连出趋势 - 近5期出现次数越多越加分
                recent_cnt = analysis.get('_recent_hits', {}).get(n, 0)
                if recent_cnt >= 3:
                    s += w['cold_hot'] / pick_cnt * 0.8
                elif recent_cnt >= 2:
                    s += w['cold_hot'] / pick_cnt * 0.4
            if n in prime_set:
                s += b['prime'] / pick_cnt * 0.8
            scores[n] = round(s, 1)
        return scores

    def rate_combo(self, combo, analysis, num_range, last, prime_set):
        """组合综合评分 (8维度 + 加分)"""
        detail = {}
        total = 0.0
        n_len = len(combo)
        w = self.weights
        b = self.bonus
        from collections import Counter as _C
        
        # 5. 跨度
        span_val = max(combo) - min(combo)
        target_span = analysis.get('span_stats', {}).get('most_common_span', num_range // 2)
        sd = abs(span_val - target_span)
        span_score = float(w['span'])
        if sd > 2: span_score = w['span'] * 0.6
        if sd > 5: span_score = w['span'] * 0.2
        if sd > 10: span_score = 0
        detail['span'] = round(span_score, 1)
        total += span_score
        
        # 6. 奇偶比
        odd_cnt = sum(1 for nn in combo if nn % 2 == 1)
        if num_range == 33:
            oe = w['odd_even'] if odd_cnt == 3 else (w['odd_even'] * 0.6 if abs(odd_cnt - 3) <= 1 else w['odd_even'] * 0.2)
        else:
            oe = w['odd_even'] if odd_cnt in (2, 3) else (w['odd_even'] * 0.6 if odd_cnt in (1, 4) else w['odd_even'] * 0.2)
        detail['odd_even'] = round(oe, 1)
        total += oe
        
        # 7. 大小比
        mid = num_range // 2 + 1
        big_cnt = sum(1 for nn in combo if nn >= mid)
        tb = 3 if num_range == 33 else 2
        bs = w['big_small'] if big_cnt == tb else (w['big_small'] * 0.6 if abs(big_cnt - tb) <= 1 else w['big_small'] * 0.2)
        detail['big_small'] = round(bs, 1)
        total += bs
        
        # 8. 跟随号
        fs = analysis.get('follow_stats', {})
        foll = 0.0
        if last:
            for ln in last:
                if ln in fs:
                    for fn, _ in fs[ln][:3]:
                        if fn in combo:
                            foll += w['follow'] / 3.0
        foll = min(foll, float(w['follow']))
        detail['follow'] = round(foll, 1)
        total += foll
        
        # 尾数多样性 — v4.2 增强: 4-5个不同尾数最佳
        tails = [nn % 10 for nn in combo]
        unique_tails = len(set(tails))
        if unique_tails >= 5:
            td_score = w['tail'] * 0.8
        elif unique_tails == 4:
            td_score = w['tail'] * 0.5
        elif unique_tails == 3:
            td_score = w['tail'] * 0.2
        else:
            td_score = -w['tail'] * 0.3
        detail['tail_diversity'] = round(td_score, 1)
        total += td_score
        
        # 质数数量加分
        pc = sum(1 for nn in combo if nn in prime_set)
        pb = b['prime'] * 0.5 if pc >= 2 else (b['prime'] * 0.3 if pc == 1 else 0)
        detail['prime_bonus'] = round(pb, 1)
        total += pb
        
        # AC值
        sr = sorted(combo)
        diffs = set()
        for i in range(len(sr)):
            for j in range(i + 1, len(sr)):
                diffs.add(sr[j] - sr[i])
        ac = len(diffs) - (len(sr) - 1)
        tmin = 7 if num_range == 33 else 6
        tmax = 10 if num_range == 33 else 9
        acs = b['ac_value'] if tmin <= ac <= tmax else (b['ac_value'] * 0.5 if tmin - 2 <= ac <= tmax + 2 else 0)
        detail['ac_value'] = round(acs, 1)
        total += acs
        
        # 相邻间距分布 — v4.2 视频差值概率: 无极端密集/稀疏
        gaps = [sr[i+1] - sr[i] for i in range(len(sr)-1)]
        gap_min, gap_max = min(gaps), max(gaps)
        avg_gap = (sr[-1] - sr[0]) / (len(sr) - 1)
        gap_score = 0.0
        if gap_min >= 1 and gap_max <= 15 and 2 <= avg_gap <= 8:
            gap_score = b.get('ac_value', 6) * 0.3  # 间距健康
        if gap_min == 1 and gap_max > 18:
            gap_score -= b.get('ac_value', 6) * 0.3  # 极端间距
        detail['gap_dist'] = round(gap_score, 1)
        total += gap_score
        
        # 和值范围
        s = sum(combo)
        lo, hi = (80, 140) if num_range == 33 else (50, 120)
        ss = b['sum_range'] if lo <= s <= hi else (b['sum_range'] * 0.5 if lo - 15 <= s <= hi + 15 else 0)
        detail['sum_range'] = round(ss, 1)
        total += ss
        
        # 位置约束 — v4.0 硬约束+软加分(位1/位N强约束, 中位软加分)
        pos_freq = analysis.get('_pos_freq', [])
        pscore = 0.0
        sr_combo = sorted(combo)
        if pos_freq and len(pos_freq) == n_len:
            for j, n in enumerate(sr_combo):
                if j < len(pos_freq):
                    pf = pos_freq[j]
                    top8 = set(sorted(pf.keys(), key=lambda k: -pf[k])[:8])
                    if j == 0 or j == n_len - 1:
                        # 首位末位: 硬约束, 不在Top8重罚
                        if n in top8:
                            pscore += b['position'] * 0.5
                        else:
                            pscore -= b['position'] * 0.8  # 强惩罚
                    else:
                        # 中间位: 在Top8加分, 不在不罚
                        if n in top8:
                            freq = pf.get(n, 0)
                            max_f = max(pf.values()) if pf else 1
                            pscore += b['position'] / n_len * (freq / max(max_f, 1)) * 0.6
        elif analysis.get('pos_stats'):
            ps = analysis.get('pos_stats', [])
            if ps and len(ps) == n_len:
                pen = 0
                for j, n in enumerate(sr_combo):
                    if j < len(ps):
                        pj = ps[j]
                        if n < pj.get('p10', 1) or n > pj.get('p90', num_range):
                            pen -= 3
                pscore = max(0.0, b['position'] + pen)
        detail['position'] = round(pscore, 1)
        total += pscore
        
        # 振幅
        amp_s = analysis.get('amp_stats', {})
        ca = amp_s.get('common_amps', [])
        ascore = 0.0
        if ca and len(ca) == n_len and last and len(last) == n_len:
            for j, n in enumerate(combo):
                if j < len(ca) and j < len(last):
                    delta = n - last[j]
                    if delta in ca[j]:
                        ascore += 1
            ascore = min(float(b['amplitude']), ascore)
        else:
            ascore = b['amplitude'] * 0.3
        detail['amplitude'] = round(ascore, 1)
        total += ascore
        
        # 重号约束
        if last:
            rc = sum(1 for nn in combo if nn in last)
            ar = analysis.get('rn_stats', {}).get('avg_repeat', 1)
            rd = abs(rc - round(ar))
            rna_c = w['rna'] * 0.3 if rd <= 1 else (w['rna'] * 0.1 if rc <= 1 else 0)
            detail['rna_combo'] = round(rna_c, 1)
            total += rna_c
        
        # 012路平衡 — 核心约束 (v3.7 强化: walkback最高命中率维度)
        def _road(n): return n % 3
        roads = [_road(n) for n in combo]
        r0, r1, r2 = roads.count(0), roads.count(1), roads.count(2)
        road_max = max(r0, r1, r2)
        road_min = min(r0, r1, r2)
        road_weight = max(w.get('cold_hot', 25), w.get('follow', 25))  # 与核心维度同级
        if n_len == 6:  # SSQ
            if road_max <= 3 and road_min >= 1:
                road_score = road_weight * 0.7  # 完美平衡: 核心级奖励
            elif road_max == 4 and road_min >= 1:
                road_score = road_weight * 0.3
            elif road_max <= 4 and road_min == 0:
                road_score = -road_weight * 0.5  # 缺路惩罚
            else:
                road_score = road_weight * 0.15
        elif n_len == 5:  # DLT front
            if road_max <= 2 and road_min >= 1:
                road_score = road_weight * 0.7
            elif road_max == 3 and road_min >= 1:
                road_score = road_weight * 0.3
            elif road_min == 0:
                road_score = -road_weight * 0.5
            else:
                road_score = road_weight * 0.15
        else:
            road_score = 0
        detail['road_012'] = round(road_score, 1)
        total += road_score

        # 区间均衡 — v3.9: 低中高区覆盖奖励
        low_cnt = sum(1 for n in combo if n <= 11)
        high_cnt = sum(1 for n in combo if n >= 23) if num_range == 33 else sum(1 for n in combo if n >= 24)
        mid_cnt = n_len - low_cnt - high_cnt
        if low_cnt >= 1 and mid_cnt >= 1 and high_cnt >= 1:
            zone_score = w.get('odd_even', 10) * 0.6  # 三区均衡奖励
        elif max(low_cnt, mid_cnt, high_cnt) <= n_len - 1:
            zone_score = w.get('odd_even', 10) * 0.2  # 至少两区有号
        else:
            zone_score = -w.get('odd_even', 10) * 0.3  # 集中一区惩罚
        detail['zone_balance'] = round(zone_score, 1)
        total += zone_score
        
        # 冷热均衡 - v4.1 3-4热+2-3冷
        hc = analysis.get('red_hot_cold' if num_range == 33 else 'front_hot_cold', {})
        hot_set = set(hc.get('hot', []))
        warm_set = set(hc.get('warm', []))
        cold_set = set(hc.get('cold', []))
        hot_cnt = sum(1 for n in combo if n in hot_set)
        warm_cnt = sum(1 for n in combo if n in warm_set)
        cold_cnt = sum(1 for n in combo if n in cold_set)
        if hot_cnt >= 2 and cold_cnt >= 2:
            ch_score = w.get('cold_hot', 10) * 0.4  # 均衡奖
        elif cold_cnt == 0:
            ch_score = -w.get('cold_hot', 10) * 0.3  # 全无冷号
        elif hot_cnt == 0:
            ch_score = -w.get('cold_hot', 10) * 0.2  # 全无热号
        else:
            ch_score = 0
        detail['coldhot_balance'] = round(ch_score, 1)
        total += ch_score
        
        # 连号惩罚
        sr2 = sorted(combo)
        cons = sum(1 for i in range(len(sr2) - 1) if sr2[i + 1] == sr2[i] + 1)
        cp = -4 if cons >= 2 else (-2 if cons == 1 else 0) if num_range == 33 else (-2 if cons >= 2 else (-1 if cons == 1 else 0))
        detail['consec_penalty'] = cp
        total += cp
        
        return round(total, 1), detail

    def select_best_ssq(self, analysis, count=5, period_seed=None):
        """多策略投票双色球 - 全量候选池 + 多样性注入"""
        from itertools import combinations
        from database import get_all_ssq
        self._sync_weights_from_cache("ssq")
        
        # 基于期号设置随机种子，保证可复现但不同期不同结果
        if period_seed is not None:
            random.seed(int(period_seed) + 2024000)
        
        scores = self.score_numbers(analysis, 33, 6)
        all_nums = list(range(1, 34))
        
        # === v4.1 候选池: +/-2邻域法(视频方案) 实测3.26/6 ===
        top_by_score = sorted(all_nums, key=lambda n: -scores[n])
        
        # 1) +/-2邻域池: 上期每个号码±1,±2 (覆盖99.6%至少1红)
        last_draw = analysis.get('_last_draw', [])
        plus_minus_pool = set()
        for n in last_draw:
            for d in [-2, -1, 1, 2]:
                v = n + d
                if 1 <= v <= 33:
                    plus_minus_pool.add(v)
        
        # 2) 频率池: 全量频次Top作为补充
        core = top_by_score[:10]
        
        # 2) 遗漏前6名（冷号回补）
        om = analysis.get('red_omission', {})
        top_om = sorted(all_nums, key=lambda n: -om.get(n, 0))[:6]
        
        # 3) 边码候选
        edge_stats = analysis.get('edge_stats', {})
        edge_cands = edge_stats.get('current_edges', [])
        
        # 4) 动量上升前4名
        momentum = analysis.get('momentum_stats', {})
        up_momentum = sorted(all_nums, key=lambda n: -momentum.get(n, {}).get('score', 0))[:4]
        
        # 5) 模式匹配前4名
        pattern = analysis.get('pattern_stats', {}).get('pattern_scores', {})
        top_pattern = sorted(all_nums, key=lambda n: -pattern.get(n, 0))[:4]
        
        # 6) 遗漏回补高分前3名
        rebound = analysis.get('rebound_stats', {})
        top_rebound = sorted(all_nums, key=lambda n: -rebound.get(n, {}).get('rebound_prob', 0))[:3]
        
        # 7) 周期到期前3名
        cycle = analysis.get('cycle_stats', {})
        top_cycle = sorted(all_nums, key=lambda n: -cycle.get(n, {}).get('due_score', 0))[:3]
        
        # v4.1: +/-2邻域池优先 + 频率Top10补充
        candidates = list(plus_minus_pool)
        for n in core:
            if n not in candidates:
                candidates.append(n)
        for n in top_om:
            if n not in candidates:
                candidates.append(n)
        if len(candidates) < 20:
            for n in top_by_score:
                if n not in candidates:
                    candidates.append(n)
                if len(candidates) >= 20:
                    break
        elif len(candidates) > 25:
            candidates = candidates[:30]
        
        # v5.1: 贝叶斯偏差加权 — 物理偏差×1.5 冷号×0.7
        try:
            bd = BiasDetector(ssq_data, 33, 6)
            bias = bd.consensus_bias([100, 300, 1000])
        except:
            bias = {}
        # 分数加微小随机扰动 + 偏差加权
        perturbed_scores = {}
        for n in range(1, 34):
            base = scores.get(n, 0)
            bw = 1.0
            if n in bias:
                bw = 1.0 + bias[n] * 0.15  # z=+2 → 1.3x, z=-2 → 0.7x
                bw = max(0.6, min(1.4, bw))
            perturbed_scores[n] = base * bw * (1 + random.uniform(-0.06, 0.06))
        
        last = analysis.get('_last_draw', [])
        prime_set = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31}
        
        # v5.0: 简化 — +/-2池 + 个号评分, 去掉所有结构约束(已证明无效)
        # 从+/-2池中按个号分数选Top组合
        pool_scores = [(n, perturbed_scores.get(n, 0)) for n in candidates]
        pool_scores.sort(key=lambda x: -x[1])
        # 取前18个做C(18,6)枚举, 只用个号总分排序
        top18 = [n for n,_ in pool_scores[:18]]
        best = []
        for combo in combinations(top18, 6):
            total = sum(perturbed_scores.get(n, 0) for n in combo)
            best.append((round(total, 1), sorted(combo), total, 0, {}))
        best.sort(key=lambda x: -x[0])
        explore_best = []  # v5.0: 探索池不再需要, 简化为空
        
        # 蓝球评分 — v4.0 频率0.4:遗漏0.25:跟随0.15:周期0.2+热号
        blue_scores = {}
        blue_freq = analysis.get('blue_frequency', {})
        blue_om = analysis.get('blue_omission', {})
        blue_follow = analysis.get('blue_follow_stats', {})
        blue_streak = analysis.get('blue_streak', {})
        last_blue = analysis.get('_last_blue', None)
        total_draws = analysis.get('total', 100)
        for n in range(1, 17):
            bv = blue_freq.get(n, 0) * 0.4
            bv += blue_om.get(n, 0) * 0.25
            bs = blue_streak.get(n, {})
            # 周期分析: 当前遗漏 vs 平均周期
            avg_gap = bs.get('avg_gap', 99)
            last_gap = bs.get('last_gap', 0)
            total = bs.get('total_appear', 0)
            if avg_gap < 50 and total > 0:
                expected_cycle = total_draws / max(total, 1)
                cycle_ratio = last_gap / max(expected_cycle, 1)
                if cycle_ratio > 2.0:
                    bv += 2.5  # 严重超期, 回补概率上升
                elif cycle_ratio > 1.5:
                    bv += 1.2
                elif cycle_ratio < 0.3:
                    bv += 0.8  # 刚出过, 可能连出
            # 连出规律
            bv += bs.get('recent_3', 0) * 0.15
            if last_blue and last_blue in blue_follow:
                for fn, fcnt in blue_follow[last_blue]:
                    if fn == n:
                        bv += fcnt * 0.3
            if n in analysis.get('blue_hot', []):
                bv += 3
            blue_scores[n] = bv * (1 + random.uniform(-0.04, 0.04))

        top_blues = sorted(blue_scores.keys(), key=lambda n: -blue_scores[n])[:8]
        bw_b = [max(0.1, blue_scores[n] - blue_scores[top_blues[-1]] + 1) for n in top_blues]
        best_blue = random.choices(top_blues, weights=bw_b, k=1)[0]
        used_blues = {best_blue}  # v3.8: 确保每组蓝球不同
        
        hc = analysis.get('red_hot_cold', {})
        om_d = analysis.get('red_omission', {})
        hh = set(hc.get('hot', []))
        ww = set(hc.get('warm', []))
        
        results = []
        seen = set()
        top_pool = best[:25]
        if top_pool:
            min_score = top_pool[-1][0]
            weights = [max(0.5, b[0] - min_score + 2) for b in top_pool]
            indices = list(range(len(top_pool)))
            for _ in range(min(count * 5, len(top_pool))):
                if len(results) >= count:
                    break
                idx = random.choices(indices, weights=weights, k=1)[0]
                total, reds, ns, cs, det = top_pool[idx]
                key = tuple(reds)
                if key not in seen:
                    seen.add(key)
                    all_detail = dict(det)
                    all_detail['cold_hot_base'] = round(sum(
                        self.weights['cold_hot'] / 6.0 * (1.2 if n in hh else 1.0 if n in ww else 0.3) for n in reds
                    ), 1)
                    all_detail['omission_base'] = round(sum(
                        min(2.5, om_d.get(n, 0) * 0.15 + 0.5) for n in reds
                    ), 1)
                    diverse_blue = random.choices([b for b in top_blues if b not in used_blues] or top_blues, weights=[bw_b[i] for i,b in enumerate(top_blues) if b not in used_blues] or bw_b, k=1)[0]; used_blues.add(diverse_blue)
                    results.append({
                        'reds': list(reds),
                        'blue': diverse_blue,
                        'score': total,
                        'detail': all_detail
                    })
        
        # 强制探索: 加入1个探索组
        if len(results) < count and explore_best:
            for entry in explore_best:
                total, reds, ns, cs, det = entry
                key = tuple(reds)
                if key not in seen:
                    seen.add(key)
                    det = dict(det)
                    det['explore'] = 1
                    diverse_blue = random.choices([b for b in top_blues if b not in used_blues] or top_blues, weights=[bw_b[i] for i,b in enumerate(top_blues) if b not in used_blues] or bw_b, k=1)[0]; used_blues.add(diverse_blue)
                    all_detail = dict(det)
                    all_detail['cold_hot_base'] = round(sum(
                        self.weights['cold_hot'] / 6.0 * (1.2 if n in hh else 1.0 if n in ww else 0.3) for n in reds
                    ), 1)
                    all_detail['omission_base'] = round(sum(
                        min(2.5, om_d.get(n, 0) * 0.15 + 0.5) for n in reds
                    ), 1)
                    all_detail['explore'] = 1
                    results.append({
                        'reds': list(reds),
                        'blue': diverse_blue,
                        'score': total,
                        'detail': all_detail
                    })
                    if len(results) >= count:
                        break

        self.scores_detail = results[0]['detail'] if results else {}
        return results

    def select_best_dlt(self, analysis, count=5, period_seed=None):
        """多策略投票大乐透 - 全量候选池 + 多样性注入"""
        from itertools import combinations
        from database import get_all_dlt
        self._sync_weights_from_cache("dlt")
        
        if period_seed is not None:
            random.seed(int(period_seed) + 2024000)
        
        scores = self.score_numbers(analysis, 35, 5)
        all_nums = list(range(1, 36))
        
        # === v4.1 候选池: +/-2邻域法(实测DLT覆盖~2.3/5) ===
        top_by_score = sorted(all_nums, key=lambda n: -scores[n])
        
        # +/-2邻域池
        last_draw_dlt = analysis.get('_last_draw', [])
        plus_minus_pool = set()
        for n in last_draw_dlt:
            for d in [-2, -1, 1, 2]:
                v = n + d
                if 1 <= v <= 35:
                    plus_minus_pool.add(v)
        
        core = top_by_score[:8]
        om = analysis.get('front_omission', {})
        top_om = sorted(all_nums, key=lambda n: -om.get(n, 0))[:5]
        
        # +/-2邻域优先 + 频率补充
        candidates = list(plus_minus_pool)
        for n in core:
            if n not in candidates:
                candidates.append(n)
        for n in top_om:
            if n not in candidates:
                candidates.append(n)
        if len(candidates) < 18:
            for n in top_by_score:
                if n not in candidates:
                    candidates.append(n)
                if len(candidates) >= 18:
                    break
        # v5.1: 贝叶斯偏差加权
        try:
            bd = BiasDetector(dlt_data, 35, 5)
            bias = bd.consensus_bias([100, 300, 1000])
        except:
            bias = {}
        perturbed_scores = {}
        for n in range(1, 36):
            base = scores.get(n, 0)
            bw = 1.0
            if n in bias:
                bw = 1.0 + bias[n] * 0.15
                bw = max(0.6, min(1.4, bw))
            perturbed_scores[n] = base * bw * (1 + random.uniform(-0.06, 0.06))
        
        last = analysis.get('_last_draw', [])
        prime_set = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31}
        
        # v5.0: 简化 — +/-2池 + 个号评分, 去掉所有结构约束
        pool_scores = [(n, perturbed_scores.get(n, 0)) for n in candidates]
        pool_scores.sort(key=lambda x: -x[1])
        top15 = [n for n,_ in pool_scores[:15]]
        best = []
        for combo in combinations(top15, 5):
            total = sum(perturbed_scores.get(n, 0) for n in combo)
            best.append((round(total, 1), sorted(combo), total, 0, {}))
        best.sort(key=lambda x: -x[0])
        explore_best = []
        
        # 后区评分（加扰动 + 多样性）— v3.7 频率0.6:遗漏0.2:跟随0.2+重号+热门组合
        back_scores = {}
        back_follow = analysis.get('back_follow_stats', {})
        last_backs_raw = analysis.get('_last_backs', [])
        back_repeat_rate = analysis.get('back_repeat_rate', 0.0)
        pair_freq = analysis.get('back_pair_freq', {})
        top_pairs = {p: c for p, c in pair_freq.get('top_pairs', [])}
        # 归一化组号频率(某号参与的组合越多越热)
        pair_num_score = {}
        for pair, cnt in top_pairs.items():
            for n in pair:
                pair_num_score[n] = pair_num_score.get(n, 0) + cnt
        max_pair_score = max(pair_num_score.values()) if pair_num_score else 1
        for n in range(1, 13):
            bv = analysis.get('back_frequency', {}).get(n, 0) * 0.6
            bv += analysis.get('back_omission', {}).get(n, 0) * 0.2
            # 热门组合加分
            if n in pair_num_score:
                bv += (pair_num_score[n] / max_pair_score) * 2.0
            for lb in last_backs_raw:
                for fn, fcnt in back_follow.get(lb, []):
                    if fn == n:
                        bv += fcnt * 0.5
            if n in last_backs_raw:
                bv += back_repeat_rate * 15
            back_scores[n] = bv * (1 + random.uniform(-0.04, 0.04))

        top_backs = sorted(back_scores.keys(), key=lambda n: -back_scores[n])[:10]
        bw = [max(0.5, len(top_backs) - i) for i, n in enumerate(top_backs)]

        def _pick_diverse_backs(used_pairs):
            # v3.7: 优先选择历史高频组合, 兼顾多样性
            # 前3次尝试用高频pair, 之后随机保证多样性
            for attempt in range(20):
                if attempt < 5 and top_pairs:
                    # 倾向于历史高频组合
                    cand_pairs = [(p, c) for p, c in top_pairs.items() if p not in used_pairs]
                    if cand_pairs:
                        cand_pairs.sort(key=lambda x: -x[1])
                        # 前3个高频对中随机选
                        top3 = cand_pairs[:min(3, len(cand_pairs))]
                        weights = [c for _, c in top3]
                        pair = random.choices([p for p, _ in top3], weights=weights, k=1)[0]
                        return list(pair)
                pair = tuple(sorted(random.choices(top_backs, weights=bw, k=2)))
                if pair[0] != pair[1] and pair not in used_pairs:
                    return list(pair)
            return sorted(random.choices(top_backs, weights=bw, k=2))


        results = []
        seen = set()
        used_back_pairs = set()
        # 混合池: 前N-1个来自主流, 最后1个来自探索池
        explore_count = min(1, count // 2 + 1) if explore_best else 0
        main_count = count - explore_count
        top_pool = best[:25]
        if top_pool:
            min_score = top_pool[-1][0]
            weights = [max(0.5, b[0] - min_score + 2) for b in top_pool]
            indices = list(range(len(top_pool)))
            for _ in range(min(count * 5, len(top_pool))):
                if len(results) >= count:
                    break
                idx = random.choices(indices, weights=weights, k=1)[0]
                total, fronts, ns, cs, det = top_pool[idx]
                key = tuple(fronts)
                if key not in seen:
                    seen.add(key)
                    diverse_backs = _pick_diverse_backs(used_back_pairs)
                    used_back_pairs.add(tuple(diverse_backs))
                    results.append({
                        'fronts': list(fronts),
                        'backs': diverse_backs,
                        'score': total,
                        'detail': det
                    })
        # 强制探索: 如果结果少于count且有探索池, 加入1个探索组
        if len(results) < count and explore_best:
            for entry in explore_best:
                total, fronts, ns, cs, det = entry
                key = tuple(fronts)
                if key not in seen:
                    seen.add(key)
                    det = dict(det)
                    det['explore'] = 1
                    diverse_backs = _pick_diverse_backs(used_back_pairs)
                    used_back_pairs.add(tuple(diverse_backs))
                    results.append({
                        'fronts': list(fronts),
                        'backs': diverse_backs,
                        'score': total,
                        'detail': det
                    })
                    if len(results) >= count:
                        break

        self.scores_detail = results[0]['detail'] if results else {}
        return results

    def self_evaluate(self, lottery_type, all_data):
        """Self-evaluate strategy hit rates and adjust weights"""
        try:
            from collections import Counter as _C4
            cand_sizes = {"cold_hot": 6, "omission": 6, "tail": 10, "follow": 4}
            perfs = {k: [] for k in cand_sizes}
            test = all_data[-500:]
            pick = 6 if lottery_type == "ssq" else 5
            for i in range(50, len(test) - 1):
                train = test[:i + 1]
                actual = test[i + 1]
                if lottery_type == "ssq":
                    truth = {actual["red%d" % j] for j in range(1, 7)}
                    import analyzer as _a
                    anl = _a.SSQAnalyzer(train).comprehensive_analysis()
                    last = anl.get("_last_draw", [])
                    om = anl.get("red_omission", {})
                    hc = anl.get("red_hot_cold", {})
                else:
                    truth = {actual["front%d" % j] for j in range(1, 6)}
                    import analyzer as _a
                    anl = _a.DLTAnalyzer(train).comprehensive_analysis()
                    last = anl.get("_last_draw", [])
                    om = anl.get("front_omission", {})
                    hc = anl.get("front_hot_cold", {})
                perfs["cold_hot"].append(sum(1 for n in hc.get("hot", []) if n in truth))
                top_om = set(sorted(om, key=om.get, reverse=True)[:6])
                perfs["omission"].append(len(top_om & truth))
                fs = anl.get("follow_stats", {})
                fh = 0
                if last:
                    for ln in last:
                        if ln in fs:
                            fh += sum(1 for fn, _ in fs[ln][:2] if fn in truth)
                perfs["follow"].append(fh)
            avg_perf = {k: sum(v) / max(len(v), 1) for k, v in perfs.items() if v}
            adj = {}
            for k, v in avg_perf.items():
                total_nums = 33 if lottery_type == "ssq" else 35
                expected = pick * cand_sizes[k] / total_nums
                ratio = v / expected if expected > 0 else 0.5
                ratio = min(ratio, 2.0)
                adj[k] = round(ratio, 2)
                if k in self.weights:
                    self.weights[k] = max(2, min(30, int(self.weights[k] * ratio)))
            return adj
        except:
            return {}
