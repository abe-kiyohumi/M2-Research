# -*- coding: utf-8 -*-
"""
シミュレーションの並列実行

MODE で実行する条件セットを切り替える。
  "test"           : 代表条件 G13 を 1 seed・100MCS だけ（動作確認用。最初に必ずこれを実行）
  "representative" : PDF第6章の代表条件（14グループ + G03通常スケール）× SEEDS
  "controls"       : 対照実験（評判リセット / ωy=1 / 10^5MCS / D消滅後も継続 / 評判丸め）× SEEDS
  "full"           : 従来の全条件（base_params × omegas × zs）。詳細ログは LOG_IN_FULL で切替

1タスク = (条件, Z, ω, seed, variant)。タスク内で b のリストを順に実行する。
"""
import os
import multiprocessing
import subprocess
import sys

from experiment_config import (REPRESENTATIVE, CONTROLS, DATA_DIR, ALL_Z, ALL_B, make_variant)

# ==========================================
# 実行設定
# ==========================================
MODE = "test"            # "test" → "representative" → "controls" の順に進める
SEEDS = [0]              # まず 1 seed で確認 → 問題なければ list(range(10)) に広げる
NUM_CORES = 10
LOG_IN_FULL = False      # full モードで詳細ログ L1〜L8 も保存するか（容量: 1条件あたり数十MB）

# full モード用（従来の all.py と同じ）
base_params = [
    ("image", "+3+1-3-1+5+3", "imageデータ"), ("image", "+5+1-5-1+5+1", "imageデータ"),
    ("image", "+5+1-5-1+8+3", "imageデータ"), ("image", "+5+1-5-1+10+5", "imageデータ"),
    ("shunning", "+3-1-3+1+5-3", "shunningデータ"), ("shunning", "+5-1-5+1+5-1", "shunningデータ"),
    ("shunning", "+5-1-5+1+8-3", "shunningデータ"), ("shunning", "+5-1-5+1+10-5", "shunningデータ"),
    ("simple", "+3+1-3+1+5+3", "simpleデータ"), ("simple", "+5+1-5+1+5+1", "simpleデータ"),
    ("simple", "+5+1-5+1+8+3", "simpleデータ"), ("simple", "+5+1-5+1+10+5", "simpleデータ"),
    ("stern", "+3-1-3+1+5-3", "sternデータ"), ("stern", "+5-1-5+1+5-1", "sternデータ"),
    ("stern", "+5-1-5+1+8-3", "sternデータ"), ("stern", "+5-1-5+1+10-5", "sternデータ"),
]
omegas = [0.01]
zs = ALL_Z


def opts_to_args(opts):
    """variant 設定 dict → run_simulation.py のオプション引数"""
    a = []
    if opts.get("steps", 10000) != 10000: a += ["--steps", str(opts["steps"])]
    if opts.get("reset_rep", "none") != "none": a += ["--reset-rep", opts["reset_rep"]]
    if opts.get("stop", "legacy") != "legacy": a += ["--stop", opts["stop"]]
    if opts.get("rep_fix", False): a += ["--rep-fix"]
    return a


def build_tasks():
    tasks = []
    if MODE in ("representative", "controls", "test"):
        table = REPRESENTATIVE if MODE != "controls" else CONTROLS
        if MODE == "test":
            table = [r for r in REPRESENTATIVE if r[0] == "G13"]
        for grp, model, pat, Z, w, bs, opts in table:
            for seed in (SEEDS if MODE != "test" else SEEDS[:1]):
                o = dict(opts)
                if MODE == "test":
                    o["steps"] = 100
                args = [model, pat, DATA_DIR[model], str(w), str(Z), "--seed", str(seed),
                        "--bs", ",".join(str(b) for b in bs)] + opts_to_args(o)
                tasks.append(("run_simulation.py", args, grp))
    elif MODE == "full":
        for model, pat, date in base_params:
            for w in omegas:
                for z in zs:
                    for seed in SEEDS:
                        args = [model, pat, date, str(w), str(z), "--seed", str(seed),
                                "--bs", ",".join(str(b) for b in ALL_B)]
                        if not LOG_IN_FULL:
                            args.append("--no-log")
                        tasks.append(("run_simulation.py", args, "full"))
    else:
        raise ValueError(f"未知の MODE: {MODE}")
    return tasks


