with open(r"C:\Users\Administrator\Documents\彩票选票机\analyzer.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Fix line 1254 (0-indexed 1253): wrong indentation
lines[1253] = "        candidates = candidates[:22]\n"

with open(r"C:\Users\Administrator\Documents\彩票选票机\analyzer.py", "w", encoding="utf-8") as f:
    f.writelines(lines)

import py_compile
py_compile.compile(r"C:\Users\Administrator\Documents\彩票选票机\analyzer.py", doraise=True)
print("Syntax OK - indentation fixed")
