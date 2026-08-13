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

def extend_over_chord_row(gray, t, staff_top, up_limit):
    """제거 밴드 위쪽에 붙은 '기타용 코드 글자 줄'까지 밴드를 확장.
    가사 줄(음절 뭉치가 많고 폭넓게 분포)은 절대 삼키지 않는다."""
    h, w = gray.shape
    dark = (gray < 160)
    rc = dark.sum(axis=1)
    if t < staff_top - 45:  # 이미 충분히 위까지 확장됨(코드 줄 포함 추정)
        return t
    # 위로 흰 구간(<=16) 건너뛰고 텍스트 밴드 찾기
    r, gap = t - 1, 0
    while r > up_limit and rc[r] <= 2 and gap <= 16:
        r -= 1
        gap += 1
    if r <= up_limit or rc[r] <= 2:
        return t
    e = r
    s = e
    while s - 1 > up_limit and rc[s - 1] > 2:
        s -= 1
    if e - s > 34:  # 텍스트 줄 높이가 아님
        return t
    cols = np.where(dark[s:e + 1].any(axis=0))[0]
    if len(cols) == 0:
        return t
    coverage = len(cols) / w
    clumps, prev = 1, cols[0]
    for c in cols[1:]:
        if c - prev > 15:
            clumps += 1
        prev = c
    if coverage < 0.30 and clumps <= 7:  # 코드 라벨 몇 개 = 코드 줄
        return max(up_limit + 1, s - 2)
    return t

def analyze(path):
    im, gray = load_gray(path)
    h, w = gray.shape
    clusters = find_staff_clusters(gray)
    # TAB(6선) 앞의 5선 보표 = 제거 대상
    removes = []
    for i, cl in enumerate(clusters):
        if cl["n"] >= 6:  # TAB
            # 앞쪽으로 잡선(빔 등 5선 미만 클러스터)은 건너뛰고 5선 보표를 찾는다
            j = i - 1
            while j >= 0 and clusters[j]["n"] < 5:
                j -= 1
            if j >= 0 and clusters[j]["n"] == 5:
                prev = clusters[j]
                up_limit = clusters[j - 1]["bot"] + 3 if j >= 1 else 0
                t, b = band_expand(gray, prev["top"], prev["bot"], up_limit, cl["top"] - 3)
                t = extend_over_chord_row(gray, t, prev["top"], up_limit)
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
