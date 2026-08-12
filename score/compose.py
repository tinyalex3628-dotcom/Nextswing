# -*- coding: utf-8 -*-
# 제거 밴드를 실제로 오려내고, 남은 밴드를 이어붙여 페이지를 재구성한다.
import numpy as np
from PIL import Image
from crop_tab import analyze

SCRATCH = "/tmp/claude-0/-home-user-Nextswing/9a4ae754-881c-5e76-a20b-08c510c7ffc4/scratchpad"
TARGET_W = 1600

def enhance(img):
    """확대 후 선명화 + 배경/잉크 대비 보정 (숫자 모양은 그대로)."""
    from PIL import ImageFilter
    img = img.filter(ImageFilter.UnsharpMask(radius=2.2, percent=170, threshold=2))
    arr = np.asarray(img).astype(np.float32)
    lum = arr.mean(axis=2, keepdims=True)
    # 배경(밝은 픽셀) -> 완전한 흰색, 잉크는 어둡게, 중간은 선형 스트레치
    lo, hi = 70.0, 200.0
    scale = np.clip((lum - lo) / (hi - lo), 0.0, 1.0)
    out = arr * (0.55 + 0.45 * (1 - scale))  # 어두운 픽셀 더 진하게
    out = np.where(lum >= hi, 255.0, out)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))

def page_strip(path):
    im, clusters, removes = analyze(path)
    w, h = im.size
    arr = np.asarray(im.convert("RGB"))
    keep_rows = np.ones(h, dtype=bool)
    for t, b in removes:
        keep_rows[t:b + 1] = False
    strip = arr[keep_rows]
    return strip, w

def drop_black_bands(strip):
    """캡처 경계의 전폭 검은 띠 제거."""
    gray = strip.mean(axis=2)
    frac = (gray < 120).mean(axis=1)
    bad = frac > 0.75
    # 오선(1~2px)은 남기고, 5px 이상 이어지는 두꺼운 띠만 제거 (±2px 여유)
    remove = np.zeros(len(strip), dtype=bool)
    i, n = 0, len(strip)
    while i < n:
        if bad[i]:
            j = i
            while j < n and bad[j]:
                j += 1
            if j - i >= 5:
                remove[max(0, i - 2):min(n, j + 2)] = True
            i = j
        else:
            i += 1
    return strip[~remove]

def collapse_white(strip, max_gap=12, cut_min_run=26):
    """연속 흰 row 구간을 max_gap으로 압축.
    반환: (압축 strip, 페이지 분할 허용 row 마스크) — 원래 길었던 흰 구간만 분할 지점."""
    gray = strip.mean(axis=2)
    dark = (gray < 200).sum(axis=1)
    is_white = dark <= 1
    n = len(strip)
    keep = np.ones(n, dtype=bool)
    # 흰 run 찾기
    runs = []
    i = 0
    while i < n:
        if is_white[i]:
            j = i
            while j < n and is_white[j]:
                j += 1
            runs.append((i, j))
            i = j
        else:
            i += 1
    cuttable = np.zeros(n, dtype=bool)
    for a, b in runs:
        if b - a > max_gap:
            keep[a + max_gap:b] = False
        if b - a >= cut_min_run:
            cuttable[a:a + max_gap] = True
    return strip[keep], cuttable[keep]

def main(pages):
    strips = []
    for p in pages:
        strip, w = page_strip(p)
        img = Image.fromarray(strip)
        if w != TARGET_W:
            img = img.resize((TARGET_W, int(img.size[1] * TARGET_W / w)), Image.LANCZOS)
        img = enhance(img)
        strips.append(np.asarray(img))
    full = np.concatenate(strips, axis=0)
    full = drop_black_bands(full)
    full, cuttable = collapse_white(full, max_gap=14)
    # 얇은 블록(코드 글자/헤더 줄)은 다음 블록과 분리 금지:
    # cuttable 갭 사이 콘텐츠 블록 높이가 작으면 그 '뒤' 갭을 잘라내기 금지로 변경
    idx = np.where(cuttable)[0]
    gaps = []
    for k in idx:
        if not gaps or k > gaps[-1][1] + 1:
            gaps.append([k, k])
        else:
            gaps[-1][1] = k
    for gi in range(1, len(gaps)):
        block_h = gaps[gi][0] - gaps[gi - 1][1]
        if block_h < 60:
            cuttable[gaps[gi][0]:gaps[gi][1] + 1] = False

    # A4 비율로 페이지 분할: 원래 시스템 사이였던 긴 흰 구간에서만 자른다
    page_h = int(TARGET_W * 1.414 * 1.08)  # 여유
    pages_out, y = [], 0
    H = len(full)
    while y < H:
        end = min(y + page_h, H)
        if end < H:
            cut = end
            for k in range(end, max(y + page_h // 2, y + 1), -1):
                if cuttable[k]:
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
