"""Repair value_context / value_src for result rows whose snippet is not verbatim on the cited page.

For each failing row, finds the single source line (or 2-line window) on any page that contains the
row's numeric tokens in the same order and contains value_reported as a whole number. Only unique
matches are applied; the value itself is never changed. Every repair is logged to
extraction/review/agent_edits.csv. Ambiguous rows are printed for manual review.

Usage: .venv/bin/python scripts/extraction/fix_context.py BATCH [--apply]
"""
import csv
import datetime
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from check_batch import has_number, pages, spaced, squash  # noqa: E402

NUM = re.compile(r'\d+(?:\.\d+)?')


def candidates(pg, ctx, val):
    toks = NUM.findall(ctx)
    pat = re.compile(r'.*?'.join(r'(?<![\d.])' + re.escape(t) + r'(?![\d]|\.\d)' for t in toks), re.S)
    hits = []
    for n, txt in pg.items():
        lines = txt.splitlines()
        for i in range(len(lines)):
            for w in (1, 2):
                win = '\n'.join(lines[i:i + w]).strip()
                if len(win) >= 25 and pat.search(win) and has_number(spaced(win), val):
                    hits.append((n, win))
                    break
    # drop 2-line windows that merely contain a matching 1-line window
    return [(n, w) for n, w in hits if not any(m == n and v != w and v in w for m, v in hits)]


def main():
    b, apply = sys.argv[1], '--apply' in sys.argv
    lst = ROOT / f'extraction/batches/batch_{b}.list'
    sid2rid = dict(l.split('\t')[:2] for l in lst.read_text(encoding='utf-8').splitlines() if l.strip())
    path = ROOT / f'extraction/codex/batch_{b}_results.csv'
    rows = list(csv.DictReader(open(path, encoding='utf-8-sig')))
    fields = list(rows[0])
    log = []
    for r in rows:
        pg = pages(ROOT / f'fulltext_text_ft/{sid2rid[r["study_id"]]}.txt')
        ctx, val = r['value_context'], squash(r['value_reported'].rstrip('%'))
        cited = [int(x) for x in re.findall(r'p\.(\d+)', r['value_src'])]
        if len(ctx) >= 25 and any(squash(ctx) in squash(pg.get(n, '')) for n in cited):
            continue
        hits = candidates(pg, ctx, val)
        uniq = {(n, w) for n, w in hits}
        if len(uniq) != 1:
            print(f'MANUAL {r["result_id"]}: {len(uniq)} candidates; ctx={ctx[:70]!r}')
            continue
        n, win = uniq.pop()
        win = win.rstrip(' -')  # a trailing '-' is read as a line-break hyphen by squash()
        rest = re.sub(r'^p\.\d+', '', r['value_src'].split(';')[0].strip()).strip()
        new_src = f'p.{n}' + (f' {rest}' if rest else '')
        print(f'FIX {r["result_id"]}: {r["value_src"]} -> {new_src}; ctx -> {win[:80]!r}')
        log.append([datetime.date.today().isoformat(), b, f'{r["result_id"]}.value_context/value_src',
                    f'{r["value_src"]!r} -> {new_src!r}; context replaced with verbatim source line',
                    'Codex snippet not verbatim on cited page; repaired by fix_context.py (value unchanged)'])
        r['value_context'], r['value_src'] = win, new_src
    if apply and log:
        with open(path, 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
        with open(ROOT / 'extraction/review/agent_edits.csv', 'a', encoding='utf-8', newline='') as f:
            csv.writer(f).writerows(log)


if __name__ == '__main__':
    main()
