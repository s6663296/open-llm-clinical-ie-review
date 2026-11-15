"""Restore the full texts of included studies for D1 extraction (PDFs and text are not in git).

For each included record (screening/full_text.csv, final_decision=include):
  - PDF records: re-download the URL recorded in fulltext/fetch_log_c2.csv (fallback fetch_log.csv)
    and verify it against the recorded sha256; a mismatch is reported, never silently accepted.
  - XML records (R0861, R1214, R1331: the OA PDF was the wrong document in C2): resolve the PMCID
    from the DOI via Europe PMC and save the full-text XML (scripts/pmc_xml_to_text.py logic).
Then write page-marked text to fulltext_text_ft/<record_id>.txt (full text, references removed,
not condensed: extraction needs Results tables). Log: extraction/fulltext_restore_log.csv.

Usage: .venv/bin/python scripts/extraction/restore_fulltext.py [--only R0011,R0020]
"""
import argparse
import csv
import hashlib
import re
import sys
import time
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from pdf_to_text import convert  # noqa: E402
from pmc_xml_to_text import URL as PMC_XML_URL, to_text as xml_to_text  # noqa: E402

XML_RECORDS = {'R0861', 'R1214', 'R1331'}
LOGS = [ROOT / 'fulltext/fetch_log_c2.csv', ROOT / 'fulltext/fetch_log.csv']
FIELDS = 'record_id kind source url sha256_expected sha256_got status text_chars note'.split()


def included():
    rows = csv.DictReader(open(ROOT / 'screening/full_text.csv', encoding='utf-8-sig'))
    return [r for r in rows if r['final_decision'] == 'include']


def log_rows():
    best = {}
    for path in reversed(LOGS):  # later file (c2) overrides
        for r in csv.DictReader(open(path, encoding='utf-8-sig')):
            if r['status'] in ('downloaded', 'exists') and r['url']:
                best[r['record_id']] = r
    return best


def pmcid_for(session, doi):
    q = quote(f'DOI:"{doi}"', safe='')
    data = session.get(f'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={q}&format=json&resultType=lite', timeout=60).json()
    for item in data.get('resultList', {}).get('result', []):
        if item.get('pmcid'):
            return item['pmcid']
    return ''


def get_with_backoff(session, url, tries=5):
    """GET with slow pacing and exponential backoff on HTTP 429 (medRxiv rate limit)."""
    wait = 20
    for i in range(tries):
        r = session.get(url, timeout=120, allow_redirects=True)
        if r.status_code != 429 or i == tries - 1:
            r.raise_for_status()
            return r
        time.sleep(wait)
        wait *= 2


def title_matches(title, text):
    """True if the first 8 title words appear (letters only) within the first ~3 pages of text."""
    words = re.findall(r'[a-z0-9]+', title.lower())[:8]
    head = ''.join(re.findall(r'[a-z0-9]+', text[:15000].lower()))
    return bool(words) and ''.join(words) in head


