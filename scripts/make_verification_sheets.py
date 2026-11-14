"""Build the human workbooks for LLM title/abstract screening with human verification.

Step 1 (blind validation): the calibration sample (50 records, same seed/IDs as the
title_abstract sheet's `calibration=yes` rows), WITHOUT any LLM output.
Step 2 (verification): every record with the LLM decision, rationale and evidence phrases;
the reviewer marks agree / override and, when overriding, the own decision.

Usage:
  python scripts/make_verification_sheets.py --records data/records_dedup.csv \
      --ai screening/ai_screen_sonnet.csv --calibration-from screening/title_abstract.xlsx \
      --out-dir screening [--force]
"""
import argparse
import sys
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import read_csv  # noqa: E402

CODES = '"X1,X2,X3,X4,X5,X6,X7,X8"'
DECISIONS = '"include,exclude,unsure"'
ACTIONS = '"agree,override"'
AI_ORDER = {'include': 0, 'unsure': 1, 'exclude': 2}


def calibration_ids(path):
    """Return record_ids marked calibration=yes in the existing title/abstract sheet."""
    ws = load_workbook(path, read_only=True)['screening']
    rows = ws.iter_rows(values_only=True)
    header = next(rows)
    i_id, i_cal = header.index('record_id'), header.index('calibration')
    return [r[i_id] for r in rows if r[i_cal] == 'yes']


def style(ws, widths, input_cols):
    """Apply header style, widths, wrapping, freeze panes and highlight input columns."""
    ws.freeze_panes = 'C2'
    for cell in ws[1]:
        cell.font = Font(bold=True)
    fill = PatternFill('solid', fgColor='FFF2CC')
    for letter, width in widths.items():
        ws.column_dimensions[letter].width = width
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical='top')
            if cell.column_letter in input_cols:
                cell.fill = fill


def add_validation(ws, formula, col, n):
    """Attach a dropdown list to rows 2..n+1 of one column."""
    dv = DataValidation(type='list', formula1=formula, allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f'{col}2:{col}{n + 1}')


def add_reference_sheets(wb, source_sheet):
    """Copy the criteria and codes sheets from the title/abstract workbook for reference."""
    src = load_workbook(source_sheet)
    for name in ('criteria', 'codes'):
        if name in src.sheetnames:
            dst = wb.create_sheet(name)
            for row in src[name].iter_rows(values_only=True):
                dst.append(list(row))
            dst.column_dimensions['A'].width = 8
            dst.column_dimensions['B'].width = 40
            dst.column_dimensions['C'].width = 90


def build_blind(records, cal_ids, out, source_sheet):
    """Write the step-1 blind workbook (no LLM output)."""
    by_id = {r['record_id']: r for r in records}
    wb = Workbook()
    ws = wb.active
    ws.title = 'blind50'
    ws.append(['record_id', 'title', 'abstract', 'year', 'venue', 'decision', 'code', 'note'])
    for rid in cal_ids:
        r = by_id[rid]
        ws.append([rid, r['title'], r['abstract'], r['year'], r['venue'], None, None, None])
    n = len(cal_ids)
    add_validation(ws, DECISIONS, 'F', n)
    add_validation(ws, CODES, 'G', n)
    style(ws, {'A': 9, 'B': 45, 'C': 90, 'D': 6, 'E': 22, 'F': 11, 'G': 7, 'H': 30}, {'F', 'G', 'H'})
    add_reference_sheets(wb, source_sheet)
    wb.save(out)
    return n


def build_verify(records, ai_rows, out, source_sheet):
    """Write the step-2 verification workbook (all records with LLM output)."""
    ai = {r['record_id']: r for r in ai_rows}
    missing = [r['record_id'] for r in records if r['record_id'] not in ai]
    if missing:
        sys.exit(f'LLM output missing for {len(missing)} records, e.g. {missing[:5]}')
    ordered = sorted(records, key=lambda r: (AI_ORDER[ai[r['record_id']]['agent_suggestion']], r['record_id']))
    wb = Workbook()
    ws = wb.active
    ws.title = 'verify'
    ws.append(['record_id', 'title', 'abstract', 'year', 'venue', 'doi',
               'ai_decision', 'ai_code', 'ai_reason', 'ai_evidence',
               'action', 'my_decision', 'my_code', 'note', 'final_decision', 'to_full_text'])
    for i, r in enumerate(ordered, start=2):
        a = ai[r['record_id']]
        final = f'=IF(L{i}<>"",L{i},IF(K{i}="agree",G{i},""))'
        to_ft = (f'=IF(O{i}="","",IF(OR(G{i}="include",G{i}="unsure",'
                 f'O{i}="include",O{i}="unsure"),"yes","no"))')
        ws.append([r['record_id'], r['title'], r['abstract'], r['year'], r['venue'], r['doi'],
                   a['agent_suggestion'], a['agent_code'], a['agent_reason'], a['agent_signals'],
                   None, None, None, None, final, to_ft])
    n = len(ordered)
    add_validation(ws, ACTIONS, 'K', n)
    add_validation(ws, DECISIONS, 'L', n)
    add_validation(ws, CODES, 'M', n)
    ws.auto_filter.ref = f'A1:P{n + 1}'
    style(ws, {'A': 9, 'B': 40, 'C': 70, 'D': 6, 'E': 18, 'F': 14, 'G': 10, 'H': 7,
               'I': 40, 'J': 35, 'K': 9, 'L': 11, 'M': 7, 'N': 25, 'O': 12, 'P': 10},
          {'K', 'L', 'M', 'N'})
    add_reference_sheets(wb, source_sheet)
    wb.save(out)
    return n


def main():
    """Parse arguments and write both workbooks, refusing to overwrite unless --force."""
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--records', required=True)
    p.add_argument('--ai', required=True)
    p.add_argument('--calibration-from', required=True)
    p.add_argument('--out-dir', default='screening')
    p.add_argument('--force', action='store_true')
    args = p.parse_args()
    out_dir = Path(args.out_dir)
    blind, verify = out_dir / 'step1_blind50.xlsx', out_dir / 'step2_verify.xlsx'
    if verify.exists() and not args.force:
        sys.exit(f'{verify} exists; use --force to overwrite (it may contain human input)')
    records = read_csv(args.records)
    if blind.exists():
        print(f'{blind}: kept as is (never overwritten; it may contain blind human input)')
    else:
        cal = calibration_ids(args.calibration_from)
        print(f'{blind}: {build_blind(records, cal, blind, args.calibration_from)} records (no LLM output)')
    print(f'{verify}: {build_verify(records, read_csv(args.ai), verify, args.calibration_from)} records')


if __name__ == '__main__':
    main()
