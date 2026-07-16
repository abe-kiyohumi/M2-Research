import os
import multiprocessing
import subprocess
import sys

# 実行したいスクリプトのパス
scripts_to_run = [
    "../image_code/+3+1-3-1+5+3/Z_b_reputation_image_punish_ninzu.py",
    "../image_code/+5+1-5-1+5+1/Z_b_reputation_image_punish_ninzu.py"
]

def run_script_to_log(script_path):
    abs_script_path = os.path.abspath(script_path)
    script_dir = os.path.dirname(abs_script_path)
    script_name = os.path.basename(abs_script_path)
    
    if not os.path.isdir(script_dir):
        print(f"❌ フォルダが見つかりません: {script_dir}")
        return
        
    # ログファイルの出力先パス
    log_file_path = os.path.join(script_dir, "simulation_run.log")
    print(f"🚀 [起動] {script_name} -> ログ: {log_file_path}")
    
    # 文字コードエラー対策
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    python_executable = sys.executable 
    
    # ログファイルを書き込みモードで開く
    with open(log_file_path, "w", encoding="utf-8") as log_file:
        # サブプロセスの起動 (標準出力・エラーをすべてログファイルへリダイレクト)
        process = subprocess.Popen(
            [python_executable, "-u", script_name],
            cwd=script_dir,
            stdout=log_file,
            stderr=log_file,
            env=env
        )
        
        try:
            # プロセスの終了を待機
            process.wait()
        except KeyboardInterrupt:
            # 途中でCtrl+Cを押された場合、確実に子プロセスをキルしてログに記録
            log_file.write("\n🛑 KeyboardInterrupt: ユーザーによって強制終了されました。\n")
            process.terminate()
            process.wait()
            raise KeyboardInterrupt
            
    print(f"✅ [完了] {script_name}")

if __name__ == "__main__":
    valid_scripts = []
    for s in scripts_to_run:
        if os.path.exists(s):
            valid_scripts.append(s)
        else:
            print(f"⚠️ ファイルが見つからないためスキップします: {s}")

    if not valid_scripts:
        print("❌ 実行可能なスクリプトがありません。パスを確認してください。")
        sys.exit(1)

    num_cores = min(multiprocessing.cpu_count() - 2, len(valid_scripts))
    num_cores = max(1, num_cores)
    
    print(f"並列実行プロセス数: {num_cores}")
    
    # キーボード中断時に一括キルする仕組み
    pool = multiprocessing.Pool(processes=num_cores)
    try:
        # map_asyncで非同期に実行
        result = pool.map_async(run_script_to_log, valid_scripts)
        # 実行完了を待つ (タイムアウトなしで待機)
        result.get()
    except KeyboardInterrupt:
        print("\n🛑 割り込みを検知しました。すべての実行ファイルを強制終了しています...")
        pool.terminate()
        pool.join()
        print("✅ すべての処理を安全に終了しました。")
        sys.exit(1)
    else:
        pool.close()
        pool.join()