# -*- coding: utf-8 -*-
# 제거 밴드를 실제로 오려내고, 남은 밴드를 이어붙여 페이지를 재구성한다.
import numpy as np
from PIL import Image
from crop_tab import analyze

SCRATCH = "/tmp/claude-0/-home-user-Nextswing/9a4ae754-881c-5e76-a20b-08c510c7ffc4/scratchpad"
TARGET_W = 1600

def enhance(img):
    """약한 선명화 + 배경만 흰색 정리 (잉크 굵기/진하기는 원본 그대로)."""
    from PIL import ImageFilter
    img = img.filter(ImageFilter.UnsharpMask(radius=1.0, percent=55, threshold=3))
    arr = np.asarray(img).astype(np.float32)
    lum = arr.mean(axis=2, keepdims=True)
    out = np.where(lum >= 205, 255.0, arr)  # 밝은 배경/노이즈만 흰색으로
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

def remove_junk_blocks(strip):
    """시스템 사이의 잡동사니(워터마크 footer, 제목, 페이지 헤더) 삭제.
    기준: 흰 구간으로 분리된 낮은 블록 중 가로 분포가 좁은 것."""
    gray = strip.mean(axis=2)
    w = gray.shape[1]
    is_white = ((gray < 200).sum(axis=1) <= 10)
    n = len(strip)
    remove = np.zeros(n, dtype=bool)
    # 블록 나누기: 12row 이상 흰 구간이 경계
    blocks, i = [], 0
    while i < n:
        if not is_white[i]:
            j = i
            gap = 0
            while j < n and gap < 12:
                if is_white[j]:
                    gap += 1
                else:
                    gap = 0
                j += 1
            blocks.append((i, j - gap))
            i = j
        else:
            i += 1
    for bi, (a, b) in enumerate(blocks):
        h = b - a
        if h >= 70 or bi == 0:  # 시스템 블록/문서 첫 블록(템포)은 유지
            continue
        dark = gray[a:b] < 160
        bins = 12
        cov = sum(dark[:, w * k // bins:w * (k + 1) // bins].any() for k in range(bins))
        if cov <= bins * 0.5:
            remove[a:b] = True
    # 블록 하단(마지막 보표선 아래) 오른쪽에 붙은 footer(akbobada.com) 제거
    dark_all = gray < 160
    linerow = dark_all.sum(axis=1) > 0.5 * w
    dc = dark_all.sum(axis=1)
    for a, b in blocks:
        lines = [r for r in range(a, b) if linerow[r]]
        if not lines:
            continue
        last = lines[-1]
        r = last + 3
        while r < b:
            if dc[r] > 10:
                s = r
                while r < b and dc[r] > 10:
                    r += 1
                cols = np.where(dark_all[s:r].any(axis=0))[0]
                if len(cols) and cols.min() > 0.55 * w:
                    remove[s:r] = True
            else:
                r += 1
    return strip[~remove]

def collapse_white(strip, max_gap=12, cut_min_run=26):
    """연속 흰 row 구간을 max_gap으로 압축.
    반환: (압축 strip, 페이지 분할 허용 row 마스크) — 원래 길었던 흰 구간만 분할 지점."""
    gray = strip.mean(axis=2)
    dark = (gray < 200).sum(axis=1)
    is_white = dark <= 10
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
    full = remove_junk_blocks(full)
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

    # A4 실치수 기준 페이지 분할: 원래 시스템 사이였던 긴 흰 구간에서만 자른다
    side_pad, top_pad = 40, 30
    canvas_w = TARGET_W + side_pad * 2
    canvas_h = int(canvas_w * 297 / 210)  # A4 비율
    page_h = canvas_h - top_pad * 2
    pages_out, y = [], 0
    H = len(full)
    while y < H:
        end = min(y + page_h, H)
        if end < H:
            # 페이지 안에 들어오는 마지막 분할 가능 지점까지 후퇴 (단 중간 절대 금지)
            cut = None
            for k in range(end, y + 1, -1):
                if cuttable[k]:
                    cut = k
                    break
            end = cut if cut is not None else end
        pages_out.append(full[y:end])
        y = end
    outs = []
    for i, pg in enumerate(pages_out, 1):
        page = np.full((canvas_h, canvas_w, 3), 255, dtype=np.uint8)
        page[top_pad:top_pad + len(pg), side_pad:side_pad + TARGET_W] = pg[:page_h]
        out = Image.fromarray(page)
        fn = f"{SCRATCH}/out_page{i}.png"
        out.save(fn)
        outs.append(out)
        print("page", i, "content rows:", len(pg))
    # A4(210mm) 폭에 캔버스 폭이 정확히 맞도록 dpi 설정 -> 인쇄 시 잘림 없음
    dpi = canvas_w / (210 / 25.4)
    outs[0].save("/home/user/Nextswing/score/나의_어릴적_이야기_탭전용.pdf",
                 save_all=True, append_images=outs[1:], resolution=dpi)
    print("pages:", len(outs), "dpi:", round(dpi, 1))

if __name__ == "__main__":
    import sys
    sys.path.insert(0, "/home/user/Nextswing/score")
    main([f"/home/user/Nextswing/{n}.PNG" for n in range(1, 6)])
