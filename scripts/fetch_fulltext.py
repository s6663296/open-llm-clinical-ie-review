"""Retrieve openly available full texts and prepare a manual retrieval list."""
import argparse
import hashlib
import os
import re
import shutil
import time
from pathlib import Path
from urllib.parse import quote, urljoin, urlparse

import requests
from openpyxl import load_workbook
from common import normalize_doi, read_csv, write_csv
from record_matching import normalize_arxiv

LOG_FIELDS = 'record_id doi title status source url bytes sha256 note'.split()
MANUAL_FIELDS = 'record_id doi title doi_url'.split()

class Client:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'sr-fulltext-fetcher/1.0'})
        self.last = {}
        self.errors = []

    def request(self, url):
        for attempt in range(3):
            try:
                current = url
                for _ in range(11):
                    parsed = urlparse(current)
                    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
                        raise ValueError('invalid HTTP URL')
                    host = parsed.hostname.lower()
                    delay = 1 - (time.monotonic() - self.last.get(host, -1e9))
                    if delay > 0: time.sleep(delay)
                    self.last[host] = time.monotonic()
                    response = self.session.get(current, timeout=30, allow_redirects=False)
                    if response.is_redirect:
                        current = urljoin(current, response.headers['Location'])
                        continue
                    response.raise_for_status()
                    return response
                raise ValueError('too many redirects')
            except (requests.RequestException, ValueError, KeyError) as exc:
                if attempt == 2:
                    self.errors.append(f'{url}: {exc}')
                    return None
        return None

    def json(self, url):
        response = self.request(url)
        if response is None: return None
        try: return response.json()
        except ValueError:
            self.errors.append(f'{url}: invalid JSON')
            return None

    def pdf(self, url):
        response = self.request(url)
        if response is None: return None
        content = response.content
        content_type = response.headers.get('Content-Type', '').split(';', 1)[0].strip().lower()
        if content.lstrip().lower().startswith((b'<!doctype html', b'<html')):
            self.errors.append(f'{url}: HTML response')
            return None
        if content and (content.startswith(b'%PDF') or content_type == 'application/pdf'):
            return content
        self.errors.append(f'{url}: not a PDF')
        return None

def valid_existing(path):
    with path.open('rb') as stream: return stream.read(4) == b'%PDF'

