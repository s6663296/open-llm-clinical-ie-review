"""Generate database queries from the protocol vocabulary."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUERY = ROOT / 'scripts' / 'queries'


def protocol_blocks():
    """Read the three literal vocabulary lists from the protocol."""
    text = (ROOT / 'protocol/protocol.md').read_text(encoding='utf-8')
    section = text.split('#### 3.4.1', 1)[1].split('#### 3.4.2', 1)[0]
    result = {}
    for line in section.splitlines():
        match = re.match(r'^\|\s*([ABC])\.[^|]*\|\s*(.*?)\s*\|$', line)
        if match:
            result[match.group(1)] = [x.strip() for x in match.group(2).split(',')]
    return result


def load_blocks():
    """Load the shared vocabulary."""
    return json.loads((QUERY / 'blocks.json').read_text(encoding='utf-8-sig'))


def expand(term):
    """Expand phrase wildcards conservatively; keep single-word truncation."""
    if '*' not in term or (' ' not in term and term != 'open-weight*'):
        return [term]
    if term.endswith('summar*'):
        return [term[:-7] + 'summary', term[:-7] + 'summaries']
    stem = term.replace('*', '')
    return [stem, stem + 's']


def quote(term):
    """Quote phrases and punctuation-bearing terms."""
    return f'"{term}"' if ' ' in term or '-' in term else term


def build(blocks, kind):
    """Render one query in the requested database syntax."""
    groups = []
    for values in blocks.values():
        terms = values if kind == 'scopus' else [v for term in values for v in expand(term)]
        if kind == 'ieee':
            group = ' OR '.join('"All Metadata":' + quote(v) for v in terms)
        elif kind == 'acm':
            joined = ' OR '.join(quote(v) for v in terms)
            group = ' OR '.join(f'{field}:({joined})' for field in ('Title', 'Abstract', 'Keyword'))
        else:
            group = ' OR '.join(quote(v) for v in terms)
        groups.append('(' + group + ')')
    combined = ' AND\n'.join(groups)
    return 'TITLE-ABS-KEY(\n' + combined + '\n) AND PUBYEAR > 2021\n' if kind == 'scopus' else combined + '\n'


def main():
    """Write queries and instructions without changing existing API queries."""
    blocks = load_blocks()
    for name in ('scopus', 'ieee', 'acm'):
        (QUERY / f'{name}.txt').write_text(build(blocks, name), encoding='utf-8')
    midpoint = (len(blocks['A']) + 1) // 2
    for index, subset in enumerate((blocks['A'][:midpoint], blocks['A'][midpoint:]), 1):
        split = dict(blocks)
        split['A'] = subset
        (QUERY / f'ieee_split_A{index}.txt').write_text(build(split, 'ieee'), encoding='utf-8')
    instructions = '''# 檢索字串\n\n- `scopus.txt`：貼至 Scopus Advanced search；另限制 2022–2026。\n- `ieee.txt`：貼至 IEEE Xplore Advanced Search；另限制 2022–2026。`ieee_split_A1.txt` 與 `ieee_split_A2.txt` 為分批備用，須合併去重。\n- `acm.txt`：貼至 ACM Digital Library Advanced Search；另限制 2022–2026。\n\n介面實際解析可能改變，執行後把介面顯示的最終查詢字串與筆數記錄到 `searches/<日期>/<db>/search_log.json`：\n\n```json\n{"database": null, "interface": null, "query": null, "executed_at": null, "filters": null, "n_results": null, "exported_files": [], "notes": null}\n```\n'''
    (QUERY / 'README.md').write_text(instructions, encoding='utf-8')


if __name__ == '__main__':
    main()
