"""Merge AI extraction batches into extraction/extraction.xlsx (classroom subset) for author verification.

Usage: python scripts/agent_extraction/merge_batches.py [--batch-dir extraction/ai_batches] [--out extraction/extraction.xlsx] [--force]
Adds study_id (S001… by record_id order), extractor=ai, empty verifier/verified columns, and author-edit columns.
Also writes extraction/studies.csv and extraction/results.csv (same content, for analysis scripts).
"""
import argparse, csv, re, sys
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_batch import S_FIELDS, R_FIELDS

VERIFY = ['extractor', 'verified', 'author_note']
S_EXTRA = ['review_flag']
FAMILIES = [('Llama', r'llama|vicuna|alpaca|meditron|openbiollm|med42|clinicalcamel|pmc-llama|gatortronllama'),
            ('Mistral', r'mistral|mixtral|biomistral|ministral|zephyr'), ('Qwen', r'qwen|qwq'),
            ('Gemma', r'gemma'), ('DeepSeek', r'deepseek'), ('Phi', r'phi')]
DERIVED = {'pub_type': '由 screening/full_text.csv 推得：preprint 欄=yes → preprint；venue 含 Proceedings/Conference/Workshop/Lecture Notes → conference；其餘 journal（作者核對）',
           'peer_reviewed': 'pub_type=preprint → no，其餘 yes',
           'review_flag': 'Agent 審查時發現、需作者判斷的問題（可能不符納入條件等）',
           'model_family': '由 model 名稱以規則推得（scripts/agent_extraction/merge_batches.py FAMILIES）；非開源 LLM 為 NA'}

def family(row):
    if row['model_class'] != 'open LLM': return 'NA'
    name = row['model'].casefold()
    return next((f for f, pat in FAMILIES if re.search(pat, name)), 'other')

def pub_type(rec):
    if rec.get('preprint') == 'yes': return 'preprint'
    return 'conference' if re.search(r'proceedings|conference|workshop|lecture notes|symposium', rec.get('venue', ''), re.I) else 'journal'

def write_sheet(ws, header, rows):
    ws.append(header)
    ws.append([DERIVED.get(h, '') for h in header])  # row 2 = notes; analyze.py skips it
    for r in rows: ws.append([r.get(h, '') for h in header])
    ws.freeze_panes = 'B3'
    for c in ws[1]: c.font = Font(bold=True)
    for i, h in enumerate(header, 1):
        ws.column_dimensions[get_column_letter(i)].width = 45 if h in ('evidence', 'value_quote', 'open_models', 'extraction_targets', 'note') else 16

def main():
    p = argparse.ArgumentParser(); p.add_argument('--batch-dir', default='extraction/ai_batches')
    p.add_argument('--out', default='extraction/extraction.xlsx'); p.add_argument('--flags', default='extraction/review_flags.csv'); p.add_argument('--force', action='store_true')
    a = p.parse_args()
    out = Path(a.out)
    if out.exists() and not a.force: p.error(f'{out} exists (may hold author edits); use --force')
    bd = Path(a.batch_dir); studies, results = [], []
    for lst in sorted(bd.glob('batch_*.list')):
        stem = lst.with_suffix('')
        studies += list(csv.DictReader(open(f'{stem}_studies.csv', encoding='utf-8-sig')))
        results += list(csv.DictReader(open(f'{stem}_results.csv', encoding='utf-8-sig')))
    for lst in sorted((bd / 'redo').glob('redo_*.list')):  # re-extractions replace the original rows
        stem = lst.with_suffix(''); ids = {l.split('	')[0] for l in lst.read_text(encoding='utf-8').splitlines() if l.strip()}
        studies = [r for r in studies if r['record_id'] not in ids] + list(csv.DictReader(open(f'{stem}_studies.csv', encoding='utf-8-sig')))
        results = [r for r in results if r['record_id'] not in ids] + list(csv.DictReader(open(f'{stem}_results.csv', encoding='utf-8-sig')))
    flags = {}
    if Path(a.flags).exists():
        for r in csv.DictReader(open(a.flags, encoding='utf-8-sig')): flags.setdefault(r['record_id'], []).append(r['flag'])
    studies.sort(key=lambda r: r['record_id'])
    sid = {r['record_id']: f'S{i:03}' for i, r in enumerate(studies, 1)}
    recs = {r['record_id']: r for r in csv.DictReader(open('screening/full_text.csv', encoding='utf-8-sig'))}
    for r in studies:
        pt = pub_type(recs[r['record_id']])
        if r['year'] in ('', 'NR') and recs[r['record_id']].get('year'):
            r['year'] = recs[r['record_id']]['year']; r['note'] = (r['note'] + '; ' if r['note'] else '') + 'year from bibliographic record'
        r['review_flag'] = ' | '.join(flags.get(r['record_id'], []))
        r.update(study_id=sid[r['record_id']], pub_type=pt, peer_reviewed='no' if pt == 'preprint' else 'yes', extractor='ai', verified='')
    results.sort(key=lambda r: r['record_id'])
    count = {}
    for r in results:
        s = sid[r['record_id']]; count[s] = count.get(s, 0) + 1
        r.update(study_id=s, result_id=f'{s}-R{count[s]:02}', model_family=family(r), extractor='ai', verified='')
    sh = ['study_id'] + S_FIELDS[:5] + ['pub_type', 'peer_reviewed'] + S_FIELDS[5:] + S_EXTRA + VERIFY
    rh = ['result_id', 'study_id'] + R_FIELDS[:5] + ['model_family'] + R_FIELDS[5:] + VERIFY
    wb = Workbook(); ws = wb.active; ws.title = 'studies'; write_sheet(ws, sh, studies)
    write_sheet(wb.create_sheet('results'), rh, results)
    readme = wb.create_sheet('說明')
    for line in ['AI 預填（Codex），Agent 驗證引句逐字與數值；作者逐列核對後在 verified 填 yes，修改處寫 author_note。',
                 '欄位定義：scripts/agent_extraction/extraction_prompt.md（課堂版：模型、任務、效能）。',
                 'evidence / value_quote 為全文文字檔逐字引句；頁碼為 PDF 頁碼。']:
        readme.append([line])
    out.parent.mkdir(parents=True, exist_ok=True); wb.save(out)
    for name, h, rows in (('studies', sh, studies), ('results', rh, results)):
        with open(out.parent / f'{name}.csv', 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.DictWriter(f, h, extrasaction='ignore'); w.writeheader(); w.writerows(rows)
    print(f'{len(studies)} studies, {len(results)} results -> {out}')

if __name__ == '__main__': main()
