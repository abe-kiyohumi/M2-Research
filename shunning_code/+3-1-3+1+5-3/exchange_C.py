import zipfile
import pandas as pd
import io
import os

PATTERN = "+3-1-3+1+5-3"
datePATTERN = "shunningデータ"
glaphPATTERN = "shunningグラフ"
modelPATTERN = "shunning"

def file_select(Z):
    INPUT_DIR  = f"../../{glaphPATTERN}/Z_change_協力率変遷/{PATTERN}/C"

    bs = ['0','0.2','0.4','0.6','0.8','1.0']

    if Z == 50:
        print("Z=50を選択しました。")
        ZIP_FILE   = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/C/{modelPATTERN}_C_Z=50_r=3.0_{PATTERN}_omega=0.1.zip"
        OUTPUT_DIR = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/C/{modelPATTERN}_C_Z=50_r=3.0_{PATTERN}_omega=0.1.zip" + '.temp'
        file_names = [f'{modelPATTERN}_C_Z=50_b={b}_r=3.0_{PATTERN}_omega=0.1.csv' for b in bs]

    elif Z == 60:
        print("Z=60を選択しました。")
        ZIP_FILE   = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/C/{modelPATTERN}_C_Z=60_r=3.0_{PATTERN}_omega=0.1.zip"
        OUTPUT_DIR = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/C/{modelPATTERN}_C_Z=60_r=3.0_{PATTERN}_omega=0.1.zip" + '.temp'
        file_names = [f'{modelPATTERN}_C_Z=60_b={b}_r=3.0_{PATTERN}_omega=0.1.csv' for b in bs]

    elif Z == 70:
        print("Z=70を選択しました。")
        ZIP_FILE   = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/C/{modelPATTERN}_C_Z=70_r=3.0_{PATTERN}_omega=0.1.zip"
        OUTPUT_DIR = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/C/{modelPATTERN}_C_Z=70_r=3.0_{PATTERN}_omega=0.1.zip" + '.temp'
        file_names = [f'{modelPATTERN}_C_Z=70_b={b}_r=3.0_{PATTERN}_omega=0.1.csv' for b in bs]

    elif Z == 80:
        print("Z=80を選択しました。")
        ZIP_FILE   = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/C/{modelPATTERN}_C_Z=80_r=3.0_{PATTERN}_omega=0.1.zip"
        OUTPUT_DIR = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/C/{modelPATTERN}_C_Z=80_r=3.0_{PATTERN}_omega=0.1.zip" + '.temp'
        file_names = [f'{modelPATTERN}_C_Z=80_b={b}_r=3.0_{PATTERN}_omega=0.1.csv' for b in bs]

    elif Z == 90:
        print("Z=90を選択しました。")
        ZIP_FILE   = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/C/{modelPATTERN}_C_Z=90_r=3.0_{PATTERN}_omega=0.1.zip"
        OUTPUT_DIR = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/C/{modelPATTERN}_C_Z=90_r=3.0_{PATTERN}_omega=0.1.zip" + '.temp'
        file_names = [f'{modelPATTERN}_C_Z=90_b={b}_r=3.0_{PATTERN}_omega=0.1.csv' for b in bs]

    elif Z == 95:
        print("Z=95を選択しました。")
        ZIP_FILE   = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/C/{modelPATTERN}_C_Z=95_r=3.0_{PATTERN}_omega=0.1.zip"
        OUTPUT_DIR = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/C/{modelPATTERN}_C_Z=95_r=3.0_{PATTERN}_omega=0.1.zip" + '.temp'
        file_names = [f'{modelPATTERN}_C_Z=95_b={b}_r=3.0_{PATTERN}_omega=0.1.csv' for b in bs]

    elif Z == 98:
        print("Z=98を選択しました。")
        ZIP_FILE   = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/C/{modelPATTERN}_C_Z=98_r=3.0_{PATTERN}_omega=0.1.zip"
        OUTPUT_DIR = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/C/{modelPATTERN}_C_Z=98_r=3.0_{PATTERN}_omega=0.1.zip" + '.temp'
        file_names = [f'{modelPATTERN}_C_Z=98_b={b}_r=3.0_{PATTERN}_omega=0.1.csv' for b in bs]

    return OUTPUT_DIR, INPUT_DIR, ZIP_FILE, file_names
for Z in [50, 60, 70, 80, 90, 95, 98]:
    OUTPUT_DIR, INPUT_DIR, ZIP_FILE, file_names = file_select(Z)
    print(f"\n--- Z={Z} の処理を開始します ---")
    # 1. ZIPファイルを読み込む
    with zipfile.ZipFile(ZIP_FILE, 'r') as zf_in:
        # 2. 新しいZIPファイルを作成
        with zipfile.ZipFile(OUTPUT_DIR, 'w', zipfile.ZIP_DEFLATED) as zf_out:
            
            # ZIP内の全ファイルをループ
            for file_info in zf_in.infolist():
                file_name = file_info.filename
                print(f"Processing {file_name}...")
                # CSVファイルだけを処理
                if file_name.endswith('.csv'):
                    with zf_in.open(file_name) as f:
                        # CSVを読み込む
                        df = pd.read_csv(f)
                        
                        # --- 置換処理 ---
                        # 1. いったん 0 を None (欠損値) に置き換える
                        df_none = df.replace(0, None)
                        # 2. 直前の値で前方補完 (Forward Fill) 
                        df = df_none.ffill()
                        # (補足) もし最初から0だった場合のために、一応残ったNoneを0に戻す安全策
                        df = df.fillna(0)
                        # ----------------

                        # メモリ上のバッファにCSV形式で書き出し
                        csv_buf = io.StringIO()
                        df.to_csv(csv_buf, index=False)
                        
                        # 新しいZIPに追加
                        zf_out.writestr(file_name, csv_buf.getvalue())
                        print(f"✅ {file_name} の置換完了")
                else:
                    # CSV以外のファイル（画像など）があれば、そのままコピー
                    zf_out.writestr(file_name, zf_in.read(file_name))

    try:
        os.remove(ZIP_FILE)  # 元のZIPファイルを削除
        os.rename(OUTPUT_DIR, ZIP_FILE)  # 新しいZIPファイルを元の名前に変更
        print(f"✅ 置換後のZIPファイルを {ZIP_FILE} として保存しました。")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
    print(f"\nすべての処理が完了しました。保存先: {OUTPUT_DIR}")