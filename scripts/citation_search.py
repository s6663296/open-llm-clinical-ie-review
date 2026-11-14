"""Trace citations using OpenAlex while preserving raw API responses."""
import argparse
import json
import re
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from common import FIELDS, normalize_doi, normalize_title, read_csv, write_csv
from search_common import Client
import requests

BASE = 'https://api.openalex.org'


def abstract_text(index):
    """Restore an abstract from OpenAlex's position index."""
    if not index:
        return ''
    positions = {position: word for word, offsets in index.items() for position in offsets}
    return ' '.join(positions.get(i, '') for i in range(max(positions) + 1)).strip() if positions else ''


def record(work, direction):
    """Map an OpenAlex work to the common record schema."""
    authors = '; '.join(x.get('author', {}).get('display_name', '') for x in work.get('authorships', []))
    location = work.get('primary_location') or {}
    source = location.get('source') or {}
    return {'source_db': 'OpenAlex ' + direction, 'source_id': work.get('id', ''), 'title': work.get('title') or '', 'abstract': abstract_text(work.get('abstract_inverted_index')), 'authors': authors, 'first_author': authors.split(';')[0], 'year': str(work.get('publication_year') or ''), 'venue': source.get('display_name') or '', 'doi': normalize_doi(work.get('doi') or ''), 'pub_type': work.get('type') or '', 'language': work.get('language') or '', 'url': work.get('id') or '', 'source_file': 'OpenAlex API'}


def main():
    """Fetch seed works, references and citing works with raw provenance."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--direction', choices=['backward', 'forward', 'both'], default='both')
    args = parser.parse_args()
    seeds = read_csv(args.seeds)
    out = Path(args.out)
    raw = out / 'raw'
    raw.mkdir(parents=True, exist_ok=True)
    client = Client(.2)
    counter = 0
    def get(path, params):
        """Save each response before parsing it."""
        nonlocal counter
        response = client.get(BASE + path, params)
        counter += 1
        (raw / f'{counter:05d}.json').write_text(response.text, encoding='utf-8')
        return response.json()
    matched = []
    unmatched = []
    for seed in seeds:
        doi = normalize_doi(seed.get('doi', ''))
        title = seed.get('title', '')
        if doi:
            try:
                work = get('/works/doi:' + doi, {})
            except requests.HTTPError as exc:
                if exc.response is None or exc.response.status_code != 404:
                    raise
                unmatched.append({'seed': seed, 'reason': 'DOI not found'})
                continue
        elif title:
            found = get('/works', {'search': title, 'per-page': 1}).get('results', [])
            work = found[0] if found else None
            similarity = SequenceMatcher(None, normalize_title(title), normalize_title((work or {}).get('title') or '')).ratio()
            if similarity < .9:
                unmatched.append({'seed': seed, 'similarity': similarity})
                continue
        else:
            unmatched.append({'seed': seed, 'reason': 'missing DOI and title'})
            continue
        matched.append(work)
    output = []
    totals = {name: {'before_filter': 0, 'after_filter': 0} for name in ('backward', 'forward')}
    for work in matched:
        for direction in ('backward', 'forward'):
            if args.direction not in (direction, 'both'):
                continue
            works = []
            if direction == 'backward':
                ids = [x.rsplit('/', 1)[-1] for x in work.get('referenced_works', [])]
                for i in range(0, len(ids), 50):
                    works.extend(get('/works', {'filter': 'openalex:' + '|'.join(ids[i:i + 50]), 'per-page': 50}).get('results', []))
            else:
                cursor = '*'
                while cursor:
                    page = get('/works', {'filter': 'cites:' + work['id'].rsplit('/', 1)[-1], 'per-page': 200, 'cursor': cursor})
                    works.extend(page.get('results', []))
                    cursor = page.get('meta', {}).get('next_cursor')
            retained = [w for w in works if (w.get('publication_year') or 0) >= 2022]
            totals[direction]['before_filter'] += len(works)
            totals[direction]['after_filter'] += len(retained)
            output.extend(record(w, direction) for w in retained)
    write_csv(out / 'records.csv', output, FIELDS)
    log = {'seed_count': len(seeds), 'matched_count': len(matched), 'unmatched': unmatched, 'directions': totals, 'executed_at': datetime.now().astimezone().isoformat()}
    text = json.dumps(log, ensure_ascii=False, indent=2)
    (out / 'search_log.json').write_text(text + '\n', encoding='utf-8')
    print(text)


if __name__ == '__main__':
    main()
