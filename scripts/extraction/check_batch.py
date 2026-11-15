"""Validate one D1 extraction batch (studies + results CSV) against its .list and the full text.

Usage:
  .venv/bin/python scripts/extraction/check_batch.py extraction/batches/batch_01.list \
      extraction/codex/batch_01_studies.csv extraction/codex/batch_01_results.csv [--text-dir fulltext_text_ft]

Errors (exit 1) = must fix. Warnings = reviewer should look. Checks:
  - headers, study_id/record_id order, controlled values, required *_src filled as 'p.N[ ...]'
  - cited page exists in the text file
  - value_context (verbatim snippet, >= 25 chars) is on the cited page and contains value_reported as a whole number
  - trivial values (0, 1, single digit) and 'not verified' notes are rejected
  - value == value_reported (/100 if percent), value in 0-1
  - f1_avg / model_family / best-flag consistency; every study has >= 1 open-LLM result
"""
import argparse
import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fields import ALLOWED, EMPTY_OK, MULTI, RESULT_FIELDS, SRC_OF, STUDY_FIELDS  # noqa: E402

SRC = re.compile(r'^p\.(\d+)\b')
NUM = re.compile(r'^-?\d+(\.\d+)?$')


def pages(path):
    """Return {page_number: text} from a '=== p.N ===' marked file."""
    text = Path(path).read_text(encoding='utf-8')
    parts = re.split(r'=== p\.(\d+) ===', text)
    return {int(parts[i]): parts[i + 1] for i in range(1, len(parts) - 1, 2)}


def squash(s):
    return re.sub(r'\s+', '', re.sub(r'-\s*\n\s*', '', s)).casefold()


def spaced(s):
    """Collapse whitespace to single spaces (keeps number boundaries in tables)."""
    return re.sub(r'\s+', ' ', re.sub(r'-\s*\n\s*', '', s)).casefold()


def has_number(hay, num):
    """num occurs in hay as a whole number (not part of a longer number)."""
    return re.search(r'(?<![\d.])' + re.escape(num) + r'(?![\d]|\.\d)', hay) is not None


def read(path, fields, errs, label):
    rows = list(csv.DictReader(open(path, encoding='utf-8-sig')))
    header = list(rows[0]) if rows else next(csv.reader(open(path, encoding='utf-8-sig')), [])
    if header != fields:
        errs.append(f'{label}: header mismatch; expected {fields}')
    return [{k: (v or '').strip() for k, v in r.items()} for r in rows]


def src_pages(src, pg, where, errs):
    out = []
    for part in [x.strip() for x in src.split(';') if x.strip()]:
        m = SRC.match(part)
        if not m:
            errs.append(f'{where}: source {part!r} must start with p.N')
            continue
        n = int(m.group(1))
        if n not in pg:
            errs.append(f'{where}: page p.{n} not in text (has p.1-p.{max(pg) if pg else 0})')
        out.append(n)
    return out