def fetch_record(row, out_dir, client, dry_run=False):
    record_id = str(row.get('record_id') or '').strip()
    if not record_id or record_id in ('.', '..') or re.search(r'[\\/:*?"<>|\x00-\x1f]', record_id):
        raise ValueError(f'Invalid record_id: {record_id!r}')
    doi = normalize_doi(str(row.get('doi') or ''))
    pmid = str(row.get('pmid') or '').strip()
    raw_arxiv = str(row.get('arxiv_id') or '').strip()
    version = re.search(r'(v\d+)(?:\.pdf)?$', raw_arxiv, re.I)
    arxiv = normalize_arxiv(raw_arxiv) + (version.group(1).lower() if version else '')
    path = out_dir / f'{record_id}.pdf'
    result = dict(record_id=record_id, doi=doi, title=row.get('title') or '', status='', source='', url='', bytes='', sha256='', note='')
    if path.is_file() and valid_existing(path):
        data = path.read_bytes(); result.update(status='exists', bytes=len(data), sha256=hashlib.sha256(data).hexdigest()); return result
    if dry_run:
        result.update(status='failed', note='dry-run: no requests or downloads'); return result
    start_errors = len(client.errors) if isinstance(client.errors, list) else 0
    tried = set()
    def download(url, source):
        if not url or url in tried: return False
        tried.add(url)
        data = client.pdf(url)
        if data is None: return False
        out_dir.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        result.update(status='downloaded', source=source, url=url, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        return True
    if arxiv and download('https://arxiv.org/pdf/' + quote(arxiv, safe='/'), 'arxiv'): return result
    if doi or pmid:
        key = 'doi:' + quote(doi, safe='/') if doi else 'pmid:' + quote(pmid, safe='')
        work = client.json('https://api.openalex.org/works/' + key)
        if isinstance(work, dict):
            locations = [work.get('best_oa_location') or {}] + [x for x in (work.get('locations') or []) if x and x.get('is_oa') is True]
            for loc in locations:
                if download(loc.get('pdf_url'), 'openalex'): return result
    if pmid:
        data = client.json('https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=' + quote('EXT_ID:' + pmid + ' AND SRC:MED', safe='') + '&format=json')
        if isinstance(data, dict):
            for item in data.get('resultList', {}).get('result', []):
                pmcid = item.get('pmcid', '')
                if re.fullmatch(r'PMC\d+', pmcid) and download('https://europepmc.org/articles/' + pmcid + '?pdf=render', 'europe_pmc'): return result
    errors = client.errors[start_errors:] if isinstance(client.errors, list) else []
    result['status'] = 'failed' if errors else 'not_oa'
    result['note'] = '; '.join(errors) if errors else 'No OA PDF URL found'
    return result

def read_input(path, id_column):
    if path.suffix.lower() == '.xlsx':
        wb = load_workbook(path, read_only=True, data_only=True)
        try:
            iterator = wb['screening'].iter_rows(values_only=True)
            headers = list(next(iterator))
            rows = [dict(zip(headers, values)) for values in iterator if any(v is not None for v in values)]
        finally: wb.close()
        if 'pdf_path' not in headers and 'fulltext_retrieved' not in headers:
            if 'final_decision' not in headers: raise ValueError('Cannot identify screening stage')
            rows = [r for r in rows if str(r.get('final_decision') or '').strip().lower() == 'include']
    else: rows = read_csv(path)
    for row in rows: row['record_id'] = str(row.get(id_column) or '').strip()
    ids = [r['record_id'] for r in rows]
    if any(not x for x in ids) or len(ids) != len(set(ids)): raise ValueError('Missing or duplicate record IDs')
    return rows

def update_sheet(path, results, out_dir):
    wb = load_workbook(path)
    ws = wb['screening']
    headers = {c.value: c.column for c in ws[1]}
    if not {'record_id', 'pdf_path', 'fulltext_retrieved'} <= headers.keys(): raise ValueError('Expected full_text screening sheet columns')
    mapping = {r['record_id']: r for r in results}
    for row in ws.iter_rows(min_row=2):
        record_id = str(row[headers['record_id']-1].value or '').strip()
        if record_id not in mapping: continue
        success = mapping[record_id]['status'] in ('exists', 'downloaded')
        ws.cell(row[0].row, headers['pdf_path']).value = os.path.relpath(out_dir / (record_id + '.pdf'), path.parent).replace('\\', '/') if success else None
        ws.cell(row[0].row, headers['fulltext_retrieved']).value = 'yes' if success else 'no'
    backup = path.with_name(path.stem + '.bak.xlsx')
    shutil.copy2(path, backup)
    wb.save(path); wb.close()

def main():
    p = argparse.ArgumentParser(description='Download OA PDFs; XLSX screening sheets with pdf_path/fulltext_retrieved process all rows; title/abstract sheets process only final_decision=include.')
    p.add_argument('--input', required=True, type=Path); p.add_argument('--out-dir', type=Path, default=Path('fulltext'))
    p.add_argument('--log', type=Path); p.add_argument('--id-column', default='record_id'); p.add_argument('--limit', type=int); p.add_argument('--dry-run', action='store_true'); p.add_argument('--update-sheet', type=Path)
    a = p.parse_args()
    if a.limit is not None and a.limit < 0: p.error('--limit must be nonnegative')
    if a.dry_run and a.update_sheet: p.error('--update-sheet cannot be used with --dry-run')
    rows = read_input(a.input, a.id_column)
    if a.limit is not None: rows = rows[:a.limit]
    client = Client(); results = []
    for row in rows:
        result = fetch_record(row, a.out_dir, client, a.dry_run); results.append(result)
        print(f"{result['record_id']}: {result['status']} {result['source']}", flush=True)
    write_csv(a.log or a.out_dir/'fetch_log.csv', results, LOG_FIELDS)
    manual = [dict(record_id=r['record_id'], doi=r['doi'], title=r['title'], doi_url='https://doi.org/' + r['doi'] if r['doi'] else '') for r in results if r['status'] not in ('downloaded','exists')]
    write_csv(a.out_dir/'manual_retrieval.csv', manual, MANUAL_FIELDS)
    if a.update_sheet: update_sheet(a.update_sheet, results, a.out_dir)

if __name__ == '__main__': main()
