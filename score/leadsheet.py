# -*- coding: utf-8 -*-
# 원본 악보에서 '가사 줄' 이미지를 오려오고, 그 위에 이조된 코드를 얹어
# 코드+가사 리드시트를 만든다. (가사는 원본 픽셀 그대로 = 오타 위험 없음)
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import sys
sys.path.insert(0, "/home/user/Nextswing/score")
from crop_tab import find_staff_clusters

OUT_W = 1600
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
KFONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"

SHARP = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
FLAT  = ["C","Db","D","Eb","E","F","Gb","G","Ab","A","Bb","B"]
IDX = {n:i for i,n in enumerate(SHARP)}
IDX.update({n:i for i,n in enumerate(FLAT)})

def trans(note, delta, flats=False):
    i = ((IDX[note] + delta) % 12 + 12) % 12
    return (FLAT if flats else SHARP)[i]

def trans_chord(c, delta):
    import re
    m = re.match(r"^([A-G][#b]?)?([^/]*)(?:/([A-G][#b]?))?$", c)
    root, suf, bass = m.group(1), m.group(2) or "", m.group(3)
    flats = (root and "b" in root) or (bass and "b" in bass)
    out = (trans(root, delta, flats) + suf) if root else suf
    if bass:
        out = (out if root else "") + "/" + trans(bass, delta, flats)
    return out

# 마디별 코드 (원키 C)
MEASURES = {
 1:["C","G/B"],2:["Am7","/G"],3:["FM7"],4:["G"],
 5:["C"],6:["G/B"],7:["Am7"],8:["Em7"],9:["F"],10:["C"],11:["D7"],12:["G7"],
 13:["C"],14:["G/B"],15:["Am7"],16:["Em7"],17:["F"],18:["C"],19:["D7"],20:["G7"],
 21:["C","G/B"],22:["Am7","/G"],23:["F","C/E"],24:["Dm7","G"],
 25:["C","G/B"],26:["Am7","/G"],27:["F"],28:["Ab","G"],
 29:["C"],30:["G/B"],31:["Am7"],32:["Em7"],33:["F"],34:["C"],35:["D7"],36:["G7"],
 37:["C"],38:["G/B"],39:["Am7"],40:["Em7"],41:["F"],42:["C"],43:["D7"],44:["G7"],
 45:["C","G/B"],46:["Am7","Gm7","C7"],47:["F","C/E"],48:["Dm7","G"],
 49:["C","G/B"],50:["Am7","G"],51:["C","FM7"],52:["Em7","Am7","Dm7","Fm"],
}
MARKS = {21:"𝄋", 29:"[1.", 45:"[2.", 28:"Fine", 52:"D.S. al Fine"}

def systems_of(path):
    im = Image.open(path).convert("RGB")
    arr = np.asarray(im)
    gray = arr.mean(axis=2)
    clusters = [c for c in find_staff_clusters(gray) if c["n"] >= 5]
    out = []
    i = 0
    while i + 2 < len(clusters) or (i + 2 <= len(clusters) - 1):
        if (clusters[i]["n"] == 5 and clusters[i+1]["n"] == 5 and clusters[i+2]["n"] >= 6):
            out.append((clusters[i], clusters[i+1], clusters[i+2]))
            i += 3
        else:
            i += 1
    return im, arr, gray, out

def barlines(gray, top, bot):
    """멜로디 보표 구간의 세로 마디선 x좌표."""
    h = bot - top
    seg = gray[top:bot+1]
    dark = (seg < 130)
    colfrac = dark.mean(axis=0)
    xs = np.where(colfrac > 0.85)[0]
    lines = []
    for x in xs:
        if lines and x - lines[-1][-1] <= 3:
            lines[-1].append(x)
        else:
            lines.append([x])
    return [int(np.mean(l)) for l in lines]

def lyric_band(gray, mel_bot, not_top):
    """멜로디 아래~기타보표 위 구간에서 '가사 줄' 밴드만 선별.
    음표 꼬리/빔 잔재(뭉치 적음)와 가사(음절 뭉치 많음)를 구분한다."""
    dark = gray < 190
    rc = dark.sum(axis=1)
    a, b = mel_bot + 2, not_top - 3
    bands, r = [], a
    while r < b:
        if rc[r] > 3:
            s = r
            gap = 0
            while r < b and gap < 3:
                gap = gap + 1 if rc[r] <= 3 else 0
                r += 1
            bands.append((s, r - gap))
        else:
            r += 1
    best, best_cl = None, 0
    for s, e in bands:
        if e - s > 45:
            continue
        cols = np.where(dark[s:e + 1].any(axis=0))[0]
        if len(cols) == 0:
            continue
        clumps, prev = 1, cols[0]
        for c in cols[1:]:
            if c - prev > 12:
                clumps += 1
            prev = c
        if clumps >= best_cl:  # 동률이면 아래쪽(가사) 우선
            best, best_cl = (s, e), clumps
    if best is None or best_cl < 6:
        return None
    # 받침/윗부분 잘림 방지: 옅은 잉크까지 포함해 위아래로 확장 + 넉넉한 패딩
    loose = (gray < 210).sum(axis=1) > 0
    s, e = best
    for _ in range(3):
        if s - 1 > mel_bot and loose[s - 1]:
            s -= 1
    for _ in range(3):
        if e + 1 < not_top - 4 and loose[e + 1]:
            e += 1
    return max(mel_bot + 1, s - 2), min(not_top - 4, e + 3)

