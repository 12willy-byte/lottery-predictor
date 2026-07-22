
"""
V5.4 CRF Prediction Engine
Drop-in replacement for gui.py prediction generation
"""
import sqlite3, json, math, os, numpy as np
from collections import Counter, defaultdict
from datetime import datetime

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "lottery.db")

class CRFBeamSearch:
    """Lightweight CRF with Beam Search"""
    
    def __init__(self, data, num_range, seq_len, beam_width=15):
        self.R = num_range
        self.L = seq_len
        self.data = data
        self.N = len(data)
        self.beam_width = beam_width
        self._fit()
    
    def _fit(self):
        self.emit_mean = np.zeros(self.L)
        self.emit_std = np.ones(self.L) * 3
        pos_data = [[] for _ in range(self.L)]
        for reds in self.data:
            for i, r in enumerate(reds): pos_data[i].append(r)
        for i in range(self.L):
            vals = pos_data[i]
            self.emit_mean[i] = np.mean(vals)
            self.emit_std[i] = max(np.std(vals), 1.5)
        
        self.trans_mean = np.zeros(self.L - 1)
        self.trans_std = np.ones(self.L - 1) * 2
        for i in range(self.L - 1):
            gaps = [self.data[j][i+1] - self.data[j][i] for j in range(self.N)]
            self.trans_mean[i] = np.mean(gaps)
            self.trans_std[i] = max(np.std(gaps), 1.0)
    
    def beam_decode(self, boost=None, k=5):
        beam = [(0.0, [])]
        for pos in range(self.L):
            candidates = []
            for beam_score, partial in beam:
                start = partial[-1] + 1 if partial else 1
                end = self.R - (self.L - pos - 1) + 1
                for n in range(start, end):
                    new_seq = partial + [n]
                    score = beam_score
                    ez = (n - self.emit_mean[pos]) / self.emit_std[pos]
                    score += -0.5 * ez * ez
                    if boost and n in boost:
                        score += boost[n]
                    if pos > 0:
                        gap = n - partial[-1]
                        tz = (gap - self.trans_mean[pos-1]) / self.trans_std[pos-1]
                        score += -0.5 * tz * tz
                    candidates.append((score, new_seq))
            candidates.sort(reverse=True)
            beam = candidates[:self.beam_width]
        
        beam.sort(reverse=True)
        results = []
        used_pairs = set()
        for score, seq in beam:
            overlap_penalty = 0
            for _, prev_seq in results:
                overlap = len(set(seq) & set(prev_seq))
                if overlap > 3:
                    overlap_penalty += (overlap - 3) * 2.0
            adj_score = score - overlap_penalty
            results.append((adj_score, seq))
        results.sort(reverse=True)
        return [(s, seq) for s, seq in results[:k]]


# Cache
_crf_ssq = None
_crf_dlt = None
_ssq_data = None
_dlt_data = None
_weights_cache = None

def _load_data():
    global _ssq_data, _dlt_data
    if _ssq_data is not None:
        return
    conn = sqlite3.connect(DB)
    c = conn.execute("SELECT red1,red2,red3,red4,red5,red6 FROM ssq ORDER BY period")
    _ssq_data = [sorted([int(r[i]) for i in range(6)]) for r in c.fetchall()]
    c2 = conn.execute("SELECT front1,front2,front3,front4,front5 FROM dlt ORDER BY period")
    _dlt_data = [sorted([int(r[i]) for i in range(5)]) for r in c2.fetchall()]
    conn.close()

def _load_blue_data():
    conn = sqlite3.connect(DB)
    c = conn.execute("SELECT blue FROM ssq ORDER BY period")
    blues = [int(r[0]) for r in c.fetchall()]
    conn.close()
    return blues

