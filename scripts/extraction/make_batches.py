"""Assign study_ids to included records and split them into extraction batches.

Writes extraction/study_ids.csv (study_id, record_id, title, doi, year, venue, text_file, text_version, text_status;
the last two come from extraction/fulltext_restore_log.csv, so run restore_fulltext.py first)
and extraction/batches/batch_NN.list (tab-separated study_id, record_id, title), <= --size per batch.
study_id order = record_id order, so reruns give the same IDs.

Usage: .venv/bin/python scripts/extraction/make_batches.py [--size 25] [--scope extraction/scope_restriction.csv]
"""
import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def text_version(entry, hosts):
    """Which version the extraction text comes from: preprint / publisher-or-repository / pmc_xml / abstract_only."""
    if not entry:
        return ''
    if entry['status'] == 'ok_abstract_only':
        return 'abstract_only'
    if entry['kind'] == 'xml':
        return 'pmc_xml'
    return 'preprint' if any(h in entry['url'].lower() for h in hosts) else 'publisher_or_repository'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--size', type=int, default=25)
    p.add_argument('--scope', help='extraction/scope_restriction.csv: batch only rows whose author_decision '
                   '(or, if empty, suggestion) is keep/check; study_ids stay those of the 174')
    a = p.parse_args()
    rows = [r for r in csv.DictReader(open(ROOT / 'screening/full_text.csv', encoding='utf-8-sig'))
            if r['final_decision'] == 'include']
    rows.sort(key=lambda r: r['record_id'])
    out = ROOT / 'extraction'
    (out / 'batches').mkdir(parents=True, exist_ok=True)
    log_path = out / 'fulltext_restore_log.csv'
    log = {r['record_id']: r for r in csv.DictReader(open(log_path, encoding='utf-8-sig'))} if log_path.exists() else {}
    preprint_hosts = ('medrxiv', 'biorxiv', 'arxiv', 'researchsquare', 'preprints.org', 'ssrn')
    ids = []
    for i, r in enumerate(rows, 1):
        ids.append(dict(study_id=f'S{i:03d}', record_id=r['record_id'], title=r['title'], doi=r['doi'],
                        year=r['year'], venue=r['venue'], text_file=f'fulltext_text_ft/{r["record_id"]}.txt',
                        text_version=text_version(log.get(r['record_id']), preprint_hosts),
                        text_status=(log.get(r['record_id']) or {}).get('status', '')))
    with open(out / 'study_ids.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, list(ids[0]))
        w.writeheader()
        w.writerows(ids)
    if a.scope:
        sc = {r['record_id']: (r['author_decision'] or r['suggestion']) for r in csv.DictReader(open(a.scope, encoding='utf-8-sig'))}
        ids = [x for x in ids if sc.get(x['record_id']) in ('keep', 'check')]
        for old in (out / 'batches').glob('batch_*.list'):
            old.unlink()
    n = 0
    for b in range(0, len(ids), a.size):
        n += 1
        chunk = ids[b:b + a.size]
        (out / 'batches' / f'batch_{n:02d}.list').write_text(
            ''.join(f'{x["study_id"]}\t{x["record_id"]}\t{x["title"]}\n' for x in chunk), encoding='utf-8')
    print(f'{len(ids)} studies batched, {n} batches')


if __name__ == '__main__':
    main()
