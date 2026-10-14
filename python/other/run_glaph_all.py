# -*- coding: utf-8 -*-
"""
グラフ作成（1タイプ分）

(A) 従来グラフ: 協力率（Base / C / PC）と罰の回数 … 出力先・ファイル名は従来どおり（seed 指定時のみ末尾に _seed=）
(B) 詳細ログ L1〜L7 のグラフ（Logs zip がある Z のみ）
      出力先: ../../{model}グラフ/Z_change_協力率変遷{variant}/{PATTERN}/Logs/
      L1 戦略・評判・免罰D・罰 / L2 戦略切替 / L3 評判分布ヒートマップ / L4 空間スナップショット
      L5 ペイオフ内訳・境界ペイオフ / L6 評判更新イベント / L7 境界長・クラスター・内外の評判
      複数 seed があれば seed 平均（太線）と 10–90% 帯を描く
(C) 条件ごとの要約指標 summary_*.csv（all_glaph.py が summary_all.csv に統合）

使い方:
  python run_glaph_all.py image +5+1-5-1+5+1 imageデータ imageグラフ 0.01 均衡型 --seeds 0 --zs 90 --group G13
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')  # ウィンドウを描画せずバックグラウンドで処理し、メモリを節約
import matplotlib.pyplot as plt
from matplotlib import font_manager
_avail = {f.name for f in font_manager.fontManager.ttflist}
# 日本語フォント: Windows の Meiryo を優先し、無い環境では見つかったものを使う（警告の連発を防ぐ）
plt.rcParams['font.family'] = next((f for f in ['Meiryo', 'Yu Gothic', 'MS Gothic', 'Noto Sans CJK JP', 'IPAexGothic']
                                    if f in _avail), 'DejaVu Sans')
plt.rcParams['axes.unicode_minus'] = False
import pandas as pd
import os
import io
import json
import zipfile
import argparse
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)   # 全NaN区間の平均など
warnings.filterwarnings("ignore", message=".*Glyph.*")

from experiment_config import root_dir, seed_suffix, log_zip_path, b_label, ALL_Z, ALL_B

# ==========================================
# 1. 引数
# ==========================================
ap = argparse.ArgumentParser()
ap.add_argument("modelPATTERN", nargs="?", default="image")
ap.add_argument("PATTERN", nargs="?", default="+0.6+0.2-0.6-0.2+1+0.6")
ap.add_argument("datePATTERN", nargs="?", default="imageデータ")
ap.add_argument("glaphPATTERN", nargs="?", default="imageグラフ")
ap.add_argument("omega", nargs="?", type=float, default=0.1)
ap.add_argument("type_name", nargs="?", default="未知のタイプ")
ap.add_argument("--seeds", type=str, default="")           # "" = seed なし（従来データ）
ap.add_argument("--variant", type=str, default="")
ap.add_argument("--zs", type=str, default=",".join(map(str, ALL_Z)))
ap.add_argument("--group", type=str, default="")
ap.add_argument("--skip-legacy", action="store_true")
ap.add_argument("--skip-logs", action="store_true")
a = ap.parse_args()

modelPATTERN, PATTERN, datePATTERN, glaphPATTERN = a.modelPATTERN, a.PATTERN, a.datePATTERN, a.glaphPATTERN
omega, type_name, VARIANT = a.omega, a.type_name, a.variant
SEEDS = [int(s) for s in a.seeds.split(",") if s.strip() != ""] or [None]
ZS = [int(z) for z in a.zs.split(",")]
DATA_ROOT = root_dir(datePATTERN, PATTERN, VARIANT)
GRAPH_ROOT = f"../../{glaphPATTERN}/Z_change_協力率変遷{VARIANT}/{PATTERN}"
LOG_GRAPH_DIR = f"{GRAPH_ROOT}/Logs"
bs = [b_label(b) for b in ALL_B]

print(f"🔧 [グラフ設定] model: {modelPATTERN} | pattern: {PATTERN} | omega: {omega} | type: {type_name} "
      f"| seeds: {SEEDS} | variant: '{VARIANT}'")

# 色: 戦略は固定の3色（色覚多様性で検証済みの順序）、b は単一色相の濃淡（順序のある量なので）
COL = {"C": "#2a78d6", "PC": "#1baf7a", "D": "#eb6834"}
INK, MUTED = "#0b0b0b", "#8a8984"


def b_color(b_str, b_list):
    """b を明→暗の青で表す（b=0 が最も濃い）"""
    ramp = ["#0d3a73", "#1f5fae", "#3f86d4", "#6ea8e2", "#9fc7ef", "#c9e0f7"]
    i = b_list.index(b_str) if b_str in b_list else 0
    idx = round(i * (len(ramp) - 1) / max(1, len(b_list) - 1))
    return ramp[idx]


def style_axis(ax):
    ax.grid(True, color="#e6e5e0", linewidth=0.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(colors="#52514e", labelsize=9)


def legacy_zip(sub_dir, base_name, seed):
    """seed 付きファイルを優先し、なければ従来名にフォールバック"""
    p = f"{DATA_ROOT}{sub_dir}/{base_name}{seed_suffix(seed)}.zip"
    if os.path.exists(p) or seed is None:
        return p
    return f"{DATA_ROOT}{sub_dir}/{base_name}.zip"


# ==========================================
# 2. (A) 協力率変遷グラフ（従来と同じ見た目。x軸の右端だけデータ長に合わせる）
# ==========================================
def plot_coop(Z, target_type, seed):
    if target_type == "Base":
        sub_dir, prefix, col_name = "", modelPATTERN, "Cooperation Rate"
        out_file = f"{modelPATTERN}_{type_name}_Z={Z}_r=3.0_omega={omega}{seed_suffix(seed)}.png"
    else:
        sub_dir, prefix, col_name = f"/{target_type}", f"{modelPATTERN}_{target_type}", f"{target_type} Rate"
        out_file = f"{modelPATTERN}_{type_name}_{target_type}_Z={Z}_r=3.0_omega={omega}{seed_suffix(seed)}.png"

    INPUT_DIR = f"{GRAPH_ROOT}{sub_dir}"
    ZIP_FILE = legacy_zip(sub_dir, f"{prefix}_Z={Z}_r=3.0_{PATTERN}_omega={omega}", seed)
    os.makedirs(INPUT_DIR, exist_ok=True)
    file_names = [f"{prefix}_Z={Z}_b={b}_r=3.0_{PATTERN}_omega={omega}.csv" for b in bs]

    if not os.path.exists(ZIP_FILE):
        print(f"⚠️ スキップ: {ZIP_FILE} が存在しません。")
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    labels, n_max = [], 1
    try:
        with zipfile.ZipFile(ZIP_FILE, 'r') as zf:
            for b, file_name in zip(bs, file_names):
                if file_name in zf.namelist():
                    with zf.open(file_name) as file:
                        data = pd.read_csv(file)
                        ax.plot(data.index, data[col_name])
                        labels.append(f"b={b}")
                        n_max = max(n_max, len(data))
    except Exception as e:
        print(f"❌ エラー({target_type} Z={Z}): {e}")
        plt.close(fig)
        return

    # 1MCS = 10 行（1000更新ごとの記録）→ 目盛りラベルは MCS 表記
    ax.set_xlabel("MCS", fontsize=20)
    ax.set_ylabel("Ρc", fontsize=20)
    ax.set_ylim(0, 1)
    ax.set_xscale('log')
    ax.set_xlim(left=1, right=max(100000, n_max))
    ax.set_title(f"{prefix}_{type_name}_Z={Z} r=3.0 ω={omega}", fontsize=20)
    ticks = [10 ** k for k in range(2, int(np.ceil(np.log10(max(100000, n_max)))) + 1)]
    ax.set_xticks(ticks)
    ax.set_xticklabels([f"{t // 10}" for t in ticks])
    ax.legend(labels=labels, fontsize=20)
    ax.grid(True)

    file_path = os.path.join(INPUT_DIR, out_file)
    plt.savefig(file_path, bbox_inches='tight')
    plt.close(fig)
    print(f"✅ 保存({target_type}): {file_path}")


def last_nonzero_step(series_x, series_y):
    nonzero_idx = series_y[series_y != 0].index
    if len(nonzero_idx) == 0:
        return series_x.iloc[0]
    return series_x.iloc[nonzero_idx[-1]]


def plot_punish(Z, seed):
    INPUT_DIR = f"{GRAPH_ROOT}/Punish"
    ZIP_FILE = legacy_zip("/Punish", f"punish_history_Z={Z}_r=3.0_{PATTERN}_omega={omega}", seed)
    os.makedirs(INPUT_DIR, exist_ok=True)
    file_names = [f"punish_Z={Z}_b={b}_r=3.0_{PATTERN}_omega={omega}.csv" for b in bs]

    if not os.path.exists(ZIP_FILE):
        print(f"⚠️ スキップ: {ZIP_FILE} が存在しません。")
        return
    datasets, labels = [], []
    try:
        with zipfile.ZipFile(ZIP_FILE, 'r') as zf:
            for b, file_name in zip(bs, file_names):
                if file_name in zf.namelist():
                    with zf.open(file_name) as f:
                        datasets.append(pd.read_csv(f)); labels.append(f"b={b}")
    except Exception as e:
        print(f"❌ エラー(Punish Z={Z}): {e}")
        return
    if not datasets:
        return

    xlim_right = max(
        max(last_nonzero_step(d['MCS_Step'], d['Punish_Count_i']) for d in datasets),
        max(last_nonzero_step(d['MCS_Step'], d['Punish_Count_j']) for d in datasets))
    xlim_right = max(xlim_right, 1)

    for col, suffix in [('Punish_Count_i', '_punish_i'), ('Punish_Count_j', '_punish_j')]:
        fig, ax = plt.subplots(figsize=(10, 6))
        for data, label in zip(datasets, labels):
            ax.plot(data['MCS_Step'], data[col], label=label)
        ax.set_xlabel("MCS", fontsize=20)
        ax.set_ylabel(col, fontsize=20)
        ax.set_xlim(left=0, right=xlim_right)
        ax.set_title(f"{modelPATTERN}_{type_name}_Z={Z} r=3.0 {col} ω={omega}", fontsize=16)
        ax.legend(fontsize=14)
        ax.grid(True)
        plt.tight_layout()
        out_path = os.path.join(INPUT_DIR, f"{modelPATTERN}_{type_name}_罰の回数グラフ_Z={Z}_r=3.0{suffix}_omega={omega}{seed_suffix(seed)}.png")
        plt.savefig(out_path)
        plt.close(fig)
        print(f"✅ 保存(Punish {col}): {out_path}")


# ==========================================
# 3. (B) 詳細ログの読み込み
# ==========================================
def load_logs(Z):
    """{b_str: {seed: {"L1": df, ..., "L4": npz, "meta": dict}}}"""
    out = {}
    for seed in SEEDS:
        p = log_zip_path(datePATTERN, modelPATTERN, PATTERN, Z, omega, seed, VARIANT)
        if not os.path.exists(p):
            continue
        with zipfile.ZipFile(p) as z:
            names = z.namelist()
            b_dirs = sorted({n.split("/")[0] for n in names if "/" in n})
            for bd in b_dirs:
                b_str = bd.split("=", 1)[1]
                d = {}
                for key, fn in [("L1", "L1_strategy.csv"), ("L2", "L2_switch.csv"), ("L3", "L3_rephist.csv"),
                                ("L5", "L5_payoff.csv"), ("L6", "L6_repupdate.csv"), ("L7", "L7_spatial.csv")]:
                    if f"{bd}/{fn}" in names:
                        d[key] = pd.read_csv(io.BytesIO(z.read(f"{bd}/{fn}")))
                if f"{bd}/L4_snapshots.npz" in names:
                    d["L4"] = dict(np.load(io.BytesIO(z.read(f"{bd}/L4_snapshots.npz"))))
                if f"{bd}/L8_meta.json" in names:
                    d["meta"] = json.loads(z.read(f"{bd}/L8_meta.json"))
                out.setdefault(b_str, {})[seed] = d
    return out


def seed_band(dfs, col, deriv=None, smooth=1):
    """seed をまたいだ平均と 10–90% 帯。行は MCS で揃える（打ち切り後は NaN）"""
    series = []
    for df in dfs:
        y = deriv(df) if deriv is not None else df[col]
        s = pd.Series(np.asarray(y, dtype=float), index=df["MCS"].values)
        if smooth > 1:
            s = s.rolling(smooth, min_periods=1, center=True).mean()
        series.append(s)
    M = pd.concat(series, axis=1)
    return M.index.values, M.mean(axis=1).values, M.quantile(0.1, axis=1).values, M.quantile(0.9, axis=1).values, M.shape[1]


def draw(ax, dfs, col, color, label, deriv=None, smooth=1, ls="-"):
    if not dfs:
        return
    x, m, lo, hi, n = seed_band(dfs, col, deriv, smooth)
    keep = x > 0                                  # 対数軸のため MCS=0 は除く
    ax.plot(x[keep], m[keep], color=color, lw=1.6, ls=ls, label=label)
    if n > 1:
        ax.fill_between(x[keep], lo[keep], hi[keep], color=color, alpha=0.18, lw=0)


def grid_fig(n_rows, b_list, title, row_h=2.6):
    n_cols = len(b_list)
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(3.6 * n_cols + 1.2, row_h * n_rows),
                             squeeze=False, sharex=True)
    fig.suptitle(title, fontsize=13, color=INK)
    for c, b in enumerate(b_list):
        axes[0, c].set_title(f"b={b}", fontsize=11, color=INK)
        for r in range(n_rows):
            axes[r, c].set_xscale("log")
            style_axis(axes[r, c])
        axes[-1, c].set_xlabel("MCS", fontsize=10)
    return fig, axes


def finish(fig, axes, row_labels, path):
    for r, lab in enumerate(row_labels):
        axes[r, 0].set_ylabel(lab, fontsize=10)
        h, l = axes[r, 0].get_legend_handles_labels()
        if h:
            axes[r, -1].legend(h, l, fontsize=8, loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"✅ 保存: {path}")


def zline(ax, Z):
    ax.axhline(Z, color=MUTED, lw=0.9, ls="--")


# ==========================================
# 4. 各ログのグラフ
# ==========================================
def plot_L1(Z, logs, b_list, tag):
    """戦略割合・平均評判・免罰D割合・罰の量"""
    fig, axes = grid_fig(4, b_list, f"L1 戦略・評判・免罰D・罰  {tag}")
    for c, b in enumerate(b_list):
        L1s = [d["L1"] for d in logs[b].values() if "L1" in d]
        if not L1s:
            continue
        Nn = L1s[0][["n_C", "n_PC", "n_D"]].iloc[0].sum()
        ax = axes[0, c]
        for s in ("C", "PC", "D"):
            draw(ax, L1s, None, COL[s], s, deriv=lambda df, s=s: df[f"n_{s}"] / Nn)
        ax.set_ylim(-0.02, 1.02)
        ax = axes[1, c]
        for s in ("C", "PC", "D"):
            draw(ax, L1s, f"meanR_{s}", COL[s], f"平均評判 {s}")
        zline(ax, Z); ax.set_ylim(0, 100)
        ax = axes[2, c]
        draw(ax, L1s, None, COL["D"], "免罰D割合 nHigh_D/n_D", deriv=lambda df: df["nHigh_D"] / df["n_D"].replace(0, np.nan))
        draw(ax, L1s, None, "#6250d6", "Z直下D割合 nNearZ_D/n_D", deriv=lambda df: df["nNearZ_D"] / df["n_D"].replace(0, np.nan))
        draw(ax, L1s, "meanF_D", MUTED, "Dの平均罰確率 f", ls="--")
        ax.set_ylim(-0.02, 1.02)
        ax = axes[3, c]
        draw(ax, L1s, "n_punish_exec", COL["PC"], "罰の執行（θ>0）")
        draw(ax, L1s, "n_punish_exec_raw", MUTED, "旧定義（θ=0 含む）", ls="--")
        draw(ax, L1s, "E_punish_exec", INK, "期待値 Σf·[θ>0]", ls=":")
    finish(fig, axes, ["戦略の割合", "平均評判", "割合 / 確率", "罰の回数 / MCS"],
           os.path.join(LOG_GRAPH_DIR, f"L1_{tag}.png"))


def plot_L2(Z, logs, b_list, tag):
    """戦略切替: 方向別フロー、ωゲート、持ち越し評判"""
    fig, axes = grid_fig(3, b_list, f"L2 戦略切替  {tag}")
    flows = [("PC_to_D", COL["D"], "-"), ("D_to_PC", COL["PC"], "-"), ("C_to_D", COL["D"], "--"),
             ("D_to_C", COL["C"], "--"), ("C_to_PC", COL["PC"], ":"), ("PC_to_C", COL["C"], ":")]
    for c, b in enumerate(b_list):
        L2s = [d["L2"] for d in logs[b].values() if "L2" in d]
        if not L2s:
            continue
        ax = axes[0, c]
        for col, colr, ls in flows:
            draw(ax, L2s, col, colr, col.replace("_to_", "→"), smooth=10, ls=ls)
        ax = axes[1, c]
        draw(ax, L2s, None, INK, "ゲート棄却 / 試行", smooth=10,
             deriv=lambda df: df["n_gate_reject"] / df["n_attempt"].replace(0, np.nan))
        draw(ax, L2s, None, COL["C"], "y高評判の試行割合", smooth=10,
             deriv=lambda df: df["n_attempt_yHigh"] / df["n_attempt"].replace(0, np.nan))
        draw(ax, L2s, None, COL["PC"], "切替のうち y高評判", smooth=10,
             deriv=lambda df: df["n_switch_yHigh"] / (df["n_switch_yHigh"] + df["n_switch_yLow"]).replace(0, np.nan))
        ax.set_ylim(-0.02, 1.02)
        ax = axes[2, c]
        draw(ax, L2s, "meanR_to_D", COL["D"], "Dへ切替時の持ち越し評判", smooth=10)
        draw(ax, L2s, "meanR_to_PC", COL["PC"], "PCへ切替時の持ち越し評判", smooth=10)
        draw(ax, L2s, "meanR_to_C", COL["C"], "Cへ切替時の持ち越し評判", smooth=10)
        zline(ax, Z); ax.set_ylim(0, 100)
    finish(fig, axes, ["切替数 / MCS（10MCS平滑）", "割合", "持ち越し評判"],
           os.path.join(LOG_GRAPH_DIR, f"L2_{tag}.png"))


def plot_L5(Z, logs, b_list, tag):
    """ペイオフ: 戦略別合計、境界での利得差、内訳"""
    fig, axes = grid_fig(3, b_list, f"L5 ペイオフ内訳  {tag}")
    for c, b in enumerate(b_list):
        L5s = [d["L5"] for d in logs[b].values() if "L5" in d]
        if not L5s:
            continue
        ax = axes[0, c]
        for s in ("C", "PC", "D"):
            draw(ax, L5s, f"{s}_total", COL[s], f"{s} 平均ペイオフ")
        draw(ax, L5s, "D_G_total", COL["D"], "D 高評判（免罰）", ls="--")
        draw(ax, L5s, "D_B_total", COL["D"], "D 低評判", ls=":")
        ax = axes[1, c]
        draw(ax, L5s, None, COL["PC"], "境界 Π(PC|D隣接) − Π(D|PC隣接)",
             deriv=lambda df: df["PC_bdD_total"] - df["D_bdPC_total"])
        draw(ax, L5s, None, COL["C"], "境界 Π(C|D隣接) − Π(D|C隣接)",
             deriv=lambda df: df["C_bdD_total"] - df["D_bdC_total"])
        ax.axhline(0, color=MUTED, lw=0.9)
        ax = axes[2, c]
        draw(ax, L5s, "PC_pcost", COL["PC"], "PC の罰コスト αΣKD")
        draw(ax, L5s, "D_fine", COL["D"], "D の罰金 βΣθ")
        draw(ax, L5s, None, INK, "共通分の差 PC−D", deriv=lambda df: df["PC_common"] - df["D_common"], ls=":")
    finish(fig, axes, ["平均ペイオフ", "境界の利得差（>0 でPC/C有利）", "内訳"],
           os.path.join(LOG_GRAPH_DIR, f"L5_{tag}.png"))


def plot_L6(Z, logs, b_list, tag):
    """評判更新イベント: 戦略別の平均変化量と、相手 y が高評判だった割合"""
    fig, axes = grid_fig(2, b_list, f"L6 評判更新イベント  {tag}")
    for c, b in enumerate(b_list):
        L6s = [d["L6"] for d in logs[b].values() if "L6" in d]
        if not L6s:
            continue
        for s in ("C", "PC", "D"):
            n_cols = [f"{s}_{k}_n" for k in ("GG", "GB", "BG", "BB")]
            d_cols = [f"{s}_{k}_dR" for k in ("GG", "GB", "BG", "BB")]
            draw(axes[0, c], L6s, None, COL[s], f"{s}: 平均ΔR / 更新", smooth=10,
                 deriv=lambda df, n=n_cols, d=d_cols: df[d].sum(axis=1) / df[n].sum(axis=1).replace(0, np.nan))
            draw(axes[1, c], L6s, None, COL[s], f"{s}: 相手y高評判の割合", smooth=10,
                 deriv=lambda df, s=s: (df[f"{s}_GG_n"] + df[f"{s}_GB_n"]) /
                 df[[f"{s}_{k}_n" for k in ("GG", "GB", "BG", "BB")]].sum(axis=1).replace(0, np.nan))
        axes[0, c].axhline(0, color=MUTED, lw=0.9)
        axes[1, c].set_ylim(-0.02, 1.02)
    finish(fig, axes, ["平均ΔR（10MCS平滑）", "割合"], os.path.join(LOG_GRAPH_DIR, f"L6_{tag}.png"))


def plot_L7(Z, logs, b_list, tag):
    """空間構造: 境界長、クラスター、PCクラスター内外の評判"""
    fig, axes = grid_fig(3, b_list, f"L7 境界・クラスター  {tag}")
    for c, b in enumerate(b_list):
        L7s = [d["L7"] for d in logs[b].values() if "L7" in d]
        if not L7s:
            continue
        E = 2 * L7s[0][["e_PC_D", "e_C_D", "e_PC_C", "e_PC_PC", "e_C_C", "e_D_D"]].iloc[0].sum() / 2
        ax = axes[0, c]
        draw(ax, L7s, None, COL["D"], "PC-D 辺", deriv=lambda df: df["e_PC_D"] / E)
        draw(ax, L7s, None, COL["C"], "C-D 辺", deriv=lambda df: df["e_C_D"] / E)
        draw(ax, L7s, None, COL["PC"], "PC-C 辺", deriv=lambda df: df["e_PC_C"] / E)
        ax = axes[1, c]
        cl = [df.dropna(subset=["maxClu_PC"]) for df in L7s]
        Nn = E / 2
        draw(ax, cl, None, COL["PC"], "最大PCクラスター / N", deriv=lambda df: df["maxClu_PC"] / Nn)
        draw(ax, cl, None, INK, "最大協力者(C∪PC)クラスター / N", deriv=lambda df: df["maxClu_Coop"] / Nn, ls="--")
        ax.set_ylim(-0.02, 1.02)
        ax = axes[2, c]
        draw(ax, L7s, "meanR_PC_int", COL["PC"], "PC 内部（D非接触）")
        draw(ax, L7s, "meanR_PC_bd", COL["PC"], "PC 境界（D接触）", ls="--")
        draw(ax, L7s, "meanR_D_bd", COL["D"], "D 境界（PC接触）", ls="--")
        draw(ax, L7s, "meanR_D_int", COL["D"], "D 内部")
        zline(ax, Z); ax.set_ylim(0, 100)
    finish(fig, axes, ["辺の割合", "サイズ / N", "平均評判"], os.path.join(LOG_GRAPH_DIR, f"L7_{tag}.png"))


def plot_L3(Z, logs, b_list, tag):
    """評判分布の時間変化（seed 合算）。行 = スナップショット時刻、列 = 戦略"""
    for b in b_list:
        L3s = [d["L3"] for d in logs[b].values() if "L3" in d]
        if not L3s:
            continue
        H = pd.concat(L3s).groupby(["MCS", "strategy", "bin_lo"], as_index=False)["count"].sum()
        times = sorted(H["MCS"].unique())
        fig, axes = plt.subplots(1, 3, figsize=(15, 0.32 * len(times) + 2.2), sharey=True)
        for k, s in enumerate(("C", "PC", "D")):
            M = (H[H["strategy"] == s].pivot(index="MCS", columns="bin_lo", values="count")
                 .reindex(index=times).fillna(0))
            ax = axes[k]
            # 行ごとに割合へ正規化（時刻で人数が大きく違うため）。R=0,100 への張り付きで色が潰れないよう
            # 上限は 99 パーセンタイルで切る（張り付き自体は最濃色で見える）
            P = M.values / np.maximum(M.values.sum(axis=1, keepdims=True), 1)
            vmax = max(np.percentile(P, 99), 1e-6)
            im = ax.imshow(P, aspect="auto", cmap="Blues", origin="upper", vmin=0, vmax=vmax,
                           extent=(0, 100, len(times), 0), interpolation="nearest")
            ax.axvline(Z, color=COL["D"], lw=1.2, ls="--")
            ax.set_title(f"{s}（Z={Z} を破線）", fontsize=11)
            ax.set_xlabel("評判 R", fontsize=10)
            ax.set_yticks(np.arange(len(times)) + 0.5)
            ax.set_yticklabels([str(t) for t in times], fontsize=8)
            fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02, label="その戦略内の割合")
        axes[0].set_ylabel("MCS", fontsize=10)
        fig.suptitle(f"L3 評判分布  {tag} b={b}", fontsize=13)
        fig.tight_layout(rect=(0, 0, 1, 0.95))
        path = os.path.join(LOG_GRAPH_DIR, f"L3_{tag}_b={b}.png")
        fig.savefig(path, dpi=130, bbox_inches="tight"); plt.close(fig)
        print(f"✅ 保存: {path}")


def plot_L4(Z, logs, b_list, tag):
    """空間スナップショット（最初の seed）。上段 = 戦略、下段 = 評判（Z 以上を濃く）"""
    from matplotlib.colors import ListedColormap
    cmap_s = ListedColormap([COL["D"], COL["C"], COL["PC"]])    # 0=D, 1=C, 2=PC
    for b in b_list:
        d0 = next((d for d in logs[b].values() if "L4" in d), None)
        if d0 is None:
            continue
        snaps = d0["L4"]
        times = sorted(int(k.split("_")[1]) for k in snaps if k.startswith("strategy_"))
        fig, axes = plt.subplots(2, len(times), figsize=(2.6 * len(times), 5.6), squeeze=False)
        for c, t in enumerate(times):
            S = snaps[f"strategy_{t:07d}"]; Rm = snaps[f"reputation_{t:07d}"]
            axes[0, c].imshow(S, cmap=cmap_s, vmin=0, vmax=2, interpolation="nearest")
            axes[0, c].set_title(f"MCS={t}", fontsize=10)
            im = axes[1, c].imshow(Rm, cmap="Greys", vmin=0, vmax=100, interpolation="nearest")
            axes[1, c].contour(Rm >= Z, levels=[0.5], colors=[COL["PC"]], linewidths=0.4)
            for r in range(2):
                axes[r, c].set_xticks([]); axes[r, c].set_yticks([])
        axes[0, 0].set_ylabel("戦略\n(橙D 青C 緑PC)", fontsize=9)
        axes[1, 0].set_ylabel(f"評判\n(緑線: R=Z={Z})", fontsize=9)
        fig.colorbar(im, ax=axes[1, :].tolist(), fraction=0.02, pad=0.01, label="R")
        fig.suptitle(f"L4 空間スナップショット  {tag} b={b}", fontsize=13)
        path = os.path.join(LOG_GRAPH_DIR, f"L4_{tag}_b={b}.png")
        fig.savefig(path, dpi=130, bbox_inches="tight"); plt.close(fig)
        print(f"✅ 保存: {path}")


# ==========================================
# 5. (C) 要約指標
# ==========================================
def first_time(mcs, cond):
    idx = np.flatnonzero(cond)
    return float(mcs[idx[0]]) if idx.size else np.nan


def pc_d_lag(L1, max_lag=300):
    """後半区間で corr(n_PC(t), n_D(t+k)) が正で最大となるラグ k [MCS]
       k>0: PC のピークの k MCS 後に D のピークが来る（PC→D の位相遅れ）。
       n_C+n_PC+n_D=N のため k=0 付近は構造的に負相関になるので、|相関| ではなく正の最大を取る"""
    df = L1[L1["MCS"] > 0]
    df = df.iloc[len(df) // 2:]
    max_lag = min(max_lag, len(df) // 4)          # 短い系列（早期終了）ではラグ範囲を縮める
    if max_lag < 5 or df["n_PC"].std() == 0 or df["n_D"].std() == 0:
        return np.nan, np.nan
    x = (df["n_PC"] - df["n_PC"].rolling(201, center=True, min_periods=1).mean()).values
    y = (df["n_D"] - df["n_D"].rolling(201, center=True, min_periods=1).mean()).values
    x = (x - x.mean()) / (x.std() + 1e-12); y = (y - y.mean()) / (y.std() + 1e-12)
    lags = range(-max_lag, max_lag + 1)
    cc = [np.mean(x[max(0, -k):len(x) - max(0, k)] * y[max(0, k):len(y) - max(0, -k)]) for k in lags]
    k = int(np.argmax(cc))
    return float(list(lags)[k]), float(cc[k])


def summarize(Z, logs):
    rows = []
    for b, by_seed in logs.items():
        for seed, d in by_seed.items():
            if "L1" not in d:
                continue
            L1 = d["L1"]; meta = d.get("meta", {})
            mcs = L1["MCS"].values
            Nn = L1[["n_C", "n_PC", "n_D"]].iloc[0].sum()
            coop = (L1["n_C"] + L1["n_PC"]).values / Nn
            fhd = (L1["nHigh_D"] / L1["n_D"].replace(0, np.nan)).values
            late = slice(int(len(L1) * 0.9), None)
            k_min, k_max = int(np.nanargmin(coop)), int(np.nanargmax(coop))
            row = dict(group=a.group, rule=modelPATTERN, pattern=PATTERN, type_name=type_name, Z=Z, omega=omega,
                       b=float(b), seed=seed, variant=VARIANT,
                       end_mcs=meta.get("end_mcs"), end_reason=meta.get("end_reason"),
                       final_C=L1["n_C"].iloc[-1] / Nn, final_PC=L1["n_PC"].iloc[-1] / Nn, final_D=L1["n_D"].iloc[-1] / Nn,
                       min_coop=coop[k_min], t_min_coop=mcs[k_min], max_coop=coop[k_max], t_max_coop=mcs[k_max],
                       t_D_extinct=first_time(mcs, L1["n_D"].values == 0),
                       t_PC_extinct=first_time(mcs, L1["n_PC"].values == 0),
                       t_C_extinct=first_time(mcs, L1["n_C"].values == 0),
                       init_fracHighD=fhd[0], max_fracHighD=np.nanmax(fhd) if np.isfinite(fhd).any() else np.nan,
                       t_max_fracHighD=mcs[int(np.nanargmax(fhd))] if np.isfinite(fhd).any() else np.nan,
                       late_coop_mean=np.nanmean(coop[late]), late_coop_std=np.nanstd(coop[late]),
                       late_fracHighD=np.nanmean(fhd[late]),
                       late_punish_exec=L1["n_punish_exec"].iloc[late].mean(),
                       late_nFloatBelowZ=L1["nFloatBelowZ"].iloc[late].mean())
            if "L2" in d:
                L2 = d["L2"].iloc[int(len(d["L2"]) * 0.9):]
                row["late_gate_reject_ratio"] = L2["n_gate_reject"].sum() / max(1, L2["n_attempt"].sum())
                row["total_nHigh_to_D"] = int(d["L2"]["nHigh_to_D"].sum())     # 免罰Dの切替による供給総数
            if "L5" in d:
                L5 = d["L5"].iloc[int(len(d["L5"]) * 0.9):]
                row["late_bd_payoff_PC_minus_D"] = (L5["PC_bdD_total"] - L5["D_bdPC_total"]).mean()
            if "L7" in d:
                L7 = d["L7"].iloc[int(len(d["L7"]) * 0.9):]
                row["late_meanR_PC_int_minus_bd"] = (L7["meanR_PC_int"] - L7["meanR_PC_bd"]).mean()
                row["late_e_PC_D"] = L7["e_PC_D"].mean()
            row["lag_PC_to_D"], row["lag_corr"] = pc_d_lag(L1)
            rows.append(row)
    return rows


# ==========================================
# 6. 実行ループ
# ==========================================
if __name__ == "__main__":
    all_rows = []
    for Z in ZS:
        print(f"\n--- Z={Z} のグラフ作成開始 ---")
        if not a.skip_legacy:
            for seed in SEEDS:
                plot_coop(Z, "Base", seed)
                plot_coop(Z, "C", seed)
                plot_coop(Z, "PC", seed)
                plot_punish(Z, seed)
        if a.skip_logs:
            continue
        logs = load_logs(Z)
        if not logs:
            print(f"ℹ️ 詳細ログなし: Z={Z}（run_simulation.py を --no-log なしで実行すると作成されます）")
            continue
        os.makedirs(LOG_GRAPH_DIR, exist_ok=True)
        b_list = sorted(logs.keys(), key=float)
        n_seed = max(len(v) for v in logs.values())
        tag = f"{modelPATTERN}_{type_name}_Z={Z}_omega={omega}_seeds={n_seed}"
        for fn in (plot_L1, plot_L2, plot_L5, plot_L6, plot_L7, plot_L3, plot_L4):
            try:
                fn(Z, logs, b_list, tag)
            except Exception as e:
                print(f"❌ エラー({fn.__name__} Z={Z}): {e}")
        all_rows += summarize(Z, logs)

    if all_rows:
        os.makedirs(LOG_GRAPH_DIR, exist_ok=True)
        out = os.path.join(LOG_GRAPH_DIR, f"summary_{modelPATTERN}_{type_name}_omega={omega}.csv")
        pd.DataFrame(all_rows).to_csv(out, index=False, encoding="utf-8-sig")
        print(f"✅ 要約指標: {out}")

    print(f"\n🎉 {modelPATTERN} / {PATTERN} / omega={omega} の全グラフ作成が完了しました！")
