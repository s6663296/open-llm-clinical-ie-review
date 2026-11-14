"""Fetch open-access full text XML from Europe PMC and write screening text for records whose PDF was wrong.

The XML has no page numbers, so the whole article is one '=== p.1 ===' block; cite it as (p.1).
References and back matter are dropped. Raw XML is kept next to the PDFs for reproducibility.

Usage:
  python scripts/pmc_xml_to_text.py R0861=PMC12266303 R1331=PMC10801236 [--xml-dir fulltext] [--out-dir fulltext_text]
"""
import argparse
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

URL = 'https://www.ebi.ac.uk/europepmc/webservices/rest/{}/fullTextXML'


def text_of(el):
    return re.sub(r'\s+', ' ', ''.join(el.itertext())).strip()


def to_text(xml):
    root = ET.fromstring(xml)
    parts = []
    title = root.find('.//article-meta//article-title')
    if title is not None:
        parts.append(text_of(title))
    abstract = root.find('.//article-meta/abstract')
    if abstract is not None:
        parts.append('Abstract\n' + text_of(abstract))
    body = root.find('.//body')
    if body is not None:
        for el in body.iter():
            if el.tag == 'title':
                parts.append('\n' + text_of(el))
            elif el.tag in ('p', 'caption', 'table'):
                parts.append(text_of(el))
    return '=== p.1 ===\n[source: Europe PMC full-text XML, unpaginated]\n' + '\n'.join(parts)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('pairs', nargs='+', help='record_id=PMCID')
    p.add_argument('--xml-dir', default='fulltext')
    p.add_argument('--out-dir', default='fulltext_text')
    a = p.parse_args()
    s = requests.Session()
    s.headers['User-Agent'] = 'sr-fulltext-fetcher/1.0'
    for pair in a.pairs:
        rid, pmcid = pair.split('=')
        r = s.get(URL.format(pmcid), timeout=90)
        r.raise_for_status()
        Path(a.xml_dir, f'{rid}.xml').write_bytes(r.content)
        text = to_text(r.content)
        Path(a.out_dir, f'{rid}.txt').write_text(text, encoding='utf-8')
        print(f'{rid}: {pmcid} -> {len(text)} chars')


if __name__ == '__main__':
    main()
