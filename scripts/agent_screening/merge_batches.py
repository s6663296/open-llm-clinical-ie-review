"""Validate and merge manually authored screening suggestions."""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import read_csv, write_csv

FIELDS = 'record_id doi pmid arxiv_id title agent_suggestion agent_code agent_reason agent_signals'.split()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--records', required=True)
    parser.add_argument('--batches', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--summary', required=True)
    args = parser.parse_args()
    records = read_csv(args.records)
    by_id = {r['record_id']: r for r in records}
    decisions = {}
    for path in sorted(Path(args.batches).glob('batch_*.csv')):
        for row in read_csv(path):
            rid = row['record_id']
            if rid not in by_id or rid in decisions:
                raise ValueError(f'unknown or duplicate record: {rid}')
            choice = row['agent_suggestion']
            code = row['agent_code']
            if choice not in ('include', 'exclude', 'unsure') or (code not in [f'X{i}' for i in range(1, 9)] if choice == 'exclude' else bool(code)) or not row['agent_reason'].strip():
                raise ValueError(f'invalid suggestion: {rid}')
            text = (by_id[rid]['title'] + ' ' + by_id[rid]['abstract']).casefold()
            if any(signal.casefold() not in text for signal in row['agent_signals'].split('; ') if signal):
                raise ValueError(f'invalid signal: {rid}')
            ids = ('doi', 'pmid', 'arxiv_id')
            decisions[rid] = {**by_id[rid], **{k: v for k, v in row.items() if k not in ids or v}}
    if len(decisions) != len(records):
        raise ValueError(f'incomplete: {len(decisions)} of {len(records)} records')
    output = [decisions[row['record_id']] for row in records]
    write_csv(args.out, output, FIELDS)
    summary = {'total': len(output), 'suggestions': dict(Counter(r['agent_suggestion'] for r in output)), 'codes': dict(Counter(r['agent_code'] for r in output if r['agent_code']))}
    Path(args.summary).write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
