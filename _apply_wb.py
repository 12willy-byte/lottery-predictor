import os
os.chdir(r"C:\Users\Administrator\Documents\彩票选票机")

with open("analyzer.py", "r", encoding="utf-8") as f:
    content = f.read()

# DLT scoring: use ALL-TIME frequency as dominant (proven by walkback +13.6%)
# Find the DLT scoring block
old_dlt_block = """            if is_dlt:
                # DLT: 频率主导 + 全量频率修正(过滤伪热号)
                recent_f = 1.2 if n in hot_set else (1.0 if n in warm_set else 0.5)
                # 全量频率因子: 缩小近期暴涨和长期冷号的差距
                alltime_freq = analysis.get('front_frequency', {}).get(n, 0)
                alltime_max = max(analysis.get('front_frequency', {}).values()) if analysis.get('front_frequency') else 1
                alltime_f = 0.5 + 0.5 * (alltime_freq / max(alltime_max, 1))
                freq_factor = recent_f * 0.6 + alltime_f * 0.4
                s += w['cold_hot'] / pick_cnt * freq_factor * 0.9"""

new_dlt_block = """            if is_dlt:
                # DLT: 全量频率主导(走回验证+13.6%), 近50期仅参考, 遗漏负信号减权
                alltime_freq = analysis.get('front_frequency', {}).get(n, 0)
                alltime_max = max(analysis.get('front_frequency', {}).values()) if analysis.get('front_frequency') else 1
                alltime_f = alltime_freq / max(alltime_max, 1)
                recent_f = (1.2 if n in hot_set else (1.0 if n in warm_set else 0.5))
                freq_factor = alltime_f * 0.7 + recent_f * 0.3
                s += w['cold_hot'] / pick_cnt * freq_factor"""

if old_dlt_block in content:
    content = content.replace(old_dlt_block, new_dlt_block)
    print("DLT scoring: 全量频率70% + 近50期30% (走回验证)")
else:
    print("Pattern not found")

with open("analyzer.py", "w", encoding="utf-8") as f:
    f.write(content)

import py_compile
py_compile.compile("analyzer.py", doraise=True)
print("Syntax OK")
