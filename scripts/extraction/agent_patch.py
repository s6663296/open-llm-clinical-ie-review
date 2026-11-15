"""Apply agent review corrections (extraction/review/agent_patches.json) to the Codex batch CSVs.

Each op is one of
  {"batch": "06", "kind": "studies"|"results", "id": "S077-R01", "set": {field: value, ...}, "reason": "..."}
  {"batch": "06", "kind": "results", "add": {full result row}, "reason": "..."}
  {"batch": "13", "kind": "results", "delete": "S170-R01", "reason": "..."}
Idempotent: a field is only written when it differs, a row is only added when its result_id is absent
and only deleted when present.
Every actual change is appended to extraction/review/agent_edits.csv (same log as agent_fix.py).
Run check_batch.py afterwards; corrected rows must still pass it.

Usage: .venv/bin/python scripts/extraction/agent_patch.py
"""
import csv
import datetime
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATCHES = ROOT / 'extraction/review/agent_patches.json'
LOG = ROOT / 'extraction/review/agent_edits.csv'


def main():
    ops = json.loads(PATCHES.read_text(encoding='utf-8'))
    today = datetime.date.today().isoformat()
    log = []
    by_file = {}
    for op in ops:
        by_file.setdefault((op['batch'], op['kind']), []).append(op)
    for (batch, kind), file_ops in by_file.items():
        path = ROOT / f'extraction/codex/batch_{batch}_{kind}.csv'
        rows = list(csv.DictReader(open(path, encoding='utf-8-sig')))
        fields = list(rows[0].keys())
        key = 'study_id' if kind == 'studies' else 'result_id'
        index = {r[key]: r for r in rows}
        for op in file_ops:
            if 'add' in op:
                new = op['add']
                missing = set(fields) - set(new)
                if missing:
                    raise SystemExit(f'{new.get(key)}: missing fields {sorted(missing)}')
                if new[key] in index:
                    continue
                row = {f: new[f] for f in fields}
                # keep rows of one study together
                pos = max(i for i, r in enumerate(rows) if r['study_id'] == row['study_id']) + 1
                rows.insert(pos, row)
                index[row[key]] = row
                log.append([today, batch, row[key], 'added row', op['reason']])
                continue
            if 'delete' in op:
                if op['delete'] in index:
                    rows.remove(index.pop(op['delete']))
                    log.append([today, batch, op['delete'], 'deleted', op['reason']])
                continue
            row = index.get(op['id'])
            if row is None:
                raise SystemExit(f'not found: {op["id"]} in {path.name}')
            for f, v in op['set'].items():
                if f not in fields:
                    raise SystemExit(f'unknown field {f}')
                if row[f] != v:
                    log.append([today, batch, f'{op["id"]}.{f}', f'changed {row[f]!r} -> {v!r}', op['reason']])
                    row[f] = v
        with open(path, 'w', encoding='utf-8', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
    with open(LOG, 'a', encoding='utf-8', newline='') as fh:
        csv.writer(fh).writerows(log)
    print(f'{len(log)} change(s) applied')
    for line in log:
        print(' ', line[2], line[3][:90])


if __name__ == '__main__':
    main()
