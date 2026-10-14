# -*- coding: utf-8 -*-
"""
ペイオフ(戦略別平均ペイオフ)のグラフ作成:1条件(モデル×PATTERN×ωy)ぶんを担当するワーカー。
all_payoff.py から呼ばれる(引数の並びは run_glaph_all.py と同じ)。

  python run_payoff.py <model> <PATTERN> <dateフォルダ> <glaphフォルダ> <omega>

読み込み元: m2/{model}データ/Z_b_change報酬罰/{PATTERN}/Payoff/payoff_history_Z=..._omega=....zip
            (中身: payoff_Z=50_b=0_r=3.0_{PATTERN}_omega=0.01.csv など)
保存先  : m2/{model}グラフ/Z_change_協力率変遷/{PATTERN}/Payoff/ (無ければ自動作成)

作るグラフ(Z・bごとの違いが一目で分かるように、bは1つの図に6本の線):
  G1 戦略別ペイオフ推移 .......... Total / C / D / PC の4面(bごとに線)
  G2 ペイオフ差(選択圧) ......... D-PC, D-C, C-PC の3面(符号が戦略更新の向きを決める)
  G3 協力率との重ね描き .......... 協力率(C, PC, 合計)・ペイオフ・ペイオフ差を縦に並べる(OVERLAY_BSのbだけ)
  G4 ヒートマップ(Z×b) .......... 時間窓ごとの平均ペイオフ差
  G5 優位の転換時刻(Z×b) ........ PC(またはC)が初めてDを上回り、連続して維持した時刻
  G6 評価ルール比較 ............. 4ルール横並び(compareモード:  python run_payoff_graph.py __compare__ <ラベル> <omega>)
"""
import os
import sys
import zipfile
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')            # ウィンドウを出さずに保存だけ行う(メモリ節約)
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

warnings.filterwarnings("ignore", category=RuntimeWarning)

# 日本語フォント(Windows / Mac / Linux のどれかにあるものが自動で使われます)
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Yu Gothic', 'Meiryo', 'MS Gothic', 'Hiragino Sans', 'IPAexGothic',
                                   'Noto Sans CJK JP', 'Noto Sans JP', 'TakaoGothic', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False       # 日本語フォント使用時にマイナス記号が化けるのを防ぐ

# ==========================================================
# 0. 設定(ここだけ環境に合わせて変えてください)
# ==========================================================
# m2 フォルダ(imageデータ・shunningデータ… が並んでいる場所)。
# スクリプトの場所(と実行時のフォルダ)から上にさかのぼって「imageデータ」がある階層を自動で探します。
# m2 直下・m2\python・m2\python\xxx_code のどこに置いても、どこから実行しても動きます。
# 見つからない場合は M2_FALLBACK を使います。
M2_FALLBACK = r"C:\Users\Admin\project\m2"

def _find_m2():
    starts = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
    for s in starts:
        p = s
        while True:
            if os.path.isdir(os.path.join(p, "imageデータ")):
                return p
            parent = os.path.dirname(p)
            if parent == p:
                break
            p = parent
    return M2_FALLBACK

DATA_ROOT = _find_m2()

Z_LIST = [50, 60, 70, 80, 90, 95, 98]
B_LIST = ['0', '0.2', '0.4', '0.6', '0.8', '1.0']
R_VAL = "3.0"                       # ファイル名の r=3.0
R_TAG = "3_0"                       # (旧形式のファイル名用) r=3.0 → 3_0
OVERLAY_BS = ['0', '1.0']           # G3(協力率との重ね描き)を作るb
SMOOTH_WINDOW = 1                   # >1 にすると移動平均(MCS)をかけてから描く(差のグラフが見やすくなる)
WINDOWS = [(1, 10), (10, 100), (100, 1000), (1000, 10000)]   # G4の時間窓(MCS)
SUSTAIN = 10                        # G5:優位が連続して何MCS続いたら「転換」とみなすか
HEAT_VLIM = 5.0                     # G4のカラースケール(±この値で飽和)

