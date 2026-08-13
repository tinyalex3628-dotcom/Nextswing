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

def page_strip(path, first=False):
    im, clusters, removes = analyze(path)
    w, h = im.size
    arr = np.asarray(im.convert("RGB"))
    keep_rows = np.ones(h, dtype=bool)
    for t, b in removes:
        keep_rows[t:b + 1] = False
    if clusters:
        gray = arr.mean(axis=2)
        rc = (gray < 160).sum(axis=1)
        # 위: 첫 보표 위의 코드 줄(+볼타 등 1개 더)까지만 유지 → 헤더/제목 제거
        top = clusters[0]["top"]
        r, gap = top - 1, 0
        while r >= 0 and rc[r] <= 2 and gap <= 45:
            r -= 1
            gap += 1
        if r >= 0 and rc[r] > 2:  # 코드 줄 발견 (볼타 등은 보통 코드 줄과 연속)
            while r - 1 >= 0 and rc[r - 1] > 2:
                r -= 1
            top = r
            # 위에 붙은 밴드가 '분리된 코드 줄'처럼 보일 때만 추가 포함.
            # 코드 줄: 라벨 뭉치 4개 이상 + 오른쪽까지 분포 / 헤더·제목: 뭉치 2~3개
            r2, gap2 = top - 1, 0
            while r2 >= 0 and rc[r2] <= 2 and gap2 <= 8:
                r2 -= 1
                gap2 += 1
            if r2 >= 0 and rc[r2] > 2 and gap2 <= 8:
                e2 = r2
                while r2 - 1 >= 0 and rc[r2 - 1] > 2:
                    r2 -= 1
                band = (gray[r2:e2 + 1] < 160)
                cols = np.where(band.any(axis=0))[0]
                if len(cols):
                    clumps, prev = 1, cols[0]
                    for c in cols[1:]:
                        if c - prev > 15:
                            clumps += 1
                        prev = c
                    if clumps >= 4 and cols.max() > 0.55 * w:
                        top = r2
        top = 0 if first else max(0, top - 4)
        # 아래: TAB에 붙은 리듬 기둥/빔(연속 잉크)을 먼저 포함
        bot = clusters[-1]["bot"]
        while bot + 1 < h and rc[bot + 1] > 2:
            bot += 1
        # 이어서 작은 기호(S, 페르마타)까지만 유지 → 조각 부스러기 제거
        r = bot + 1
        while r < h:
            if rc[r] <= 2:
                # 흰 구간 12 초과면 종료
                s = r
                while r < h and rc[r] <= 2:
                    r += 1
                if r - s > 12:
                    break
            else:
                s = r
                while r < h and rc[r] > 2:
                    r += 1
                band_h = r - s
                if band_h > 24 or (rc[s:r] > 0.4 * w).any():
                    break  # 보표 부스러기
                bot = r - 1
        bot = min(h - 1, bot + 4)
        keep_rows[:top] = False
        keep_rows[bot + 1:] = False
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

def main(pages, out_pdf="/home/user/Nextswing/score/나의_어릴적_이야기_탭전용.pdf",
         out_prefix="out_page"):
    strips = []
    for pi, p in enumerate(pages):
        strip, w = page_strip(p, first=(pi == 0))
        img = Image.fromarray(strip)
        if w != TARGET_W:
            img = img.resize((TARGET_W, int(img.size[1] * TARGET_W / w)), Image.LANCZOS)
        img = enhance(img)
        strips.append(np.asarray(img))
    # 조각(=시스템) 단위로 정리 후, 조각 사이에 고정 간격을 넣고 그 지점만 분할 허용
    SPACER = 18
    cleaned = []
    for s in strips:
        s = drop_black_bands(s)
        s = remove_junk_blocks(s)
        s, _ = collapse_white(s, max_gap=14)
        cleaned.append(s)
    parts, cut_parts = [], []
    spacer = np.full((SPACER, TARGET_W, 3), 255, dtype=np.uint8)
    for i, s in enumerate(cleaned):
        if i > 0:
            parts.append(spacer)
            cut_parts.append(np.ones(SPACER, dtype=bool))
        parts.append(s)
        cut_parts.append(np.zeros(len(s), dtype=bool))
    full = np.concatenate(parts, axis=0)
    cuttable = np.concatenate(cut_parts)

    # A4 실치수 기준 페이지 분할: 원래 시스템 사이였던 긴 흰 구간에서만 자른다
    side_pad, top_pad = 70, 30
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
        fn = f"{SCRATCH}/{out_prefix}{i}.png"
        out.save(fn)
        outs.append(out)
        print("page", i, "content rows:", len(pg))
    # A4(210mm) 폭에 캔버스 폭이 정확히 맞도록 dpi 설정 -> 인쇄 시 잘림 없음
    dpi = canvas_w / (210 / 25.4)
    outs[0].save(out_pdf,
                 save_all=True, append_images=outs[1:], resolution=dpi)
    print("pages:", len(outs), "dpi:", round(dpi, 1))

if __name__ == "__main__":
    import sys
    sys.path.insert(0, "/home/user/Nextswing/score")
    main([f"/home/user/Nextswing/{n}.PNG" for n in range(1, 6)])
