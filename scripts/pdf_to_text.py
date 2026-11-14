"""Convert full-text PDFs to page-marked plain text for AI full-text screening.

Each output file has '=== p.N ===' markers (PDF page numbers from 1) so screeners can cite pages.
Text after a trailing 'References'/'Bibliography' heading is dropped, and output is capped.

Usage:
  python scripts/pdf_to_text.py --ids screening/to_full_text.csv --pdf-dir fulltext --out-dir fulltext_text
"""
import argparse
import csv
import re
from pathlib import Path

from pypdf import PdfReader

REF = re.compile(r'^\s*(references|bibliography|literature cited)\s*$', re.I | re.M)


HEAD = r'^\s*(?:\d+(?:\.\d+)*\.?\s*|[IVX]+\.\s*)?{}\b'
METHODS = re.compile(HEAD.format(r'(materials?\s+and\s+methods|methods?|methodology|experimental\s+setup|experiments?|study\s+design|data\s+and\s+methods)'), re.I | re.M)
DISCUSSION = re.compile(HEAD.format(r'(discussion|conclusions?|limitations)'), re.I | re.M)


def condense(full, head_chars=6000):
    """Keep the first page block (title/abstract) plus Methods through Results, dropping intro and discussion.

    Page markers are kept so page citations stay valid. Falls back to the full text when headings are not found.
    """
    m = METHODS.search(full, head_chars // 2)
    if not m:
        return full
    d = DISCUSSION.search(full, m.end())
    end = d.start() if d and d.start() > m.end() + 2000 else len(full)
    head = full[:min(head_chars, m.start())]
    marker = re.findall(r'=== p\.\d+ ===', full[len(head):m.start()])
    if len(head) == m.start():
        lead = '\n'
    else:
        lead = '\n[... introduction / related work omitted ...]\n' + (marker[-1] + '\n' if marker else '')
    return head + lead + full[m.start():end] + '\n[... discussion / conclusion omitted ...]'


def convert(pdf, cap, condensed=False):
    """Return page-marked text with the reference list removed and length capped."""
    pages = []
    for i, page in enumerate(PdfReader(pdf).pages, start=1):
        try:
            text = page.extract_text() or ''
        except Exception as exc:  # damaged page: keep going, note it
            text = f'[page text extraction failed: {exc}]'
        pages.append(f'=== p.{i} ===\n{text}')
    full = '\n'.join(pages)
    hits = list(REF.finditer(full))
    if hits and hits[-1].start() > len(full) * 0.5:
        full = full[:hits[-1].start()] + '\n[references removed]'
    if condensed:
        full = condense(full)
    if len(full) > cap:
        full = full[:cap] + '\n[truncated]'
    return full


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--ids', required=True)
    p.add_argument('--pdf-dir', default='fulltext')
    p.add_argument('--out-dir', default='fulltext_text')
    p.add_argument('--cap', type=int, default=60000)
    p.add_argument('--condensed', action='store_true', help='keep title/abstract + methods..results only')
    a = p.parse_args()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    ids = [r['record_id'] for r in csv.DictReader(open(a.ids, encoding='utf-8-sig'))]
    done = failed = missing = 0
    for rid in ids:
        pdf = Path(a.pdf_dir) / f'{rid}.pdf'
        if not pdf.exists():
            missing += 1
            continue
        try:
            text = convert(pdf, a.cap, a.condensed)
        except Exception as exc:
            print(f'{rid}: failed ({exc})')
            failed += 1
            continue
        if len(text.strip()) < 2000:
            print(f'{rid}: very little text ({len(text)} chars), probably scanned or not a paper')
        (out / f'{rid}.txt').write_text(text, encoding='utf-8', errors='replace')
        done += 1
    print(f'converted {done}, failed {failed}, no PDF {missing}')


if __name__ == '__main__':
    main()
