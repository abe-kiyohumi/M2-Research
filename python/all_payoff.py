# -*- coding: utf-8 -*-
"""
ペイオフグラフの一括作成(all_payoff.py と同じ構造)。
  4ルール × パターン(a〜d, a'〜d') × ωy を並列に実行し、最後に4ルール比較グラフも作ります。
  使い方:  python all_payoff.py
  (run_payoff.py を同じフォルダに置いてください)
  ペイオフCSVが無い組み合わせは自動でスキップされます。
"""
import os
import sys
import multiprocessing
import subprocess

# どのフォルダから実行しても run_payoff.py(このファイルと同じ場所)を使う
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from run_payoff import MODEL_INFO, PATTERNS, DATA_ROOT   # モデル名・パターン文字列の定義を共有

WORKER = os.path.join(SCRIPT_DIR, "run_payoff.py")
# 作るパターン(不要なものは消してください)
#   a〜d   = 通常スケール
#   a'〜d' = a〜d の値を 1/5 にしたもの(例: image の d' = +1+0.2-1-0.2+2+1)
LABELS = ["a", "b", "c", "d", "a'", "b'", "c'", "d'"]
MODELS = ["image", "shunning", "simple", "stern"]
omegas = [0.1, 0.01]
NUM_CORES = 10                                        # 並列プロセス数
MAKE_COMPARE = True                                   # 最後に4ルール比較グラフを作るか

# ---- タスク生成: (スクリプト, 引数リスト) ----
tasks_to_run = []
for label in LABELS:
    for model in MODELS:
        pat = PATTERNS[label][model]
        date_dir, graph_dir = MODEL_INFO[model]
        for w in omegas:
            tasks_to_run.append((WORKER, [model, pat, date_dir, graph_dir, str(w)]))
compare_tasks = []
if MAKE_COMPARE:
    for label in LABELS:
        for w in omegas:
            compare_tasks.append((WORKER, ["__compare__", label, str(w)]))

# ==========================================
# 並列実行 & ログ統合
# ==========================================
def init_worker(lock):
    global shared_lock
    shared_lock = lock

def run_script_to_log(task):
    script_path, script_args = task
    abs_script_path = os.path.abspath(script_path)
    script_dir = os.path.dirname(abs_script_path)
    script_name = os.path.basename(abs_script_path)

    if script_args[0] == "__compare__":
        type_name, pattern_raw, omega_val = "compare", script_args[1], script_args[2]
    else:
        type_name, pattern_raw, omega_val = script_args[0], script_args[1], script_args[4]
    pattern_name = pattern_raw.replace('+', 'p').replace('-', 'm').replace("'", "prime")

    log_dir = os.path.join(script_dir, "log_payoff")
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, f"payoff_{type_name}_{pattern_name}.log")

    print(f"🚀 [起動] ペイオフグラフ: {type_name} ({pattern_raw}) w={omega_val}")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [sys.executable, "-u", script_name] + [str(a) for a in script_args]
    try:
        result = subprocess.run(cmd, cwd=script_dir, capture_output=True, text=True,
                                encoding="utf-8", env=env)
        with shared_lock:
            with open(log_file_path, "a", encoding="utf-8") as f:
                f.write(f"\n{'=' * 60}\n▶ START: omega={omega_val}\n{'=' * 60}\n")
                f.write(result.stdout)
                if result.stderr:
                    f.write("\n[STDERR - エラー出力]\n" + result.stderr)
                f.write(f"✅ END: omega={omega_val} (Exit Code: {result.returncode})\n{'=' * 60}\n")
        if result.returncode == 0:
            print(f"✅ [完了] {type_name} ({pattern_raw}) w={omega_val}")
            return {"task": task, "status": "SUCCESS"}
        print(f"❌ [失敗] {type_name} ({pattern_raw}) w={omega_val}")
        return {"task": task, "status": "FAILED", "code": result.returncode}
    except Exception as e:
        with shared_lock:
            with open(log_file_path, "a", encoding="utf-8") as f:
                f.write(f"\n❌ 例外発生 (w={omega_val}): {e}\n")
        return {"task": task, "status": "FAILED", "code": -1, "msg": str(e)}

def run_pool(tasks, lock):
    pool = multiprocessing.Pool(processes=NUM_CORES, initializer=init_worker, initargs=(lock,))
    try:
        results = pool.map_async(run_script_to_log, tasks).get()
    except KeyboardInterrupt:
        print("\n🛑 割り込みを検知しました。全プロセスを強制終了しています...")
        pool.terminate(); pool.join(); sys.exit(1)
    pool.close(); pool.join()
    return results

if __name__ == "__main__":
    if not os.path.exists(WORKER):
        print(f"❌ '{WORKER}' が見つかりません(all_payoff.py と同じフォルダに置いてください)。")
        sys.exit(1)

    # 古いログを初期化(ワーカー側と同じ場所: このスクリプトのフォルダ/log_payoff)
    log_dir = os.path.join(SCRIPT_DIR, "log_payoff")
    os.makedirs(log_dir, exist_ok=True)
    for _, args in tasks_to_run + compare_tasks:
        raw = args[1]
        name = raw.replace('+', 'p').replace('-', 'm').replace("'", "prime")
        t = "compare" if args[0] == "__compare__" else args[0]
        with open(os.path.join(log_dir, f"payoff_{t}_{name}.log"), "w", encoding="utf-8") as f:
            f.write(f"=== ペイオフグラフ作成ログ: {t} / {raw} ===\n")

    print("=== 一括ペイオフグラフ作成 開始 ===")
    print(f"  ・m2フォルダ     : {DATA_ROOT}")
    print(f"  ・並列プロセス数 : {NUM_CORES}")
    print(f"  ・総タスク数     : {len(tasks_to_run)} 件 (+比較 {len(compare_tasks)} 件)")
    print("==========================")

    manager = multiprocessing.Manager()
    lock = manager.Lock()
    results = run_pool(tasks_to_run, lock)
    if compare_tasks:
        print("\n--- 4ルール比較グラフ ---")
        results += run_pool(compare_tasks, lock)

    print("\n" + "=" * 70 + "\n 📊 実行結果レポート\n" + "=" * 70)
    success = [r for r in results if r["status"] == "SUCCESS"]
    failed = [r for r in results if r["status"] == "FAILED"]
    print(f" 正常終了 : {len(success)} 件\n エラー   : {len(failed)} 件")
    print(" ※「正常終了」でもペイオフCSVが無い組み合わせはスキップされています(log_payoff を確認)")
    if failed:
        print("\n❌ エラーが発生したタスク:")
        for item in failed:
            print("  -", " / ".join(item['task'][1]))