"""Create the risk-of-bias assessment workbook."""
import argparse
from pathlib import Path
from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter
from form_common import ROOT, questions, format_sheet, validation


def overall(values):
    """Apply the four-domain overall judgement rule."""
    if len(values) != 4 or any(v not in ('Low', 'High', 'Unclear') for v in values):
        return ''
    if 'High' in values:
        return 'High'
    return 'Low' if all(v == 'Low' for v in values) else 'Unclear'


def main():
    """Create three assessor sheets and the source question sheet."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default=str(ROOT / 'extraction/risk_of_bias.xlsx'))
    parser.add_argument('--from-extraction')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    out = Path(args.out)
    if out.exists() and not args.force:
        parser.error('output exists; use --force')
    qs = questions()
    fields = ['study_id'] + [q[0] for q in qs] + [f'D{i}_judgement' for i in range(1, 5)] + [f'D{i}_applicability' for i in range(1, 3)] + [f'D{i}_rationale' for i in range(1, 5)] + ['overall']
    studies = []
    if args.from_extraction:
        source = load_workbook(args.from_extraction, read_only=True, data_only=True)
        studies = [r[0] for r in source['studies'].iter_rows(min_row=3, values_only=True) if r[0]]
        source.close()
    wb = Workbook()
    wb.remove(wb.active)
    for name in ('R1', 'R2', 'consensus'):
        ws = wb.create_sheet(name)
        ws.append(fields)
        ws.append(['研究 ID'] + [q[1] for q in qs] + [''] * (len(fields) - len(qs) - 1))
        format_sheet(ws)
        for i, field in enumerate(fields, 1):
            if field in dict(qs):
                validation(ws, i, ['Y', 'N', 'U', 'NA'])
            elif field.endswith(('judgement', 'applicability')):
                validation(ws, i, ['Low', 'High', 'Unclear'])
        for row in range(3, max(1003, len(studies) + 3)):
            if row - 3 < len(studies):
                ws.cell(row, 1, studies[row - 3])
            first = get_column_letter(fields.index('D1_judgement') + 1)
            last = get_column_letter(fields.index('D4_judgement') + 1)
            cells = f'{first}{row}:{last}{row}'
            ws.cell(row, len(fields), f'=IF(COUNTIF({cells},"Low")+COUNTIF({cells},"High")+COUNTIF({cells},"Unclear")<4,"",IF(COUNTIF({cells},"High")>0,"High",IF(COUNTIF({cells},"Low")=4,"Low","Unclear")))')
    ws = wb.create_sheet('questions')
    ws.append(['id', 'question'])
    for item in qs:
        ws.append(item)
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    print(out)


if __name__ == '__main__':
    main()
