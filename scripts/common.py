import csv, re, unicodedata, html
from pathlib import Path

FIELDS = 'source_db source_id title abstract authors first_author year venue doi pmid arxiv_id pub_type language keywords url source_file'.split()

def normalize_doi(value):
    return re.sub(r'^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)', '', (value or '').strip(), flags=re.I).strip().lower()

def normalize_title(value):
    value = ''.join(c for c in unicodedata.normalize('NFKD', html.unescape(value or '')) if not unicodedata.combining(c)).lower()
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', value).split())

def first_author(value):
    author = (value or '').split(';')[0].strip()
    if ',' in author: return author.split(',')[0].strip()
    parts = author.split()
    if not parts: return ''
    if len(parts) == 1: return parts[0]
    return parts[-1] if parts[0].endswith('.') else parts[0]

def read_csv(path):
    with open(path, encoding='utf-8-sig', newline='') as f: return list(csv.DictReader(f))

def write_csv(path, rows, fields):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore'); w.writeheader(); w.writerows(rows)
