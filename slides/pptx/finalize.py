"""Post-process the built deck: drop ZIP folder entries (they break cloud co-editing), then make QA contact sheets.

Usage (repo root):
  node slides/pptx/build_deck.js
  .venv/Scripts/python.exe slides/pptx/finalize.py            # strip folder entries
  powershell -File slides/pptx/render.ps1                     # export slides with PowerPoint
  .venv/Scripts/python.exe slides/pptx/finalize.py --sheets   # rename exports to sNN.png, build sheetN.png
"""
import os
import re
import shutil
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DECK = HERE / 'open_llm_clinical_ie_review.pptx'
QA = HERE / 'qa'


def strip_dirs():
    tmp = DECK.with_suffix('.tmp')
    with zipfile.ZipFile(DECK) as zi, zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
        for info in zi.infolist():
            if not info.filename.endswith('/'):
                zo.writestr(info, zi.read(info.filename))
    shutil.move(tmp, DECK)


def sheets():
    from PIL import Image
    for f in os.listdir(QA):
        if f.lower().endswith('.png') and not re.fullmatch(r's\d+\.png|sheet\d+\.png', f):
            os.replace(QA / f, QA / f's{int(re.findall(r"\d+", f)[-1]):02d}.png')
    files = sorted(f for f in os.listdir(QA) if re.fullmatch(r's\d+\.png', f))
    for k in range(0, len(files), 6):
        sheet = Image.new('RGB', (1600, 1350), 'white')
        for j, f in enumerate(files[k:k + 6]):
            sheet.paste(Image.open(QA / f).resize((800, 450)), ((j % 2) * 800, (j // 2) * 450))
        sheet.save(QA / f'sheet{k // 6 + 1}.png')
    print(len(files), 'slides')


if __name__ == '__main__':
    sheets() if '--sheets' in sys.argv else strip_dirs()
