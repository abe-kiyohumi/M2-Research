import numpy as np
import random
import math
import matplotlib.pyplot as plt
import pandas as pd
import os
import time
import zipfile
import io
import shutil
# 定数設定
L = 100
G = 5
K = 0.5
alpha = 0.1
beta = 1.0
#b = 0
num_steps = 12000
OUTPUT_DIR = "../../sternデータ/Z_b_change報酬罰/+3-1-3+1+5-3"   #変更点
OUTPUT_DIR_C = "../../sternデータ/Z_b_change報酬罰/+3-1-3+1+5-3/C"
OUTPUT_DIR_CP = "../../sternデータ/Z_b_change報酬罰/+3-1-3+1+5-3/CP"
OUTPUT_DIR_PUNISH = "../../sternデータ/Z_b_change報酬罰/+3-1-3+1+5-3/Punish" # ★ 罰データ用フォルダ追加
OUTPUT_DIRS = [OUTPUT_DIR, OUTPUT_DIR_C, OUTPUT_DIR_CP, OUTPUT_DIR_PUNISH]

def append_to_summary(Z, b, rate, Crate, CPrate):
    FILE_PATHS = {
    "rate": os.path.join(OUTPUT_DIR, f"summary_rate_omega_r={R}.csv"),
    "Crate": os.path.join(OUTPUT_DIR_C, f"summary_Crate_omega_r={R}.csv"),
    "CPrate": os.path.join(OUTPUT_DIR_CP, f"summary_CPrate_omega_r={R}.csv"),
    }
    results = {"rate": {"Z": Z, "b": b, "R": R, "Rate": rate}}
    results_C = {"Crate": {"Z": Z, "b": b, "R": R, "CRate": Crate}}
    results_CP = {"CPrate": {"Z": Z, "b": b, "R": R, "CPRate": CPrate}} 

    for key, data in results.items():
        file_path = FILE_PATHS[key]
        df_rate = pd.DataFrame([data])
        if not os.path.exists(file_path):
            df_rate.to_csv(file_path, index=False, mode='w', encoding='utf-8')
        else:
            df_rate.to_csv(file_path, index=False, mode='a', header=False, encoding='utf-8')

    for key_C, data_C in results_C.items():
        file_path_C = FILE_PATHS[key_C]
        df_rate_C = pd.DataFrame([data_C])
        if not os.path.exists(file_path_C):
            df_rate_C.to_csv(file_path_C, index=False, mode='w', encoding='utf-8')
        else:
            df_rate_C.to_csv(file_path_C, index=False, mode='a', header=False, encoding='utf-8')

    for key_CP, data_CP in results_CP.items():
        file_path_CP = FILE_PATHS[key_CP]
        df_rate_CP = pd.DataFrame([data_CP])
        if not os.path.exists(file_path_CP):
            df_rate_CP.to_csv(file_path_CP, index=False, mode='w', encoding='utf-8')
        else:
            df_rate_CP.to_csv(file_path_CP, index=False, mode='a', header=False, encoding='utf-8')

def clear_output_directory(directory):
    if os.path.exists(directory):
        shutil.rmtree(directory)
    os.makedirs(directory, exist_ok=True)

