# -*- coding: utf-8 -*-
"""
研究進捗9月.pptx のスライド318以降の画像を入れ替え、研究進捗9月修正版.pptx として保存する。

準備:  pip install python-pptx
実行:  python replace_images.py
最初は DRY_RUN = True のまま実行し、ログで対応関係を確認してから False にしてください。
"""
import re
import unicodedata
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

# ===== 設定 =====
BASE = Path(r"C:\Users\Admin\project\m2")   # m2 フォルダの場所
SRC = BASE / "powerpoint" / "研究進捗9月.pptx"
DST = BASE / "powerpoint" / "研究進捗9月修正版.pptx"
START_SLIDE = 318                       # このスライド番号から最後まで
DRY_RUN = False                         # True: 確認のみ(保存しない) / False: 実際に入れ替えて保存
# =================

WORDS = ["shunning", "simple", "stern", "image"]
Z_LIST = [50, 60, 70, 80, 90, 95, 98]   # Zなしスライドの画像1〜7
NUM = r"([0-9]+(?:\.[0-9]+)?)"


def norm(s):
    """全角/半角・濁点の合成差(Macのファイル名)・マイナス記号の揺れを吸収"""
    s = unicodedata.normalize("NFKC", s)
    return s.replace("\u2212", "-").replace("\u2010", "-").replace("\u2013", "-")


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
}
FALLBACK = "{http://schemas.openxmlformats.org/markup-compatibility/2006}Fallback"
T_TAGS = ("{%s}t" % NS["a"], "{%s}t" % NS["m"])


def live(el):
    """数式の代替表示(Fallback)側の要素は無視する"""
    return not any(anc.tag == FALLBACK for anc in el.iterancestors())


def el_text(el):
    """通常の文字(a:t)と数式の文字(m:t)を両方、順番どおりに取り出す"""
    paras = []
    for para in el.iter("{%s}p" % NS["a"]):
        if not live(para):
            continue
        paras.append("".join(t.text or "" for t in para.iter(*T_TAGS) if live(t)))
    return norm(" ".join(paras))


def title_text(slide):
    """数式入りの図形は python-pptx の shapes に出てこないので XML を直接読む"""
    titles, others = [], []
    for sp in slide._element.iter("{%s}sp" % NS["p"]):
        if not live(sp):
            continue
        txt = el_text(sp)
        if not txt.strip():
            continue
        ph = sp.find(".//p:nvPr/p:ph", NS)
        is_title = ph is not None and ph.get("type") in ("title", "ctrTitle")
        (titles if is_title else others).append(txt)
    for txt in titles + others:
        if any(w in txt.lower() for w in WORDS):
            return txt
    return titles[0] if titles else ""


def parse_title(t):
    word = next((w for w in WORDS if w in t.lower()), None)
    m = re.search(r"[ωΩw]\s*_?\s*y?\s*[=:]\s*" + NUM, t)
    omega = m.group(1) if m else None
    m = re.search(r"Z\s*[=:]\s*" + NUM, t)
    z = m.group(1) if m else None
    return word, omega, z


def table_tokens(slide):
    tbls = [t for t in slide._element.iter("{%s}tbl" % NS["a"]) if live(t)]
    if not tbls:
        return None

    def top(tbl):
        for anc in tbl.iterancestors("{%s}graphicFrame" % NS["p"]):
            off = anc.find("p:xfrm/a:off", NS)
            if off is not None:
                return int(off.get("y", 0))
        return 0

    tbls.sort(key=top)
    return re.findall(r"[+-]?\d+(?:\.\d+)?", el_text(tbls[0]))


def find_dir(parent, pred):
    return [d for d in parent.iterdir() if d.is_dir() and pred(norm(d.name))]


def find_param_dir(zdir, tokens):
    """表の数字のうち偶数番目(2,4,6,...番目)を使ってフォルダを特定する"""
    key = tokens[1::2]
    kf = [float(t) for t in key]
    dirs = [d for d in zdir.iterdir() if d.is_dir()]

    def nums(d):
        return [float(t) for t in re.findall(r"[+-]?\d+(?:\.\d+)?", norm(d.name))]

    # 1) 符号込みで並びが一致  2) 表に符号がない場合は絶対値で一致  3) 文字として全て含む
    for test in (lambda d: nums(d) == kf,
                 lambda d: [abs(x) for x in nums(d)] == [abs(x) for x in kf],
                 lambda d: all(t in norm(d.name) for t in key)):
        cands = [d for d in dirs if test(d)]
        if len(cands) == 1:
            return cands[0], None
        if len(cands) > 1:
            return None, "表の偶数番目 %s に該当するフォルダが複数: %s" % (
                key, ", ".join(d.name for d in cands))
    return None, "表の偶数番目 %s に一致するフォルダなし" % key


def find_png(folder, template, word, z, omega):
    """template 中の {Z} {W} を数値として比較して探す (0.5 と 0.50 などの揺れを吸収)"""
    if not folder.is_dir():
        return None
    pat = re.escape(template.replace("{word}", word))
    pat = pat.replace(re.escape("{Z}"), NUM).replace(re.escape("{W}"), NUM)
    rx = re.compile("^" + pat + "$", re.IGNORECASE)
    for f in folder.iterdir():
        m = rx.match(norm(f.name))
        if m and float(m.group(1)) == float(z) and float(m.group(2)) == float(omega):
            return f
    return None


R_EMBED = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
P_PIC, P_GRP = "{%s}pic" % NS["p"], "{%s}grpSp" % NS["p"]