# 評価ルール: model → (dateフォルダ, glaphフォルダ)
MODEL_INFO = {
    "image":    ("imageデータ",    "imageグラフ"),
    "shunning": ("shunningデータ", "shunningグラフ"),
    "simple":   ("simpleデータ",   "simpleグラフ"),
    "stern":    ("sternデータ",    "sternグラフ"),
}
# 報酬モデル: ラベル → {model: PATTERN}
#   a〜d   = 通常スケール
#   a'〜d' = a〜d の各値を 1/5 にしたもの
def _pat(c_g, c_b, d_g, d_b, pc_g, pc_b):
    """(3, 1, -3, -1, 5, 3) → '+3+1-3-1+5+3'、(0.6, 0.2, ...) → '+0.6+0.2...'(1.0 は '1' と書く)"""
    f = lambda v: ("+" if v >= 0 else "-") + f"{abs(round(v, 6)):g}"
    return "".join(f(v) for v in (c_g, c_b, d_g, d_b, pc_g, pc_b))

_BASE = {   # (C|y=G, C|y=B, D|y=G, D|y=B, PC|y=G, PC|y=B) の通常スケール値
    "image":    {"a": (3, 1, -3, -1, 5, 3), "b": (5, 1, -5, -1, 5, 1), "c": (5, 1, -5, -1, 8, 3), "d": (5, 1, -5, -1, 10, 5)},
    "shunning": {"a": (3, -1, -3, 1, 5, -3), "b": (5, -1, -5, 1, 5, -1), "c": (5, -1, -5, 1, 8, -3), "d": (5, -1, -5, 1, 10, -5)},
    "simple":   {"a": (3, 1, -3, 1, 5, 3), "b": (5, 1, -5, 1, 5, 1), "c": (5, 1, -5, 1, 8, 3), "d": (5, 1, -5, 1, 10, 5)},
    "stern":    {"a": (3, -1, -3, 1, 5, -3), "b": (5, -1, -5, 1, 5, -1), "c": (5, -1, -5, 1, 8, -3), "d": (5, -1, -5, 1, 10, -5)},
}
# a'〜d' を追加(各値を 1/5)
SCALE_PRIME = 5
for _m, _d in _BASE.items():
    for _k in list(_d.keys()):
        _d[_k + "'"] = tuple(round(x / SCALE_PRIME, 6) for x in _d[_k])
# 例: image の a' = (0.6, 0.2, -0.6, -0.2, 1, 0.6), d' = (1, 0.2, -1, -0.2, 2, 1)

PATTERNS = {}      # PATTERNS[label][model] = PATTERN文字列
for _m, _d in _BASE.items():
    for _k, _v in _d.items():
        PATTERNS.setdefault(_k, {})[_m] = _pat(*_v)
# 例: PATTERNS["a"]["image"]  == "+3+1-3-1+5+3"
#     PATTERNS["d'"]["image"] == "+1+0.2-1-0.2+2+1"

# ==========================================================
# 1. ファイルの探索と読み込み
# ==========================================================
def tag(x):
    """0.01 → '0_01', '1.0' → '1_0'(ファイル名の表記に合わせる)"""
    return str(x).replace('.', '_')

def b_variants(b):
    v = {tag(b)}
    try:
        v.add(tag(f"{float(b):.1f}"))          # '0' → '0_0' も試す
    except ValueError:
        pass
    return sorted(v)

