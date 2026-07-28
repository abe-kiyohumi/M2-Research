import os
import multiprocessing
import subprocess
import sys

# 実行したいスクリプトのパス
scripts_to_run = [
    "../image_code/+3+1-3-1+5+3/Z_b_reputation_image_punish_ninzu.py",
    "../image_code/+5+1-5-1+5+1/Z_b_reputation_image_punish_ninzu.py",
    "../image_code/+5+1-5-1+8+3/Z_b_reputation_image_punish_ninzu.py"
]

def run_script_realtime(script_path):
    abs_script_path = os.path.abspath(script_path)
    script_dir = os.path.dirname(abs_script_path)
    script_name = os.path.basename(abs_script_path)
    
    if not os.path.isdir(script_dir):
        print(f"❌ フォルダが見つかりません: {script_dir}")
        return
        
    print(f"🚀 [起動] {script_name} (in {script_dir})")
    
    # 文字コードエラー対策
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    python_executable = sys.executable 
    
    # サブプロセスの起動
    process = subprocess.Popen(
        [python_executable, "-u", script_name],
        cwd=script_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
        encoding="utf-8"
    )
    
    try:
        for line in iter(process.stdout.readline, ''):
            sys.stdout.write(f"[{script_name}] {line}")
            sys.stdout.flush()
    except KeyboardInterrupt:
        # 途中でCtrl+Cを押された場合、確実にこの子プロセスもキルする
        process.terminate()
        process.wait()
        raise KeyboardInterrupt # 親プロセスの例外処理へ引き渡す
        
    process.stdout.close()
    process.wait()
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
    
    # キーボード中断時にプロセスプール全体を一括キルする仕組み
    pool = multiprocessing.Pool(processes=num_cores)
    try:
        # map_async を使うことで、メインスレッドがキーボード割り込み(Ctrl+C)を検知できるようにする
        result = pool.map_async(run_script_realtime, valid_scripts)
        # 実行完了を待つ (タイムアウトなしで待機)
        result.get()
    except KeyboardInterrupt:
        print("\n🛑 割り込みを検知しました。すべての実行ファイルを強制終了しています...")
        pool.terminate() # 動いているタスクを即座に破棄
        pool.join()      # プロセスの後片付け
        print("✅ すべての処理を安全に終了しました。")
        sys.exit(1)
    else:
        pool.close()
        pool.join()