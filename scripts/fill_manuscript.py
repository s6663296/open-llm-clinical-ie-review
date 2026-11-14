"""Fill known manuscript placeholders without altering the source."""
import json
import re
from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parents[1]
PATTERN = re.compile(r'\{\{([A-Z][A-Z0-9_]*)\}\}')


def substitute(text, values):
    """Replace known values and return all remaining keys."""
    def replace(match):
        """Keep missing and null values visible for manual completion."""
        value = values.get(match.group(1))
        return str(value) if value is not None else match.group(0)
    result = PATTERN.sub(replace, text)
    return result, sorted(set(PATTERN.findall(result)))


def main():
    """Merge available value files and write a filled copy and inventory."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--strict', action='store_true')
    args = parser.parse_args()
    manuscript = ROOT / 'manuscript'
    text = (manuscript / 'manuscript.md').read_text(encoding='utf-8')
    keys = sorted(set(PATTERN.findall(text)))
    manual = manuscript / 'values.json'
    if not manual.exists():
        manual.write_text(json.dumps({key: None for key in keys}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    values = {}
    sources = {}
    for file in (ROOT / 'analysis/prisma_counts.json', ROOT / 'analysis/results_numbers.json', manual):
        if not file.exists():
            continue
        data = json.loads(file.read_text(encoding='utf-8-sig'))
        if file.name == 'prisma_counts.json':
            aliases = {'duplicates_removed': 'N_DUPLICATES', 'screened': 'N_SCREENED', 'title_abstract_excluded': 'N_EXCLUDED_TA', 'full_text_not_retrieved': 'N_NOT_RETRIEVED', 'full_text_assessed': 'N_ASSESSED', 'citation_identified': 'N_CITATION', 'citation_included': 'N_CITATION_INCLUDED'}
            data.update({alias: data.get(key) for key, alias in aliases.items()})
            counts = data.get('database_counts')
            if isinstance(counts, dict) and all(isinstance(v, int) for v in counts.values()):
                data['N_IDENTIFIED'] = sum(counts.values())
                data['N_BY_SOURCE'] = ', '.join(f'{k}: {v}' for k, v in counts.items())
            if data.get('screened') is not None and data.get('title_abstract_excluded') is not None:
                data['N_SOUGHT'] = data['screened'] - data['title_abstract_excluded']
            if data.get('included') is not None and data.get('citation_included') is not None:
                data['N_REPORTS'] = data['included'] + data['citation_included']
            reasons = data.get('full_text_excluded_by_code')
            if isinstance(reasons, dict):
                data['N_EXCLUDED_FT'] = sum(reasons.values())
                data['FT_EXCLUSION_REASONS'] = ', '.join(f'{k}: {v}' for k, v in reasons.items())
        for key, value in data.items():
            upper = key.upper()
            if value is not None and not isinstance(value, (dict, list)):
                values[upper] = value
                sources[upper] = str(file.relative_to(ROOT)).replace('\\', '/')
    filled, missing = substitute(text, values)
    (manuscript / 'manuscript_filled.md').write_text(filled, encoding='utf-8')
    lines = ['# 稿件佔位符', '', '| 鍵 | 目前值 | 來源 |', '|---|---|---|']
    for key in keys:
        lines.append(f'| {key} | {values.get(key, "null")} | {sources.get(key, "未填")} |')
    (manuscript / 'placeholders.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('未填鍵：' + (', '.join(missing) if missing else '無'))
    if args.strict and missing:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