def payoff_filenames(Z, b, pattern, omega):
    """
    探すCSV名の候補(先頭が実際のデータの形式)。
      新: payoff_Z=50_b=0_r=3.0_+1+0.2-1-0.2+2+1_omega=0.01.csv
      旧: payoff_Z_50_b_0_r_3_0__1_0_2-1-0_2_2_1_omega_0_01.csv
    """
    names = []
    for bb in [b, f"{float(b):.1f}", f"{float(b):g}"]:
        nm = f"payoff_Z={Z}_b={bb}_r={R_VAL}_{pattern}_omega={omega}.csv"
        if nm not in names:
            names.append(nm)
    pat = pattern.replace('+', '_').replace('.', '_')
    names += [f"payoff_Z_{Z}_b_{bb}_r_{R_TAG}_{pat}_omega_{tag(omega)}.csv" for bb in b_variants(b)]
    return names

_INDEX_CACHE = {}
def build_index(root, any_zip=False):
    """
    root以下の csv / zip の中身を一度だけ走査して索引を作る。
      csvs[ファイル名] = パス
      zmem[ファイル名] = (zipのパス, zip内のメンバー名)
    any_zip=True : 名前を問わずすべてのzipの中身を調べる(Payoffフォルダ用)
    any_zip=False: 名前に 'payoff' を含むzipだけ調べる(予備の広域検索用)
    """
    key = (root, any_zip)
    if key in _INDEX_CACHE:
        return _INDEX_CACHE[key]
    csvs, zmem = {}, {}
    if os.path.isdir(root):
        for dp, _, fns in os.walk(root):
            for fn in fns:
                p = os.path.join(dp, fn)
                low = fn.lower()
                if low.endswith('.csv'):
                    csvs[fn] = p
                elif low.endswith('.zip') and (any_zip or 'payoff' in low):
                    try:
                        with zipfile.ZipFile(p) as zf:
                            for n in zf.namelist():
                                zmem[os.path.basename(n)] = (p, n)
                    except zipfile.BadZipFile:
                        print(f"⚠️ 壊れたzipをスキップ: {p}")
    _INDEX_CACHE[key] = (csvs, zmem)
    return _INDEX_CACHE[key]

def payoff_dir(model, pattern):
    """例: m2/imageデータ/Z_b_change報酬罰/+1+0.2-1-0.2+2+1/Payoff"""
    return os.path.join(DATA_ROOT, MODEL_INFO[model][0], "Z_b_change報酬罰", pattern, "Payoff")

def graph_dir_of(graph_folder, pattern):
    """例: m2/imageグラフ/Z_change_協力率変遷/+1+0.2-1-0.2+2+1/Payoff"""
    return os.path.join(DATA_ROOT, graph_folder, "Z_change_協力率変遷", pattern, "Payoff")

def read_payoff(Z, b, model, pattern, omega):
    """生のDataFrameを返す。見つからなければ None"""
    names = payoff_filenames(Z, b, pattern, omega)
    # ① Payoffフォルダ(csv直置き、または zip の中。zip名は何でもよい)
    # ② 見つからなければ {dateフォルダ}/Z_b_change報酬罰/{PATTERN} 全体から探す(予備)
    fallback = os.path.join(DATA_ROOT, MODEL_INFO[model][0], "Z_b_change報酬罰", pattern)
    for root, any_zip in ((payoff_dir(model, pattern), True), (fallback, False)):
        csvs, zmem = build_index(root, any_zip)
        for nm in names:
            if nm in csvs:
                return pd.read_csv(csvs[nm])
            if nm in zmem:
                zp, member = zmem[nm]
                with zipfile.ZipFile(zp) as zf, zf.open(member) as f:
                    return pd.read_csv(f)
    return None

PAY_COLS = ['Avg_Payoff_Total', 'Avg_Payoff_C', 'Avg_Payoff_D', 'Avg_Payoff_PC']

