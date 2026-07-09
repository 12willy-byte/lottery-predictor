# -*- coding: utf-8 -*-
"""选号策略增强模块 v3.0"""
import math
from collections import Counter, defaultdict
from itertools import combinations
PHI=(1+math.sqrt(5))/2;PHI_INV=1/PHI
def golden_points(num_range,count=5):
 pts=set()
 for i in range(count):
  p=round(num_range*PHI_INV**i)
  if 1<=p<=num_range:pts.add(p)
  q=round(num_range*(1-PHI_INV**i))
  if 1<=q<=num_range:pts.add(q)
 return sorted(pts)
