"""Merge checked Codex batches into extraction/extraction_scope62.xlsx for agent review and author verification.

Reads extraction/codex/batch_NN_{studies,results}.csv (only batches that pass check_batch.py),
writes sheets studies / results / codebook plus review columns:
  agent_review (ok / fix / query), agent_note, verified (yes / corrected / no), verifier_note.
Review columns already in an existing extraction_scope62.xlsx are carried over by study_id / result_id,
so rerunning after new batches never erases the author's work. Agent review from
extraction/review/agent_review.csv fills review cells that are still empty.
Also writes extraction/extraction_scope62_summary.json (counts only).

Usage: .venv/bin/python scripts/extraction/merge.py
"""
import csv
import json
import sys
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font
from openpyxl.worksheet.datavalidation import DataValidation

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from check_batch import check  # noqa: E402
from fields import RESULT_FIELDS, STUDY_FIELDS  # noqa: E402

REVIEW = ['agent_review', 'agent_note', 'verified', 'verifier_note']
OUT = ROOT / 'extraction/extraction_scope62.xlsx'


def old_review(sheet, key):
    if not OUT.exists():
        return {}
    wb = load_workbook(OUT, read_only=True)
    if sheet not in wb.sheetnames:
        return {}
    it = wb[sheet].iter_rows(values_only=True)
    head = list(next(it))
    keep = {}
    for row in it:
        d = dict(zip(head, row))
        if d.get(key):
            keep[d[key]] = {k: d.get(k) for k in REVIEW}
    return keep


AGENT_REVIEW = ROOT / 'extraction/review/agent_review.csv'


def agent_review():
    """Agent review notes kept in a CSV (id = study_id or result_id); fill only empty xlsx cells."""
    if not AGENT_REVIEW.exists():
        return {}
    return {r['id']: r for r in csv.DictReader(open(AGENT_REVIEW, encoding='utf-8-sig'))}


def write(wb, name, fields, rows, key):
    keep = old_review(name, key)
    for rid, a in agent_review().items():
        prev = keep.setdefault(rid, {})
        for k in ('agent_review', 'agent_note'):
            if not prev.get(k):
                prev[k] = a.get(k)
    ws = wb.create_sheet(name)
    ws.append(fields + REVIEW)
    for r in rows:
        prev = keep.get(r[key], {})
        ws.append([r.get(f, '') for f in fields] + [prev.get(k) or '' for k in REVIEW])
    for c in ws[1]:
        c.font = Font(bold=True)
    ws.freeze_panes = 'C2'
    n = len(fields)
    for col, choices in ((n + 1, 'ok,fix,query'), (n + 3, 'yes,corrected,no')):
        dv = DataValidation(type='list', formula1=f'"{choices}"')
        ws.add_data_validation(dv)
        letter = ws.cell(1, col).column_letter
        dv.add(f'{letter}2:{letter}5000')


def main():
    studies, results, used, skipped = [], [], [], []
    for lst in sorted((ROOT / 'extraction/batches').glob('batch_*.list')):
        b = lst.stem
        s, r = ROOT / f'extraction/codex/{b}_studies.csv', ROOT / f'extraction/codex/{b}_results.csv'
        if not (s.exists() and r.exists()):
            continue
        errs, _ = check(lst, s, r, ROOT / 'fulltext_text_ft')
        if errs:
            skipped.append(f'{b} ({len(errs)} errors)')
            continue
        used.append(b)
        studies += list(csv.DictReader(open(s, encoding='utf-8-sig')))
        results += list(csv.DictReader(open(r, encoding='utf-8-sig')))
    wb = Workbook()
    wb.remove(wb.active)
    write(wb, 'studies', STUDY_FIELDS, studies, 'study_id')
    write(wb, 'results', RESULT_FIELDS, results, 'result_id')
    cb = wb.create_sheet('codebook')
    for line in (ROOT / 'extraction/d1_codex_brief.md').read_text(encoding='utf-8').splitlines():
        cb.append([line])
    wb.save(OUT)
    summary = dict(batches_merged=used, batches_skipped=skipped, studies=len(studies), results=len(results),
                   open_llm_results=sum(r['model_class'] == 'open LLM' for r in results))
    (ROOT / 'extraction/extraction_scope62_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
