"""Apply a logged agent correction to a Codex batch CSV and append it to extraction/review/agent_edits.csv.

Usage: .venv/bin/python scripts/extraction/agent_fix.py BATCH {studies|results} ID FIELD NEW_VALUE "reason"
"""
import csv
import datetime
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    batch, kind, rid, field, new, reason = sys.argv[1:7]
    path = ROOT / f'extraction/codex/batch_{batch}_{kind}.csv'
    key = 'study_id' if kind == 'studies' else 'result_id'
    rows = list(csv.DictReader(open(path, encoding='utf-8-sig')))
    fields = list(rows[0].keys())
    hit = [r for r in rows if r[key] == rid]
    if len(hit) != 1 or field not in fields:
        sys.exit(f'not found: {rid} {field}')
    old = hit[0][field]
    hit[0][field] = new
    with open(path, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    log = ROOT / 'extraction/review/agent_edits.csv'
    with open(log, 'a', encoding='utf-8', newline='') as f:
        csv.writer(f).writerow([datetime.date.today().isoformat(), batch, f'{rid}.{field}',
                                f'changed {old!r} -> {new!r}', reason])
    print(f'{rid}.{field}: {old!r} -> {new!r}')


if __name__ == '__main__':
    main()
