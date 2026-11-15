"""以 record_id 比對兩套萃取，產生供作者查核的優先清單。"""
import csv
import json
import re
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIELDS = 'study_id record_id in_provisional_38 scope_suggestion agent_review open62_model open62_value open62_src open174_model open174_value open174_src closed62_model closed62_value closed174_model closed174_value status priority detail'.split()
STATUSES = ('agree', 'differ_value', 'differ_model', 'differ_closed', 'missing_174', 'missing_62')


def normalize_model(name):
    name = (name or '').lower()
    name = re.sub(r'\([^)]*\)', ' ', name)
    name = re.split(r'\s+with\s+', name, maxsplit=1)[0]
    name = re.sub(r'(?<![a-z0-9])nr(?![a-z0-9])', ' ', name)
    name = re.sub(r'^\s*meta(?=[\s._-])', '', name)
    name = re.sub(r'(?:[\s._-]+(?:instruct|chat|it|hf|ft|finetuned|fine[-_ ]tuned))+$', '', name.strip())
    return re.sub(r'[\s._-]+', '', name)


def models_match(a, b):
    a, b = normalize_model(a), normalize_model(b)
    if not a or not b:
        return False, False
    if a == b:
        return True, False
    short, long = sorted((a, b), key=len)
    prefix = bool(re.search(r'[a-z]\d', short) and long.startswith(short))
    return prefix, prefix


def numeric(value):
    try:
        result = Decimal(str(value).strip())
        return result if result.is_finite() else None
    except (InvalidOperation, ValueError):
        return None


def compare_values(a, b):
    a, b = numeric(a), numeric(b)
    if a is None or b is None:
        return False, False
    converted = (a > 1 and b <= 1) or (b > 1 and a <= 1)
    if converted:
        if a > 1:
            a /= 100
        else:
            b /= 100
    return abs(a - b) <= Decimal('0.005'), converted


def determine_status(open62, open174, closed62=None, closed174=None):
    if not open62 or numeric(open62.get('value')) is None:
        return 'missing_62'
    if not open174 or numeric(open174.get('value')) is None:
        return 'missing_174'
    if not models_match(open62.get('model'), open174.get('model'))[0]:
        return 'differ_model'
    if not compare_values(open62.get('value'), open174.get('value'))[0]:
        return 'differ_value'
    if closed62 and closed174:
        if (not models_match(closed62.get('model'), closed174.get('model'))[0]
                or not compare_values(closed62.get('value'), closed174.get('value'))[0]):
            return 'differ_closed'
    return 'agree'


def choose(rows, kind):
    if kind == 'open':
        candidates = [r for r in rows if r.get('is_best_open', '').strip().lower() == 'yes']
    else:
        candidates = [r for r in rows if r.get('model_class', '').strip().lower() == 'closed llm']
        marked = [r for r in candidates if r.get('is_best_comparator', '').strip().lower() == 'yes']
        if marked:
            candidates = marked
    valid = [r for r in candidates if numeric(r.get('value')) is not None]
    return (max(valid, key=lambda r: numeric(r['value'])) if valid else None), len(candidates)


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def describe(status, a, b, c, d, counts):
    if status == 'agree':
        parts = ['開源結果一致']
    elif status == 'missing_62':
        parts = ['課堂版缺少最佳開源數值']
    elif status == 'missing_174':
        parts = ['174 篇版本缺少對應紀錄或最佳開源數值']
    elif status == 'differ_model':
        parts = [f"開源模型 {a['model']} 與 {b['model']} 不同"]
    elif status == 'differ_value':
        parts = [f"開源數值 {a['value']} 與 {b['value']} 不同"]
    else:
        parts = [f"閉源結果 {c['model']} {c['value']} 與 {d['model']} {d['value']} 不同"]
    for label, count in counts:
        if count > 1:
            parts.append(f'{label}多任務 {count} 列')
    for label, x, y in [('開源', a, b), ('閉源', c, d)]:
        if x and y and models_match(x.get('model'), y.get('model'))[1]:
            parts.append(f'{label}??????????????')
        if x and y and compare_values(x.get('value'), y.get('value'))[1]:
            parts.append(f'{label}數值比較已換算百分比')
    return '；'.join(parts) + '。'


def main():
    base = ROOT / 'extraction'
    studies, results62 = [], defaultdict(list)
    for path in sorted((base / 'codex').glob('batch_*_studies.csv')):
        studies.extend(read_csv(path))
    for path in sorted((base / 'codex').glob('batch_*_results.csv')):
        for row in read_csv(path):
            results62[row['study_id']].append(row)
    results174 = defaultdict(list)
    for row in read_csv(base / 'results.csv'):
        results174[row['record_id']].append(row)
    scope = {r['study_id']: r for r in read_csv(base / 'scope_restriction.csv')}
    reviews = {r['id']: r for r in read_csv(base / 'review' / 'agent_review.csv')}
    included = set(json.loads((ROOT / 'analysis' / 'slide_numbers.json').read_text(encoding='utf-8-sig'))['study_ids'])
    output = []
    for study in studies:
        sid, rid = study['study_id'], study['record_id']
        a, na = choose(results62[sid], 'open')
        b, nb = choose(results174[rid], 'open')
        c, nc = choose(results62[sid], 'closed')
        d, nd = choose(results174[rid], 'closed')
        status = determine_status(a, b, c, d)
        review = reviews.get(sid, {}).get('agent_review', '')
        priority = 1 if (sid in included and status != 'agree') or review.strip().lower() == 'fix' else 2 if sid in included else 3
        out = dict(study_id=sid, record_id=rid, in_provisional_38='yes' if sid in included else 'no', scope_suggestion=scope.get(sid, {}).get('suggestion', ''), agent_review=review, status=status, priority=priority, detail=describe(status, a, b, c, d, [('課堂版開源', na), ('174 篇版開源', nb), ('課堂版閉源', nc), ('174 篇版閉源', nd)]))
        for prefix, row in [('open62', a), ('open174', b), ('closed62', c), ('closed174', d)]:
            for column, key in [('model', 'model'), ('value', 'value'), ('src', 'value_src')]:
                if f'{prefix}_{column}' in FIELDS:
                    out[f'{prefix}_{column}'] = (row or {}).get(key, '')
        output.append(out)
    output.sort(key=lambda r: (r['priority'], r['study_id']))
    target = base / 'review' / 'crosscheck_62_vs_174.csv'
    with target.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(output)
    status_counts = Counter(r['status'] for r in output)
    priority_counts = Counter(r['priority'] for r in output)
    summary = {'total': len(output), 'status': {s: status_counts[s] for s in STATUSES}, 'priority': {str(p): priority_counts[p] for p in (1, 2, 3)}}
    (base / 'review' / 'crosscheck_62_vs_174_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