def clean_payoff(df):
    """
    ・最後に非ゼロの行より後ろ → シミュレーション終了後のゼロ埋めなので NaN
      (全員がC/PCになって1.0に到達、またはD全滅の吸収状態で打ち切られたとき)
    ・戦略ごとの平均が厳密に 0.0 → その戦略が(その時点で)存在しない → NaN
    """
    d = df.copy()
    nz = (d[PAY_COLS] != 0).any(axis=1)
    last = nz[nz].index.max() if nz.any() else -1
    d.loc[d.index > last, PAY_COLS] = np.nan
    for c in ['Avg_Payoff_C', 'Avg_Payoff_D', 'Avg_Payoff_PC']:
        d.loc[d[c] == 0, c] = np.nan
    d['dD_PC'] = d['Avg_Payoff_D'] - d['Avg_Payoff_PC']      # >0:DがPCより有利
    d['dD_C'] = d['Avg_Payoff_D'] - d['Avg_Payoff_C']        # >0:DがCより有利
    d['dC_PC'] = d['Avg_Payoff_C'] - d['Avg_Payoff_PC']      # >0:CがPCより有利(理論上は罰コスト分)
    if SMOOTH_WINDOW > 1:
        for c in PAY_COLS + ['dD_PC', 'dD_C', 'dC_PC']:
            d[c] = d[c].rolling(SMOOTH_WINDOW, min_periods=1, center=True).mean().where(d[c].notna())
    d.attrs['last_step'] = int(d.loc[last, 'MCS_Step']) if last >= 0 else None
    return d

def load_all(model, pattern, omega):
    """data[Z][b] = 整形済みDataFrame(無ければ None)"""
    data = {}
    for Z in Z_LIST:
        data[Z] = {}
        for b in B_LIST:
            raw = read_payoff(Z, b, model, pattern, omega)
            data[Z][b] = clean_payoff(raw) if raw is not None else None
            if data[Z][b] is not None:
                data[Z][b].attrs['n_rows_raw'] = len(raw)
    return data

# ----- 協力率(既存の zip と同じ場所・同じ列名)-----
def read_coop(Z, b, model, pattern, omega, kind):
    date_dir = MODEL_INFO[model][0]
    sub = "" if kind == "Base" else f"/{kind}"
    prefix = model if kind == "Base" else f"{model}_{kind}"
    col = "Cooperation Rate" if kind == "Base" else f"{kind} Rate"
    zp = f"{DATA_ROOT}/{date_dir}/Z_b_change報酬罰/{pattern}{sub}/{prefix}_Z={Z}_r=3.0_{pattern}_omega={omega}.zip"
    fn = f"{prefix}_Z={Z}_b={b}_r=3.0_{pattern}_omega={omega}.csv"
    if not os.path.exists(zp):
        return None
    try:
        with zipfile.ZipFile(zp) as zf:
            if fn in zf.namelist():
                with zf.open(fn) as f:
                    return pd.read_csv(f)[col]
    except Exception as e:
        print(f"❌ 協力率の読み込みエラー({kind} Z={Z} b={b}): {e}")
    return None

# ==========================================================
# 2. 共通の描画ヘルパー
# ==========================================================
def b_colors():
    return {b: plt.cm.tab10(i) for i, b in enumerate(B_LIST)}   # 既存グラフと同じ既定色の並び

def style_log_axis(ax, xmax=10000):
    ax.set_xscale('log')
    ax.set_xlim(1, xmax)
    ax.grid(True, which='major', alpha=0.6)
    ax.set_xlabel("MCS", fontsize=13)

def set_symlog(ax):
    ax.set_yscale('symlog', linthresh=1.0)
    ticks = [-10, -3, -1, 0, 1, 3, 10]
    ax.set_yticks(ticks); ax.set_yticklabels([str(t) for t in ticks])
    ax.set_ylim(-12, 12)

def savefig(fig, outdir, name):
    os.makedirs(outdir, exist_ok=True)
    p = os.path.join(outdir, name)
    fig.savefig(p, bbox_inches='tight', dpi=130)
    plt.close(fig)
    print(f"✅ 保存: {p}")

