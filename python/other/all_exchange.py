import os
import multiprocessing
import subprocess
import sys

# 実行したいモデルとパターンのリスト (元の all_exchange.py のパス情報から構築)
base_params = [
    # (モデル名, PATTERN, dateデータフォルダ, glaphグラフフォルダ, タイプ)
    ("image", "+3+1-3-1+5+3", "imageデータ"),
    ("image", "+5+1-5-1+5+1", "imageデータ"),
    ("image", "+5+1-5-1+8+3", "imageデータ"),
    ("image", "+5+1-5-1+10+5", "imageデータ"),
    
    ("shunning", "+3-1-3+1+5-3", "shunningデータ"),
    ("shunning", "+5-1-5+1+5-1", "shunningデータ"),
    ("shunning", "+5-1-5+1+8-3", "shunningデータ"),
    ("shunning", "+5-1-5+1+10-5", "shunningデータ"),
    
    ("simple", "+3+1-3+1+5+3", "simpleデータ"),
    ("simple", "+5+1-5+1+5+1", "simpleデータ"),
    ("simple", "+5+1-5+1+8+3", "simpleデータ"),
    ("simple", "+5+1-5+1+10+5", "simpleデータ"),
    
    ("stern", "+3-1-3+1+5-3", "sternデータ"),
    ("stern", "+5-1-5+1+5-1", "sternデータ"),
    ("stern", "+5-1-5+1+8-3", "sternデータ"),
    ("stern", "+5-1-5+1+10-5", "sternデータ"),

    # (モデル名, PATTERN, dateデータフォルダ, glaphグラフフォルダ)
    ("image", "+0.6+0.2-0.6-0.2+1+0.6", "imageデータ"),
    ("image", "+1+0.2-1-0.2+1+0.2", "imageデータ"),
    ("image", "+1+0.2-1-0.2+1.6+0.6", "imageデータ"),
    ("image", "+1+0.2-1-0.2+2+1", "imageデータ"),
    
    ("shunning", "+0.6-0.2-0.6+0.2+1-0.6", "shunningデータ"),
    ("shunning", "+1-0.2-1+0.2+1-0.2", "shunningデータ"),
    ("shunning", "+1-0.2-1+0.2+1.6-0.6", "shunningデータ"),
    ("shunning", "+1-0.2-1+0.2+2-1", "shunningデータ"),
    
    ("simple", "+0.6+0.2-0.6+0.2+1+0.6", "simpleデータ"),
    ("simple", "+1+0.2-1+0.2+1+0.2", "simpleデータ"),
    ("simple", "+1+0.2-1+0.2+1.6+0.6", "simpleデータ"),
    ("simple", "+1+0.2-1+0.2+2+1", "simpleデータ"),
    
    ("stern", "+0.6-0.2-0.6+0.2+1-0.6", "sternデータ"),
    ("stern", "+1-0.2-1+0.2+1-0.2", "sternデータ"),
    ("stern", "+1-0.2-1+0.2+1.6-0.6", "sternデータ"),
    ("stern", "+1-0.2-1+0.2+2-1", "sternデータ"), 
]

# ==========================================
# 実行設定
#   MODE = "legacy"         : 従来データ（seed なし）を base_params × omegas で処理
#   MODE = "representative" / "controls" : all.py と同じ条件セット（seed 付き）。
#       改修版 run_simulation.py の出力は埋め済みなので自動でスキップされる（旧形式のみ処理）
# ==========================================
from experiment_config import REPRESENTATIVE, CONTROLS, DATA_DIR, make_variant

MODE = "legacy"
SEEDS = [0]
omegas = [0.1, 0.01]

tasks_to_run = []
if MODE == "legacy":
    for model, pat, date in base_params:
        for w in omegas:
            tasks_to_run.append(("run_exchange_all.py", [model, pat, date, str(w)]))
else:
    table = REPRESENTATIVE if MODE == "representative" else CONTROLS
    for grp, model, pat, Z, w, bs, opts in table:
        variant = make_variant(opts.get("steps", 10000), opts.get("reset_rep", "none"),
                               opts.get("stop", "legacy"), opts.get("rep_fix", False))
        for seed in SEEDS:
            args = [model, pat, DATA_DIR[model], str(w), "--seed", str(seed), "--zs", str(Z)]
            if variant:
                args += ["--variant", variant]
            tasks_to_run.append(("run_exchange_all.py", args))

