# -*- coding: utf-8 -*-
# "나의 어릴 적 이야기" — 코드 + 가사 + TAB 압축 악보 생성기
# 사용자가 제공한 원본 악보(6페이지)를 기준으로 오선 음표를 제거하고
# 코드/가사/기타 TAB만 남긴 버전을 HTML로 만든다.

import unicodedata

# 코드 폼: (베이스현 인덱스, 베이스 프렛, [(현, 프렛) 아르페지오 고음부 g->b->e])
# 현 인덱스: 0=e(1번줄) 1=B 2=G 3=D 4=A 5=E(6번줄)
SHAPES = {
    "G":       (5, 3, [(2, 0), (1, 0), (0, 3)]),
    "D/F#":    (5, 2, [(2, 2), (1, 3), (0, 2)]),
    "Em":      (5, 0, [(2, 0), (1, 0), (0, 0)]),
    "Bm/D":    (3, 0, [(2, 4), (1, 3), (0, 2)]),
    "G/D":     (3, 0, [(2, 0), (1, 0), (0, 3)]),
    "C":       (4, 3, [(2, 0), (1, 1), (0, 0)]),
    "D":       (3, 0, [(2, 2), (1, 3), (0, 2)]),
    "D7":      (3, 0, [(2, 2), (1, 1), (0, 2)]),
    "D7sus4":  (3, 0, [(2, 2), (1, 1), (0, 3)]),
    "Am":      (4, 0, [(2, 2), (1, 1), (0, 0)]),
    "Gsus4":   (5, 3, [(2, 0), (1, 1), (0, 3)]),
    "G7":      (5, 3, [(2, 0), (1, 0), (0, 1)]),
    "D#dim7":  (3, 1, [(2, 2), (1, 1), (0, 2)]),
    "C#m7b5":  (4, 4, [(3, 2), (2, 0), (1, 0)]),
    "C#dim7":  (4, 4, [(3, 2), (1, 2), (0, 0)]),
}
LABEL = {"C#m7b5": "C#m7(b5)"}

# 마디 데이터: (마디번호, [코드들], 가사)
MEASURES = [
    (1,  ["C", "D", "D#dim7"], ""),
    (2,  ["Em", "Bm/D", "C#m7b5"], ""),
    (3,  ["Am"], ""),
    (4,  ["Am"], ""),
    (5,  ["D7"], "어느"),
    (6,  ["G", "D/F#"], "날 갑자기 생각나"),
    (7,  ["Em", "Bm/D"], "내 이름 부르시던"),
    (8,  ["C", "G"], "목소리"),
    (9,  ["Am", "D7sus4", "D7"], "지금"),
    (10, ["C", "G", "D/F#"], "도 내 귓가에"),
    (11, ["Em", "G/D"], "울리는데"),
    (12, ["C", "D"], "아무도 기억 못하나"),
    (13, ["G", "Gsus4", "G"], "보다,  사진"),
    (14, ["G", "D/F#"], "속 우리 바라보니"),
    (15, ["Em", "G/D"], "그때는"),
    (16, ["C", "G"], "아주 평범했구나"),
    (17, ["Am", "D7sus4", "D7"], "생각"),
    (18, ["C", "G", "D/F#"], "만 해도 내 맘"),
    (19, ["Em", "G/D"], "이렇게 아픈데"),
    (20, ["C", "D"], "아무도 기억 못하나"),
    (21, ["G", "G7"], "보다,  내 얘"),
    (22, ["C", "D"], "기만 듣고 가세요"),
    (23, ["Em", "Bm/D"], "한 번도"),
    (24, ["Am", "D"], "용기 내지 못한"),
    (25, ["G", "G7"], "평생"),
    (26, ["C", "D", "D#dim7"], "을 나 기억할게요"),
    (27, ["Em", "Bm/D"], ""),
    (28, ["Am"], "내 말 듣고 가세요"),
    (29, ["D7sus4", "D7"], "저기"),
    (30, ["G", "D/F#"], "요 아저씨 잠시만요"),
    (31, ["Em", "Bm/D"], ""),
    (32, ["C", "G"], "사진 좀 같이 찍어 주세"),
    (33, ["Am", "D7sus4", "D7"], "요,  언젠"),
    (34, ["C", "G", "D/F#"], "가 당신 얼굴"),
    (35, ["Em", "G/D"], "잊어버릴까"),
    (36, ["C", "D"], "나는요 여기 남길랍"),
    (37, ["G", "Gsus4", "G"], "니다"),
    (38, ["G", "D/F#"], "(간주)"),
    (39, ["Em", "G/D"], ""),
    (40, ["C", "G"], ""),
    (41, ["Am", "D7sus4", "D7"], ""),
    (42, ["C", "G", "D/F#"], ""),
    (43, ["Em", "G/D"], ""),
    (44, ["C", "D"], ""),
    (45, ["G", "Gsus4", "G"], "어느"),
    (46, ["G", "D/F#"], "날 갑자기 생각이나"),
    (47, ["Em", "G/D"], "손잡고 거닐던"),
    (48, ["C", "G"], "그 골목길"),
    (49, ["Am", "D7sus4", "D7"], "하나"),
    (50, ["C", "G", "D/F#"], "둘 셋 걸으며"),
    (51, ["Em", "G/D"], "모두 좋았는데"),
    (52, ["C", "D"], "아무도 기억 못하나"),
    (53, ["G", "G7"], "보다,  내 얘"),
    (54, ["C", "D"], "기만 듣고 가세요"),
    (55, ["Em", "Bm/D"], "한 번도"),
    (56, ["Am", "D"], "용기 내지 못한"),
    (57, ["G"], "평생"),
    (58, ["C", "D", "D#dim7"], "을 나 기억할게요"),
    (59, ["Em", "Bm/D", "C#dim7"], ""),
    (60, ["Am"], "내 말 듣고 가세요"),
    (61, ["D7sus4", "D7"], "저기"),
    (62, ["G", "D/F#"], "요 아저씨 잠시만요"),
    (63, ["Em", "G/D"], ""),
    (64, ["C", "G"], "사진 좀 같이 찍어 주세"),
    (65, ["Am", "D7sus4", "D7"], "요,  언젠"),
    (66, ["C", "G", "D/F#"], "가 당신 얼굴"),
    (67, ["Em", "G/D"], "잊어버릴까"),
    (68, ["C", "D"], "나는요 여기 남길랍"),
    (69, ["G", "Gsus4", "G"], "니다,  내가"),
    (70, ["C", "D"], "요 평생 기억할"),
    (71, ["G", "Gsus4", "G"], "게요"),
    (72, ["C", "D7"], ""),
    (73, ["D7"], "(Gt.2: 1번줄 10-12 슬라이드)"),
    (74, ["G", "D/F#"], "(아웃트로)"),
    (75, ["Em", "G/D"], ""),
    (76, ["C", "D7"], "rit."),
    (77, ["G"], "(끝)"),
]

