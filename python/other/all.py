import os
import multiprocessing
import subprocess
import sys

# ベースとなるパラメータ設定 (モデル, PATTERN, データフォルダ)
base_params = [
    # Image Score
    ("image", "+3+1-3-1+5+3", "imageデータ"),
    ("image", "+5+1-5-1+5+1", "imageデータ"),
    ("image", "+5+1-5-1+8+3", "imageデータ"),
    ("image", "+5+1-5-1+10+5", "imageデータ"),
    
    # Shunning
    ("shunning", "+3-1-3+1+5-3", "shunningデータ"),
    ("shunning", "+5-1-5+1+5-1", "shunningデータ"),
    ("shunning", "+5-1-5+1+8-3", "shunningデータ"),
    ("shunning", "+5-1-5+1+10-5", "shunningデータ"),
    
    # Simple Standing
    ("simple", "+3+1-3+1+5+3", "simpleデータ"),
    ("simple", "+5+1-5+1+5+1", "simpleデータ"),
    ("simple", "+5+1-5+1+8+3", "simpleデータ"),
    ("simple", "+5+1-5+1+10+5", "simpleデータ"),
    
    # Stern Judging
    ("stern", "+3-1-3+1+5-3", "sternデータ"),
    ("stern", "+5-1-5+1+5-1", "sternデータ"),
    ("stern", "+5-1-5+1+8-3", "sternデータ"),
    ("stern", "+5-1-5+1+10-5", "sternデータ"),
]

omegas = [0.1]
zs = [50, 60, 70, 80, 90, 95, 98]

# 全組み合わせのタスクを生成
tasks_to_run = []
for model, pat, date in base_params:
    for w in omegas:
        for z in zs:
            tasks_to_run.append(("run_simulation.py", [model, pat, date, str(w), str(z)]))

# ==========================================
# マルチプロセス間でログ書き込みを安全に行うためのLock初期化
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
    z_val = script_args[4]
    
    # ログファイル名は type と PATTERN だけでグループ化
    log_dir = os.path.join(script_dir, "log")
    log_filename = f"sim_{type_name}_{pattern_name}.log"
    log_file_path = os.path.join(log_dir, log_filename)
    
    print(f"🚀 [起動] {type_name} ({script_args[1]}) w={omega_val} z={z_val}")
    
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    python_executable = sys.executable 
    
    cmd = [python_executable, "-u", script_name] + [str(arg) for arg in script_args]
    
    try:
        # subprocess.run で出力を直接ファイルに書かず、一旦キャプチャする
        result = subprocess.run(
            cmd,
            cwd=script_dir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env
        )
        
        # Lockを使って安全に追記(aモード)する
        with shared_lock:
            with open(log_file_path, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"▶ START: omega={omega_val}, Z={z_val}\n")
                f.write(f"{'='*60}\n")
                f.write(result.stdout)
                
                if result.stderr:
                    f.write("\n[STDERR - エラー出力]\n")
                    f.write(result.stderr)
                    
                f.write(f"✅ END: omega={omega_val}, Z={z_val} (Exit Code: {result.returncode})\n")
                f.write(f"{'='*60}\n")
        
        if result.returncode == 0:
            print(f"✅ [完了] {type_name} ({script_args[1]}) w={omega_val} z={z_val}")
            return {"task": task, "status": "SUCCESS"}
        else:
            print(f"❌ [失敗] {type_name} ({script_args[1]}) w={omega_val} z={z_val}")
            return {"task": task, "status": "FAILED", "code": result.returncode}
            
    except Exception as e:
        with shared_lock:
            with open(log_file_path, "a", encoding="utf-8") as f:
                f.write(f"\n❌ 例外発生 (w={omega_val}, Z={z_val}): {str(e)}\n")
        return {"task": task, "status": "FAILED", "code": -1, "msg": str(e)}

if __name__ == "__main__":
    valid_tasks = [t for t in tasks_to_run if os.path.exists(t[0])]
    
    # 実行前に古いログファイルをクリア（初期化）する
    if valid_tasks:
        script_dir = os.path.dirname(os.path.abspath(valid_tasks[0][0]))
        log_dir = os.path.join(script_dir, "log")
        os.makedirs(log_dir, exist_ok=True)
        
        for model, pat, _ in base_params:
            pattern_name = pat.replace('+', 'p').replace('-', 'm')
            log_filename = f"sim_{model}_{pattern_name}.log"
            log_file_path = os.path.join(log_dir, log_filename)
            # 新規作成(wモード)して閉じることで空にする
            with open(log_file_path, "w", encoding="utf-8") as f:
                f.write(f"=== ログ: {model} / {pat} ===\n")
    
    num_cores = 10
    print(f"=== 並列処理開始 ===")
    print(f"  ・並列プロセス数 : {num_cores}")
    print(f"  ・総タスク数     : {len(valid_tasks)} 件")
    print(f"====================")

    manager = multiprocessing.Manager()
    shared_lock = manager.Lock()
    pool = multiprocessing.Pool(processes=num_cores, initializer=init_worker, initargs=(shared_lock,))
    results = []
    
    try:
        result_async = pool.map_async(run_script_to_log, valid_tasks)
        results = result_async.get()
    except KeyboardInterrupt:
        print("\n🛑 割り込みを検知しました。全プロセスを強制終了しています...")
        pool.terminate()
        pool.join()
        sys.exit(1)
    else:
        pool.close()
        pool.join()

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
            args = item['task'][1]
            print(f"  - {args[0]} / {args[1]} / w={args[3]} / z={args[4]}")