# ==========================================
# 並列実行 & ログ統合の仕組み
# ==========================================
def init_worker(lock):
    global shared_lock
    shared_lock = lock

def run_script_to_log(task):
    script_path, script_args = task
    abs_script_path = os.path.abspath(script_path)
    script_dir = os.path.dirname(abs_script_path)
    script_name = os.path.basename(abs_script_path)
    
    type_name = script_args[0]
    pattern_name = script_args[1].replace('+', 'p').replace('-', 'm')
    omega_val = script_args[3]
    
    # ログは「log_exchange」フォルダに出力し、typeとPATTERNでファイルをグループ化
    log_dir = os.path.join(script_dir, "log_exchange")
    os.makedirs(log_dir, exist_ok=True)
    log_filename = f"exchange_{type_name}_{pattern_name}.log"
    log_file_path = os.path.join(log_dir, log_filename)
    
    print(f"🚀 [起動] 置換処理: {type_name} ({script_args[1]}) w={omega_val}")
    
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    python_executable = sys.executable 
    
    cmd = [python_executable, "-u", script_name] + [str(arg) for arg in script_args]
    
    try:
        # 実行と出力のキャプチャ (文字化け対策 utf-8)
        result = subprocess.run(
            cmd,
            cwd=script_dir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env
        )
        
        # 排他制御でログファイルに追記
        with shared_lock:
            with open(log_file_path, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"▶ START: omega={omega_val}\n")
                f.write(f"{'='*60}\n")
                f.write(result.stdout)
                
                if result.stderr:
                    f.write("\n[STDERR - エラー出力]\n")
                    f.write(result.stderr)
                    
                f.write(f"✅ END: omega={omega_val} (Exit Code: {result.returncode})\n")
                f.write(f"{'='*60}\n")
        
        if result.returncode == 0:
            print(f"✅ [完了] {type_name} ({script_args[1]}) w={omega_val}")
            return {"task": task, "status": "SUCCESS"}
        else:
            print(f"❌ [失敗] {type_name} ({script_args[1]}) w={omega_val}")
            return {"task": task, "status": "FAILED", "code": result.returncode}
            
    except Exception as e:
        with shared_lock:
            with open(log_file_path, "a", encoding="utf-8") as f:
                f.write(f"\n❌ 例外発生 (w={omega_val}): {str(e)}\n")
        return {"task": task, "status": "FAILED", "code": -1, "msg": str(e)}

if __name__ == "__main__":
    if not os.path.exists("run_exchange_all.py"):
        print("❌ 'run_exchange_all.py' が同じディレクトリに見つかりません。")
        sys.exit(1)

    # 実行前に古い置換ログファイルを初期化
    log_dir = os.path.join(os.getcwd(), "log_exchange")
    os.makedirs(log_dir, exist_ok=True)
    for model, pat, _ in base_params:
        pattern_name = pat.replace('+', 'p').replace('-', 'm')
        log_filename = f"exchange_{model}_{pattern_name}.log"
        log_file_path = os.path.join(log_dir, log_filename)
        with open(log_file_path, "w", encoding="utf-8") as f:
            f.write(f"=== 置換ログ: {model} / {pat} ===\n")
    
    num_cores = 10  # 並列プロセス数
    print(f"=== 一括置換処理 開始 ===")
    print(f"  ・並列プロセス数 : {num_cores}")
    print(f"  ・総タスク数     : {len(tasks_to_run)} 件")
    print(f"=========================")

    manager = multiprocessing.Manager()
    shared_lock = manager.Lock()
    pool = multiprocessing.Pool(processes=num_cores, initializer=init_worker, initargs=(shared_lock,))
    results = []
    
    try:
        result_async = pool.map_async(run_script_to_log, tasks_to_run)
        results = result_async.get()
    except KeyboardInterrupt:
        print("\n🛑 割り込みを検知しました。全プロセスを強制終了しています...")
        pool.terminate()
        pool.join()
        sys.exit(1)
    else:
        pool.close()
        pool.join()

    # レポート表示
    print("\n" + "="*70)
    print(" 📊 実行結果レポート")
    print("="*70)
    success = [r for r in results if r["status"] == "SUCCESS"]
    failed = [r for r in results if r["status"] == "FAILED"]
    
    print(f" 正常終了 : {len(success)} 件")
    print(f" エラー   : {len(failed)} 件")
    
    if failed:
        print("\n❌ エラーが発生したタスク:")
        for item in failed:
            print("  - " + " ".join(item['task'][1]))