# ==========================================
# マルチプロセス間でログ書き込みを安全に行うためのLock初期化
# ==========================================
def init_worker(lock):
    global shared_lock
    shared_lock = lock


def log_path_for(script_dir, script_args):
    pattern_name = script_args[1].replace('+', 'p').replace('-', 'm')
    return os.path.join(script_dir, "log", f"sim_{script_args[0]}_{pattern_name}.log")


def run_script_to_log(task):
    script_path, script_args, grp = task
    abs_script_path = os.path.abspath(script_path)
    script_dir = os.path.dirname(abs_script_path)
    script_name = os.path.basename(abs_script_path)
    label = f"[{grp}] {script_args[0]} ({script_args[1]}) w={script_args[3]} z={script_args[4]} " + " ".join(script_args[5:])
    log_file_path = log_path_for(script_dir, script_args)

    print(f"🚀 [起動] {label}")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [sys.executable, "-u", script_name] + [str(arg) for arg in script_args]

    try:
        result = subprocess.run(cmd, cwd=script_dir, capture_output=True, text=True, encoding="utf-8", env=env)
        with shared_lock:
            with open(log_file_path, "a", encoding="utf-8") as f:
                f.write(f"\n{'=' * 60}\n▶ START: {label}\n{'=' * 60}\n")
                f.write(result.stdout)
                if result.stderr:
                    f.write("\n[STDERR - エラー出力]\n")
                    f.write(result.stderr)
                f.write(f"✅ END: {label} (Exit Code: {result.returncode})\n{'=' * 60}\n")
        if result.returncode == 0:
            print(f"✅ [完了] {label}")
            return {"task": task, "status": "SUCCESS"}
        print(f"❌ [失敗] {label}")
        return {"task": task, "status": "FAILED", "code": result.returncode}
    except Exception as e:
        with shared_lock:
            with open(log_file_path, "a", encoding="utf-8") as f:
                f.write(f"\n❌ 例外発生 ({label}): {str(e)}\n")
        return {"task": task, "status": "FAILED", "code": -1, "msg": str(e)}


if __name__ == "__main__":
    tasks_to_run = build_tasks()
    valid_tasks = [t for t in tasks_to_run if os.path.exists(t[0])]
    if not valid_tasks:
        print("❌ run_simulation.py が見つかりません（python/other で実行してください）")
        sys.exit(1)

    # 実行前に古いログファイルをクリア（初期化）する
    script_dir = os.path.dirname(os.path.abspath(valid_tasks[0][0]))
    os.makedirs(os.path.join(script_dir, "log"), exist_ok=True)
    for t in valid_tasks:
        p = log_path_for(script_dir, t[1])
        with open(p, "w", encoding="utf-8") as f:
            f.write(f"=== ログ: {t[1][0]} / {t[1][1]} / MODE={MODE} ===\n")

    num_cores = min(NUM_CORES, len(valid_tasks))
    print("=== 並列処理開始 ===")
    print(f"  ・MODE           : {MODE}")
    print(f"  ・SEEDS          : {SEEDS}")
    print(f"  ・並列プロセス数 : {num_cores}")
    print(f"  ・総タスク数     : {len(valid_tasks)} 件")
    print("====================")

    manager = multiprocessing.Manager()
    shared_lock = manager.Lock()
    pool = multiprocessing.Pool(processes=num_cores, initializer=init_worker, initargs=(shared_lock,))
    results = []
    try:
        results = pool.map_async(run_script_to_log, valid_tasks, chunksize=1).get()
    except KeyboardInterrupt:
        print("\n🛑 割り込みを検知しました。全プロセスを強制終了しています...")
        pool.terminate(); pool.join()
        sys.exit(1)
    else:
        pool.close(); pool.join()

    print("\n" + "=" * 70)
    print(" 📊 実行結果レポート")
    print("=" * 70)
    success = [r for r in results if r["status"] == "SUCCESS"]
    failed = [r for r in results if r["status"] == "FAILED"]
    print(f" 正常終了 : {len(success)} 件")
    print(f" エラー   : {len(failed)} 件")
    if failed:
        print("\n❌ エラーが発生したタスク:")
        for item in failed:
            print("  - " + " ".join(item['task'][1]))
