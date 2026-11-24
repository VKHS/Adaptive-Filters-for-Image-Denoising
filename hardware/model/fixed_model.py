"""Independent integer replay of all six golden transaction streams (stdlib only).

This is an arithmetic reference, not an HDL simulation.
Run from any directory: python3 hardware/model/fixed_model.py
"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
Q = 4096
WIDTHS = {"a": 2, "b": 1, "c": 1, "d": 25, "e": 81, "f": 1}


def sat(x):
    return max(-32768, min(32767, x))


def words(h, count):
    v = int(h, 16)
    ans = []
    for _ in range(count):
        t = v & 65535
        ans.append(t - 65536 if t >= 32768 else t)
        v >>= 16
    assert v == 0
    return ans


def mask(window, r, h):
    k = 2*r+1
    return [v for j, v in enumerate(window)
            if max(abs(j//k-r), abs(j%k-r)) > h]


class LMS:
    def __init__(self, taps, mu_shift, initial=0):
        self.w = [initial]*taps
        self.shift = mu_shift

    def step(self, d, target, x, adapt, mode=0, threshold=0, bypass=False):
        assert len(x) == len(self.w)
        pred = 0 if bypass else sat(sum(w*t for w,t in zip(self.w,x)) >> 12)
        err = target-pred
        flag = mode == 2 and abs(err) > threshold and not bypass
        if bypass:
            y = d
        elif mode == 1:
            y = pred
        elif mode == 2:
            y = pred if flag else d
        else:
            y = sat(d-pred)
        if adapt and not bypass and not flag:
            self.w = [sat(w+((err*t) >> (12+self.shift))) for w,t in zip(self.w,x)]
        return [y,pred,err,int(flag)]


def replay(case):
    config = {"a": (2,3,0), "c": (4,3,0), "d": (24,5,170),
              "e": (56,5,0), "f": (1,3,0)}
    core = LMS(*config[case]) if case != "b" else None
    bias = 0
    history = []
    results = []
    for i,line in enumerate((ROOT/"vectors"/(case+".txt")).read_text().splitlines()):
        v = line.split()
        assert len(v) == 13, (case,i)
        d,t,prev,slow,adapt,gate,row,th = map(int,v[:8])
        x = words(v[8],WIDTHS[case])
        expected = list(map(int,v[9:]))
        if case == "b":
            if row:
                bias = 0
            if adapt:
                e = d-prev-bias
                bias = sat(bias+64*((e>0)-(e<0)))
            actual = [d if adapt else sat(d-bias+slow),bias,0,int(not adapt)]
        elif case == "c":
            if row:
                history.clear()
            bypass = len(history)<5
            refs = (history+[0]*5)[1:5]
            actual = core.step(d,t,refs,adapt,bypass=bypass)
            history = [t]+history[:4]
        elif case == "d":
            actual = core.step(d,t,mask(x,2,0),adapt,2 if gate else 1,th)
        elif case == "e":
            actual = core.step(d,t,mask(x,4,2),adapt,1)
        else:
            actual = core.step(d,t,x,adapt)
        assert actual == expected, f"{case.upper()} #{i}: {actual} != {expected}"
        results.append(actual)
    assert results
    # Properties independent of the stored per-transaction expected columns.
    if case == "a":
        assert max(abs(x[0]-512) for x in results[-8:]) < 15
    elif case == "b":
        assert results[19][1] == 512 and results[27][0] == 2246 and results[47][1] == -384
    elif case == "c":
        assert all(x[1]==0 for x in results[:5]+results[192:197])
        assert max(abs(x[0]-1500) for x in results[-16:]) < 45
    elif case == "d":
        assert sum(x[3] for x in results) >= 4
    elif case == "e":
        assert max(abs(x[0]-(768 if i%2==0 else -768)) for i,x in enumerate(results[-16:])) < 80
    elif case == "f":
        assert max(abs(x[0]-2048) for x in results[-18:-2]) < 30
        assert [x[0] for x in results[-2:]] == [32767,-32768]
    print(f"PASS {case.upper()}: {len(results)} integer transactions")
    return len(results)


if __name__ == "__main__":
    total = sum(replay(c) for c in "abcdef")
    stored = json.loads((ROOT/"results"/"reference_smoke.json").read_text())
    assert total == stored["total_transactions"]
    print(f"PASS: all six fixed-point reference streams ({total} transactions)")
