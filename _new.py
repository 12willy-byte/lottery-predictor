import sys, os
os.chdir(r"C:\Users\Administrator\Documents\彩票选票机")
sys.path.insert(0, ".")
from database import init_db, get_all_ssq, get_all_dlt
init_db()
s = get_all_ssq()
d = get_all_dlt()
print(f"SSQ: {len(s)}期 最新{s[-1]['period']}期")
print(f"  红: {[s[-1]['red%d'%j] for j in range(1,7)]} 蓝: {s[-1]['blue']}")
print(f"DLT: {len(d)}期 最新{d[-1]['period']}期")
print(f"  前: {[d[-1]['front%d'%j] for j in range(1,6)]} 后: ({d[-1]['back1']},{d[-1]['back2']})")
# Show last 2 periods for context
print(f"\n最近2期:")
for dd in s[-2:]:
    print(f"  SSQ{dd['period']}: 红{[dd['red%d'%j] for j in range(1,7)]} 蓝{dd['blue']}")
for dd in d[-2:]:
    print(f"  DLT{dd['period']}: 前{[dd['front%d'%j] for j in range(1,6)]} 后({dd['back1']},{dd['back2']})")