# ==========================================================
# 3. グラフ
# ==========================================================
def plot_G1_G2(model, pattern, omega, Z, dz, outdir):
    """G1 戦略別ペイオフ推移 / G2 ペイオフ差。dz = {b: DataFrame}"""
    col = b_colors()
    # ---- G1
    fig, axs = plt.subplots(2, 2, figsize=(14, 9), sharex=True)
    panels = [('Avg_Payoff_Total', '全体の平均'), ('Avg_Payoff_C', 'C(貢献者)'),
              ('Avg_Payoff_D', 'D(非協力者)'), ('Avg_Payoff_PC', 'PC(罰則者)')]
    for ax, (c, lab) in zip(axs.ravel(), panels):
        for b in B_LIST:
            d = dz.get(b)
            if d is not None:
                ax.plot(d['MCS_Step'], d[c], color=col[b], lw=1.0, label=f"b={b}")
        ax.axhline(0, color='k', lw=0.8)
        ax.axhline(10, color='gray', lw=0.8, ls='--')        # 全員C/PC(r=3)のときの上限 = 10
        ax.set_title(lab, fontsize=14); ax.set_ylabel("平均ペイオフ(5ゲーム合計)", fontsize=11)
        style_log_axis(ax)
    axs[0, 0].legend(fontsize=11)
    fig.suptitle(f"{model} Z={Z} r=3.0 ω={omega}  戦略別の平均ペイオフ(破線=10:完全協力時)", fontsize=15, y=1.0)
    savefig(fig, outdir, f"{model}ペイオフ_戦略別_Z={Z}_r=3.0_omega={omega}.png")
    # ---- G2
    fig, axs = plt.subplots(1, 3, figsize=(18, 5.5), sharex=True)
    diffs = [('dD_PC', 'Π_D − Π_PC', '上:Dが有利 / 下:PCが有利'),
             ('dD_C', 'Π_D − Π_C', '上:Dが有利 / 下:Cが有利'),
             ('dC_PC', 'Π_C − Π_PC', '上:Cが有利 / 下:PCが有利')]
    for ax, (c, lab, sub) in zip(axs, diffs):
        for b in B_LIST:
            d = dz.get(b)
            if d is not None:
                ax.plot(d['MCS_Step'], d[c], color=col[b], lw=1.0, label=f"b={b}")
        ax.axhline(0, color='k', lw=1.0)
        set_symlog(ax)
        ax.set_title(f"{lab}\n({sub})", fontsize=13); ax.set_ylabel("ペイオフ差(symlog)", fontsize=11)
        style_log_axis(ax)
    axs[0].legend(fontsize=10)
    fig.suptitle(f"{model} Z={Z} r=3.0 ω={omega}  ペイオフ差(K=0.5なので差が1でも模倣確率は大きく偏る)", fontsize=15, y=1.06)
    savefig(fig, outdir, f"{model}ペイオフ_差_Z={Z}_r=3.0_omega={omega}.png")

