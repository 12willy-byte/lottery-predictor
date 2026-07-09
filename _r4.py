with open("analyzer.py", "r", encoding="utf-8") as f:
    content = f.read()
# Find STRATEGY_WEIGHTS
idx = content.find("STRATEGY_WEIGHTS")
print(content[idx:idx+300])
print("---BONUS---")
idx2 = content.find("BONUS_WEIGHTS")
print(content[idx2:idx2+300])