def check(lst, studies_csv, results_csv, text_dir):
    errs, warns = [], []
    expected = [l.split('\t')[:2] for l in Path(lst).read_text(encoding='utf-8').splitlines() if l.strip()]
    sid2rid = dict(expected)
    studies = read(studies_csv, STUDY_FIELDS, errs, 'studies')
    notes = {s["study_id"]: s.get("note", "") for s in studies}
    results = read(results_csv, RESULT_FIELDS, errs, 'results')
    if errs:
        return errs, warns
    if [[s['study_id'], s['record_id']] for s in studies] != expected:
        errs.append('studies: study_id/record_id list or order differs from .list')
    texts = {}
    for sid, rid in expected:
        f = Path(text_dir, rid + '.txt')
        texts[sid] = pages(f) if f.exists() else {}
        if not texts[sid]:
            errs.append(f'{sid}: text file missing or unpaged: {f}')

    for s in studies:
        sid, pg = s['study_id'], texts.get(s['study_id'], {})
        if s['extractor'] != 'codex':
            errs.append(f'{sid}: extractor must be codex')
        if not re.fullmatch(r'20(2[2-7])', s['year']):
            errs.append(f'{sid}: year {s["year"]!r}')
        for k, allowed in ALLOWED.items():
            if k in s and s[k] not in allowed:
                errs.append(f'{sid}: {k}={s[k]!r} not in {sorted(allowed)}')
        for k, allowed in MULTI.items():
            if k in s:
                bad = [v for v in s[k].split('; ') if v not in allowed]
                if bad or not s[k]:
                    errs.append(f'{sid}: {k} has invalid {bad or "empty"}')
        for src, cols in SRC_OF.items():
            filled = any(s[c] and s[c] not in EMPTY_OK for c in cols)
            if filled and not s[src]:
                errs.append(f'{sid}: {src} empty but {cols} filled')
            if s[src]:
                src_pages(s[src], pg, f'{sid}.{src}', errs)
        if re.search(r'not verified|unverified|尚未確認|未確認', s['note'], re.I):
            errs.append(f'{sid}: note says "not verified"; read Methods/Results and state what the closed model was used for, with page')
        srcs = [s[k] for k in SRC_OF if s[k]]
        if len(pg) > 3 and srcs and all(x.strip() == 'p.1' for x in srcs):
            warns.append(f'{sid}: every source is p.1 in a {len(pg)}-page text; check sources')
        for c in ('first_author', 'open_models', 'extraction_targets', 'datasets'):
            if not s[c] or s[c] in EMPTY_OK:
                errs.append(f'{sid}: {c} must be filled')

    by_sid = defaultdict(list)
    seen = set()
    for r in results:
        rid, sid = r['result_id'], r['study_id']
        where = rid or '(no result_id)'
        if sid not in sid2rid:
            errs.append(f'{where}: study_id {sid!r} not in batch')
            continue
        by_sid[sid].append(r)
        if not re.fullmatch(re.escape(sid) + r'-R\d{2}', rid) or rid in seen:
            errs.append(f'{where}: result_id must be unique {sid}-RNN')
        seen.add(rid)
        if r['extractor'] not in ('codex', 'agent'):  # agent = row added in review (agent_patch.py, logged)
            errs.append(f'{where}: extractor must be codex or agent')
        for k, allowed in ALLOWED.items():
            if k in r and r[k] not in allowed:
                errs.append(f'{where}: {k}={r[k]!r} not in {sorted(allowed)}')
        for c in ('task', 'dataset', 'model', 'test_n'):
            if not r[c]:
                errs.append(f'{where}: {c} empty')
        if (r['metric'] == 'F1') != (r['f1_avg'] != 'NA'):
            errs.append(f'{where}: f1_avg must be NA iff metric is not F1')
        if (r['model_class'] == 'open LLM') != (r['model_family'] != 'NA'):
            errs.append(f'{where}: model_family must be NA iff model_class is not open LLM')
        if r['model_class'] == 'open LLM' and r['strategy'] == 'NA':
            errs.append(f'{where}: open LLM row needs a strategy')
        if r['params_b'] != 'NR' and not NUM.match(r['params_b']):
            errs.append(f'{where}: params_b {r["params_b"]!r} must be a number or NR')
        if r['params_b'] != 'NR' and NUM.match(r['params_b']) and r['model_class'] == 'open LLM' and float(r['params_b']) < 1:
            warns.append(f'{where}: open LLM with params_b < 1 (protocol requires >= 1B)')
        if not NUM.match(r['value']):
            errs.append(f'{where}: value {r["value"]!r} must be numeric 0-1')
            continue
        v = float(r['value'])
        if not 0 <= v <= 1:
            errs.append(f'{where}: value {v} outside 0-1')
        if not NUM.match(r['value_reported'].rstrip('%')):
            errs.append(f'{where}: value_reported {r["value_reported"]!r} must be the number as printed')
            continue
        rep = float(r['value_reported'].rstrip('%'))
        expect = rep / 100 if r['metric_scale_original'] == 'percent' else rep
        if abs(expect - v) > 0.0006:
            errs.append(f'{where}: value {v} != value_reported {r["value_reported"]} ({r["metric_scale_original"]})')
        if rep in (0.0, 1.0) or len(r['value_reported'].rstrip('%').replace('.', '')) < 2:
            errs.append(f'{where}: value_reported {r["value_reported"]!r} is too trivial to verify; give the real reported number')
        pg = texts.get(sid, {})
        nums = src_pages(r['value_src'], pg, where, errs)
        ctx = r['value_context']
        needle = squash(r['value_reported'].rstrip('%'))
        if len(ctx) < 25:
            errs.append(f'{where}: value_context must be a verbatim snippet (>= 25 chars) containing the number')
        elif not has_number(spaced(ctx), needle):
            errs.append(f'{where}: value_context does not contain value_reported {r["value_reported"]!r}')
        elif nums and not any(squash(ctx) in squash(pg.get(n, '')) for n in nums):
            errs.append(f'{where}: value_context not found verbatim on cited page(s) {nums}: {ctx[:60]!r}')

    for sid, rid in expected:
        rows = by_sid.get(sid, [])
        if not any(r['model_class'] == 'open LLM' for r in rows):
            if 'QUERY' in notes.get(sid, ''):
                warns.append(f'{sid}: no open-LLM result row (QUERY in studies.note; reviewer to decide)')
                continue
            errs.append(f'{sid}: no open-LLM result row (explain in studies.note and flag for reviewer if truly none)')
        groups = defaultdict(list)
        for r in rows:
            groups[(r['task'], r['dataset'])].append(r)
        for key, g in groups.items():
            best_open = [r for r in g if r['is_best_open'] == 'yes']
            if any(r['model_class'] == 'open LLM' for r in g) and len(best_open) != 1:
                errs.append(f'{sid} {key}: need exactly one is_best_open=yes, got {len(best_open)}')
            if any(r['is_best_open'] == 'yes' and r['model_class'] != 'open LLM' for r in g):
                errs.append(f'{sid} {key}: is_best_open=yes on a non-open row')
            cls = Counter(r['model_class'] for r in g if r['is_best_comparator'] == 'yes')
            if cls.get('open LLM'):
                errs.append(f'{sid} {key}: is_best_comparator=yes on an open-LLM row')
            for c, n in cls.items():
                if n > 1:
                    errs.append(f'{sid} {key}: {n} is_best_comparator=yes rows for {c}')
        if len(rows) > 40:
            warns.append(f'{sid}: {len(rows)} result rows; check the row-selection rules were followed')
    return errs, warns


def main():
    p = argparse.ArgumentParser()
    p.add_argument('lst')
    p.add_argument('studies')
    p.add_argument('results')
    p.add_argument('--text-dir', default='fulltext_text_ft')
    a = p.parse_args()
    errs, warns = check(a.lst, a.studies, a.results, a.text_dir)
    for w in warns:
        print('WARN', w)
    for e in errs:
        print('ERROR', e)
    print('OK' if not errs else f'{len(errs)} errors', f'({len(warns)} warnings)')
    sys.exit(1 if errs else 0)


if __name__ == '__main__':
    main()
