"""Apply adjudicated decisions to the merged AI full-text screening and write the final full-text sheet.

Inputs: screening/ft_ai_merged.csv (merge_ft.py) and screening/step4_ft_disagreements.xlsx (my_decision/my_code filled).
Output: screening/full_text.xlsx (sheet 'screening', read by scripts/prisma_counts.py) and screening/full_text.csv.

Usage: python scripts/agent_screening/finalize_ft.py
"""
import csv
from collections import Counter

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font

COLS = ['record_id', 'title', 'doi', 'year', 'venue', 'preprint', 'same_study_main', 'fulltext_retrieved',
        'ai_decision', 'ai_code', 'status', 'final_decision', 'final_code', 'decided_by', 'note',
        'model_open', 'text_type', 'task', 'metric', 'sonnet_reason', 'opus_reason']


def main():
    rows = list(csv.DictReader(open('screening/ft_ai_merged.csv', encoding='utf-8-sig')))
    ws = load_workbook('screening/step4_ft_disagreements.xlsx').active
    head = [c.value for c in ws[1]]
    adj = {}
    for values in ws.iter_rows(min_row=2, values_only=True):
        r = dict(zip(head, values))
        d, c = (r['my_decision'] or '').strip(), (r['my_code'] or '').strip()
        if d not in ('include', 'exclude') or (d == 'exclude') != bool(c):
            raise SystemExit(f'{r["record_id"]}: incomplete adjudication')
        adj[r['record_id']] = (d, c, r['my_note'] or '')

    out = []
    for r in rows:
        rid = r['record_id']
        row = {k: r.get(k, '') for k in COLS}
        row['fulltext_retrieved'] = r['retrieved']
        if r['retrieved'] == 'no':
            row.update(final_decision='', final_code='', decided_by='not_retrieved', note=r['sonnet_reason'])
        elif rid in adj:
            d, c, note = adj[rid]
            row.update(final_decision=d, final_code=c, decided_by='adjudicated', note=note)
        elif r['ai_decision'] in ('include', 'exclude'):
            row.update(final_decision=r['ai_decision'], final_code=r['ai_code'], decided_by='ai')
        else:
            raise SystemExit(f'{rid}: unresolved {r["ai_decision"]}')
        out.append(row)

    wb = Workbook()
    sh = wb.active
    sh.title = 'screening'
    sh.append(COLS)
    for row in out:
        sh.append([row[k] for k in COLS])
    for cell in sh[1]:
        cell.font = Font(bold=True)
    sh.freeze_panes = 'C2'
    wb.save('screening/full_text.xlsx')
    with open('screening/full_text.csv', 'w', encoding='utf-8-sig', newline='') as h:
        w = csv.DictWriter(h, COLS)
        w.writeheader()
        w.writerows(out)
    assessed = [r for r in out if r['fulltext_retrieved'] == 'yes']
    print('assessed', len(assessed), Counter(r['final_decision'] for r in assessed),
          Counter(r['final_code'] for r in assessed if r['final_decision'] == 'exclude'))


if __name__ == '__main__':
    main()
