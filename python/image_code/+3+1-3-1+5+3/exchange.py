import zipfile
import pandas as pd
import io
import os
import sys

# 引数の受け取り (第1引数: omega, 第2引数: カンマ区切りZリスト)
if len(sys.argv) > 1:
    omega = float(sys.argv[1])
else:
    omega = 0.1

if len(sys.argv) > 2:
    target_z_list = [int(z) for z in sys.argv[2].split(',')]
else:
    target_z_list = [50, 60, 70, 80, 90, 95, 98]

print(f"🔧 設定 -> omega: {omega}, 対象Z: {target_z_list}")

PATTERN = "+0.6+0.2-0.6-0.2+1+0.6"
datePATTERN = "imageデータ"
glaphPATTERN = "imageグラフ"
modelPATTERN = "image"

def file_select(Z):
    INPUT_DIR  = f"../../../{glaphPATTERN}/Z_change_協力率変遷/{PATTERN}"
    bs = ['0','0.2','0.4','0.6','0.8','1.0']

    ZIP_FILE   = f"../../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/{modelPATTERN}_Z={Z}_r=3.0_{PATTERN}_omega={omega}.zip"
    OUTPUT_DIR = ZIP_FILE + '.temp'
    file_names = [f'{modelPATTERN}_Z={Z}_b={b}_r=3.0_{PATTERN}_omega={omega}.csv' for b in bs]

    return OUTPUT_DIR, INPUT_DIR, ZIP_FILE, file_names

for Z in target_z_list:
    OUTPUT_DIR, INPUT_DIR, ZIP_FILE, file_names = file_select(Z)
    print(f"\n--- Z={Z} の処理を開始します ---")
    
    if not os.path.exists(ZIP_FILE):
        print(f"⚠️ スキップ: ZIPファイルが存在しません -> {ZIP_FILE}")
        continue

    try:
        with zipfile.ZipFile(ZIP_FILE, 'r') as zf_in:
            with zipfile.ZipFile(OUTPUT_DIR, 'w', zipfile.ZIP_DEFLATED) as zf_out:
                for file_info in zf_in.infolist():
                    file_name = file_info.filename
                    if file_name.endswith('.csv'):
                        with zf_in.open(file_name) as f:
                            df = pd.read_csv(f)
                            df_none = df.replace(0, None)
                            df = df_none.ffill().fillna(0)

                            csv_buf = io.StringIO()
                            df.to_csv(csv_buf, index=False)
                            zf_out.writestr(file_name, csv_buf.getvalue())
                    else:
                        zf_out.writestr(file_name, zf_in.read(file_name))

        os.remove(ZIP_FILE)
        os.rename(OUTPUT_DIR, ZIP_FILE)
        print(f"✅ 置換後のZIPファイルを {ZIP_FILE} として保存しました。")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")