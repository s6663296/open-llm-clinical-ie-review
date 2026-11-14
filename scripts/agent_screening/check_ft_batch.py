"""Validate one AI full-text screening batch CSV against its .list file and the extracted text.

Usage: python scripts/agent_screening/check_ft_batch.py <batch.list> <batch.csv> [--text-dir fulltext_text]
Checks: same record_ids/order, decision include|exclude, code rules, evidence quotes carry (p.N)
and each quote (whitespace-normalised, case-insensitive) occurs in the extracted text.
"""
import argparse, csv, re, sys
from pathlib import Path

FIELDS = 'record_id decision code model_open text_type task metric reason evidence'.split()
norm = lambda s: re.sub(r'\s+', ' ', re.sub(r'-\s*\n\s*', '', s)).strip().casefold()

def main():
    p = argparse.ArgumentParser(); p.add_argument('lst'); p.add_argument('csv'); p.add_argument('--text-dir', default='fulltext_text')
    a = p.parse_args()
    ids = [l.split('\t')[0] for l in Path(a.lst).read_text(encoding='utf-8').splitlines() if l.strip()]
    rows = list(csv.DictReader(open(a.csv, encoding='utf-8-sig')))
    errs = []
    if [r['record_id'] for r in rows] != ids: errs.append('record_id list/order mismatch')
    for r in rows:
        if list(r) != FIELDS: errs.append(f'bad header {list(r)}'); break
        rid, d, c = r['record_id'], r['decision'], r['code']
        if d not in ('include', 'exclude'): errs.append(f'{rid}: decision {d!r}')
        if d == 'exclude' and c not in [f'X{i}' for i in range(1, 9)]: errs.append(f'{rid}: exclude needs X1-X8')
        if d == 'include' and c: errs.append(f'{rid}: include must have empty code')
        text = norm(Path(a.text_dir, rid + '.txt').read_text(encoding='utf-8'))
        quotes = [q.strip() for q in r['evidence'].split(' | ') if q.strip()]
        if not quotes: errs.append(f'{rid}: no evidence')
        for q in quotes:
            m = re.match(r'^(.*?)\s*\(p\.\s*\d+\)\s*$', q, re.S)
            if not m: errs.append(f'{rid}: quote lacks (p.N): {q[:60]}'); continue
            body = norm(m.group(1).strip().strip('"“”'))
            if body and body not in text: errs.append(f'{rid}: quote not verbatim: {body[:60]}')
    print('\n'.join(errs) if errs else f'OK {len(rows)} rows')
    sys.exit(1 if errs else 0)

if __name__ == '__main__': main()