def fetch_xml(session, rec, pdf_dir, row):
    """Europe PMC full-text XML by DOI -> page-less text (cite as p.1)."""
    pmcid = pmcid_for(session, rec['doi'])
    row.update(kind='xml', source='europe_pmc', url=pmcid, sha256_expected='', sha256_got='')
    if not pmcid:
        raise ValueError('no PMCID for DOI ' + rec['doi'])
    xml_path = pdf_dir / f'{rec["record_id"]}.xml'
    if not xml_path.exists():
        r = session.get(PMC_XML_URL.format(pmcid), timeout=90)
        r.raise_for_status()
        xml_path.write_bytes(r.content)
    row['status'] = 'ok'
    return xml_to_text(xml_path.read_bytes())


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--only', default='')
    p.add_argument('--pdf-dir', default=str(ROOT / 'fulltext'))
    p.add_argument('--out-dir', default=str(ROOT / 'fulltext_text_ft'))
    p.add_argument('--cap', type=int, default=150000)
    a = p.parse_args()
    only = set(filter(None, a.only.split(',')))
    pdf_dir, out_dir = Path(a.pdf_dir), Path(a.out_dir)
    pdf_dir.mkdir(exist_ok=True)
    out_dir.mkdir(exist_ok=True)
    s = requests.Session()
    s.headers['User-Agent'] = 'sr-fulltext-fetcher/1.0'
    logs = log_rows()
    mpath = ROOT / 'extraction/fulltext_manual_checks.csv'
    manual = {r['record_id']: r for r in csv.DictReader(open(mpath, encoding='utf-8-sig'))} if mpath.exists() else {}
    out = []
    for rec in included():
        rid = rec['record_id']
        if only and rid not in only:
            continue
        row = dict(record_id=rid, kind='', source='', url='', sha256_expected='', sha256_got='', status='', text_chars='', note='')
        try:
            if rid in XML_RECORDS:
                text = fetch_xml(s, rec, pdf_dir, row)
            else:
                lg = logs[rid]
                pdf = pdf_dir / f'{rid}.pdf'
                row.update(kind='pdf', source=lg['source'], url=lg['url'], sha256_expected=lg['sha256'])
                if not pdf.exists():
                    r = get_with_backoff(s, lg['url'])
                    if not r.content.startswith(b'%PDF'):
                        raise ValueError('response is not a PDF')
                    pdf.write_bytes(r.content)
                    time.sleep(5 if 'medrxiv' in lg['url'] else 1)
                got = hashlib.sha256(pdf.read_bytes()).hexdigest()
                row['sha256_got'] = got
                text = convert(pdf, a.cap)
                if got == lg['sha256']:
                    row['status'] = 'ok'
                elif title_matches(rec['title'], text):
                    # medRxiv and some repositories regenerate the PDF on each download (stamps/metadata)
                    row['status'] = 'ok_title_match'
                    row['note'] = 'sha256 differs from C2 download (server regenerates PDF); title found on first pages'
                elif manual.get(rid, {}).get('verdict') == 'same_study':
                    row['status'] = 'ok_manual'
                    row['note'] = 'title differs (preprint version / layout); same study confirmed in extraction/fulltext_manual_checks.csv'
                else:
                    row['status'] = 'sha256_mismatch'
                    row['note'] = 'file differs from C2 download and title not found; check paper/version'
            (out_dir / f'{rid}.txt').write_text(text, encoding='utf-8', errors='replace')
            row['text_chars'] = len(text)
            if manual.get(rid, {}).get('verdict') == 'abstract_only':
                row['status'] = 'ok_abstract_only'
                row['note'] = (row['note'] + '; ' if row['note'] else '') + manual[rid]['note']
            if len(text) < 5000:
                row['note'] = (row['note'] + '; ' if row['note'] else '') + 'very little text'
        except Exception as exc:  # PDF failed: try Europe PMC XML, else report
            try:
                text = fetch_xml(s, rec, pdf_dir, row)
                row['note'] = 'PDF failed (' + str(exc)[:120] + '); used Europe PMC XML, unpaginated (p.1)'
                (out_dir / f'{rid}.txt').write_text(text, encoding='utf-8', errors='replace')
                row['text_chars'] = len(text)
            except Exception as exc2:
                row['status'] = 'failed'
                row['note'] = (str(exc)[:200] + ' | XML fallback: ' + str(exc2)[:100])
        print(rid, row['status'], row['text_chars'], row['note'])
        out.append(row)
    log = ROOT / 'extraction/fulltext_restore_log.csv'
    if only and log.exists():
        keep = [r for r in csv.DictReader(open(log, encoding='utf-8-sig')) if r['record_id'] not in only]
        out = sorted(keep + out, key=lambda r: r['record_id'])
    with open(log, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        w.writerows(out)
    bad = [r['record_id'] for r in out if not r['status'].startswith('ok')]
    print(f'ok {len(out) - len(bad)}, problems {len(bad)}: {bad}')


if __name__ == '__main__':
    main()