def plot_G3(model, pattern, omega, Z, b, d, outdir):
    """G3 協力率(C, PC, 合計)・ペイオフ・ペイオフ差を同じ時間軸で縦に並べる"""
    coop = {k: read_coop(Z, b, model, pattern, omega, k) for k in ("Base", "C", "PC")}
    have_coop = all(v is not None for v in coop.values())
    n = 3 if have_coop else 2
    fig, axs = plt.subplots(n, 1, figsize=(11, 3.6 * n), sharex=True)
    axs = np.atleast_1d(axs); i = 0
    if have_coop:
        raw_len = d.attrs.get('n_rows_raw', len(d))
        per_mcs = max(1, int(round(len(coop["Base"]) / raw_len)))      # 協力率CSVが1MCSあたり何行か(自動推定)
        if per_mcs != 1:
            print(f"ℹ️ 協力率CSVの行数/ペイオフCSVの行数 = {per_mcs}:時間軸を {per_mcs} で割って揃えます")
        x = np.arange(len(coop["Base"])) / per_mcs
        ax = axs[i]; i += 1
        ax.plot(x, coop["Base"], color='k', label='C+PC')
        ax.plot(x, coop["C"], color='tab:green', label='C')
        ax.plot(x, coop["PC"], color='tab:red', label='PC')
        ax.set_ylim(0, 1); ax.set_ylabel("協力率", fontsize=12); ax.legend(fontsize=11); style_log_axis(ax)
    ax = axs[i]; i += 1
    for c, lab, colr in [('Avg_Payoff_C', 'Π_C', 'tab:green'), ('Avg_Payoff_D', 'Π_D', 'tab:blue'), ('Avg_Payoff_PC', 'Π_PC', 'tab:red')]:
        ax.plot(d['MCS_Step'], d[c], color=colr, lw=1.0, label=lab)
    ax.axhline(0, color='k', lw=0.8); ax.set_ylabel("平均ペイオフ", fontsize=12); ax.legend(fontsize=11); style_log_axis(ax)
    ax = axs[i]
    ax.plot(d['MCS_Step'], d['dD_PC'], color='tab:purple', lw=1.0, label='Π_D−Π_PC')
    ax.plot(d['MCS_Step'], d['dD_C'], color='tab:orange', lw=1.0, label='Π_D−Π_C')
    ax.axhline(0, color='k', lw=1.0); set_symlog(ax)
    ax.set_ylabel("ペイオフ差(symlog)", fontsize=12); ax.legend(fontsize=11); style_log_axis(ax)
    axs[0].set_title(f"{model} Z={Z} b={b} r=3.0 ω={omega}", fontsize=15)
    savefig(fig, outdir, f"{model}ペイオフ_協力率重ね_Z={Z}_b={b}_r=3.0_omega={omega}.png")

def window_mean(d, lo, hi, col):
    m = (d['MCS_Step'] >= lo) & (d['MCS_Step'] < hi)
    v = d.loc[m, col]
    return float(v.median()) if v.notna().any() else np.nan     # 終了直前の少数Dによる外れ値を避けるため中央値

def plot_G4(model, pattern, omega, data, outdir):
    """G4 Z×b ヒートマップ:時間窓ごとのペイオフ差(中央値)(赤=前者が有利、青=後者が有利、灰=データなし/終了)"""
    pairs = [('dD_PC', 'Π_D − Π_PC'), ('dD_C', 'Π_D − Π_C'), ('dC_PC', 'Π_C − Π_PC')]
    fig, axs = plt.subplots(len(pairs), len(WINDOWS), figsize=(4.2 * len(WINDOWS), 3.9 * len(pairs)))
    cmap = plt.get_cmap('RdBu_r').copy(); cmap.set_bad('lightgray')
    for r, (c, lab) in enumerate(pairs):
        for k, (lo, hi) in enumerate(WINDOWS):
            M = np.full((len(Z_LIST), len(B_LIST)), np.nan)
            for i, Z in enumerate(Z_LIST):
                for j, b in enumerate(B_LIST):
                    d = data[Z][b]
                    if d is not None:
                        M[i, j] = window_mean(d, lo, hi, c)
            ax = axs[r, k]
            im = ax.imshow(np.ma.masked_invalid(M), cmap=cmap, vmin=-HEAT_VLIM, vmax=HEAT_VLIM, aspect='auto')
            ax.set_xticks(range(len(B_LIST))); ax.set_xticklabels(B_LIST, fontsize=9)
            ax.set_yticks(range(len(Z_LIST))); ax.set_yticklabels(Z_LIST, fontsize=9)
            ax.set_title(f"{lab}\nMCS {lo}〜{hi}", fontsize=11)
            if k == 0: ax.set_ylabel("Z", fontsize=11)
            if r == len(pairs) - 1: ax.set_xlabel("b", fontsize=11)
            for i in range(M.shape[0]):
                for j in range(M.shape[1]):
                    if not np.isnan(M[i, j]):
                        ax.text(j, i, f"{M[i, j]:.1f}", ha='center', va='center', fontsize=7,
                                color='white' if abs(M[i, j]) > 0.6 * HEAT_VLIM else 'black')
    fig.subplots_adjust(hspace=0.55, wspace=0.3, right=0.88)
    cax = fig.add_axes([0.91, 0.25, 0.015, 0.5])
    fig.colorbar(im, cax=cax, label=f"ペイオフ差の中央値(±{HEAT_VLIM:g}で飽和 / 赤=前者が有利)")
    fig.suptitle(f"{model} r=3.0 ω={omega}  Z×b のペイオフ差(時間窓の中央値)", fontsize=15)
    savefig(fig, outdir, f"{model}ペイオフ_ヒートマップ_Z×b_r=3.0_omega={omega}.png")

