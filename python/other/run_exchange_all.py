# -*- coding: utf-8 -*-
"""
打ち切り後の 0 埋めを「最終記録値」で置き換える（1タイプ分）

■ 旧版からの変更点（重要）
  旧版は df.replace(0, None).ffill() で「すべての 0」を直前値に置換していたため、
  実行途中で本当に 0 になった値（例: C Rate High が一時的に 0、C が絶滅して C Rate = 0）まで
  直前の値で上書きされていた。
  新版は「打ち切り後の未記録部分（末尾）」だけを最終記録値で埋める。
    ・各記録行では 協力率 + D率 = 1 なので、Base と D のどちらかは必ず非 0。
      → 末尾から見て Base か D が非 0 の最後の行 = 最後の記録行 n_valid-1 と確定できる。
    ・Base / C / PC / D の4ファイルを同じ n_valid で揃えて埋める。
  改修版 run_simulation.py の出力（zip 内に _PADDED_v2.txt がある）は既に埋め済みなのでスキップする。

使い方:
  python run_exchange_all.py shunning +0.6-0.2-0.6+0.2+1-0.6 shunningデータ 0.1 [--seed 0] [--variant _T100000]
"""
import zipfile
import pandas as pd
import numpy as np
import io
import os
import sys
import argparse

from experiment_config import root_dir, seed_suffix, ALL_Z

ap = argparse.ArgumentParser()
ap.add_argument("modelPATTERN", nargs="?", default="shunning")
ap.add_argument("PATTERN", nargs="?", default="+0.6-0.2-0.6+0.2+1-0.6")
ap.add_argument("datePATTERN", nargs="?", default="shunningデータ")
ap.add_argument("omega", nargs="?", type=float, default=0.1)
ap.add_argument("--seed", type=int, default=None)
ap.add_argument("--variant", type=str, default="")
ap.add_argument("--zs", type=str, default=",".join(map(str, ALL_Z)))
a = ap.parse_args()
modelPATTERN, PATTERN, datePATTERN, omega = a.modelPATTERN, a.PATTERN, a.datePATTERN, a.omega
SFX = seed_suffix(a.seed)
ROOT = root_dir(datePATTERN, PATTERN, a.variant)

print(f"🔧 [設定] model: {modelPATTERN} | pattern: {PATTERN} | date: {datePATTERN} | omega: {omega} | seed: {a.seed} | variant: '{a.variant}'")

TYPES = ["", "C", "PC", "D"]
MARKER = "_PADDED_v2.txt"


def zip_path(Z, t):
    sub = f"/{t}" if t else ""
    prefix = f"{modelPATTERN}_{t}" if t else modelPATTERN
    return f"{ROOT}{sub}/{prefix}_Z={Z}_r=3.0_{PATTERN}_omega={omega}{SFX}.zip"


def read_all(path):
    with zipfile.ZipFile(path, "r") as z:
        names = z.namelist()
        data = {n: pd.read_csv(io.BytesIO(z.read(n))) for n in names if n.endswith(".csv")}
        others = {n: z.read(n) for n in names if not n.endswith(".csv")}
    return data, others


def csv_key(name, t):
    """CSV名から b 部分を取り出して、タイプ間で対応づけるキーにする"""
    i = name.find("_b=")
    return name[i:] if i >= 0 else name


def last_valid_row(df):
    nz = np.flatnonzero((df.values != 0).any(axis=1))
    return int(nz[-1]) + 1 if nz.size else 0


def process_Z(Z):
    paths = {t: zip_path(Z, t) for t in TYPES}
    if not os.path.exists(paths[""]):
        print(f"⚠️ スキップ: ファイルが存在しません -> {paths['']}")
        return
    with zipfile.ZipFile(paths[""]) as z:
        if MARKER in z.namelist():
            print(f"⏭️ 埋め済み（新形式）: Z={Z}")
            return

    contents = {t: read_all(p) for t, p in paths.items() if os.path.exists(p)}
    base_data = contents[""][0]
    d_data = contents["D"][0] if "D" in contents else {}
    d_by_key = {csv_key(n, "D"): df for n, df in d_data.items()}

    # b ごとに最後の記録行 n_valid を決める（Base と D のどちらかが非0の最後の行）
    n_valid = {}
    for n, df in base_data.items():
        k = csv_key(n, "")
        nv = last_valid_row(df)
        if k in d_by_key:
            nv = max(nv, last_valid_row(d_by_key[k]))
        n_valid[k] = nv

    for t, (data, others) in contents.items():
        out_path = paths[t] + ".temp"
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf_out:
            for n, df in data.items():
                nv = n_valid.get(csv_key(n, t), last_valid_row(df))
                if 0 < nv < len(df):
                    df.iloc[nv:] = df.iloc[nv - 1].values      # 末尾だけを最終記録値で埋める
                buf = io.StringIO()
                df.to_csv(buf, index=False)
                zf_out.writestr(n, buf.getvalue())
            for n, raw in others.items():
                zf_out.writestr(n, raw)
            zf_out.writestr(MARKER, "tail rows padded by run_exchange_all.py (v2)\n")
        try:
            os.replace(out_path, paths[t])
            print(f"✅ 保存完了: {paths[t]}")
        except Exception as e:
            print(f"❌ エラー発生 ({paths[t]}): {e}")


if __name__ == "__main__":
    for Z in [int(z) for z in a.zs.split(",")]:
        process_Z(Z)
    print(f"\n🎉 {modelPATTERN} / {PATTERN} / omega={omega} の全置換処理が完了しました！")
