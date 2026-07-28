import os
import multiprocessing
import subprocess
import sys

# 実行したいスクリプトのパス
scripts_to_run = [
    "../image_code/+3+1-3-1+5+3/glaph_single.py",
    "../image_code/+3+1-3-1+5+3/glaph_single_C.py",
    "../image_code/+3+1-3-1+5+3/glaph_single_CP.py",
    "../image_code/+3+1-3-1+5+3/glaph_punish.py",

    "../image_code/+5+1-5-1+5+1/glaph_single.py",
    "../image_code/+5+1-5-1+5+1/glaph_single_C.py",
    "../image_code/+5+1-5-1+5+1/glaph_single_CP.py",
    "../image_code/+5+1-5-1+5+1/glaph_punish.py",

    "../image_code/+5+1-5-1+8+3/glaph_single.py",
    "../image_code/+5+1-5-1+8+3/glaph_single_C.py",
    "../image_code/+5+1-5-1+8+3/glaph_single_CP.py",
    "../image_code/+5+1-5-1+8+3/glaph_punish.py",

    "../image_code/+5+1-5-1+10+5/glaph_single.py",
    "../image_code/+5+1-5-1+10+5/glaph_single_C.py",
    "../image_code/+5+1-5-1+10+5/glaph_single_CP.py",
    "../image_code/+5+1-5-1+10+5/glaph_punish.py",

    "../shunning_code/+3-1-3+1+5-3/glaph_single.py",
    "../shunning_code/+3-1-3+1+5-3/glaph_single_C.py",
    "../shunning_code/+3-1-3+1+5-3/glaph_single_CP.py",
    "../shunning_code/+3-1-3+1+5-3/glaph_punish.py",

    "../shunning_code/+5-1-5+1+5-1/glaph_single.py",
    "../shunning_code/+5-1-5+1+5-1/glaph_single_C.py",
    "../shunning_code/+5-1-5+1+5-1/glaph_single_CP.py",
    "../shunning_code/+5-1-5+1+5-1/glaph_punish.py",

    "../shunning_code/+5-1-5+1+8-3/glaph_single.py",
    "../shunning_code/+5-1-5+1+8-3/glaph_single_C.py",
    "../shunning_code/+5-1-5+1+8-3/glaph_single_CP.py",
    "../shunning_code/+5-1-5+1+8-3/glaph_punish.py",

    "../shunning_code/+5-1-5+1+10-5/glaph_single.py",
    "../shunning_code/+5-1-5+1+10-5/glaph_single_C.py",
    "../shunning_code/+5-1-5+1+10-5/glaph_single_CP.py",
    "../shunning_code/+5-1-5+1+10-5/glaph_punish.py",

    "../simple_code/+3+1-3+1+5+3/glaph_single.py",
    "../simple_code/+3+1-3+1+5+3/glaph_single_C.py",
    "../simple_code/+3+1-3+1+5+3/glaph_single_CP.py",
    "../simple_code/+3+1-3+1+5+3/glaph_punish.py",

    "../simple_code/+5+1-5+1+5+1/glaph_single.py",
    "../simple_code/+5+1-5+1+5+1/glaph_single_C.py",
    "../simple_code/+5+1-5+1+5+1/glaph_single_CP.py",
    "../simple_code/+5+1-5+1+5+1/glaph_punish.py",

    "../simple_code/+5+1-5+1+8+3/glaph_single.py",
    "../simple_code/+5+1-5+1+8+3/glaph_single_C.py",
    "../simple_code/+5+1-5+1+8+3/glaph_single_CP.py",
    "../simple_code/+5+1-5+1+8+3/glaph_punish.py",

    "../simple_code/+5+1-5+1+10+5/glaph_single.py",
    "../simple_code/+5+1-5+1+10+5/glaph_single_C.py",
    "../simple_code/+5+1-5+1+10+5/glaph_single_CP.py",
    "../simple_code/+5+1-5+1+10+5/glaph_punish.py",

    "../stern_code/+3-1-3+1+5-3/glaph_single.py",
    "../stern_code/+3-1-3+1+5-3/glaph_single_C.py",
    "../stern_code/+3-1-3+1+5-3/glaph_single_CP.py",
    "../stern_code/+3-1-3+1+5-3/glaph_punish.py",

    "../stern_code/+5-1-5+1+5-1/glaph_single.py",
    "../stern_code/+5-1-5+1+5-1/glaph_single_C.py",
    "../stern_code/+5-1-5+1+5-1/glaph_single_CP.py",
    "../stern_code/+5-1-5+1+5-1/glaph_punish.py",

    "../stern_code/+5-1-5+1+8-3/glaph_single.py",
    "../stern_code/+5-1-5+1+8-3/glaph_single_C.py",
    "../stern_code/+5-1-5+1+8-3/glaph_single_CP.py",
    "../stern_code/+5-1-5+1+8-3/glaph_punish.py",

    "../stern_code/+5-1-5+1+10-5/glaph_single.py",
    "../stern_code/+5-1-5+1+10-5/glaph_single_C.py",
    "../stern_code/+5-1-5+1+10-5/glaph_single_CP.py",
    "../stern_code/+5-1-5+1+10-5/glaph_punish.py"
]