def first_sustained(series, cond, run=SUSTAIN):
    """cond(series)がrun行連続でTrueになる最初のMCS(無ければ nan)"""
    ok = cond(series).fillna(False).astype(int).values
    if len(ok) < run:
        return np.nan
    s = np.convolve(ok, np.ones(run, dtype=int), mode='valid')
    idx = np.where(s >= run)[0]
    return float(idx[0]) if len(idx) else np.nan

def plot_G5(model, pattern, omega, data, outdir):
    """G5 優位の転換時刻:PC(またはC)が初めてDを連続して上回る時刻(Z×b)"""
    items = [('dD_PC', 'PCがDを上回り始める時刻\n(Π_D−Π_PC<0が連続)'), ('dD_C', 'CがDを上回り始める時刻\n(Π_D−Π_C<0が連続)')]
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.6))
    cmap = plt.get_cmap('viridis').copy(); cmap.set_bad('lightgray')
    for ax, (c, lab) in zip(axs, items):
        M = np.full((len(Z_LIST), len(B_LIST)), np.nan)
        for i, Z in enumerate(Z_LIST):
            for j, b in enumerate(B_LIST):
                d = data[Z][b]
                if d is not None:
                    t = first_sustained(d[c], lambda s: s < 0)
                    if not np.isnan(t):
                        M[i, j] = max(d['MCS_Step'].iloc[int(t)], 1)
        im = ax.imshow(np.ma.masked_invalid(M), cmap=cmap, norm=LogNorm(vmin=1, vmax=10000), aspect='auto')
        ax.set_xticks(range(len(B_LIST))); ax.set_xticklabels(B_LIST)
        ax.set_yticks(range(len(Z_LIST))); ax.set_yticklabels(Z_LIST)
        ax.set_xlabel("b", fontsize=11); ax.set_ylabel("Z", fontsize=11); ax.set_title(lab, fontsize=12)
        for i in range(M.shape[0]):
            for j in range(M.shape[1]):
                if not np.isnan(M[i, j]):
                    ax.text(j, i, f"{int(M[i, j])}", ha='center', va='center', fontsize=8, color='white')
        fig.colorbar(im, ax=ax, shrink=0.8, label="MCS(灰=一度も連続して上回らない/データなし)")
    fig.suptitle(f"{model} r=3.0 ω={omega}  優位の転換時刻(連続{SUSTAIN}MCS)", fontsize=14, y=1.08)
    savefig(fig, outdir, f"{model}ペイオフ_転換時刻_Z×b_r=3.0_omega={omega}.png")

