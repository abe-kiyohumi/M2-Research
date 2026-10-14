# -*- coding: utf-8 -*-
"""
3次評判評価 × 評判ベース確率的罰 を持つ空間公共財ゲーム（1条件の実行）

従来の出力（協力率・C・PC・D・罰の回数・ペイオフの zip）はそのまま残し、
考察用の詳細ログ L1〜L8 を追加で保存する。

■ 計算ロジックは変更していない（seed を固定すれば旧コードと協力率が一致する。test_equivalence.py で確認）
  ・乱数（random / np.random）の消費順序は旧コードと同一。ログ計算は乱数を一切使わない。
  ・毎MCS末の全プレイヤーのペイオフ計算（旧: 二重 for ループ）は numpy でベクトル化したが、
    罰判定に使う random.random() の呼び出し回数・順序（D の行優先順 × 5グループ）は旧コードと同一。
    → ダイナミクスは不変で、実行時間だけ短縮される。

■ 使い方（位置引数は従来どおり）
  python run_simulation.py image +5+1-5-1+5+1 imageデータ 0.01 90
  python run_simulation.py image +5+1-5-1+5+1 imageデータ 0.01 90 --seed 0 --bs 0,1.0
  オプション:
    --seed N        乱数シード（未指定なら従来どおり非固定。全 b で同じ seed = 同じ初期配置）
    --bs 0,0.2,...  実行する b のリスト
    --steps N       MCS 数（既定 10000）
    --no-log        詳細ログ L1〜L8 を保存しない
    --reset-rep {none,uniform,mid}  対照実験: 戦略切替時に評判をリセット（uniform: 1〜100一様, mid: 50）
    --stop {legacy,mono}            legacy: C+PC=0 or 1 で打ち切り（従来） / mono: 単一戦略になるまで続ける
    --rep-fix       対照実験: 評判更新後に round(R, 6) して 1/5 スケールの浮動小数点誤差を除去
"""
import numpy as np
import random
import math
import pandas as pd
import os
import time
import zipfile
import io
import sys
import re
import json
import argparse
import hashlib
import datetime
import platform

from experiment_config import (make_variant, root_dir, seed_suffix, log_zip_path,
                               b_label, pattern_scale, TYPE_NAME)

# ==========================================
# 0. 引数の受け取りと設定
# ==========================================
def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("typePATTERN", nargs="?", default="image")
    p.add_argument("PATTERN", nargs="?", default="+0.6+0.2-0.6-0.2+1+0.6")
    p.add_argument("datePATTERN", nargs="?", default="imageデータ")
    p.add_argument("omega", nargs="?", type=float, default=0.1)
    p.add_argument("Z", nargs="?", type=int, default=50)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--bs", type=str, default="0,0.2,0.4,0.6,0.8,1.0")
    p.add_argument("--steps", type=int, default=10000)
    p.add_argument("--L", type=int, default=100)            # 動作確認用（本番は 100）
    p.add_argument("--no-log", action="store_true")
    p.add_argument("--reset-rep", choices=["none", "uniform", "mid"], default="none")
    p.add_argument("--stop", choices=["legacy", "mono"], default="legacy")
    p.add_argument("--rep-fix", action="store_true")
    p.add_argument("--cluster-every", type=int, default=10)  # L7 のクラスター計算間隔 [MCS]
    return p.parse_args()

args = parse_args()
typePATTERN = args.typePATTERN
PATTERN = args.PATTERN
datePATTERN = args.datePATTERN
omega = args.omega
Z = args.Z
SEED = args.seed
B_LIST = [float(x) for x in args.bs.split(",") if x.strip() != ""]
VARIANT = make_variant(args.steps, args.reset_rep, args.stop, args.rep_fix)
DO_LOG = not args.no_log

print(f"🔧 [設定] type: {typePATTERN} | pattern: {PATTERN} | date: {datePATTERN} | omega: {omega} | Z: {Z} "
      f"| seed: {SEED} | b: {B_LIST} | steps: {args.steps} | variant: '{VARIANT}'")

def parse_pattern(pattern_str):
    """PATTERNから6つの数値を抽出し、絶対値のリストを返す"""
    numbers = [abs(float(x)) for x in re.findall(r'[+-]?\d+(?:\.\d+)?', pattern_str)]
    if len(numbers) != 6:
        raise ValueError(f"PATTERN のフォーマットが不正です（6つの数値が必要です）: {pattern_str}")
    return numbers

p_vals = parse_pattern(PATTERN)
print("パターン", p_vals)
if typePATTERN not in ("image", "shunning", "stern", "simple"):
    raise ValueError(f"未知の評価ルールです: {typePATTERN}")
if not (0.0 <= omega <= 1.0):
    raise ValueError(f"omega は 0〜1 で指定してください: {omega}")
if not (0 < Z <= 100):
    raise ValueError(f"Z は 1〜100 で指定してください: {Z}")

# 定数設定（旧コードと同一）
L = args.L
G = 5
R = 3.0
K = 0.5
alpha = 0.1
beta = 1.0
num_steps = args.steps
N = L * L
RECORD_INTERVAL = 1000                        # 協力率は 1000 更新ごとに記録（L=100 で 0.1MCS 刻み）
REC_PER_MCS = (N + RECORD_INTERVAL - 1) // RECORD_INTERVAL

ROOT = root_dir(datePATTERN, PATTERN, VARIANT)
OUTPUT_DIR        = ROOT
OUTPUT_DIR_C      = f"{ROOT}/C"
OUTPUT_DIR_PC     = f"{ROOT}/PC"
OUTPUT_DIR_D      = f"{ROOT}/D"
OUTPUT_DIR_PUNISH = f"{ROOT}/Punish"
OUTPUT_DIR_PAYOFF = f"{ROOT}/Payoff"
OUTPUT_DIRS = [OUTPUT_DIR, OUTPUT_DIR_C, OUTPUT_DIR_PC, OUTPUT_DIR_D, OUTPUT_DIR_PUNISH, OUTPUT_DIR_PAYOFF]

