import zipfile
import pandas as pd
import io
import os
import sys

pd.set_option('future.no_silent_downcasting', True)

# ==========================================
# 1. 親プログラム (all_exchange.py) から引数を受け取る
# ==========================================
if len(sys.argv) > 4:
    modelPATTERN = sys.argv[1]
    PATTERN = sys.argv[2]
    datePATTERN = sys.argv[3]
    omega = float(sys.argv[4])
else:
    # デフォルト値（直接実行したときのテスト用）
    modelPATTERN = "shunning"
    PATTERN = "+0.6-0.2-0.6+0.2+1-0.6"
    datePATTERN = "shunningデータ"
    omega = 0.1

print(f"🔧 [設定] model: {modelPATTERN} | pattern: {PATTERN} | date: {datePATTERN} | omega: {omega}")

# ==========================================
# 2. Base, C, PC の処理をまとめた共通関数
# ==========================================
def process_zip(Z, target_type):
    """
    target_type: "" (Base), "C", または "PC" を受け取る
    """
    # フォルダパスとファイル名のプレフィックスを target_type に応じて切り替え
    if target_type == "":
        sub_dir = ""
        prefix = f"{modelPATTERN}"
    else:
        sub_dir = f"/{target_type}"
        prefix = f"{modelPATTERN}_{target_type}"

    # ZIPファイルのパス構築[cite: 1, 2, 3]
    ZIP_FILE = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}{sub_dir}/{prefix}_Z={Z}_r=3.0_{PATTERN}_omega={omega}.zip"
    OUTPUT_DIR = ZIP_FILE + '.temp'

    if not os.path.exists(ZIP_FILE):
        print(f"⚠️ スキップ: ファイルが存在しません -> {ZIP_FILE}")
        return

    print(f"🔄 処理中: Z={Z}, タイプ={target_type if target_type else 'Base'}")
    
    with zipfile.ZipFile(ZIP_FILE, 'r') as zf_in:
        with zipfile.ZipFile(OUTPUT_DIR, 'w', zipfile.ZIP_DEFLATED) as zf_out:
            for file_info in zf_in.infolist():
                file_name = file_info.filename
                
                # CSVファイルだけを処理[cite: 1]
                if file_name.endswith('.csv'):
                    with zf_in.open(file_name) as f:
                        df = pd.read_csv(f)
                        
                        # --- 置換処理 ---
                        df_none = df.replace(0, None) # 0をNoneに[cite: 1]
                        df = df_none.ffill()          # 前方補完[cite: 1]
                        df = df.fillna(0)             # 残ったNoneを0に[cite: 1]
                        
                        csv_buf = io.StringIO()
                        df.to_csv(csv_buf, index=False)
                        zf_out.writestr(file_name, csv_buf.getvalue())
                else:
                    # CSV以外はそのままコピー[cite: 1]
                    zf_out.writestr(file_name, zf_in.read(file_name))

    # 元ファイルを削除し、新しいファイルに置き換え[cite: 1]
    try:
        os.remove(ZIP_FILE)
        os.rename(OUTPUT_DIR, ZIP_FILE)
        print(f"✅ 保存完了: {ZIP_FILE}")
    except Exception as e:
        print(f"❌ エラー発生 ({ZIP_FILE}): {e}")

# ==========================================
# 3. 実行ループ (Z=50~98 と Base,C,PC を全網羅)
# ==========================================
if __name__ == "__main__":
    zs = [50, 60, 70, 80, 90, 95, 98]
    types = ["", "C", "PC"]
    
    for Z in zs:
        for t in types:
            process_zip(Z, t)
            
    print(f"\n🎉 {modelPATTERN} / {PATTERN} / omega={omega} の全置換処理が完了しました！")