"""Merge dual-AI full-text screening (Sonnet all, Opus re-checks Sonnet's excludes) and build the adjudication sheet.

Rules (protocol 3.5; ROADMAP decisions 2026-11-14):
- Not retrieved: fetch status != downloaded, plus records whose downloaded file was the wrong paper and no correct OA copy exists.
- Sonnet include -> AI include. Sonnet exclude + Opus exclude -> AI exclude (Sonnet's code; code differences noted).
  Sonnet exclude + Opus include -> disagreement, author decides. Sonnet X8 is not re-checked by Opus.
- Same study, two records (identical PDF sha256, or Sonnet X8 note): the peer-reviewed record is the main report and the
  preprint gets X8 unless it is already excluded for X1–X7. If the two records' AI decisions differ, the study goes
  to the author.

Usage: python scripts/agent_screening/merge_ft.py
"""
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font

WRONG_FILE_NOT_RETRIEVED = {'R0891': 'OA PDF 為另一篇論文（DrugProt 概述，DOI 誤植）；Europe PMC 無 OA 版'}
PREPRINT_DOI = ('10.1101/', '10.64898/', '10.48550/')


def read(path):
    return list(csv.DictReader(open(path, encoding='utf-8-sig')))


def batches(folder):
    return {r['record_id']: r for f in sorted(Path(folder).glob('batch_*.csv')) for r in read(f)}


def is_preprint(rec):
    return rec['doi'].lower().startswith(PREPRINT_DOI) or set(rec['sources'].split('; ')) <= {'arXiv', 'Europe PMC'}


