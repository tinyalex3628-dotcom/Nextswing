#!/usr/bin/env python3
"""
골프 유튜브 레슨 대본 — 인쇄용 HTML/PDF 빌드 스크립트

src/*.html 조각을 읽어서
  1) 편별 HTML + PDF  (pdf/01_....pdf)
  2) 전체 통합 HTML + PDF (pdf/골프레슨_대본_전체.pdf)
를 만든다.

사용법:  python3 build.py
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
OUT_HTML = ROOT / "html"
OUT_PDF = ROOT / "pdf"
CSS = (ROOT / "assets" / "print.css").read_text(encoding="utf-8")

CHROME_CANDIDATES = [
    "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
    "/opt/pw-browsers/chromium/chrome-linux/chrome",
    shutil.which("chromium") or "",
    shutil.which("chromium-browser") or "",
    shutil.which("google-chrome") or "",
]

PAGE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
{css}
</style>
</head>
<body>
<div class="sheet">
{body}
</div>
</body>
</html>
"""


def find_chrome() -> str:
    for c in CHROME_CANDIDATES:
        if c and Path(c).exists():
            return c
    sys.exit("Chromium 실행 파일을 찾지 못했습니다.")


def fragments() -> list[Path]:
    return sorted(p for p in SRC.glob("*.html"))


def title_of(fragment: str, fallback: str) -> str:
    m = re.search(r'<!--\s*TITLE:\s*(.+?)\s*-->', fragment)
    return m.group(1) if m else fallback


def write_page(path: Path, title: str, body: str) -> Path:
    path.write_text(PAGE.format(title=title, css=CSS, body=body), encoding="utf-8")
    return path


def to_pdf(chrome: str, html: Path, pdf: Path) -> None:
    pdf.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        chrome,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        "--no-pdf-header-footer",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=6000",
        f"--print-to-pdf={pdf}",
        html.resolve().as_uri(),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if not pdf.exists() or pdf.stat().st_size == 0:
        sys.exit(f"PDF 생성 실패: {pdf}\n{res.stderr[-2000:]}")


def main() -> None:
    chrome = find_chrome()
    OUT_HTML.mkdir(exist_ok=True)
    OUT_PDF.mkdir(exist_ok=True)

    parts = fragments()
    if not parts:
        sys.exit("src/ 안에 대본 조각이 없습니다.")

    combined: list[str] = []
    for frag_path in parts:
        raw = frag_path.read_text(encoding="utf-8")
        title = title_of(raw, frag_path.stem)
        combined.append(raw)

        # 편별 단독 파일은 첫 장 강제 개행을 없앤다
        solo = raw.replace('class="script"', 'class="script solo"', 1)
        solo = solo.replace('class="guide"', 'class="guide solo"', 1)
        solo = solo.replace(
            "</style>", "</style>", 1
        )
        stem = frag_path.stem
        html_path = write_page(
            OUT_HTML / f"{stem}.html",
            title,
            '<style>.solo{page-break-before:auto !important;}</style>\n' + solo,
        )
        to_pdf(chrome, html_path, OUT_PDF / f"{stem}.pdf")
        print(f"  · {stem}.pdf")

    all_html = write_page(
        OUT_HTML / "골프레슨_대본_전체.html",
        "골프 레슨 유튜브 대본 모음",
        "\n\n".join(combined),
    )
    to_pdf(chrome, all_html, OUT_PDF / "골프레슨_대본_전체.pdf")
    print("  · 골프레슨_대본_전체.pdf")
    print("\n완료. pdf/ 폴더를 확인하세요.")


if __name__ == "__main__":
    main()
