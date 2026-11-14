"""Compare the blind human calibration sample with the LLM screening decisions.

Reports three-category and binary Cohen's kappa (include+unsure = pass to full text),
AI sensitivity / specificity against the human pass decision, and every disagreement.

Usage:
  python scripts/blind_vs_ai.py --blind screening/step1_blind50.xlsx \
      --ai screening/ai_screen_sonnet.csv --json analysis/blind50_vs_ai.json \
      --disagreements analysis/blind50_vs_ai_disagreements.csv
"""
import argparse
import json
import sys
from pathlib import Path

from openpyxl import load_workbook

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import read_csv, write_csv  # noqa: E402
from kappa import calculate  # noqa: E402

LABELS = ['include', 'exclude', 'unsure']


def to_pass(decision):
    """Collapse to the full-text gate: include/unsure pass, exclude does not."""
    return 'exclude' if decision == 'exclude' else 'pass'


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--blind', required=True)
    p.add_argument('--ai', required=True)
    p.add_argument('--json', required=True)
    p.add_argument('--disagreements', required=True)
    a = p.parse_args()

    ws = load_workbook(a.blind, read_only=True)['blind50']
    it = ws.iter_rows(values_only=True)
    header = next(it)
    human = [dict(zip(header, r)) for r in it if r[0]]
    ai = {r['record_id']: r for r in read_csv(a.ai)}

    pairs, rows = [], []
    for h in human:
        hd = str(h['decision'] or '').strip().lower()
        if hd not in LABELS:
            sys.exit(f"incomplete or invalid human decision: {h['record_id']}")
        r = ai[h['record_id']]
        pairs.append((hd, r['agent_suggestion']))
        if hd != r['agent_suggestion']:
            rows.append({'record_id': h['record_id'], 'title': h['title'],
                         'human': hd, 'human_code': h['code'] or '', 'human_note': h['note'] or '',
                         'ai': r['agent_suggestion'], 'ai_code': r['agent_code'], 'ai_reason': r['agent_reason'],
                         'gate_conflict': 'yes' if to_pass(hd) != to_pass(r['agent_suggestion']) else 'no'})

    binary = [(to_pass(x), to_pass(y)) for x, y in pairs]
    tp = sum(x == 'pass' and y == 'pass' for x, y in binary)
    fn = sum(x == 'pass' and y == 'exclude' for x, y in binary)
    tn = sum(x == 'exclude' and y == 'exclude' for x, y in binary)
    fp = sum(x == 'exclude' and y == 'pass' for x, y in binary)
    result = {
        'n': len(pairs),
        'reference': 'step1_blind50 decision (include/unsure = pass)',
        'three_category': calculate(pairs, LABELS),
        'binary_pass_vs_exclude': calculate(binary, ['pass', 'exclude']),
        'ai_vs_human': {'tp': tp, 'fn': fn, 'tn': tn, 'fp': fp,
                        'sensitivity': tp / (tp + fn) if tp + fn else None,
                        'specificity': tn / (tn + fp) if tn + fp else None},
        'disagreements': len(rows),
        'gate_conflicts': sum(r['gate_conflict'] == 'yes' for r in rows),
    }
    Path(a.json).parent.mkdir(parents=True, exist_ok=True)
    Path(a.json).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    write_csv(a.disagreements, rows, list(rows[0]) if rows else ['record_id'])
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