def initialize_grid():
    values = np.ones(L * L)
    values[L * L // 2:] = -1
    values[:L * L // 4] = 2
    np.random.shuffle(values)
    grid = values.reshape(L, L)
    count_C_CP = np.sum(grid==1) + np.sum(grid==2)
    print("初期協力率:", count_C_CP/(L*L))
    return grid

def initialize_reputationgrid():
    reputationgrid = np.random.randint(1, 101, size=(L, L))
    print("初期評判:", np.mean(reputationgrid))
    return reputationgrid

def cal_sita(NPc, grid, reputationgrid, i, j, count_punish):
    f = cal_f(Z, reputationgrid, b, i, j)
    if random.random() < f:
        sita = NPc
        count_punish += 1  # 罰が発動したら確実にカウントアップ
    else:
        sita = 0
    return sita, count_punish

def cal_f(Z, reputationgrid, b, i, j):
    if reputationgrid[i, j] < Z:
        f = ((Z - reputationgrid[i, j]) / Z) ** b
    else:
        f = 0
    return f

def cal_KD(grid, i, j, my_neighbors, reputationgrid):
    NBD = 0
    for _ in range(G):
        if grid[my_neighbors[_]] == -1 and reputationgrid[my_neighbors[_]] < Z:
            NBD += 1
    if grid[i, j] == 2:
        KD = NBD
    else:
        KD = 0
    return KD

# ★ 最終的な点数計算（戻り値にcount_punishを含めるよう修正）
def game(i, j, Nc, NPc, R, grid, reputationgrid, my_neighbors, count_punish):
    if grid[i, j] == 1:
        return ((R * (Nc + NPc)) / G) - 1, count_punish
    elif grid[i, j] == 2:
        KD = cal_KD(grid, i, j, my_neighbors, reputationgrid)
        return ((R * (Nc + NPc)) / G) - 1 - (alpha * KD), count_punish
    else:
        sita, count_punish = cal_sita(NPc, grid, reputationgrid, i, j, count_punish)
        return ((R * (Nc + NPc)) / G) - (beta * sita), count_punish

# ★ 点数計算（引き継がれたcount_punishを正しく累積して返すよう修正）
def cal_point(i, j, R, grid, reputationgrid, count_punish):
    point = 0.0
    my_neighbors = [
        ((i-1) % L, j), ((i+1) % L, j),
        (i, (j-1) % L), (i, (j+1) % L),
        (i, j)
    ]     
    Nc = 0
    NPc = 0
    for _ in range(G):
        if grid[my_neighbors[_]] == 1:
            Nc += 1
        elif grid[my_neighbors[_]] == 2:
            NPc += 1
    
    p, count_punish = game(i, j, Nc, NPc, R, grid, reputationgrid, my_neighbors, count_punish)
    point += p
    
    for l in range(G - 1):
        Nc = 0
        NPc = 0
        neii , neij = my_neighbors[l]
        nei_neighbors = [
            ((neii-1) % L, neij), ((neii+1) % L, neij),
            (neii, (neij-1) % L), (neii, (neij+1) % L),
            (neii, neij)
        ]  
        for _ in range(G):
            if grid[nei_neighbors[_]] == 1:
                Nc += 1
            elif grid[nei_neighbors[_]] == 2:
                NPc += 1

        p, count_punish = game(i, j, Nc, NPc, R, grid, reputationgrid, nei_neighbors, count_punish)
        point += p
    return point, count_punish

def update_reputation(reputationgrid, grid, i, j, ni, nj):
    if grid[i, j] == 1:
        if reputationgrid[ni, nj] >= Z and reputationgrid[i, j] >= Z: #相手；高評判　自分；高評判　自分；協力       変更点
            reputationgrid[i, j] = reputationgrid[i, j] + 3
        elif reputationgrid[ni, nj] >= Z and reputationgrid[i, j] < Z: #相手；高評判　自分；低評判　自分；協力
            reputationgrid[i, j] = reputationgrid[i, j] + 3
        elif reputationgrid[ni, nj] < Z and reputationgrid[i, j] >= Z: #相手；低評判　自分；高評判　自分；協力
            reputationgrid[i, j] = reputationgrid[i, j] + 1
        elif reputationgrid[ni, nj] < Z and reputationgrid[i, j] < Z: #相手；低評判　自分；低評判　自分；協力
            reputationgrid[i, j] = reputationgrid[i, j] - 1
    elif grid[i, j] == -1:
        if reputationgrid[ni, nj] >= Z and reputationgrid[i, j] >= Z: #相手；高評判　自分；高評判　自分；裏切り
            reputationgrid[i, j] = reputationgrid[i, j] - 3
        elif reputationgrid[ni, nj] >= Z and reputationgrid[i, j] < Z: #相手；高評判　自分；低評判　自分；裏切り
            reputationgrid[i, j] = reputationgrid[i, j] - 3
        elif reputationgrid[ni, nj] < Z and reputationgrid[i, j] >= Z: #相手；低評判　自分；高評判　自分；裏切り
            reputationgrid[i, j] = reputationgrid[i, j] + 1
        elif reputationgrid[ni, nj] < Z and reputationgrid[i, j] < Z: #相手；低評判　自分；低評判　自分；裏切り
            reputationgrid[i, j] = reputationgrid[i, j] - 1
    else:
        if reputationgrid[ni, nj] >= Z and reputationgrid[i, j] >= Z: #相手；高評判　自分；高評判　自分；懲罰者
            reputationgrid[i, j] = reputationgrid[i, j] + 5
        elif reputationgrid[ni, nj] >= Z and reputationgrid[i, j] < Z: #相手；高評判　自分；低評判　自分；懲罰者
            reputationgrid[i, j] = reputationgrid[i, j] + 5
        elif reputationgrid[ni, nj] < Z and reputationgrid[i, j] >= Z: #相手；低評判　自分；高評判　自分；懲罰者
            reputationgrid[i, j] = reputationgrid[i, j] + 3
        elif reputationgrid[ni, nj] < Z and reputationgrid[i, j] < Z: #相手；低評判　自分；低評判　自分；懲罰者
            reputationgrid[i, j] = reputationgrid[i, j] - 3
    #評判の範囲制限
    if reputationgrid[i, j] > 100:
        reputationgrid[i, j] = 100
    if reputationgrid[i, j] < 0:
        reputationgrid[i, j] = 0
    return reputationgrid


# モンテカルロステップ
def simulation(record_index):
    grid = initialize_grid()
    reputationgrid = initialize_reputationgrid()
    indices = np.array([[i, j] for i in range(L) for j in range(L)])
    check = 0
    rast = 0
    sum_rate = 0; sum_rateC = 0; sum_ratePC = 0
    count = 0
    
    for mcsstep in range(num_steps):
        # ★ 1MCS内でのプレイヤーi, jそれぞれの罰の合計カウント用変数
        mcs_punish_X = 0
        mcs_punish_Y = 0
        
        np.random.shuffle(indices)
        for _ in range(L*L):
            if check == 0:
                i, j = indices[_]
                my_neighbors = [
                    ((i-1) % L, j), ((i+1) % L, j),
                    (i, (j-1) % L), (i, (j+1) % L)
                ] 
                ni, nj = my_neighbors[random.randint(0,3)]
                
                if grid[i, j] == grid[ni, nj]:
                    reputationgrid = update_reputation(reputationgrid, grid, i, j, ni, nj)
                    count_C_CP = np.sum(grid==1) + np.sum(grid==2)
                    rate = count_C_CP/(L*L) 
                    Crate = np.sum(grid==1)/(L*L)
                    CPrate = np.sum(grid==2)/(L*L)
                    
                    if rate == 0: check = 1; rast = mcsstep
                    if rate == 1.0: check = 2; rast = mcsstep
                    
                    """if _ % 1000 == 0 and mcsstep < 10000:
                        rates_array[record_index] = rate
                        Crates_array[record_index] = Crate
                        CPrates_array[record_index] = CPrate
                        record_index += 1 """
                    continue
                
                # ★ 各対戦ごとのカウント用変数をリセットして渡す
                count_punishX = 0
                count_punishY = 0
                pointx, count_punishX = cal_point(i, j, R, grid, reputationgrid, count_punishX)
                pointy, count_punishY = cal_point(ni, nj, R, grid, reputationgrid, count_punishY)
                
                # ★ 1MCSの総数へ個別に加算
                mcs_punish_X += count_punishX
                mcs_punish_Y += count_punishY
                
                if reputationgrid[ni, nj] >= Z:
                    omega = 1.0
                else:
                    omega = 0.01
                    
                if random.random() < omega * (1 / (1 + math.exp((pointx - pointy) / K))):
                    grid[i, j] = grid[ni, nj]
                    
                reputationgrid = update_reputation(reputationgrid, grid, i, j, ni, nj)
                count_C_CP = np.sum(grid==1) + np.sum(grid==2)
                rate = count_C_CP/(L*L) 
                Crate = np.sum(grid==1)/(L*L)
                CPrate = np.sum(grid==2)/(L*L)
                
                """if _ % 1000 == 0 and mcsstep < 10000:
                    rates_array[record_index] = rate
                    Crates_array[record_index] = Crate
                    CPrates_array[record_index] = CPrate
                    record_index += 1 """
                    
                if rate == 0: check = 1; rast = mcsstep
                if rate == 1.0: check = 2; rast = mcsstep
            else:
                """if _ % 1000 == 0 and mcsstep < 10000:
                    rates_array[record_index] = rate
                    Crates_array[record_index] = Crate
                    CPrates_array[record_index] = CPrate
                    record_index += 1 """
                break
                
        # ★ 1MCSループが終了した時点で、そのステップの罰総数を時系列配列に格納
        if mcsstep < num_steps:
            punish_X_time_series[mcsstep] = mcs_punish_X
            punish_Y_time_series[mcsstep] = mcs_punish_Y

        rates_array[record_index] = rate

        if mcsstep % 1000 == 0:
            print(f"ステップ数 {mcsstep} 協力率 {rate:.4f} | 罰回数 i: {mcs_punish_X}, j: {mcs_punish_Y}")
            
        if check != 0: break
        if mcsstep >= 10000:
            sum_rate += rate
            sum_rateC += Crate
            sum_ratePC += CPrate
            count += 1
            
    if check == 0 and num_steps >= 10000: 
        rate = sum_rate / count
        Crate = sum_rateC / count
        CPrate = sum_ratePC / count
    print("0または1になったステップ数", rast)
    return rates_array, Crates_array, CPrates_array, rate, Crate, CPrate

# メイン処理
start = time.time()
for R in [3.0]:
    print("R=", R)
    for Z in [50,60,70,80,90,95,98]: # ループ内固定値を反映
        print("現在のZ値:", Z, "OUTPUT_DIR:", OUTPUT_DIR)
        
        ZIP_NAME = f"stern_Z={Z}_r={R}_+3-1-3+1+5-3_omega_punish.zip"
        ZIP_NAME_C = f"stern_C_Z={Z}_r={R}_+3-1-3+1+5-3_omega.zip"
        ZIP_NAME_CP = f"stern_CP_Z={Z}_r={R}_+3-1-3+1+5-3_omega.zip"
        ZIP_NAME_PUNISH = f"stern_punish_history_Z={Z}_r={R}_+3-1-3+1+5-3_omega.zip" # ★ 罰データ用ZIP名定義
        
        zip_buffer = io.BytesIO()
        zip_buffer_C = io.BytesIO()
        zip_buffer_CP = io.BytesIO()
        zip_buffer_P = io.BytesIO() # ★ 罰データ用バッファ
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf, \
             zipfile.ZipFile(zip_buffer_C, 'w', zipfile.ZIP_DEFLATED) as zf_C, \
             zipfile.ZipFile(zip_buffer_CP, 'w', zipfile.ZIP_DEFLATED) as zf_CP, \
             zipfile.ZipFile(zip_buffer_P, 'w', zipfile.ZIP_DEFLATED) as zf_P: # ★ zf_Pを追加
                 
            for b in [0,0.2,0.4,0.6,0.8,1.0]: # ループ内固定値を反映
                expected_size = 100000
                rates_array = np.zeros(expected_size, dtype=np.float32)
                Crates_array = np.zeros(expected_size, dtype=np.float32)
                CPrates_array = np.zeros(expected_size, dtype=np.float32)
                
                # ★ 1MCSごとの時系列（最大12000要素）を保持する配列を定義
                punish_X_time_series = np.zeros(num_steps, dtype=np.int32)
                punish_Y_time_series = np.zeros(num_steps, dtype=np.int32)
                
                print("現在のb値:", b)
                record_index = 0
                rates_array, Crates_array, CPrates_array, rate, Crate, CPrate = simulation(record_index)
                
                # 各種協力率データの追加
                csv_buf = io.StringIO()
                pd.DataFrame(rates_array, columns=["Cooperation Rate"]).to_csv(csv_buf, index=False)
                zf.writestr(f"stern_Z={Z}_b={b}_r={R}_+3-1-3+1+5-3_omega_punish.csv", csv_buf.getvalue())
                
                """csv_buf_C = io.StringIO()
                pd.DataFrame(Crates_array, columns=["C Rate"]).to_csv(csv_buf_C, index=False)
                zf_C.writestr(f"stern_C_Z={Z}_b={b}_r={R}_+3-1-3+1+5-3_omega.csv", csv_buf_C.getvalue())
                
                csv_buf_CP = io.StringIO()
                pd.DataFrame(CPrates_array, columns=["CP Rate"]).to_csv(csv_buf_CP, index=False)
                zf_CP.writestr(f"stern_CP_Z={Z}_b={b}_r={R}_+3-1-3+1+5-3_omega.csv", csv_buf_CP.getvalue())  """
                
                # ★ 【追加】1MCSごとのプレイヤーiとプレイヤーjの罰回数データをCSVにまとめて格納
                csv_buf_P = io.StringIO()
                punish_df = pd.DataFrame({
                    "MCS_Step": np.arange(num_steps),
                    "Punish_Count_i": punish_X_time_series,
                    "Punish_Count_j": punish_Y_time_series
                })
                punish_df.to_csv(csv_buf_P, index=False)
                zf_P.writestr(f"stern_punish_Z={Z}_b={b}_r={R}_+3-1-3+1+5-3_omega.csv", csv_buf_P.getvalue())
                
                del rates_array, Crates_array, CPrates_array, punish_X_time_series, punish_Y_time_series
                #append_to_summary(Z, b, rate, Crate, CPrate) 

        # ディレクトリの作成と保存
        for d in OUTPUT_DIRS: os.makedirs(d, exist_ok=True)
        
        save_files = [
            (zip_buffer, ZIP_NAME, OUTPUT_DIRS[0]),
            #(zip_buffer_C, ZIP_NAME_C, OUTPUT_DIRS[1]),
            #(zip_buffer_CP, ZIP_NAME_CP, OUTPUT_DIRS[2]),
            (zip_buffer_P, ZIP_NAME_PUNISH, OUTPUT_DIRS[3]) # ★ 罰用ファイルの追加
        ]
        for buf, filename, target_dir in save_files:
            local_path = os.path.join(target_dir, filename)
            with open(local_path, 'wb') as f:
                f.write(buf.getvalue())
            print(f"{filename}が{local_path}に保存されました") 
            buf.close()  
        del csv_buf, csv_buf_P 

end = time.time()
print("実行時間:", end - start, "秒")