def run_script_to_log(script_path):
    """個別のスクリプトを実行し、実行結果オブジェクト（dict）を返す"""
    abs_script_path = os.path.abspath(script_path)
    script_dir = os.path.dirname(abs_script_path)
    script_name = os.path.basename(abs_script_path)
    
    # 拡張子を除いたファイル名を取得 (例: "glaph_single.py" -> "glaph_single")
    script_stem = os.path.splitext(script_name)[0]
    
    if not os.path.isdir(script_dir):
        print(f"❌ フォルダが見つかりません: {script_dir}")
        return {"path": script_path, "status": "FAILED", "code": -1, "msg": "フォルダが存在しません", "log_path": None}
        
    # スクリプト名に合わせた個別のログファイルパスを作成 (例: "glaph_single.log")
    log_file_path = os.path.join(script_dir, f"{script_stem}.log")
    print(f"🚀 [起動] {script_path}")
    
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    python_executable = sys.executable 
    
    try:
        with open(log_file_path, "w", encoding="utf-8") as log_file:
            process = subprocess.Popen(
                [python_executable, "-u", script_name],
                cwd=script_dir,
                stdout=log_file,
                stderr=log_file,
                env=env
            )
            
            # プロセスの終了を待機
            process.wait()
            
            # 終了ステータスの判定
            if process.returncode == 0:
                print(f"✅ [完了] {script_path}")
                return {"path": script_path, "status": "SUCCESS", "code": 0, "msg": "正常終了", "log_path": log_file_path}
            else:
                print(f"❌ [失敗] {script_path} (Exit Code: {process.returncode})")
                return {"path": script_path, "status": "FAILED", "code": process.returncode, "msg": f"エラー終了 (コード: {process.returncode})", "log_path": log_file_path}
                
    except KeyboardInterrupt:
        print(f"🛑 [中断] {script_path}")
        raise KeyboardInterrupt
    except Exception as e:
        print(f"❌ [例外] {script_path}: {e}")
        return {"path": script_path, "status": "FAILED", "code": -1, "msg": str(e), "log_path": log_file_path}

if __name__ == "__main__":
    valid_scripts = []
    missing_scripts = []

    # 1. 存在するファイルと存在しないファイルを分類
    for s in scripts_to_run:
        if os.path.exists(s):
            valid_scripts.append(s)
        else:
            missing_scripts.append(s)

    num_cores = 10
    print(f"=== 処理開始 (並列数: {num_cores} / 対象ファイル: {len(valid_scripts)} 件) ===")

    results = []
    pool = multiprocessing.Pool(processes=num_cores)
    
    try:
        result_async = pool.map_async(run_script_to_log, valid_scripts)
        results = result_async.get()
    except KeyboardInterrupt:
        print("\n🛑 割り込みを検知しました。すべての実行ファイルを強制終了しています...")
        pool.terminate()
        pool.join()
        print("✅ 安全に停止しました。")
        sys.exit(1)
    else:
        pool.close()
        pool.join()

    # 2. 実行結果の集計・最終レポートの出力
    success_list = [r["path"] for r in results if r["status"] == "SUCCESS"]
    failed_list = [r for r in results if r["status"] == "FAILED"]

    print("\n" + "="*70)
    print(" 📊 最終実行結果レポート")
    print("="*70)
    print(f" 実行対象総数 : {len(scripts_to_run)} 件")
    print(f"  ・ 正常終了  : {len(success_list)} 件")
    print(f"  ・ 実行エラー: {len(failed_list)} 件")
    print(f"  ・ ファイル無: {len(missing_scripts)} 件")
    print("-" * 70)

    # ❌ 実行エラーになったファイル一覧
    if failed_list:
        print("\n❌【実行エラーが発生したファイル】")
        for item in failed_list:
            print(f"  - {item['path']} ({item['msg']})")
            if item.get("log_path"):
                print(f"    └ ログ確認場所: {item['log_path']}")

    # ⚠️ ファイルが存在せずスキップされた一覧
    if missing_scripts:
        print("\n⚠️【ファイルが存在しないためスキップされたパス】")
        for path in missing_scripts:
            print(f"  - {path}")

    # ✅ 正常終了したファイル一覧
    if success_list:
        print("\n✅【正常終了したファイル】")
        for path in success_list:
            print(f"  - {path}")

    print("\n" + "="*70)