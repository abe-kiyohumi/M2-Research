import os
import multiprocessing
import subprocess
import sys

# 実行したいモデルとパターンのリスト (exchange_all.pyと同様の構造)
base_params = [
    # (モデル名, PATTERN, dateデータフォルダ, glaphグラフフォルダ, タイプ)
    ("image", "+3+1-3-1+5+3", "imageデータ", "imageグラフ","穏健型"),
    ("image", "+5+1-5-1+5+1", "imageデータ", "imageグラフ","均衡型"),
    ("image", "+5+1-5-1+8+3", "imageデータ", "imageグラフ","罰者優遇型"),
    ("image", "+5+1-5-1+10+5", "imageデータ", "imageグラフ","罰者強優遇型"),
    
    ("shunning", "+3-1-3+1+5-3", "shunningデータ", "shunningグラフ","穏健型"),
    ("shunning", "+5-1-5+1+5-1", "shunningデータ", "shunningグラフ","均衡型"),
    ("shunning", "+5-1-5+1+8-3", "shunningデータ", "shunningグラフ","罰者優遇型"),
    ("shunning", "+5-1-5+1+10-5", "shunningデータ", "shunningグラフ","罰者強優遇型"),
    
    ("simple", "+3+1-3+1+5+3", "simpleデータ", "simpleグラフ","穏健型"),
    ("simple", "+5+1-5+1+5+1", "simpleデータ", "simpleグラフ","均衡型"),
    ("simple", "+5+1-5+1+8+3", "simpleデータ", "simpleグラフ","罰者優遇型"),
    ("simple", "+5+1-5+1+10+5", "simpleデータ", "simpleグラフ","罰者強優遇型"),
    
    ("stern", "+3-1-3+1+5-3", "sternデータ", "sternグラフ","穏健型"),
    ("stern", "+5-1-5+1+5-1", "sternデータ", "sternグラフ","均衡型"),
    ("stern", "+5-1-5+1+8-3", "sternデータ", "sternグラフ","罰者優遇型"),
    ("stern", "+5-1-5+1+10-5", "sternデータ", "sternグラフ","罰者強優遇型"),

    # (モデル名, PATTERN, dateデータフォルダ, glaphグラフフォルダ)
    ("image", "+0.6+0.2-0.6-0.2+1+0.6", "imageデータ", "imageグラフ","穏健型・弱"),
    ("image", "+1+0.2-1-0.2+1+0.2", "imageデータ", "imageグラフ","均衡型・弱"),
    ("image", "+1+0.2-1-0.2+1.6+0.6", "imageデータ", "imageグラフ","罰者優遇型・弱"),
    ("image", "+1+0.2-1-0.2+2+1", "imageデータ", "imageグラフ","罰者強優遇型・弱"),
    
    ("shunning", "+0.6-0.2-0.6+0.2+1-0.6", "shunningデータ", "shunningグラフ","穏健型・弱"),
    ("shunning", "+1-0.2-1+0.2+1-0.2", "shunningデータ", "shunningグラフ","均衡型・弱"),
    ("shunning", "+1-0.2-1+0.2+1.6-0.6", "shunningデータ", "shunningグラフ","罰者優遇型・弱"),
    ("shunning", "+1-0.2-1+0.2+2-1", "shunningデータ", "shunningグラフ","罰者強優遇型・弱"),
    
    ("simple", "+0.6+0.2-0.6+0.2+1+0.6", "simpleデータ", "simpleグラフ","穏健型・弱"),
    ("simple", "+1+0.2-1+0.2+1+0.2", "simpleデータ", "simpleグラフ","均衡型・弱"),
    ("simple", "+1+0.2-1+0.2+1.6+0.6", "simpleデータ", "simpleグラフ","罰者優遇型・弱"),
    ("simple", "+1+0.2-1+0.2+2+1", "simpleデータ", "simpleグラフ","罰者強優遇型・弱"),
    
    ("stern", "+0.6-0.2-0.6+0.2+1-0.6", "sternデータ", "sternグラフ","穏健型・弱"),
    ("stern", "+1-0.2-1+0.2+1-0.2", "sternデータ", "sternグラフ","均衡型・弱"),
    ("stern", "+1-0.2-1+0.2+1.6-0.6", "sternデータ", "sternグラフ","罰者優遇型・弱"),
    ("stern", "+1-0.2-1+0.2+2-1", "sternデータ", "sternグラフ","罰者強優遇型・弱"), 
]