def make(delta, out_pdf, title_note):
    files = [f"/home/user/Nextswing/10-{n}.PNG" for n in range(1, 7)]
    font = ImageFont.truetype(FONT, 30)
    small = ImageFont.truetype(FONT, 22)
    try:
        kfont = ImageFont.truetype(KFONT, 24)
    except Exception:
        kfont = small
    blocks = []  # (PIL Image) 시스템당: 코드줄 + 가사줄(이미지)
    measure_no = 1
    for path in files:
        im, arr, gray, systems = systems_of(path)
        w = im.size[0]
        scale = OUT_W / w
        for mel, notn, tab in systems:
            # 이 곡은 모든 단이 4마디: 보표 가로 범위를 균등 분할
            rowseg = (gray[mel["top"]:mel["bot"] + 1] < 130)
            cols = np.where(rowseg.any(axis=0))[0]
            x_l, x_r = int(cols.min()), int(cols.max())
            music_start = x_l + int((x_r - x_l) * 0.075)  # 음자리표/박자표 이후
            nbars = 4
            bl = [music_start + int((x_r - music_start) * k / nbars) for k in range(nbars + 1)]
            band = lyric_band(gray, mel["bot"], notn["top"])
            # 코드 줄 캔버스
            ch_h = 64
            canvas_parts = []
            chord_img = Image.new("RGB", (OUT_W, ch_h), "white")
            d = ImageDraw.Draw(chord_img)
            for k in range(nbars):
                m = measure_no + k
                chords = MEASURES.get(m, [])
                x0, x1 = bl[k] * scale, bl[k+1] * scale
                if m in MARKS:
                    mark = MARKS[m]
                    mx = x1 - 150 if ("Fine" in mark or "D.S." in mark) else x0 - 26
                    d.text((max(0, mx), 2), mark, font=small, fill=(150, 95, 20))
                f = font if len(chords) <= 2 else ImageFont.truetype(FONT, 24 if len(chords) == 3 else 21)
                for j, c in enumerate(chords):
                    t = trans_chord(c, delta)
                    x = x0 + 14 + (x1 - x0 - 24) * (j / max(1, len(chords)))
                    d.text((x, 30), t, font=f, fill=(20, 20, 20))
            canvas_parts.append(chord_img)
            if band:
                a, b = band
                ly = Image.fromarray(arr[a:b+1]).resize(
                    (OUT_W, int((b + 1 - a) * scale)), Image.LANCZOS)
                # 배경 정리 + 왼쪽 음자리표 꼬리 영역 지우기
                la = np.asarray(ly).astype(np.float32)
                lum = la.mean(axis=2, keepdims=True)
                la = np.where(lum >= 205, 255.0, la)
                la[:, :int((x_l + (x_r - x_l) * 0.045) * scale)] = 255.0
                canvas_parts.append(Image.fromarray(la.astype(np.uint8)))
            else:
                inst = Image.new("RGB", (OUT_W, 30), "white")
                ImageDraw.Draw(inst).text((20, 2), "(연주)", font=kfont, fill=(120, 120, 120))
                canvas_parts.append(inst)
            total_h = sum(p.size[1] for p in canvas_parts) + 16
            block = Image.new("RGB", (OUT_W, total_h), "white")
            y = 0
            for p in canvas_parts:
                block.paste(p, (0, y))
                y += p.size[1]
            blocks.append(block)
            measure_no += nbars
    # 헤더
    head = Image.new("RGB", (OUT_W, 100), "white")
    d = ImageDraw.Draw(head)
    try:
        ktitle = ImageFont.truetype(KFONT, 36)
        ksub = ImageFont.truetype(KFONT, 22)
        d.text((0, 0), title_note, font=ktitle, fill=(20, 20, 20))
        d.text((0, 52), "원키 C에서 2키 내림(실음 B♭) · 카포 3프렛 → G폼으로 연주",
               font=ksub, fill=(120, 120, 120))
    except Exception:
        d.text((0, 0), "Lead Sheet  |  Capo 3 = G form  |  sounding Bb (-2)",
               font=font, fill=(20, 20, 20))
    blocks.insert(0, head)
    # 페이지 조립 (A4)
    side, top_pad = 70, 40
    cw = OUT_W + side * 2
    chh = int(cw * 297 / 210)
    pages, cur, y = [], Image.new("RGB", (cw, chh), "white"), top_pad
    for b in blocks:
        if y + b.size[1] > chh - top_pad:
            pages.append(cur)
            cur, y = Image.new("RGB", (cw, chh), "white"), top_pad
        cur.paste(b, (side, y))
        y += b.size[1]
    pages.append(cur)
    dpi = cw / (210 / 25.4)
    pages[0].save(out_pdf, save_all=True, append_images=pages[1:], resolution=dpi)
    for i, p in enumerate(pages, 1):
        p.save(f"/tmp/claude-0/-home-user-Nextswing/9a4ae754-881c-5e76-a20b-08c510c7ffc4/scratchpad/lead{i}.png")
    print("pages:", len(pages), "measures:", measure_no - 1)

if __name__ == "__main__":
    make(-5, "/home/user/Nextswing/score/리드시트_카포3.pdf",
         "내 기억 속에 남아 있는 그대 모습은")
