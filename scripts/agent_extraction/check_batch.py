"""Validate one AI extraction batch (studies + results CSV) against its .list and the extracted text.

Usage: python scripts/agent_extraction/check_batch.py extraction/ai_batches/batch_01.list [--text-dir fulltext_text_full]
Expects batch_01_studies.csv and batch_01_results.csv next to the .list file.
"""
import argparse, csv, re, sys
from pathlib import Path

S_FIELDS = ('record_id title_match first_author year country note_language text_type clinical_domain datasets '
            'task_types extraction_targets open_models medical_domain_model closed_comparators other_comparators '
            'strategies deployment n_documents_test note evidence').split()
R_FIELDS = ('record_id task dataset model model_class params_b strategy metric f1_avg value eval_level '
            'is_best_open is_best_comparator value_src value_quote note').split()
ENUM = {
    'model_class': {'open LLM', 'closed LLM', 'BERT-type', 'rule-based', 'other'},
    'strategy': {'zero-shot', 'few-shot', 'CoT', 'LoRA', 'QLoRA', 'full FT', 'RAG', 'other'},
    'metric': {'F1', 'precision', 'recall', 'accuracy', 'other'},
    'f1_avg': {'micro', 'macro', 'weighted', 'NR', 'NA'},
    'eval_level': {'entity', 'relation', 'field', 'document', 'NR'},
    'is_best_open': {'yes', 'no'}, 'is_best_comparator': {'yes', 'no'},
}
norm = lambda s: re.sub(r'\s+', '', re.sub(r'-\s*\n\s*', '', s)).casefold()  # drop all whitespace: pypdf spacing is unreliable

def quote_ok(q, text):
    return norm(q.strip().strip('"“”')) in text

def main():
    p = argparse.ArgumentParser(); p.add_argument('lst'); p.add_argument('--text-dir', default='fulltext_text_full')
    a = p.parse_args()
    lst = Path(a.lst); stem = lst.with_suffix('')
    ids = [l.split('\t')[0] for l in lst.read_text(encoding='utf-8').splitlines() if l.strip()]
    errs = []
    try:
        srows = list(csv.DictReader(open(f'{stem}_studies.csv', encoding='utf-8-sig')))
        rrows = list(csv.DictReader(open(f'{stem}_results.csv', encoding='utf-8-sig')))
    except FileNotFoundError as e:
        print(f'missing file: {e.filename}'); sys.exit(1)
    if srows and list(srows[0]) != S_FIELDS: errs.append(f'studies header {list(srows[0])}')
    if rrows and list(rrows[0]) != R_FIELDS: errs.append(f'results header {list(rrows[0])}')
    if errs: print('\n'.join(errs)); sys.exit(1)
    if [r['record_id'] for r in srows] != ids: errs.append('studies record_id list/order mismatch')
    texts = {i: norm(Path(a.text_dir, i + '.txt').read_text(encoding='utf-8')) for i in ids}
    matched = set()
    for r in srows:
        rid = r['record_id']
        if rid not in texts: continue
        if r['title_match'] not in ('yes', 'version', 'no'): errs.append(f'{rid}: title_match {r["title_match"]!r}')
        if r['title_match'] in ('yes', 'version'): matched.add(rid)
        if r['medical_domain_model'] not in ('yes', 'no', 'NA'): errs.append(f'{rid}: medical_domain_model')
        if rid in matched:
            for f in ('open_models', 'task_types', 'extraction_targets'):
                if not r[f].strip() or r[f] in ('NR', 'NA'): errs.append(f'{rid}: {f} empty')
        qs = [q for q in r['evidence'].split(' | ') if q.strip()]
        if rid in matched and not qs: errs.append(f'{rid}: no evidence')
        for q in qs:
            m = re.match(r'^(.*?)\s*\(p\.\s*\d+\)\s*$', q, re.S)
            if not m: errs.append(f'{rid}: evidence lacks (p.N): {q[:60]}'); continue
            if len(m.group(1).strip()) < 20: errs.append(f'{rid}: evidence too short')
            elif not quote_ok(m.group(1), texts[rid]): errs.append(f'{rid}: evidence not verbatim: {m.group(1)[:60]}')
    best_open = set()
    for n, r in enumerate(rrows, 2):
        rid = r['record_id']; tag = f'{rid} results line {n}'
        if rid not in texts: errs.append(f'{tag}: record_id not in batch'); continue
        for f, allowed in ENUM.items():
            if r[f] not in allowed: errs.append(f'{tag}: {f}={r[f]!r}')
        if r['is_best_open'] == 'yes':
            best_open.add(rid)
            if r['model_class'] != 'open LLM': errs.append(f'{tag}: is_best_open on non-open model')
        if r['params_b'] != 'NR':
            try: float(r['params_b'])
            except ValueError: errs.append(f'{tag}: params_b {r["params_b"]!r}')
        if r['value'] == 'NR':
            if not r['note'].strip(): errs.append(f'{tag}: value NR needs note')
            continue
        try:
            v = float(r['value'])
            if not 0 <= v <= 1: errs.append(f'{tag}: value {v} not in 0-1')
        except ValueError:
            errs.append(f'{tag}: value {r["value"]!r}'); continue
        if not re.search(r'p\.\s*\d+', r['value_src']): errs.append(f'{tag}: value_src lacks p.N')
        q = r['value_quote']
        if len(q.strip()) < 8: errs.append(f'{tag}: value_quote too short')
        elif not quote_ok(q, texts[rid]): errs.append(f'{tag}: value_quote not verbatim: {q[:60]}')
        else:
            pct, dec = f'{v * 100:g}', f'{v:g}'
            cands = {pct, dec, f'{v * 100:.1f}', f'{v * 100:.2f}', f'{v:.2f}', f'{v:.3f}', f'{v:.4f}', dec.lstrip('0')}
            if not any(c in q for c in cands): errs.append(f'{tag}: value {v} not visible in value_quote')
    for rid in matched - best_open: errs.append(f'{rid}: no is_best_open=yes result')
    print('\n'.join(errs) if errs else f'OK {len(srows)} studies, {len(rrows)} results')
    sys.exit(1 if errs else 0)

if __name__ == '__main__': main()
