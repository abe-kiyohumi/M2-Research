# 詳細ログ L1〜L8 の仕様と実行手順（2026-10-15 改修）

## 実行手順
1. `python test_equivalence.py` … 旧コード（run_simulation_old.py）と同一 seed で協力率・罰・ペイオフが一致することを確認
2. `all.py` の `MODE="test"` で実行（G13 代表条件・100MCS、数十秒）→ `all_glaph.py` も `MODE="test"` で実行し、グラフを確認
3. `MODE="representative"`（14グループ代表条件, b=0/1.0, G04 のみ b 6値）→ `SEEDS=list(range(10))` に拡大
4. `MODE="controls"`（評判リセット / ωy=1 / 10^5MCS / D消滅後も継続 / 評判丸め）
5. `all_glaph.py` を同じ MODE・SEEDS で実行 → `m2/summary_all.csv` に全条件の要約指標が統合される

## 出力先
- 従来 zip: `m2/{rule}データ/Z_b_change報酬罰{variant}/{PATTERN}/...`（seed 指定時のみ末尾 `_seed=N`）
- 詳細ログ: `.../{PATTERN}/Logs/{rule}_Z={Z}_omega={ω}_seed={N}.zip`（中に `b=0/`, `b=1.0/` …）
- グラフ: `m2/{rule}グラフ/Z_change_協力率変遷{variant}/{PATTERN}/Logs/`
- variant: `_T100000`（長時間）, `_reset-uniform`, `_stop-mono`, `_repfix`（既定条件は空文字＝従来フォルダ）

## 行の定義
L1/L5/L7: `MCS=t` は t MCS 完了後の状態（t=0 は初期状態）。L2/L6: t 番目の MCS 中に起きたイベント数。
ログ計算は乱数を使わないので、ダイナミクスは旧コードと同一。