STR_NAMES = ["e", "B", "G", "D", "A", "E"]
COL_W = 3  # 한 칼럼당 문자 수

def dwidth(s):
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)

def pad_to(s, w):
    d = dwidth(s)
    return s + " " * max(0, w - d)

def chord_cell(name, n_chords):
    """코드 하나의 칼럼 리스트. 각 칼럼은 {현: 프렛} dict."""
    bass_s, bass_f, treb = SHAPES[name]
    cols = []
    if n_chords >= 3:  # 짧은 코드: 베이스 + 화음 스택
        cols.append({bass_s: bass_f})
        cols.append({s: f for s, f in treb})
    else:
        cols.append({bass_s: bass_f})
        for s, f in treb:
            cols.append({s: f})
        if n_chords == 1:  # 온마디 코드: 패턴 반복
            cols.append({bass_s: bass_f})
            for s, f in treb:
                cols.append({s: f})
    return cols

def render_system(measures):
    chord_line, lyric_line = "", ""
    tab_lines = [STR_NAMES[i] + "|" for i in range(6)]
    for num, chords, lyric in measures:
        m_cols, labels = [], []  # labels: (col_index, label)
        for ch in chords:
            labels.append((len(m_cols), LABEL.get(ch, ch)))
            m_cols.extend(chord_cell(ch, len(chords)))
        width = len(m_cols) * COL_W
        # 코드 라인
        cl = ""
        for idx, lab in labels:
            pos = idx * COL_W
            if dwidth(cl) < pos:
                cl += " " * (pos - dwidth(cl))
            cl += lab + " "
        chord_line += pad_to(cl, width) + " "
        lyric_line += pad_to(" " + lyric, width) + " "
        for i in range(6):
            row = ""
            for col in m_cols:
                row += (str(col[i]) if i in col else "-").ljust(COL_W, "-")
            tab_lines[i] += row + "|"
    return chord_line, lyric_line, tab_lines

def main():
    systems, i = [], 0
    while i < len(MEASURES):
        n = 4
        # 시스템당 총 칼럼 수 제한(3코드 마디가 많으면 폭 증가 방지)
        systems.append(MEASURES[i:i + n])
        i += n

    blocks = []
    for sys_measures in systems:
        chord_line, lyric_line, tab_lines = render_system(sys_measures)
        first = sys_measures[0][0]
        head = f"{first:>2}"
        lines = [("   " + chord_line).rstrip(),
                 ("   " + lyric_line).rstrip()]
        for j, tl in enumerate(tab_lines):
            prefix = head + " " if j == 0 else "   "
            lines.append(prefix + tl)
        blocks.append("\n".join(lines))

    intro_note = ("Gt.2 (인트로 멜로디, 2번줄): 8→10 s, 10→12 s, 12-10-8 … 8→10 s, 10  "
                  "(마디 1–5, 간주에서도 동일)")

    body = "\n\n".join(blocks)
    html = f"""<meta charset="utf-8">
<style>
@page {{ size: A4; margin: 9mm; }}
body {{ font-family: 'DejaVu Sans Mono', monospace; }}
h1 {{ font: bold 15px sans-serif; margin: 0 0 2px; text-align: center; }}
.meta {{ font: 11px sans-serif; text-align: center; margin-bottom: 6px; }}
.note {{ font: 10px sans-serif; color: #444; margin-bottom: 8px; }}
pre {{ font-size: 8.6px; line-height: 1.25; margin: 0; }}
.block {{ page-break-inside: avoid; margin-bottom: 7px; }}
</style>
<h1>나의 어릴 적 이야기 — Guitar TAB (코드+가사+TAB 압축판)</h1>
<div class="meta">♩= 66 &nbsp;|&nbsp; Key: G &nbsp;|&nbsp; Capo 없음 &nbsp;|&nbsp; 원본: Guitar 1&amp;2 편곡 6p → 압축</div>
<div class="note">{intro_note}<br>
※ TAB은 원본 악보의 오픈 코드 폼 기반 아르페지오(베이스→3→2→1번줄) 패턴. 세부 리듬 변주는 원본 참조.</div>
"""
    for b in blocks:
        html += f'<div class="block"><pre>{b}</pre></div>\n'

    with open("/home/user/Nextswing/score/나의_어릴적_이야기_tab.html", "w") as f:
        f.write(html)
    with open("/home/user/Nextswing/score/나의_어릴적_이야기_tab.txt", "w") as f:
        f.write("나의 어릴 적 이야기 — 코드+가사+TAB\n\n" + intro_note + "\n\n" + body + "\n")
    print("systems:", len(systems))

main()
