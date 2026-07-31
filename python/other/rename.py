# -*- coding: utf-8 -*-
"""
指定フォルダ配下(サブフォルダも全階層対象)のすべての.zipファイルについて、
  1. ZIP内のファイル名に含まれる "CP" を "PC" に変更
  2. CSVファイルの1行目に含まれる "CP rate" を "PC rate" に変更
を行うスクリプト。

使い方:
    1. 下の ROOT_PATH を対象フォルダのパスに書き換える
    2. 実行前に必ずフォルダ全体をバックアップする
    3. python rename_cp_to_pc.py を実行
"""

import os
import zipfile
import shutil
import tempfile

# ==== 設定 ====
ROOT_PATH = r"C:\Users\Admin\project\m2"   # 対象の親フォルダ
TARGET_FOLDER_NAME = "PC"   # このフォルダ名の中にあるzipファイルだけを対象にする
DRY_RUN = False   # True にすると実際には変更せず、変更予定だけを表示します(テスト用)


def try_decode(data: bytes):
    """CSVのバイト列を複数の文字コードで試してデコードする"""
    for enc in ("utf-8-sig", "utf-8", "cp932", "shift_jis"):
        try:
            return data.decode(enc), enc
        except (UnicodeDecodeError, LookupError):
            continue
    # どれもダメなら誤り無視のutf-8で強制デコード
    return data.decode("utf-8", errors="replace"), "utf-8(replace)"


def process_zip(zip_path: str):
    print(f"\n=== {zip_path} ===")
    changed_names = 0
    changed_contents = 0

    # 一時ファイルに新しいzipを作る
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".zip")
    os.close(tmp_fd)

    try:
        with zipfile.ZipFile(zip_path, "r") as zin, \
             zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:

            for item in zin.infolist():
                data = zin.read(item.filename)
                new_filename = item.filename

                # ---- 1. ファイル名の CP -> PC ----
                base = os.path.basename(item.filename)
                dirpart = os.path.dirname(item.filename)
                if "CP" in base:
                    new_base = base.replace("CP", "PC")
                    new_filename = f"{dirpart}/{new_base}" if dirpart else new_base
                    changed_names += 1
                    print(f"  [ファイル名] {base} -> {new_base}")

                # ---- 2. CSVの1行目にある "CP" をすべて "PC" に置換 ----
                # 例: "CP Rate" -> "PC Rate", "CP Rate H" -> "PC Rate H" など
                if base.lower().endswith(".csv"):
                    text, enc = try_decode(data)
                    lines = text.splitlines(keepends=True)
                    if lines and "CP" in lines[0]:
                        lines[0] = lines[0].replace("CP", "PC")
                        text = "".join(lines)
                        data = text.encode(enc.split("(")[0] if "replace" not in enc else "utf-8")
                        changed_contents += 1
                        print(f"  [中身1行目] {base} のヘッダー内の CP -> PC を置換 ({enc})")

                if not DRY_RUN:
                    zout.writestr(new_filename, data)
                else:
                    zout.writestr(item.filename, zin.read(item.filename))  # 変更せずそのままコピー(DRY RUN用)

        if not DRY_RUN:
            shutil.move(tmp_path, zip_path)
        else:
            os.remove(tmp_path)

        if changed_names == 0 and changed_contents == 0:
            print("  変更対象なし")
        else:
            print(f"  -> ファイル名変更: {changed_names}件 / 中身変更: {changed_contents}件")

    except Exception as e:
        print(f"  エラー: {e}")
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def main():
    zip_files = []
    for dirpath, _, filenames in os.walk(ROOT_PATH):
        # パスの階層(フォルダ名)の中に "PC" という名前のフォルダが
        # 含まれている場合のみ対象にする
        path_parts = dirpath.split(os.sep)
        if TARGET_FOLDER_NAME not in path_parts:
            continue

        for f in filenames:
            if f.lower().endswith(".zip"):
                zip_files.append(os.path.join(dirpath, f))

    print(f"対象ZIPファイル数: {len(zip_files)}")
    if DRY_RUN:
        print("*** DRY RUN モード: 実際の変更は行われません ***")

    for zp in zip_files:
        process_zip(zp)

    print("\n=== 完了 ===")


if __name__ == "__main__":
    main()