# ==========================================================
# 4. 評価ルール比較(compareモード)
# ==========================================================
def plot_compare(label, omega):
    """G6 4ルールを横に並べる。行=Z、列=評価ルール、線=b(0と1.0)"""
    models = list(MODEL_INFO.keys())
    fig, axs = plt.subplots(len(Z_LIST), len(models), figsize=(4.6 * len(models), 2.6 * len(Z_LIST)), sharex=True, sharey=True)
    colors = {'0': 'tab:blue', '1.0': 'tab:red'}
    any_data = False
    for j, m in enumerate(models):
        pattern = PATTERNS[label][m]
        for i, Z in enumerate(Z_LIST):
            ax = axs[i, j]
            for b in ('0', '1.0'):
                raw = read_payoff(Z, b, m, pattern, omega)
                if raw is None:
                    continue
                d = clean_payoff(raw); any_data = True
                ax.plot(d['MCS_Step'], d['dD_PC'], color=colors[b], lw=0.9, label=f"b={b}")
            ax.axhline(0, color='k', lw=0.8); set_symlog(ax)
            style_log_axis(ax); ax.set_xlabel("")
            if i == 0: ax.set_title(f"{m}\n{pattern}", fontsize=11)
            if j == 0: ax.set_ylabel(f"Z={Z}\nΠ_D−Π_PC", fontsize=10)
    if not any_data:
        plt.close(fig); print(f"⚠️ スキップ: 比較用データなし (label={label}, omega={omega})"); return
    axs[0, 0].legend(fontsize=9)
    for j in range(len(models)): axs[-1, j].set_xlabel("MCS", fontsize=11)
    fig.suptitle(f"4ルール比較 パターン{label} ω={omega}  Π_D−Π_PC(>0:Dが有利)", fontsize=15, y=1.0)
    safe = label.replace("'", "prime")
    savefig(fig, os.path.join(DATA_ROOT, "比較グラフ", "Payoff比較"), f"payoff_ルール比較_パターン{safe}_r=3.0_omega={omega}.png")

# ==========================================================
# 5. メイン
# ==========================================================
def main(argv):
    if len(argv) > 3 and argv[1] == "__compare__":
        plot_compare(argv[2], float(argv[3]))
        return
    if len(argv) > 5:
        model, pattern, date_dir, graph_dir, omega = argv[1], argv[2], argv[3], argv[4], float(argv[5])
    else:                                    # 直接実行したときのデフォルト(d' の image, ω=0.01)
        model, omega = "image", 0.01
        pattern = PATTERNS["d'"][model]      # "+1+0.2-1-0.2+2+1"
        date_dir, graph_dir = MODEL_INFO[model]
    MODEL_INFO[model] = (date_dir, graph_dir)
    print(f"🔧 [ペイオフグラフ設定] model: {model} | pattern: {pattern} | omega: {omega}")
    print(f"   m2フォルダ: {DATA_ROOT}")
    outdir = graph_dir_of(graph_dir, pattern)    # Payoffフォルダが無ければ savefig() で自動作成

    data = load_all(model, pattern, omega)
    n_found = sum(1 for Z in Z_LIST for b in B_LIST if data[Z][b] is not None)
    print(f"📂 ペイオフCSV: {n_found}/{len(Z_LIST) * len(B_LIST)} 件を読み込み")
    if n_found == 0:
        print(f"⚠️ スキップ: ペイオフCSVが1件も見つかりません。想定の保存先: {os.path.abspath(payoff_dir(model, pattern))}")
        print(f"   探したファイル名の例: {payoff_filenames(Z_LIST[0], B_LIST[0], pattern, omega)[0]}")
        return
    for Z in Z_LIST:
        dz = {b: data[Z][b] for b in B_LIST if data[Z][b] is not None}
        if not dz:
            print(f"⚠️ スキップ: Z={Z} のペイオフCSVなし"); continue
        plot_G1_G2(model, pattern, omega, Z, dz, outdir)
        for b in OVERLAY_BS:
            if b in dz:
                plot_G3(model, pattern, omega, Z, b, dz[b], outdir)
    plot_G4(model, pattern, omega, data, outdir)
    plot_G5(model, pattern, omega, data, outdir)
    print(f"\n🎉 {model} / {pattern} / omega={omega} のペイオフグラフ作成が完了しました！")

if __name__ == "__main__":
    main(sys.argv)