def predict_ssq(k=5):
    """Generate SSQ predictions. Returns list of {reds, blue, score}"""
    global _crf_ssq, _weights_cache
    _load_data()
    
    if _crf_ssq is None:
        _crf_ssq = CRFBeamSearch(_ssq_data, 33, 6, beam_width=15)
    
    # Load learned weights
    wf = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "v54_breakthrough.json")
    if _weights_cache is None and os.path.exists(wf):
        with open(wf, encoding="utf-8") as f:
            _weights_cache = json.load(f)
    
    # Bias
    freq = Counter()
    for reds in _ssq_data:
        for n in reds: freq[n] += 1
    N = len(_ssq_data)
    exp_r = N * 6.0 / 33
    std_r = math.sqrt(N * 6.0 / 33 * 27.0 / 33)
    
    if _weights_cache and "learned_weights_ssq" in _weights_cache:
        w = _weights_cache["learned_weights_ssq"]["best_weights"]
    else:
        w = [0.30, 0.40, 0.20, 0.10]  # Default from grid search
    
    boost = {}
    for n in range(1, 34):
        z = (freq[n] - exp_r) / max(std_r, 0.01)
        boost[n] = z * w[0]
    
    # Neighbor boost
    last = _ssq_data[-1]
    pool = set()
    for n in last:
        for d in [-2, -1, 0, 1, 2]:
            v = n + d
            if 1 <= v <= 33: pool.add(v)
    for n in pool:
        boost[n] = boost.get(n, 0) + w[3]
    
    preds = _crf_ssq.beam_decode(boost=boost, k=k)
    
    # Blue ball prediction
    blues = _load_blue_data()
    last_blue = blues[-1]
    
    # Markov transition
    trans = defaultdict(lambda: defaultdict(int))
    for i in range(len(blues)-1):
        trans[blues[i]][blues[i+1]] += 1
    
    bfreq = Counter(blues)
    bscores = {}
    for b in range(1, 17):
        s = bfreq.get(b, 0) / len(blues) * 0.3
        if last_blue in trans:
            tot = sum(trans[last_blue].values())
            if tot > 0:
                s += trans[last_blue].get(b, 0) / tot * 0.4
        recent = blues[-30:]
        s += recent.count(b) / 30 * 0.2
        om = 0
        for i in range(len(blues)-1, -1, -1):
            if blues[i] == b: break
            om += 1
        s += min(om / 50, 1.0) * 0.1
        bscores[b] = s
    
    top_blues = sorted(bscores, key=bscores.get, reverse=True)[:3]
    
    results = []
    for i, (score, seq) in enumerate(preds):
        results.append({
            "reds": [int(x) for x in seq],
            "blue": top_blues[i % len(top_blues)],
            "score": round(score, 2)
        })
    
    return results

def predict_dlt(k=5):
    """Generate DLT predictions. Returns list of {reds, blues, score}"""
    global _crf_dlt, _weights_cache
    _load_data()
    
    if _crf_dlt is None:
        _crf_dlt = CRFBeamSearch(_dlt_data, 35, 5, beam_width=15)
    
    wf = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "v54_breakthrough.json")
    if _weights_cache is None and os.path.exists(wf):
        with open(wf, encoding="utf-8") as f:
            _weights_cache = json.load(f)
    
    freq = Counter()
    for reds in _dlt_data:
        for n in reds: freq[n] += 1
    N = len(_dlt_data)
    exp_r = N * 5.0 / 35
    std_r = math.sqrt(N * 5.0 / 35 * 30.0 / 35)
    
    if _weights_cache and "learned_weights_dlt" in _weights_cache:
        w = _weights_cache["learned_weights_dlt"]["best_weights"]
    else:
        w = [0.20, 0.30, 0.30, 0.20]
    
    boost = {}
    for n in range(1, 36):
        z = (freq[n] - exp_r) / max(std_r, 0.01)
        boost[n] = z * w[0]
    
    last = _dlt_data[-1]
    pool = set()
    for n in last:
        for d in [-2, -1, 0, 1, 2]:
            v = n + d
            if 1 <= v <= 35: pool.add(v)
    for n in pool:
        boost[n] = boost.get(n, 0) + w[3]
    
    preds = _crf_dlt.beam_decode(boost=boost, k=k)
    
    # DLT back zone
    conn = sqlite3.connect(DB)
    c = conn.execute("SELECT back1, back2 FROM dlt ORDER BY period")
    all_backs = [(int(r[0]), int(r[1])) for r in c.fetchall()]
    conn.close()
    
    bfreq = Counter()
    for b1, b2 in all_backs:
        bfreq[b1] += 1; bfreq[b2] += 1
    top_b = sorted(range(1, 13), key=lambda b: bfreq.get(b, 0), reverse=True)
    
    results = []
    for i, (score, seq) in enumerate(preds):
        results.append({
            "reds": [int(x) for x in seq],
            "blues": [top_b[i*2 % 12], top_b[(i*2+1) % 12]],
            "score": round(score, 2)
        })
    
    return results