def geom(pic):
    off = pic.find("p:spPr/a:xfrm/a:off", NS)
    ext = pic.find("p:spPr/a:xfrm/a:ext", NS)
    if off is None or ext is None:
        return 0, 0, 1
    return int(off.get("x", 0)), int(off.get("y", 0)), int(ext.get("cy", 1))


def sort_pics(pics):
    """上の行の左→右、次に下の行の左→右"""
    pics = sorted(pics, key=lambda p: geom(p)[1])
    rows, cur = [], [pics[0]]
    for p in pics[1:]:
        if geom(p)[1] - geom(cur[0])[1] < geom(cur[0])[2] / 2:
            cur.append(p)
        else:
            rows.append(cur)
            cur = [p]
    rows.append(cur)
    return [p for r in rows for p in sorted(r, key=lambda p: geom(p)[0])]


P_SP = "{%s}sp" % NS["p"]


def blip_of(el):
    """画像の参照要素を返す。通常の画像(p:pic)と、画像で塗りつぶした図形(p:sp)の両方に対応"""
    if el.tag == P_PIC:
        return el.find("p:blipFill/a:blip", NS)
    return el.find("p:spPr/a:blipFill/a:blip", NS)


def picture_like(root):
    return [e for e in root.iter(P_PIC, P_SP) if live(e) and blip_of(e) is not None]


def ordered_pictures(slide, count):
    """count 枚の画像を探す。グループ(入れ子も可) → グループ外の画像 → スライド全体 の順。
    戻り値: (画像リスト or None, 見つからない時の内訳)"""
    root = slide._element
    all_pics = picture_like(root)
    groups = [picture_like(g) for g in root.iter(P_GRP) if live(g)]
    loose = [p for p in all_pics if not any(True for _ in p.iterancestors(P_GRP))]
    for cand in groups + [loose, all_pics]:
        if len(cand) == count:
            return sort_pics(cand), None
    return None, "グループごとの画像数=%s, グループ外=%d, 合計=%d" % (
        [len(g) for g in groups], len(loose), len(all_pics))


def replace(slide, pic, path):
    """枠の位置・大きさはそのままに、中身の画像だけ差し替える"""
    _, rid = slide.part.get_or_add_image_part(str(path))
    blip_of(pic).set(R_EMBED, rid)


MAIN = "{word}10000協力率_まとめ_Z={Z}_r=3.0_omega={W}.png"
T_C = "{word}10000協力率_C_まとめ_Z={Z}_r=3.0_omega={W}.png"
T_PC = "{word}10000協力率_PC_まとめ_Z={Z}_r=3.0_omega={W}.png"
T_PUN = "{word}罰の回数グラフ_Z={Z}_r=3.0_punish_i_omega={W}.png"


def main():
    prs = Presentation(str(SRC))
    done = skipped = 0
    for no, slide in enumerate(prs.slides, start=1):
        if no < START_SLIDE:
            continue
        title = title_text(slide)
        word, omega, z = parse_title(title)
        tokens = table_tokens(slide)

        def skip(reason):
            print("[スキップ] スライド%d: %s  (タイトル: %s)" % (no, reason, title))

        if not word or not omega:
            skipped += 1; skip("タイトルから英単語またはωyを読めない"); continue
        if not tokens:
            skipped += 1; skip("表が見つからない/数字がない"); continue
        gdirs = find_dir(BASE, lambda n: word in n.lower() and "グラフ" in n)
        if len(gdirs) != 1:
            skipped += 1; skip("'%s'+グラフ のフォルダを特定できない" % word); continue
        zdir = gdirs[0] / "Z_change_協力率変遷"
        if not zdir.is_dir():
            cand = find_dir(gdirs[0], lambda n: n == "Z_change_協力率変遷")
            if not cand:
                skipped += 1; skip("Z_change_協力率変遷 がない"); continue
            zdir = cand[0]
        pdir, err = find_param_dir(zdir, tokens)
        if err:
            skipped += 1; skip(err); continue

        if z is None:   # Zなし: 7枚
            jobs = [(pdir, MAIN, zz) for zz in Z_LIST]
        else:           # Zあり: 4枚 (まとめ, C, PC, Punish)
            jobs = [(pdir, MAIN, z), (pdir / "C", T_C, z),
                    (pdir / "PC", T_PC, z), (pdir / "Punish", T_PUN, z)]
        pics, diag = ordered_pictures(slide, len(jobs))
        if pics is None:
            skipped += 1; skip("画像%d枚の組が見つからない [%s]" % (len(jobs), diag)); continue
        files = [find_png(d, t, word, zz, omega) for d, t, zz in jobs]
        if any(f is None for f in files):
            miss = [i + 1 for i, f in enumerate(files) if f is None]
            skipped += 1; skip("%s 内で画像 %s 番のファイルが見つからない" % (pdir.name, miss)); continue

        print("[OK] スライド%d: %s ωy=%s Z=%s フォルダ=%s" % (no, word, omega, z or "なし", pdir.name))
        for i, (pic, f) in enumerate(zip(pics, files), start=1):
            print("      %d: %s" % (i, f.name))
            if not DRY_RUN:
                replace(slide, pic, f)
        done += 1

    print("\n対象 %d 枚 / スキップ %d 枚" % (done, skipped))
    if DRY_RUN:
        print("DRY_RUN のため保存していません。問題なければ DRY_RUN = False にして再実行してください。")
    else:
        prs.save(str(DST))
        print("保存しました:", DST)


if __name__ == "__main__":
    main()