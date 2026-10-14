# -*- coding: utf-8 -*-
"""
等価性テスト: 改修版 run_simulation.py が旧コードと同じダイナミクスを再現するかを確認する。

  旧コード（run_simulation_old.py）に「同じ seed」と「小さい L・短い MCS」を差し込んで実行し、
  改修版（--seed 指定）の出力と比較する。
    ・協力率/C/PC/D の CSV : 記録済みの行が完全一致すること（打ち切り後の埋め値は除外）
    ・罰の回数 CSV          : 完全一致
    ・ペイオフ CSV          : 1e-4 以内（ベクトル化で加算順が変わるため丸め誤差のみ許容）

使い方（python/other で）:
  python test_equivalence.py               # 既定の条件セット
  python test_equivalence.py --L 30 --steps 500
"""
import argparse, io, os, re, shutil, subprocess, sys, tempfile, zipfile
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CASES = [
    ("image", "+5+1-5-1+5+1", "imageデータ", "0.01", "90"),
    ("shunning", "+1-0.2-1+0.2+2-1", "shunningデータ", "0.1", "70"),
    ("stern", "+5-1-5+1+8-3", "sternデータ", "0.1", "90"),
    ("simple", "+1+0.2-1+0.2+1.6+0.6", "simpleデータ", "0.01", "60"),
]

def make_old(src, dst, L, steps, seed, bs):
    code = open(src, encoding="utf-8").read()
    code = re.sub(r"^L = 100$", f"L = {L}", code, flags=re.M)
    code = re.sub(r"^num_steps = 10000$", f"num_steps = {steps}", code, flags=re.M)
    code = code.replace("for b in [0, 0.2, 0.4, 0.6, 0.8, 1.0]:",
                        f"for b in {bs}:\n            random.seed({seed}); np.random.seed({seed})")
    open(dst, "w", encoding="utf-8").write(code)

def read_zip(path):
    out = {}
    with zipfile.ZipFile(path) as z:
        for n in z.namelist():
            if n.endswith(".csv"):
                out[n] = pd.read_csv(io.BytesIO(z.read(n)))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", default=os.path.join(HERE, "run_simulation_old.py"))
    ap.add_argument("--L", type=int, default=20)
    ap.add_argument("--steps", type=int, default=300)
    ap.add_argument("--seed", type=int, default=12345)
    a = ap.parse_args()
    bs = [0, 1.0]
    ok_all = True
    work = tempfile.mkdtemp(prefix="eqtest_")
    try:
        for model, pat, date, w, z in CASES:
            ref_dir = os.path.join(work, "ref", "x", "y"); new_dir = os.path.join(work, "new", "x", "y")
            for d in (ref_dir, new_dir):
                shutil.rmtree(os.path.dirname(os.path.dirname(d)), ignore_errors=True); os.makedirs(d)
            make_old(a.old, os.path.join(ref_dir, "run_simulation.py"), a.L, a.steps, a.seed, bs)
            for f in ("run_simulation.py", "experiment_config.py"):
                shutil.copy(os.path.join(HERE, f), new_dir)
            env = dict(os.environ, PYTHONIOENCODING="utf-8")
            subprocess.run([sys.executable, "run_simulation.py", model, pat, date, w, z],
                           cwd=ref_dir, check=True, capture_output=True, env=env)
            subprocess.run([sys.executable, "run_simulation.py", model, pat, date, w, z, "--seed", str(a.seed),
                            "--L", str(a.L), "--steps", str(a.steps), "--bs", "0,1.0"],
                           cwd=new_dir, check=True, capture_output=True, env=env)
            ref_root = os.path.join(work, "ref", date, "Z_b_change報酬罰", pat)
            new_root = os.path.join(work, "new", date, "Z_b_change報酬罰" + ("" if a.steps == 10000 else f"_T{a.steps}"), pat)
            for sub, prefix in [("", f"{model}_"), ("C", f"{model}_C_"), ("PC", f"{model}_PC_"), ("D", f"{model}_D_"),
                                ("Punish", "punish_history_"), ("Payoff", "payoff_history_")]:
                rz = os.path.join(ref_root, sub, f"{prefix}Z={z}_r=3.0_{pat}_omega={w}.zip")
                nz = os.path.join(new_root, sub, f"{prefix}Z={z}_r=3.0_{pat}_omega={w}_seed={a.seed}.zip")
                R_, N_ = read_zip(rz), read_zip(nz)
                for name, rdf in R_.items():
                    ndf = N_[name]
                    if sub == "Payoff":
                        good = np.allclose(rdf.values, ndf.values, atol=1e-4)
                    elif sub == "Punish":
                        good = rdf.equals(ndf)
                    else:
                        # 旧コードは打ち切り後が 0。記録済み行（どこかの列が非0の最後の行まで）を比較
                        nz_rows = np.flatnonzero((rdf.values != 0).any(axis=1))
                        n = nz_rows[-1] + 1 if nz_rows.size else 1
                        good = np.array_equal(rdf.values[:n], ndf.values[:n])
                    ok_all &= good
                    print(f"{'OK ' if good else 'NG '} {model:9s} {pat:24s} {sub or 'Base':7s} {name}")
    finally:
        shutil.rmtree(work, ignore_errors=True)
    print("\n=== 結果:", "すべて一致（計算ロジック不変）" if ok_all else "不一致あり", "===")
    sys.exit(0 if ok_all else 1)

if __name__ == "__main__":
    main()