def main():
    recs = {r['record_id']: r for r in read('data/records_dedup.csv')}
    ids = [r['record_id'] for r in read('screening/to_full_text.csv')]
    fetch = {r['record_id']: r for r in read('fulltext/fetch_log_c2.csv')}
    son, opus = batches('screening/ft_sonnet'), batches('screening/ft_opus')

    # same-study pairs
    by_sha = defaultdict(list)
    for rid in ids:
        if fetch[rid]['status'] == 'downloaded' and fetch[rid]['sha256'] and rid not in WRONG_FILE_NOT_RETRIEVED:
            by_sha[fetch[rid]['sha256']].append(rid)
    groups = [g for g in by_sha.values() if len(g) > 1]
    for rid, r in son.items():
        m = re.search(r'R\d{4}', r['reason'] + ' ' + r['model_open']) if r['code'] == 'X8' else None
        if m and m.group() != rid and not any(rid in g for g in groups):
            groups.append([m.group(), rid])
    main_of = {}
    for g in groups:
        mains = [x for x in g if not is_preprint(recs[x])] or [g[0]]
        for x in g:
            if x != mains[0]:
                main_of[x] = mains[0]

    out = []
    for rid in ids:
        rec, s, o = recs[rid], son.get(rid), opus.get(rid)
        row = {'record_id': rid, 'title': rec['title'], 'doi': rec['doi'], 'year': rec['year'], 'venue': rec['venue'],
               'preprint': 'yes' if is_preprint(rec) else '', 'same_study_main': main_of.get(rid, ''),
               'retrieved': '', 'sonnet_decision': '', 'sonnet_code': '', 'sonnet_reason': '', 'sonnet_evidence': '',
               'opus_decision': '', 'opus_code': '', 'opus_reason': '', 'opus_evidence': '',
               'model_open': '', 'text_type': '', 'task': '', 'metric': '', 'ai_decision': '', 'ai_code': '', 'status': ''}
        if fetch[rid]['status'] != 'downloaded' or rid in WRONG_FILE_NOT_RETRIEVED:
            row.update(retrieved='no', ai_decision='not_retrieved', status='not_retrieved',
                       sonnet_reason=WRONG_FILE_NOT_RETRIEVED.get(rid, fetch[rid]['note'] or fetch[rid]['status']))
            out.append(row)
            continue
        row['retrieved'] = 'yes'
        for k in ('model_open', 'text_type', 'task', 'metric'):
            row[k] = s[k]
        row.update(sonnet_decision=s['decision'], sonnet_code=s['code'], sonnet_reason=s['reason'], sonnet_evidence=s['evidence'])
        if o:
            row.update(opus_decision=o['decision'], opus_code=o['code'], opus_reason=o['reason'], opus_evidence=o['evidence'])
        if s['decision'] == 'include':
            row.update(ai_decision='include', status='sonnet_include')
        elif s['code'] == 'X8':
            row.update(ai_decision='exclude', ai_code='X8', status='sonnet_x8')
        elif o is None:
            raise SystemExit(f'{rid}: Sonnet exclude without Opus review')
        elif o['decision'] == 'exclude':
            row.update(ai_decision='exclude', ai_code=s['code'],
                       status='both_exclude' if o['code'] == s['code'] else f'both_exclude_code_diff({o["code"]})')
        else:
            row.update(ai_decision='disagree', status='disagree')
        out.append(row)

    # apply same-study rule
    by_id = {r['record_id']: r for r in out}
    for pre, main_id in main_of.items():
        p, m = by_id.get(pre), by_id.get(main_id)
        if not p or not m or p['retrieved'] != 'yes' or m['retrieved'] != 'yes':
            continue
        own = lambda r: r['ai_decision'] if r['ai_code'] != 'X8' else None
        same_text = Path('fulltext_text', f'{pre}.txt').read_bytes() == Path('fulltext_text', f'{main_id}.txt').read_bytes()
        if same_text and own(p) and own(m) and own(p) != own(m):  # same text judged differently
            m['status'] += '; same_study_conflict'
            p['status'] += '; same_study_conflict'
        if p['ai_decision'] != 'exclude':  # X1–X7 come before X8 ("first code that applies")
            p.update(ai_decision='exclude', ai_code='X8', status=p['status'] + f'; X8→{main_id}')

    fields = list(out[0])
    with open('screening/ft_ai_merged.csv', 'w', encoding='utf-8-sig', newline='') as h:
        w = csv.DictWriter(h, fields)
        w.writeheader()
        w.writerows(out)

    todo = [r for r in out if r['ai_decision'] == 'disagree' or 'same_study_conflict' in r['status'] or 'code_diff' in r['status']]
    wb = Workbook()
    ws = wb.active
    ws.title = 'adjudicate'
    cols = ['record_id', 'title', 'status', 'same_study_main', 'sonnet_decision', 'sonnet_code', 'sonnet_reason', 'sonnet_evidence',
            'opus_decision', 'opus_code', 'opus_reason', 'opus_evidence', 'my_decision', 'my_code', 'my_note']
    ws.append(cols)
    for r in todo:
        ws.append([r.get(c, '') for c in cols])
    for c, wdt in zip('ABCDEFGHIJKLMNO', [9, 50, 22, 10, 9, 6, 50, 60, 9, 6, 50, 60, 12, 8, 30]):
        ws.column_dimensions[c].width = wdt
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical='top')
    for cell in ws[1]:
        cell.font = Font(bold=True)
    ws.freeze_panes = 'C2'
    wb.save('screening/step4_ft_disagreements.xlsx')

    summary = {
        'to_full_text': len(out),
        'not_retrieved': sum(r['retrieved'] == 'no' for r in out),
        'assessed': sum(r['retrieved'] == 'yes' for r in out),
        'ai_decision': Counter(r['ai_decision'] for r in out),
        'exclude_codes': Counter(r['ai_code'] for r in out if r['ai_decision'] == 'exclude'),
        'opus_reviewed': len(opus),
        'opus_agrees_exclude': sum(r['status'].startswith('both_exclude') for r in out),
        'code_diff': sum('code_diff' in r['status'] for r in out),
        'same_study_pairs': len(main_of),
        'same_study_conflicts': sum('same_study_conflict' in r['status'] for r in out) // 2,
        'to_adjudicate': len(todo),
    }
    Path('screening/ft_ai_merged_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
