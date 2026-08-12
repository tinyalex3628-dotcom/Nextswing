# -*- coding: utf-8 -*-
# 원본 악보 이미지에서 기타 '음표 오선'(TAB 바로 위 5선)만 제거하고
# 코드/멜로디 오선/가사/TAB은 픽셀 그대로 유지해 재조판한다.
import sys
import numpy as np
from PIL import Image, ImageDraw

def load_gray(path):
    im = Image.open(path).convert("RGB")
    arr = np.asarray(im)
    gray = arr.mean(axis=2)
    return im, gray

def find_staff_clusters(gray):
    """수평으로 긴 검은 줄(오선/탭선) row 위치를 찾고 클러스터로 묶는다."""
    h, w = gray.shape
    dark = (gray < 140)
    rowcount = dark.sum(axis=1)
    line_rows = np.where(rowcount > 0.55 * w)[0]
    # 연속 row 묶기 -> 개별 선
    lines = []
    for r in line_rows:
        if lines and r - lines[-1][-1] <= 1:
            lines[-1].append(r)
        else:
            lines.append([r])
    centers = [int(np.mean(l)) for l in lines]
    # 선들을 간격으로 클러스터링 (한 보표 내 선 간격은 작다)
    clusters = []
    for c in centers:
        if clusters and c - clusters[-1][-1] <= 12:
            clusters[-1].append(c)
        else:
            clusters.append([c])
    out = []
    for cl in clusters:
        out.append({"lines": cl, "n": len(cl), "top": cl[0], "bot": cl[-1]})
    return out

def band_expand(gray, top, bot, up_limit, down_limit):
    """보표 클러스터를 위아래로 확장: 잉크가 이어진 구간(빔/기둥/기호) 포함,
    거의 흰 row를 만나면 멈춤."""
    h, w = gray.shape
    dark = (gray < 160)
    rowcount = dark.sum(axis=1)
    t = top
    while t - 1 > up_limit and rowcount[t - 1] > 2:
        t -= 1
    b = bot
    while b + 1 < down_limit and rowcount[b + 1] > 2:
        b += 1
    return t, b

def analyze(path):
    im, gray = load_gray(path)
    h, w = gray.shape
    clusters = find_staff_clusters(gray)
    # TAB(6선) 앞의 5선 보표 = 제거 대상
    removes = []
    for i, cl in enumerate(clusters):
        if cl["n"] >= 6:  # TAB
            # 바로 앞 클러스터가 5선이면 제거 대상
            if i > 0 and clusters[i - 1]["n"] == 5:
                prev = clusters[i - 1]
                up_limit = clusters[i - 2]["bot"] + 3 if i >= 2 else 0
                t, b = band_expand(gray, prev["top"], prev["bot"], up_limit, cl["top"] - 3)
                removes.append((t, b))
    return im, clusters, removes

def debug_draw(path, out):
    im, clusters, removes = analyze(path)
    d = ImageDraw.Draw(im)
    for cl in clusters:
        color = (0, 160, 0) if cl["n"] >= 6 else (0, 0, 255)
        d.rectangle([0, cl["top"], im.size[0] - 1, cl["bot"]], outline=color)
        d.text((2, cl["top"] - 8), str(cl["n"]), fill=color)
    for t, b in removes:
        d.rectangle([0, t, im.size[0] - 1, b], outline=(255, 0, 0), width=2)
    im.save(out)
    print(path, "clusters:", [(c["n"], c["top"], c["bot"]) for c in clusters])
    print("  removes:", removes)

if __name__ == "__main__":
    for n in range(1, 6):
        debug_draw(f"/home/user/Nextswing/{n}.PNG",
                   f"/tmp/claude-0/-home-user-Nextswing/9a4ae754-881c-5e76-a20b-08c510c7ffc4/scratchpad/dbg{n}.png")
