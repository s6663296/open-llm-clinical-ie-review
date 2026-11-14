import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from common import read_csv
from build_queries import build, expand, load_blocks

class ImportEntityTests(unittest.TestCase):
    def test_bibtex_import_decodes_title_abstract_and_venue(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            bib = base / 'records.bib'
            bib.write_text('@article{x, title={A &amp; B}, abstract={C &lt; D}, journal={E &amp; F}, year={2024}}', encoding='utf8')
            config = base / 'config.json'
            config.write_text(json.dumps({'sources': [{'db': 'Test', 'format': 'bibtex', 'files': [str(bib)]}]}), encoding='utf8')
            subprocess.run([sys.executable, str(ROOT / 'scripts/import_records.py'), '--config', str(config), '--out', str(base / 'out')], check=True, capture_output=True)
            row = read_csv(base / 'out/records_raw.csv')[0]
            self.assertEqual((row['title'], row['abstract'], row['venue']), ('A & B', 'C < D', 'E & F'))
    def test_generated_term_counts(self):
        blocks = load_blocks()
        for kind in ('scopus', 'ieee', 'acm'):
            query = build(blocks, kind)
            if kind == 'scopus':
                self.assertEqual(query.count(' OR ') + 3, sum(map(len, blocks.values())))
            elif kind == 'ieee':
                self.assertEqual(query.count('"All Metadata":'), sum(len(expand(x)) for values in blocks.values() for x in values))
            else:
                expected = sum(len(expand(x)) for values in blocks.values() for x in values)
                self.assertEqual((query.count(' OR ') + 3) // 3, expected)

