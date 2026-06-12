import zipfile
import pandas as pd
import io
import os

def file_select(Z):
    if Z == 50:
        print("Z=50を選択しました。")
        INPUT_DIR = "../../shunningグラフ/Z_change_協力率変遷/+3-1-3+1+5-3"
        INPUT_FILE = "shunning10000協力率_まとめ_Z=50_r=3.0.png"
        ZIP_FILE = "../../shunningデータ/Z_b_change報酬罰/+3-1-3+1+5-3/shunning_Z=50_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.zip"
        OUTPUT_DIR = "../../shunningデータ/Z_b_change報酬罰/+3-1-3+1+5-3/shunning_Z=50_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.zip" + '.temp'
        file_names = ['shunning_Z=50_b=0_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv','shunning_Z=50_b=0.2_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv','shunning_Z=50_b=0.4_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv',
                      'shunning_Z=50_b=0.6_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv','shunning_Z=50_b=0.8_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv','shunning_Z=50_b=1_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv']

    elif Z == 60:
        print("Z=60を選択しました。")
        INPUT_DIR = "../../shunningグラフ/Z_change_協力率変遷/+3-1-3+1+5-3"
        INPUT_FILE = "shunning10000協力率_まとめ_Z=60_r=3.0.png"
        ZIP_FILE = "../../shunningデータ/Z_b_change報酬罰/+3-1-3+1+5-3/shunning_Z=60_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.zip"
        OUTPUT_DIR = "../../shunningデータ/Z_b_change報酬罰/+3-1-3+1+5-3/shunning_Z=60_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.zip" + '.temp'
        file_names = ['shunning_Z=60_b=0_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv','shunning_Z=60_b=0.2_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv','shunning_Z=60_b=0.4_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv',
                      'shunning_Z=60_b=0.6_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv','shunning_Z=60_b=0.6_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv','shunning_Z=60_b=1_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv']

    elif Z == 70:
        print("Z=70を選択しました。")
        INPUT_DIR = "../../shunningグラフ/Z_change_協力率変遷/+3-1-3+1+5-3"
        INPUT_FILE = "shunning10000協力率_まとめ_Z=70_r=3.0.png"
        ZIP_FILE = "../../shunningデータ/Z_b_change報酬罰/+3-1-3+1+5-3/shunning_Z=70_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.zip"
        OUTPUT_DIR = "../../shunningデータ/Z_b_change報酬罰/+3-1-3+1+5-3/shunning_Z=70_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.zip" + '.temp'
        file_names = ['shunning_Z=70_b=0_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv','shunning_Z=70_b=0.2_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv','shunning_Z=70_b=0.4_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv',
                      'shunning_Z=70_b=0.6_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv','shunning_Z=70_b=0.6_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv','shunning_Z=70_b=1_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv']

    elif Z == 80:
        print("Z=80を選択しました。")
        INPUT_DIR = "../../shunningグラフ/Z_change_協力率変遷/+3-1-3+1+5-3"
        INPUT_FILE = "shunning10000協力率_まとめ_Z=80_r=3.0.png"
        ZIP_FILE = "../../shunningデータ/Z_b_change報酬罰/+3-1-3+1+5-3/shunning_Z=80_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.zip"
        OUTPUT_DIR = "../../shunningデータ/Z_b_change報酬罰/+3-1-3+1+5-3/shunning_Z=80_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.zip" + '.temp'
        file_names = ['shunning_Z=80_b=0_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv','shunning_Z=80_b=0.2_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv','shunning_Z=80_b=0.4_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv',
                      'shunning_Z=80_b=0.6_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv','shunning_Z=80_b=0.6_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv','shunning_Z=80_b=1_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv'] 
 
    elif Z == 90:
        print("Z=90を選択しました。")
        INPUT_DIR = "../../shunningグラフ/Z_change_協力率変遷/+3-1-3+1+5-3"
        INPUT_FILE = "shunning10000協力率_まとめ_Z=90_r=3.0.png"
        ZIP_FILE = "../../shunningデータ/Z_b_change報酬罰/+3-1-3+1+5-3/shunning_Z=90_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.zip"
        OUTPUT_DIR = "../../shunningデータ/Z_b_change報酬罰/+3-1-3+1+5-3/shunning_Z=90_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.zip" + '.temp'
        file_names = ['shunning_Z=90_b=0_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv','shunning_Z=90_b=0.2_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv','shunning_Z=90_b=0.4_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv',
                      'shunning_Z=90_b=0.6_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv','shunning_Z=90_b=0.6_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv','shunning_Z=90_b=1_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv']
    
    elif Z == 95:
        print("Z=95を選択しました。")
        INPUT_DIR = "../../shunningグラフ/Z_change_協力率変遷/+3-1-3+1+5-3"
        INPUT_FILE = "shunning10000協力率_まとめ_Z=95_r=3.0.png"
        ZIP_FILE = "../../shunningデータ/Z_b_change報酬罰/+3-1-3+1+5-3/shunning_Z=95_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.zip"
        OUTPUT_DIR = "../../shunningデータ/Z_b_change報酬罰/+3-1-3+1+5-3/shunning_Z=95_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.zip" + '.temp'
        file_names = ['shunning_Z=95_b=0_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv','shunning_Z=95_b=0.2_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv','shunning_Z=95_b=0.4_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv',
                    'shunning_Z=95_b=0.6_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv','shunning_Z=95_b=0.6_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv','shunning_Z=95_b=1_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv']

    elif Z == 98:
        print("Z=98を選択しました。")
        INPUT_DIR = "../../shunningグラフ/Z_change_協力率変遷/+3-1-3+1+5-3"
        INPUT_FILE = "shunning10000協力率_まとめ_Z=98_r=3.0.png"
        ZIP_FILE = "../../shunningデータ/Z_b_change報酬罰/+3-1-3+1+5-3/shunning_Z=98_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.zip"
        OUTPUT_DIR = "../../shunningデータ/Z_b_change報酬罰/+3-1-3+1+5-3/shunning_Z=98_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.zip" + '.temp'
        file_names = ['shunning_Z=98_b=0_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv','shunning_Z=98_b=0.2_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv','shunning_Z=98_b=0.4_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv',
                    'shunning_Z=98_b=0.6_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv','shunning_Z=98_b=0.6_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv','shunning_Z=98_b=1_r=3.0_α=0.1_β=1.0_+3-1-3+1+5-3_omega.csv']

    return OUTPUT_DIR, INPUT_DIR, INPUT_FILE, ZIP_FILE, file_names
for Z in [50, 60, 70, 80, 90, 95, 98]:
    OUTPUT_DIR, INPUT_DIR, INPUT_FILE, ZIP_FILE, file_names = file_select(Z)
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
                        # 0 を 1 に置換
                        df = df.replace(0, 1)
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