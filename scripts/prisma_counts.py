"""Calculate PRISMA counts only when screening decisions are complete."""
import argparse
import json
from collections import Counter
from pathlib import Path
from openpyxl import load_workbook


def sheet(path):
    """Read a screening workbook or return None when it is unavailable."""
    if not path or not Path(path).exists():
        return None
    wb = load_workbook(path, read_only=True, data_only=True)
    it = wb['screening'].iter_rows(values_only=True)
    headers = next(it)
    rows = [dict(zip(headers, row)) for row in it if any(x is not None for x in row)]
    wb.close()
    return rows


def completed(rows, field, allowed):
    """Return whether each row contains an allowed final value."""
    return rows is not None and all(str(row.get(field) or '').strip().lower() in allowed for row in rows)


def main():
    """Compute database and citation pathway counts without filling gaps."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', required=True)
    parser.add_argument('--title-abstract')
    parser.add_argument('--full-text')
    parser.add_argument('--citation-screening')
    parser.add_argument('--citation-full-text')
    parser.add_argument('--out')
    args = parser.parse_args()
    summary = json.loads(Path(args.summary).read_text(encoding='utf-8-sig'))
    ta = sheet(args.title_abstract)
    ft = sheet(args.full_text)
    citation = sheet(args.citation_screening)
    citation_ft = sheet(args.citation_full_text)
    result = {'database_counts': summary['source_counts'], 'duplicates_removed': summary['duplicates_removed'], 'screened': None, 'title_abstract_excluded': None, 'full_text_not_retrieved': None, 'full_text_assessed': None, 'full_text_excluded_by_code': None, 'included': None, 'citation_identified': None, 'citation_screened': None, 'citation_excluded': None, 'citation_not_retrieved': None, 'citation_assessed': None, 'citation_excluded_by_code': None, 'citation_included': None}
    if completed(ta, 'final_decision', ('include', 'exclude')):
        result['screened'] = len(ta)
        result['title_abstract_excluded'] = sum(str(r['final_decision']).strip().lower() == 'exclude' for r in ta)
    if completed(ft, 'fulltext_retrieved', ('yes', 'no')):
        result['full_text_not_retrieved'] = sum(str(r['fulltext_retrieved']).strip().lower() == 'no' for r in ft)
        retrieved = [r for r in ft if str(r['fulltext_retrieved']).strip().lower() == 'yes']
        result['full_text_assessed'] = len(retrieved)
        if completed(retrieved, 'final_decision', ('include', 'exclude')) and all(r.get('final_code') for r in retrieved if str(r['final_decision']).strip().lower() == 'exclude'):
            result['full_text_excluded_by_code'] = dict(Counter(str(r['final_code']).strip() for r in retrieved if str(r['final_decision']).strip().lower() == 'exclude'))
            result['included'] = sum(str(r['final_decision']).strip().lower() == 'include' for r in retrieved)
    if citation is not None:
        result['citation_identified'] = len(citation)
        if completed(citation, 'final_decision', ('include', 'exclude')):
            result['citation_screened'] = len(citation)
            result['citation_excluded'] = sum(str(r['final_decision']).strip().lower() == 'exclude' for r in citation)
    if completed(citation_ft, 'fulltext_retrieved', ('yes', 'no')):
        result['citation_not_retrieved'] = sum(str(r['fulltext_retrieved']).strip().lower() == 'no' for r in citation_ft)
        retrieved = [r for r in citation_ft if str(r['fulltext_retrieved']).strip().lower() == 'yes']
        result['citation_assessed'] = len(retrieved)
        if completed(retrieved, 'final_decision', ('include', 'exclude')) and all(r.get('final_code') for r in retrieved if str(r['final_decision']).strip().lower() == 'exclude'):
            result['citation_excluded_by_code'] = dict(Counter(str(r['final_code']).strip() for r in retrieved if str(r['final_decision']).strip().lower() == 'exclude'))
            result['citation_included'] = sum(str(r['final_decision']).strip().lower() == 'include' for r in retrieved)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    print(text)
    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
