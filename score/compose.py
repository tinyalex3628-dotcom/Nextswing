# -*- coding: utf-8 -*-
# 제거 밴드를 실제로 오려내고, 남은 밴드를 이어붙여 페이지를 재구성한다.
import numpy as np
from PIL import Image
from crop_tab import analyze

SCRATCH = "/tmp/claude-0/-home-user-Nextswing/9a4ae754-881c-5e76-a20b-08c510c7ffc4/scratchpad"
TARGET_W = 1000

def page_strip(path):
    im, clusters, removes = analyze(path)
    w, h = im.size
    arr = np.asarray(im.convert("RGB"))
    keep_rows = np.ones(h, dtype=bool)
    for t, b in removes:
        keep_rows[t:b + 1] = False
    strip = arr[keep_rows]
    return strip, w

def collapse_white(strip, max_gap=12):
    """연속 흰 row 구간을 max_gap으로 압축."""
    gray = strip.mean(axis=2)
    dark = (gray < 200).sum(axis=1)
    is_white = dark <= 1
    keep = np.ones(len(strip), dtype=bool)
    run = 0
    for i, wht in enumerate(is_white):
        if wht:
            run += 1
            if run > max_gap:
                keep[i] = False
        else:
            run = 0
    return strip[keep]

def main(pages):
    strips = []
    for p in pages:
        strip, w = page_strip(p)
        img = Image.fromarray(strip)
        if w != TARGET_W:
            img = img.resize((TARGET_W, int(img.size[1] * TARGET_W / w)), Image.LANCZOS)
        strips.append(np.asarray(img))
    full = np.concatenate(strips, axis=0)
    full = collapse_white(full, max_gap=14)

    # A4 비율로 페이지 분할하되, 시스템 중간에서 자르지 않게 흰 row에서 자른다
    page_h = int(TARGET_W * 1.414 * 1.08)  # 여유
    gray = full.mean(axis=2)
    darkc = (gray < 200).sum(axis=1)
    pages_out, y = [], 0
    H = len(full)
    while y < H:
        end = min(y + page_h, H)
        if end < H:
            # end 근처 위쪽으로 흰 row 탐색
            cut = end
            for k in range(end, max(y + page_h // 2, y + 1), -1):
                if darkc[k] <= 1:
                    cut = k
                    break
            end = cut
        pages_out.append(full[y:end])
        y = end
    outs = []
    for i, pg in enumerate(pages_out, 1):
        canvas = np.full((page_h, TARGET_W, 3), 255, dtype=np.uint8)
        canvas[:len(pg)] = pg
        # 좌우 여백 추가
        pad = 40
        page = np.full((page_h + 60, TARGET_W + pad * 2, 3), 255, dtype=np.uint8)
        page[30:30 + page_h, pad:pad + TARGET_W] = canvas
        out = Image.fromarray(page)
        fn = f"{SCRATCH}/out_page{i}.png"
        out.save(fn)
        outs.append(out)
        print("page", i, "content rows:", len(pg))
    outs[0].save("/home/user/Nextswing/score/나의_어릴적_이야기_탭전용.pdf",
                 save_all=True, append_images=outs[1:], resolution=120)
    print("pages:", len(outs))

if __name__ == "__main__":
    import sys
    sys.path.insert(0, "/home/user/Nextswing/score")
    main([f"/home/user/Nextswing/{n}.PNG" for n in range(1, 6)])