# ==========================================
# 実行設定
#   MODE = "legacy"         : 従来データ（seed なし）を base_params × omegas で描画（詳細ログがあればそれも）
#   MODE = "representative" / "controls" : all.py と同じ条件セット。seed 平均の詳細ロググラフ + 要約指標
#   MODE = "test"           : all.py の MODE="test"（G13・100MCS）の結果を描画
# ==========================================
import glob
import pandas as pd
from experiment_config import REPRESENTATIVE, CONTROLS, DATA_DIR, GRAPH_DIR, TYPE_NAME, make_variant

MODE = "test"            # all.py と同じ MODE にそろえる（"test" → "representative" → "controls"）
SEEDS = [0]              # 複数 seed を一括で読み込み、平均と 10–90% 帯を描く
omegas = [0.1, 0.01]

tasks_to_run = []
if MODE == "legacy":
    for model, pat, date_dir, graph_dir, type_name in base_params:
        for w in omegas:
            tasks_to_run.append(("run_glaph_all.py", [model, pat, date_dir, graph_dir, str(w), type_name]))
else:
    table = {"representative": REPRESENTATIVE, "controls": CONTROLS,
             "test": [r[:6] + ({"steps": 100},) for r in REPRESENTATIVE if r[0] == "G13"]}[MODE]
    for grp, model, pat, Z, w, bs, opts in table:
        variant = make_variant(opts.get("steps", 10000), opts.get("reset_rep", "none"),
                               opts.get("stop", "legacy"), opts.get("rep_fix", False))
        args = [model, pat, DATA_DIR[model], GRAPH_DIR[model], str(w), TYPE_NAME[(model, pat)],
                "--seeds", ",".join(map(str, SEEDS)), "--zs", str(Z), "--group", grp]
        if variant:
            args += ["--variant", variant]
        tasks_to_run.append(("run_glaph_all.py", args))

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
    
    type_name = script_args[5]
    pattern_name = script_args[1].replace('+', 'p').replace('-', 'm')
    omega_val = script_args[4]
    
    # ログは「log_glaph」フォルダに出力
    log_dir = os.path.join(script_dir, "log_glaph")
    os.makedirs(log_dir, exist_ok=True)
    log_filename = f"glaph_{script_args[0]}_{pattern_name}_{type_name}.log"
    log_file_path = os.path.join(log_dir, log_filename)
    
    print(f"🚀 [起動] グラフ作成: {type_name} ({script_args[1]}) w={omega_val}")
    
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    python_executable = sys.executable 
    
    cmd = [python_executable, "-u", script_name] + [str(arg) for arg in script_args]
    
    try:
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
    if not os.path.exists("run_glaph_all.py"):
        print("❌ 'run_glaph_all.py' が同じディレクトリに見つかりません。")
        sys.exit(1)

    # 実行前に古いログファイルを初期化
    log_dir = os.path.join(os.getcwd(), "log_glaph")
    os.makedirs(log_dir, exist_ok=True)
    for model, pat, _, _, type_name in base_params:
        pattern_name = pat.replace('+', 'p').replace('-', 'm')
        log_filename = f"glaph_{model}_{pattern_name}_{type_name}.log"
        log_file_path = os.path.join(log_dir, log_filename)
        with open(log_file_path, "w", encoding="utf-8") as f:
            f.write(f"=== グラフ作成ログ: {model} / {pat} / {type_name} ===\n")
    
    num_cores = 10  # 並列プロセス数
    print(f"=== 一括グラフ作成 開始 ===")
    print(f"  ・並列プロセス数 : {num_cores}")
    print(f"  ・総タスク数     : {len(tasks_to_run)} 件")
    print(f"==========================")

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

    # 要約指標を1つの CSV に統合（../../summary_all{_MODE}.csv）
    files = glob.glob(os.path.join("..", "..", "*グラフ", "Z_change_協力率変遷*", "*", "Logs", "summary_*.csv"))
    if files:
        df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
        out = os.path.join("..", "..", "summary_all.csv")
        df.to_csv(out, index=False, encoding="utf-8-sig")
        print(f"\n📄 要約指標を統合: {out}（{len(df)} 行, {len(files)} ファイル）")