# スナップショット時刻（MCS=t は「t MCS 完了後」, t=0 は初期状態）
L3_TIMES = sorted({t for t in [0, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000,
                               20000, 50000, 100000, 200000, 500000, 1000000] if t <= num_steps} | {num_steps})
L4_TIMES = sorted({t for t in [0, 10, 100, 1000, 3000, 10000, 30000, 100000, 300000, 1000000]
                   if t <= num_steps} | {num_steps})
HIST_EDGES = np.arange(0, 101, 1)              # L3: 評判ヒストグラム 幅1（後で5刻みに集約可能）

# ==========================================
# 1. 近傍テーブルの事前計算（周期境界）
#    旧コードと同じ並び順: 上(i-1), 下(i+1), 左(j-1), 右(j+1), 自分
# ==========================================
NB5 = [[[((i - 1) % L, j), ((i + 1) % L, j), (i, (j - 1) % L), (i, (j + 1) % L), (i, j)]
         for j in range(L)] for i in range(L)]
# 自分を中心とするグループ = NB5 と同じ集合なので、グループ構成員表としても使う
GROUP = NB5

# ==========================================
# 2. 共通関数 & 増減表に基づく評判更新（旧コードと同一の演算）
# ==========================================
def initialize_grid():
    values = np.ones(L * L)
    values[L * L // 2:] = -1
    values[:L * L // 4] = 2
    np.random.shuffle(values)
    return values.reshape(L, L)

def initialize_reputationgrid():
    return np.random.randint(1, 101, size=(L, L)).astype(np.float64)

def cal_f(Z, reputationgrid, b, i, j):
    # 罰確率 f = ((Z-R)/Z)^b  (R<Z), 0 (R>=Z)
    rep_val = reputationgrid[i, j]
    return ((Z - rep_val) / Z) ** b if rep_val < Z else 0.0

def game(i, j, Nc, NPc, grid, reputationgrid, grp, count_punish, Z, b):
    """1グループ分のペイオフ。D の罰判定で random.random() を1回消費する（旧コードと同じ）"""
    g_val = grid[i, j]
    base_payoff = (R * (Nc + NPc)) / G
    if g_val == 1:
        return base_payoff - 1.0, count_punish
    elif g_val == 2:
        # KD: グループ内の「低評判(R<Z)の」D の人数（旧 cal_KD と同一。※PDFの記述「D人数」とは異なる）
        KD = 0
        for n in grp:
            if grid[n] == -1 and reputationgrid[n] < Z:
                KD += 1
        return base_payoff - 1.0 - (alpha * KD), count_punish
    else:
        f = cal_f(Z, reputationgrid, b, i, j)
        if random.random() < f:
            sita = NPc
            count_punish += 1          # 旧定義: θ=0（グループにPCなし）でも +1 される
        else:
            sita = 0
        return base_payoff - (beta * sita), count_punish

def cal_point(i, j, grid, reputationgrid, count_punish, Z, b):
    """プレイヤー(i,j)が参加する5グループのペイオフ合計（旧コードと同じ順序で加算）"""
    point = 0.0
    for ni, nj in NB5[i][j]:
        grp = GROUP[ni][nj]
        Nc, NPc = 0, 0
        for pos in grp:
            val = grid[pos]
            if val == 1: Nc += 1
            elif val == 2: NPc += 1
        p, count_punish = game(i, j, Nc, NPc, grid, reputationgrid, grp, count_punish, Z, b)
        point += p
    return point, count_punish

# L6 用: 評判更新イベントのカウンタ（戦略3 × (y,x)のG/B 4 = 12セル）
#   セル番号 = s*4 + k,  s: C=0, PC=1, D=2,  k: (yG,xG)=0, (yG,xB)=1, (yB,xG)=2, (yB,xB)=3
EV_COUNT = [0] * 12
EV_DSUM = [0.0] * 12
S_INDEX = {1.0: 0, 2.0: 1, -1.0: 2}

def update_reputation(reputationgrid, grid, i, j, ni, nj, Z, typePATTERN, p_vals):
    v1, v2, v3, v4, v5, v6 = p_vals
    g_val = grid[i, j]
    rep_nj = reputationgrid[ni, nj]
    rep_ij = reputationgrid[i, j]

    cond_nj = rep_nj >= Z
    cond_ij = rep_ij >= Z

    diff = 0.0

    if typePATTERN == "image":
        if g_val == 1:     diff = v1 if cond_nj else v2
        elif g_val == -1:  diff = -v3 if cond_nj else -v4
        elif g_val == 2:   diff = v5 if cond_nj else v6

    elif typePATTERN == "shunning":
        if g_val == 1:     diff = v1 if cond_nj else -v2
        elif g_val == -1:
            if cond_nj:    diff = -v3
            else:          diff = v4 if cond_ij else -v4
        elif g_val == 2:   diff = v5 if cond_nj else -v6

    elif typePATTERN == "stern":
        if g_val == 1:
            if cond_nj:    diff = v1
            else:          diff = v2 if cond_ij else -v2
        elif g_val == -1:
            if cond_nj:    diff = -v3
            else:          diff = v4 if cond_ij else -v4
        elif g_val == 2:
            if cond_nj:    diff = v5
            else:          diff = v6 if cond_ij else -v6

    elif typePATTERN == "simple":
        if g_val == 1:     diff = v1 if cond_nj else v2
        elif g_val == -1:
            if cond_nj:    diff = -v3
            else:          diff = v4 if cond_ij else -v4
        elif g_val == 2:   diff = v5 if cond_nj else v6

    new_rep = np.clip(rep_ij + diff, 0.0, 100.0)
    if args.rep_fix:
        new_rep = round(float(new_rep), 6)     # 対照実験: 0.2 刻みの浮動小数点誤差を除去
    reputationgrid[i, j] = new_rep

    # --- L6: イベント記録（乱数を使わない） ---
    cell = S_INDEX[float(g_val)] * 4 + (0 if cond_nj else 2) + (0 if cond_ij else 1)
    EV_COUNT[cell] += 1
    EV_DSUM[cell] += float(new_rep) - float(rep_ij)     # clip 後の実際の変化量
    return reputationgrid

# ==========================================
# 3. ベクトル化ユーティリティ（乱数を使わない）
# ==========================================
def gsum(A):
    """各セルを中心とする5人グループ内の合計（中心+上下左右, 周期境界）"""
    A = A.astype(np.int64)
    return A + np.roll(A, 1, 0) + np.roll(A, -1, 0) + np.roll(A, 1, 1) + np.roll(A, -1, 1)

def nbsum(A):
    """上下左右4近傍の合計"""
    A = A.astype(np.int64)
    return np.roll(A, 1, 0) + np.roll(A, -1, 0) + np.roll(A, 1, 1) + np.roll(A, -1, 1)

def five_views(A):
    """プレイヤー(i,j)が参加する5グループ（中心 = 上,下,左,右,自分）の値を (5,L,L) で返す
       np.roll(A,1,0)[i,j] = A[i-1,j] なので旧コードの my_neighbors と同じ順序になる"""
    return np.stack([np.roll(A, 1, 0), np.roll(A, -1, 0), np.roll(A, 1, 1), np.roll(A, -1, 1), A])

def f_array(rep, b):
    """全プレイヤーの罰確率 f（cal_f と同じ式）"""
    f = np.zeros_like(rep)
    low = rep < Z
    f[low] = ((Z - rep[low]) / Z) ** b
    return f

def full_payoff(grid, rep, b):
    """
    毎MCS末の全プレイヤーのペイオフ（旧コードの二重 for ループ + cal_point を置換）
      乱数: D プレイヤーを行優先順に走査し、各5グループで random.random() を1回ずつ消費（旧コードと同一順序）
    返り値: dict（合計ペイオフと内訳、罰の集計）
    """
    isC, isPC, isD = (grid == 1), (grid == 2), (grid == -1)
    lowD = isD & (rep < Z)
    Nc_g, NPc_g, KD_g = gsum(isC), gsum(isPC), gsum(lowD)
    base_g = (R * (Nc_g + NPc_g)) / G                  # 各グループの共通分
    base5, NPc5, KD5 = five_views(base_g), five_views(NPc_g), five_views(KD_g)

    common = base5.sum(axis=0)                          # 共通分（5グループ合計）
    contrib = np.where(isC | isPC, 5.0, 0.0)            # 貢献コスト 1×5グループ
    pcost = np.where(isPC, alpha * KD5.sum(axis=0), 0.0)  # 罰コスト α·KD
    fine = np.zeros((L, L))

    f = f_array(rep, b)
    d_idx = np.flatnonzero(isD.ravel())                 # 行優先順 = 旧ループ順
    nD = d_idx.size
    stats = dict(n_punish_trial=0, n_punish_exec=0, n_punish_exec_raw=0, sum_theta=0,
                 E_punish_exec=0.0, E_sum_theta=0.0)
    if nD > 0:
        u = np.array([random.random() for _ in range(5 * nD)]).reshape(nD, 5)
        fD = f.ravel()[d_idx]                            # (nD,)
        theta5 = NPc5.reshape(5, -1)[:, d_idx].T         # (nD,5) 各グループのPC人数
        execd = u < fD[:, None]                          # 罰の執行判定（旧: random() < f）
        theta_exec = np.where(execd, theta5, 0)
        fine.ravel()[d_idx] = beta * theta_exec.sum(axis=1)
        stats["n_punish_trial"] = int(5 * np.count_nonzero(fD > 0))          # 罰判定（f>0）を受けた回数
        stats["n_punish_exec_raw"] = int(execd.sum())                        # 旧定義（θ=0 も含む）
        stats["n_punish_exec"] = int((execd & (theta5 > 0)).sum())           # 実際に罰金が発生した回数
        stats["sum_theta"] = int(theta_exec.sum())                           # 執行時 θ の合計
        stats["E_punish_exec"] = float((fD[:, None] * (theta5 > 0)).sum())   # 期待値（乱数ノイズなし）
        stats["E_sum_theta"] = float((fD[:, None] * theta5).sum())

    total = common - contrib - pcost - fine
    return dict(total=total, common=common, contrib=contrib, pcost=pcost, fine=fine, f=f, **stats)

def count_edges(A, B):
    """A-B 隣接辺数（各辺を1回だけ数える）"""
    dn_A, rt_A = np.roll(A, -1, 0), np.roll(A, -1, 1)
    if A is B:
        return int((A & dn_A).sum() + (A & rt_A).sum())
    dn_B, rt_B = np.roll(B, -1, 0), np.roll(B, -1, 1)
    return int((A & dn_B).sum() + (B & dn_A).sum() + (A & rt_B).sum() + (B & rt_A).sum())

def cluster_stats(mask):
    """周期境界でのクラスター（4近傍連結）数と最大サイズ。scipy不要のラベル伝播 + ポインタジャンプ"""
    if not mask.any():
        return 0, 0
    big = N
    lab = np.where(mask, np.arange(N).reshape(L, L), big)
    while True:
        m = lab.copy()
        for sh, ax in ((1, 0), (-1, 0), (1, 1), (-1, 1)):
            nb = np.roll(lab, sh, ax)
            m = np.where(mask & (nb < m), nb, m)
        flat = m.ravel()
        v = flat < big
        for _ in range(4):                               # ポインタジャンプで収束を加速
            flat[v] = flat[flat[v]]
        if np.array_equal(m, lab):
            break
        lab = m
    _, counts = np.unique(lab[mask], return_counts=True)
    return int(counts.size), int(counts.max())

def safe_mean(x):
    return float(np.mean(x)) if x.size > 0 else np.nan

# ==========================================
# 4. 1MCS ごとのログ行（乱数を使わない）
# ==========================================
def l1_row(mcs, grid, rep, b, fp):
    isC, isPC, isD = (grid == 1), (grid == 2), (grid == -1)
    high = rep >= Z
    f = fp["f"] if fp is not None else f_array(rep, b)
    near = isD & (rep >= Z - 10) & (rep < Z)
    row = dict(MCS=mcs,
               n_C=int(isC.sum()), n_PC=int(isPC.sum()), n_D=int(isD.sum()),
               meanR_C=safe_mean(rep[isC]), meanR_PC=safe_mean(rep[isPC]), meanR_D=safe_mean(rep[isD]),
               nHigh_C=int((isC & high).sum()), nHigh_PC=int((isPC & high).sum()), nHigh_D=int((isD & high).sum()),
               nNearZ_D=int(near.sum()),
               meanF_D=safe_mean(f[isD]),
               # Z ちょうどの値が浮動小数点誤差で Z 未満になっている人数（1/5 スケールで発生）
               nFloatBelowZ=int(((rep < Z) & (Z - rep < 1e-6)).sum()))
    if fp is not None:
        for k in ("n_punish_exec", "n_punish_exec_raw", "n_punish_trial", "sum_theta",
                  "E_punish_exec", "E_sum_theta"):
            row[k] = fp[k]
    else:   # MCS=0（初期状態）は乱数を使う罰判定をしないので期待値のみ
        row.update(n_punish_exec=np.nan, n_punish_exec_raw=np.nan, n_punish_trial=np.nan, sum_theta=np.nan)
        lowD_f = f[isD]
        nb_pc = five_views(gsum(isPC)).reshape(5, -1)[:, np.flatnonzero(isD.ravel())].T
        row["E_punish_exec"] = float((lowD_f[:, None] * (nb_pc > 0)).sum()) if lowD_f.size else 0.0
        row["E_sum_theta"] = float((lowD_f[:, None] * nb_pc).sum()) if lowD_f.size else 0.0
    return row

def l5_row(mcs, grid, rep, fp):
    isC, isPC, isD = (grid == 1), (grid == 2), (grid == -1)
    high = rep >= Z
    nbD, nbPC = nbsum(isD), nbsum(isPC)
    row = {"MCS": mcs}
    comps = {"C": ["common", "contrib", "total"],
             "PC": ["common", "contrib", "pcost", "total"],
             "D": ["common", "fine", "total"]}
    masks = {"C": isC, "PC": isPC, "D": isD}
    for s, cs in comps.items():
        m = masks[s]
        for c in cs:
            row[f"{s}_{c}"] = safe_mean(fp[c][m])
        row[f"{s}_G_total"] = safe_mean(fp["total"][m & high])     # 高評判の平均合計ペイオフ
        row[f"{s}_B_total"] = safe_mean(fp["total"][m & ~high])    # 低評判
    # 境界ペイオフ（模倣が実際に起きる場所での利得比較）
    row["PC_bdD_total"] = safe_mean(fp["total"][isPC & (nbD > 0)])  # D に接する PC
    row["D_bdPC_total"] = safe_mean(fp["total"][isD & (nbPC > 0)])  # PC に接する D
    row["C_bdD_total"] = safe_mean(fp["total"][isC & (nbD > 0)])
    row["D_bdC_total"] = safe_mean(fp["total"][isD & (nbsum(isC) > 0)])
    return row

def l7_row(mcs, grid, rep, do_cluster):
    isC, isPC, isD = (grid == 1), (grid == 2), (grid == -1)
    nbD, nbPC = nbsum(isD), nbsum(isPC)
    row = dict(MCS=mcs,
               e_PC_D=count_edges(isPC, isD), e_C_D=count_edges(isC, isD), e_PC_C=count_edges(isPC, isC),
               e_PC_PC=count_edges(isPC, isPC), e_C_C=count_edges(isC, isC), e_D_D=count_edges(isD, isD),
               meanR_PC_int=safe_mean(rep[isPC & (nbD == 0)]),   # D に接しない PC（クラスター内部）
               meanR_PC_bd=safe_mean(rep[isPC & (nbD > 0)]),     # D に接する PC（境界）
               meanR_D_bd=safe_mean(rep[isD & (nbPC > 0)]),      # PC に接する D
               meanR_D_int=safe_mean(rep[isD & (nbPC == 0)]))
    if do_cluster:
        row["nClu_PC"], row["maxClu_PC"] = cluster_stats(isPC)
        row["nClu_Coop"], row["maxClu_Coop"] = cluster_stats(isC | isPC)
        row["nClu_D"], row["maxClu_D"] = cluster_stats(isD)
    else:
        for k in ("nClu_PC", "maxClu_PC", "nClu_Coop", "maxClu_Coop", "nClu_D", "maxClu_D"):
            row[k] = np.nan
    return row

def l3_rows(mcs, grid, rep):
    rows = []
    for s_name, s_val in (("C", 1), ("PC", 2), ("D", -1)):
        cnt, _ = np.histogram(rep[grid == s_val], bins=HIST_EDGES)
        for k in range(cnt.size):
            rows.append((mcs, s_name, HIST_EDGES[k], HIST_EDGES[k + 1], int(cnt[k])))
    return rows

TRANS = [(1, 2), (1, -1), (2, 1), (2, -1), (-1, 1), (-1, 2)]
TRANS_NAME = {(1, 2): "C_to_PC", (1, -1): "C_to_D", (2, 1): "PC_to_C",
              (2, -1): "PC_to_D", (-1, 1): "D_to_C", (-1, 2): "D_to_PC"}
DEST_NAME = {1: "C", 2: "PC", -1: "D"}

# ==========================================
# 5. モンテカルロステップ
# ==========================================
def simulation(record_index, omega_copy, Z, b, logger):
    grid = initialize_grid()
    reputationgrid = initialize_reputationgrid()
    indices = np.array([[i, j] for i in range(L) for j in range(L)])
    check = 0
    rast = 0
    end_reason = "completed"
    reset_rng = np.random.default_rng(None if SEED is None else SEED + 7919)  # リセット用（本流の乱数を乱さない）

    # 初期状態のログ（MCS=0）
    if logger is not None:
        logger["L1"].append(l1_row(0, grid, reputationgrid, b, None))
        logger["L7"].append(l7_row(0, grid, reputationgrid, True))
        logger["L3"].extend(l3_rows(0, grid, reputationgrid))
        logger["L4"][0] = (grid.copy(), reputationgrid.copy())

    rate = C_high_rate = C_low_rate = PC_high_rate = PC_low_rate = D_high_rate = D_low_rate = 0.0

    def record(rec_idx):
        """協力率など（旧コードの記録処理と同一）"""
        nonlocal rate, C_high_rate, C_low_rate, PC_high_rate, PC_low_rate, D_high_rate, D_low_rate
        grid_is_1 = (grid == 1)
        grid_is_2 = (grid == 2)
        grid_is_m1 = (grid == -1)
        count_C_PC = np.sum(grid_is_1) + np.sum(grid_is_2)
        rate = count_C_PC / (L * L)
        high_rep = (reputationgrid >= Z)
        low_rep = (reputationgrid < Z)
        C_high_rate = np.sum(grid_is_1 & high_rep) / (L * L)
        C_low_rate = np.sum(grid_is_1 & low_rep) / (L * L)
        PC_high_rate = np.sum(grid_is_2 & high_rep) / (L * L)
        PC_low_rate = np.sum(grid_is_2 & low_rep) / (L * L)
        D_high_rate = np.sum(grid_is_m1 & high_rep) / (L * L)
        D_low_rate = np.sum(grid_is_m1 & low_rep) / (L * L)
        store(rec_idx)

    def store(rec_idx):
        rates_array[rec_idx] = rate
        Crates_array[rec_idx] = C_high_rate + C_low_rate
        PCrates_array[rec_idx] = PC_high_rate + PC_low_rate
        Drates_array[rec_idx] = D_high_rate + D_low_rate
        rate_high_rates_array[rec_idx] = C_high_rate + PC_high_rate
        rate_low_rates_array[rec_idx] = C_low_rate + PC_low_rate
        C_high_rates_array[rec_idx] = C_high_rate
        C_low_rates_array[rec_idx] = C_low_rate
        PC_high_rates_array[rec_idx] = PC_high_rate
        PC_low_rates_array[rec_idx] = PC_low_rate
        D_high_rates_array[rec_idx] = D_high_rate
        D_low_rates_array[rec_idx] = D_low_rate

    def check_stop():
        """打ち切り判定。legacy: C+PC=0 または 1（旧コード）, mono: 単一戦略のみ"""
        nonlocal check, rast, end_reason
        if args.stop == "legacy":
            if rate == 0: check = 1; rast = mcsstep; end_reason = "all_D"
            if rate == 1.0: check = 2; rast = mcsstep; end_reason = "no_D"
        else:
            nC, nPC = int(np.sum(grid == 1)), int(np.sum(grid == 2))
            if rate == 0: check = 1; rast = mcsstep; end_reason = "all_D"
            elif nC == N: check = 2; rast = mcsstep; end_reason = "all_C"
            elif nPC == N: check = 2; rast = mcsstep; end_reason = "all_PC"

    mcsstep = 0
    for mcsstep in range(num_steps):
        mcs_punish_X = 0
        mcs_punish_Y = 0
        np.random.shuffle(indices)
        neighbor_choices = np.random.randint(0, 4, size=L * L)

        # L2: 戦略切替のカウンタ（この MCS 内）
        tr_count = {t: 0 for t in TRANS}
        to_n = {1: 0, 2: 0, -1: 0}; to_sumR = {1: 0.0, 2: 0.0, -1: 0.0}; to_high = {1: 0, 2: 0, -1: 0}
        n_attempt = n_attempt_yH = n_sw_yH = n_sw_yL = n_gate_reject = 0
        for c in range(12):
            EV_COUNT[c] = 0; EV_DSUM[c] = 0.0

        for _ in range(L * L):
            if check == 0:
                i, j = indices[_]
                im1, ip1 = (i - 1) % L, (i + 1) % L
                jm1, jp1 = (j - 1) % L, (j + 1) % L

                choice = neighbor_choices[_]
                if choice == 0: ni, nj = im1, j
                elif choice == 1: ni, nj = ip1, j
                elif choice == 2: ni, nj = i, jm1
                else: ni, nj = i, jp1

                if grid[i, j] == grid[ni, nj]:
                    reputationgrid = update_reputation(reputationgrid, grid, i, j, ni, nj, Z, typePATTERN, p_vals)
                    if _ % RECORD_INTERVAL == 0 and mcsstep < num_steps:
                        record(record_index)
                        check_stop()
                        record_index += 1
                    continue

                count_punishX, count_punishY = 0, 0
                pointx, count_punishX = cal_point(i, j, grid, reputationgrid, count_punishX, Z, b)
                pointy, count_punishY = cal_point(ni, nj, grid, reputationgrid, count_punishY, Z, b)

                mcs_punish_X += count_punishX
                mcs_punish_Y += count_punishY

                y_high = reputationgrid[ni, nj] >= Z
                current_omega = 1.0 if y_high else omega_copy

                # Fermi 則（旧コードと同一の式・同一の乱数1回）
                fermi = (1 / (1 + math.exp((pointx - pointy) / K)))
                u = random.random()
                n_attempt += 1
                if y_high: n_attempt_yH += 1
                if u < current_omega * fermi:
                    old_s, new_s = float(grid[i, j]), float(grid[ni, nj])
                    carried = float(reputationgrid[i, j])           # 切替時に持ち越される評判
                    tr_count[(int(old_s), int(new_s))] += 1
                    to_n[int(new_s)] += 1; to_sumR[int(new_s)] += carried
                    if carried >= Z: to_high[int(new_s)] += 1
                    if y_high: n_sw_yH += 1
                    else: n_sw_yL += 1
                    grid[i, j] = grid[ni, nj]
                    # 対照実験: 切替時に評判をリセット（既定 none では何もしない）
                    if args.reset_rep == "uniform":
                        reputationgrid[i, j] = float(reset_rng.integers(1, 101))
                    elif args.reset_rep == "mid":
                        reputationgrid[i, j] = 50.0
                elif u < fermi:
                    n_gate_reject += 1     # ωy=1 なら模倣されていたが、低評判ゲートで棄却された

                reputationgrid = update_reputation(reputationgrid, grid, i, j, ni, nj, Z, typePATTERN, p_vals)

                if _ % RECORD_INTERVAL == 0 and mcsstep < num_steps:
                    record(record_index)
                    check_stop()
                    record_index += 1
            else:
                if _ % RECORD_INTERVAL == 0 and mcsstep < num_steps:
                    store(record_index)
                    record_index += 1
                break

        if mcsstep < num_steps:
            punish_X_time_series[mcsstep] = mcs_punish_X
            punish_Y_time_series[mcsstep] = mcs_punish_Y

            # 全プレイヤーのペイオフ（ベクトル化。乱数消費は旧コードと同一）
            fp = full_payoff(grid, reputationgrid, b)
            all_payoffs = fp["total"]
            mask_C = (grid == 1)
            mask_D = (grid == -1)
            mask_PC = (grid == 2)
            payoff_history_all[mcsstep] = np.mean(all_payoffs)
            payoff_history_C[mcsstep] = np.mean(all_payoffs[mask_C]) if np.any(mask_C) else 0.0
            payoff_history_D[mcsstep] = np.mean(all_payoffs[mask_D]) if np.any(mask_D) else 0.0
            payoff_history_PC[mcsstep] = np.mean(all_payoffs[mask_PC]) if np.any(mask_PC) else 0.0

            # ---------- 詳細ログ（MCS = mcsstep+1 完了後の状態） ----------
            if logger is not None:
                t = mcsstep + 1
                logger["L1"].append(l1_row(t, grid, reputationgrid, b, fp))
                logger["L5"].append(l5_row(t, grid, reputationgrid, fp))
                logger["L7"].append(l7_row(t, grid, reputationgrid,
                                           (t % args.cluster_every == 0) or check != 0))
                l2 = {"MCS": t, "n_attempt": n_attempt, "n_attempt_yHigh": n_attempt_yH,
                      "n_switch_yHigh": n_sw_yH, "n_switch_yLow": n_sw_yL, "n_gate_reject": n_gate_reject}
                for tr in TRANS:
                    l2[TRANS_NAME[tr]] = tr_count[tr]
                for d, nm in DEST_NAME.items():
                    l2[f"n_to_{nm}"] = to_n[d]
                    l2[f"meanR_to_{nm}"] = to_sumR[d] / to_n[d] if to_n[d] > 0 else np.nan
                    l2[f"nHigh_to_{nm}"] = to_high[d]     # 高評判のまま切り替わった人数（to_D は免罰Dの供給）
                logger["L2"].append(l2)
                l6 = {"MCS": t}
                for s_i, s_nm in enumerate(["C", "PC", "D"]):
                    for k, k_nm in enumerate(["GG", "GB", "BG", "BB"]):   # (y, x) の順
                        l6[f"{s_nm}_{k_nm}_n"] = EV_COUNT[s_i * 4 + k]
                        l6[f"{s_nm}_{k_nm}_dR"] = EV_DSUM[s_i * 4 + k]
                logger["L6"].append(l6)
                if t in L3_TIMES or check != 0:
                    logger["L3"].extend(l3_rows(t, grid, reputationgrid))
                if t in L4_TIMES or check != 0:
                    logger["L4"][t] = (grid.copy(), reputationgrid.copy())

        if mcsstep % 1000 == 0:
            print(f"ステップ数 {mcsstep} 協力率 {rate:.4f} | 罰回数 i: {mcs_punish_X}, j: {mcs_punish_Y}")
        if check != 0: break

    print("0または1になったステップ数", rast)
    end_mcs = (mcsstep + 1) if check != 0 else num_steps
    return record_index, end_mcs, (end_reason if check != 0 else "completed")

# ==========================================
# 6. 補助: 保存
# ==========================================
def df_to_csv_bytes(df):
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()

def file_sha256(path):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return None

def pad_tail(arr, n_valid):
    """打ち切り後の未記録部分を最終記録値で埋める（旧 run_exchange_all の処理を正しい形で置換）"""
    if 0 < n_valid < arr.size:
        arr[n_valid:] = arr[n_valid - 1]

# ==========================================
# 7. メイン実行処理
# ==========================================
if __name__ == "__main__":
    start = time.time()
    sfx = seed_suffix(SEED)

    ZIP_NAME        = f"{typePATTERN}_Z={Z}_r={R}_{PATTERN}_omega={omega}{sfx}.zip"
    ZIP_NAME_C      = f"{typePATTERN}_C_Z={Z}_r={R}_{PATTERN}_omega={omega}{sfx}.zip"
    ZIP_NAME_PC     = f"{typePATTERN}_PC_Z={Z}_r={R}_{PATTERN}_omega={omega}{sfx}.zip"
    ZIP_NAME_D      = f"{typePATTERN}_D_Z={Z}_r={R}_{PATTERN}_omega={omega}{sfx}.zip"
    ZIP_NAME_PUNISH = f"punish_history_Z={Z}_r={R}_{PATTERN}_omega={omega}{sfx}.zip"
    ZIP_NAME_PAYOFF = f"payoff_history_Z={Z}_r={R}_{PATTERN}_omega={omega}{sfx}.zip"

    zip_buffer = io.BytesIO(); zip_buffer_C = io.BytesIO(); zip_buffer_PC = io.BytesIO()
    zip_buffer_D = io.BytesIO(); zip_buffer_P = io.BytesIO(); zip_buffer_payoff = io.BytesIO()
    zip_buffer_log = io.BytesIO()

    script_path = os.path.abspath(__file__)
    run_meta_common = dict(
        rule=typePATTERN, pattern=PATTERN, type_name=TYPE_NAME.get((typePATTERN, PATTERN), ""),
        scale=pattern_scale(PATTERN), Z=Z, omega_y=omega, seed=SEED, L=L, G=G, r=R, K=K,
        alpha=alpha, beta=beta, num_steps=num_steps, variant=VARIANT,
        reset_rep=args.reset_rep, stop=args.stop, rep_fix=args.rep_fix,
        record_interval_updates=RECORD_INTERVAL, rec_per_mcs=REC_PER_MCS,
        script=os.path.basename(script_path), script_sha256=file_sha256(script_path),
        python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__,
        started_at=datetime.datetime.now().isoformat(timespec="seconds"),
        l1_l5_l7_row_definition="MCS=t は t MCS 完了後の状態（t=0 は初期状態）。L2/L6 は t 番目のMCS中のイベント数",
    )

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf, \
         zipfile.ZipFile(zip_buffer_C, 'w', zipfile.ZIP_DEFLATED) as zf_C, \
         zipfile.ZipFile(zip_buffer_PC, 'w', zipfile.ZIP_DEFLATED) as zf_PC, \
         zipfile.ZipFile(zip_buffer_D, 'w', zipfile.ZIP_DEFLATED) as zf_D, \
         zipfile.ZipFile(zip_buffer_P, 'w', zipfile.ZIP_DEFLATED) as zf_P, \
         zipfile.ZipFile(zip_buffer_payoff, 'w', zipfile.ZIP_DEFLATED) as zf_payoff, \
         zipfile.ZipFile(zip_buffer_log, 'w', zipfile.ZIP_DEFLATED) as zf_log:

        # 打ち切り後を最終値で埋め済みであることを示すマーカー（run_exchange_all.py はこれを見てスキップ）
        for z in (zf, zf_C, zf_PC, zf_D):
            z.writestr("_PADDED_v2.txt", "tail rows after early stop are padded with the final recorded state\n")

        for b in B_LIST:
            b_str = b_label(b)
            t0 = time.time()
            # 乱数シード（全 b で同一 = 共通乱数法: 初期配置が同じなので b の差を純粋に比較できる）
            if SEED is not None:
                random.seed(SEED)
                np.random.seed(SEED)

            expected_size = num_steps * REC_PER_MCS
            rates_array = np.zeros(expected_size, dtype=np.float32)
            Crates_array = np.zeros(expected_size, dtype=np.float32)
            PCrates_array = np.zeros(expected_size, dtype=np.float32)
            Drates_array = np.zeros(expected_size, dtype=np.float32)
            rate_high_rates_array = np.zeros(expected_size, dtype=np.float32)
            rate_low_rates_array = np.zeros(expected_size, dtype=np.float32)
            C_high_rates_array = np.zeros(expected_size, dtype=np.float32)
            C_low_rates_array = np.zeros(expected_size, dtype=np.float32)
            PC_high_rates_array = np.zeros(expected_size, dtype=np.float32)
            PC_low_rates_array = np.zeros(expected_size, dtype=np.float32)
            D_high_rates_array = np.zeros(expected_size, dtype=np.float32)
            D_low_rates_array = np.zeros(expected_size, dtype=np.float32)
            punish_X_time_series = np.zeros(num_steps, dtype=np.int32)
            punish_Y_time_series = np.zeros(num_steps, dtype=np.int32)
            payoff_history_all = np.zeros(num_steps, dtype=np.float32)
            payoff_history_C = np.zeros(num_steps, dtype=np.float32)
            payoff_history_D = np.zeros(num_steps, dtype=np.float32)
            payoff_history_PC = np.zeros(num_steps, dtype=np.float32)
            print(f"現在のb値: {b} (omega={omega}, Z={Z}, seed={SEED})")

            logger = {"L1": [], "L2": [], "L3": [], "L4": {}, "L5": [], "L6": [], "L7": []} if DO_LOG else None
            n_valid, end_mcs, end_reason = simulation(0, omega, Z, b, logger)

            rate_arrays = [rates_array, Crates_array, PCrates_array, Drates_array, rate_high_rates_array,
                           rate_low_rates_array, C_high_rates_array, C_low_rates_array, PC_high_rates_array,
                           PC_low_rates_array, D_high_rates_array, D_low_rates_array]
            for a in rate_arrays:
                pad_tail(a, n_valid)

            # ---- 従来の CSV（列名・ファイル名は従来どおり。seed 指定時のみ zip 名に _seed=） ----
            zf.writestr(f"{typePATTERN}_Z={Z}_b={b_str}_r={R}_{PATTERN}_omega={omega}.csv", df_to_csv_bytes(
                pd.DataFrame({"Cooperation Rate": rates_array, "Cooperation Rate High": rate_high_rates_array,
                              "Cooperation Rate Low": rate_low_rates_array})))
            zf_C.writestr(f"{typePATTERN}_C_Z={Z}_b={b_str}_r={R}_{PATTERN}_omega={omega}.csv", df_to_csv_bytes(
                pd.DataFrame({"C Rate": Crates_array, "C Rate High": C_high_rates_array, "C Rate Low": C_low_rates_array})))
            zf_PC.writestr(f"{typePATTERN}_PC_Z={Z}_b={b_str}_r={R}_{PATTERN}_omega={omega}.csv", df_to_csv_bytes(
                pd.DataFrame({"PC Rate": PCrates_array, "PC Rate High": PC_high_rates_array, "PC Rate Low": PC_low_rates_array})))
            zf_D.writestr(f"{typePATTERN}_D_Z={Z}_b={b_str}_r={R}_{PATTERN}_omega={omega}.csv", df_to_csv_bytes(
                pd.DataFrame({"D Rate": Drates_array, "D Rate High": D_high_rates_array, "D Rate Low": D_low_rates_array})))
            zf_P.writestr(f"punish_Z={Z}_b={b_str}_r={R}_{PATTERN}_omega={omega}.csv", df_to_csv_bytes(
                pd.DataFrame({"MCS_Step": np.arange(num_steps), "Punish_Count_i": punish_X_time_series,
                              "Punish_Count_j": punish_Y_time_series})))
            zf_payoff.writestr(f"payoff_Z={Z}_b={b_str}_r={R}_{PATTERN}_omega={omega}.csv", df_to_csv_bytes(
                pd.DataFrame({"MCS_Step": np.arange(num_steps), "Avg_Payoff_Total": payoff_history_all,
                              "Avg_Payoff_C": payoff_history_C, "Avg_Payoff_D": payoff_history_D,
                              "Avg_Payoff_PC": payoff_history_PC})))

            # ---- 詳細ログ L1〜L8 ----
            if DO_LOG:
                pre = f"b={b_str}/"
                zf_log.writestr(pre + "L1_strategy.csv", df_to_csv_bytes(pd.DataFrame(logger["L1"])))
                zf_log.writestr(pre + "L2_switch.csv", df_to_csv_bytes(pd.DataFrame(logger["L2"])))
                zf_log.writestr(pre + "L3_rephist.csv", df_to_csv_bytes(pd.DataFrame(
                    logger["L3"], columns=["MCS", "strategy", "bin_lo", "bin_hi", "count"])))
                npz = io.BytesIO()
                arrs = {}
                for t, (g_arr, r_arr) in sorted(logger["L4"].items()):
                    # 戦略: 0=D, 1=C, 2=PC（uint8）/ 評判: float32（1/5スケールの 0.2 刻みを保持）
                    s_arr = np.where(g_arr == -1, 0, g_arr).astype(np.uint8)
                    arrs[f"strategy_{t:07d}"] = s_arr
                    arrs[f"reputation_{t:07d}"] = r_arr.astype(np.float32)
                np.savez_compressed(npz, **arrs)
                zf_log.writestr(pre + "L4_snapshots.npz", npz.getvalue())
                zf_log.writestr(pre + "L5_payoff.csv", df_to_csv_bytes(pd.DataFrame(logger["L5"])))
                zf_log.writestr(pre + "L6_repupdate.csv", df_to_csv_bytes(pd.DataFrame(logger["L6"])))
                zf_log.writestr(pre + "L7_spatial.csv", df_to_csv_bytes(pd.DataFrame(logger["L7"])))
                meta = dict(run_meta_common, b=b, end_mcs=int(end_mcs), end_reason=end_reason,
                            n_valid_rate_rows=int(n_valid), runtime_sec=round(time.time() - t0, 1),
                            finished_at=datetime.datetime.now().isoformat(timespec="seconds"),
                            L3_times=[t for t in L3_TIMES if t <= end_mcs], L4_times=sorted(logger["L4"].keys()))
                zf_log.writestr(pre + "L8_meta.json", json.dumps(meta, ensure_ascii=False, indent=2))
            print(f"  → 終了 MCS={end_mcs} ({end_reason}), {time.time() - t0:.1f} 秒")

    # 保存処理
    for d in OUTPUT_DIRS:
        os.makedirs(d, exist_ok=True)
    save_files = [
        (zip_buffer, ZIP_NAME, OUTPUT_DIRS[0]),
        (zip_buffer_C, ZIP_NAME_C, OUTPUT_DIRS[1]),
        (zip_buffer_PC, ZIP_NAME_PC, OUTPUT_DIRS[2]),
        (zip_buffer_D, ZIP_NAME_D, OUTPUT_DIRS[3]),
        (zip_buffer_P, ZIP_NAME_PUNISH, OUTPUT_DIRS[4]),
        (zip_buffer_payoff, ZIP_NAME_PAYOFF, OUTPUT_DIRS[5]),
    ]
    if DO_LOG:
        log_path = log_zip_path(datePATTERN, typePATTERN, PATTERN, Z, omega, SEED, VARIANT)
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        save_files.append((zip_buffer_log, os.path.basename(log_path), os.path.dirname(log_path)))

    for buf, filename, target_dir in save_files:
        local_path = os.path.join(target_dir, filename)
        tmp_path = local_path + ".tmp"
        with open(tmp_path, 'wb') as f:          # 一時ファイル → 置換（書き込み途中で中断しても既存ファイルを壊さない）
            f.write(buf.getvalue())
        os.replace(tmp_path, local_path)
        print(f"✅ 保存完了: {local_path}")
        buf.close()

    end = time.time()
    print("実行時間:", end - start, "秒")
