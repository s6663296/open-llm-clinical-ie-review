import re
from pathlib import Path
import sys
import unittest
from openpyxl import load_workbook
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_queries import ROOT, load_blocks, build, expand

class GeneratedOutputTests(unittest.TestCase):
    def test_scopus_terms_equal_protocol_expression(self):
        text = (ROOT / 'protocol/protocol.md').read_text(encoding='utf8').split('#### 3.4.3', 1)[1].split('#### 3.4.4', 1)[0].split('```')[1]
        expected = re.findall(r'"([^"]+)"|\b(?!OR\b|AND\b|TITLE\b|ABS\b|KEY\b|PUBYEAR\b)([A-Za-z][A-Za-z0-9*]*)', text.split('AND PUBYEAR')[0])
        expected = {a or b for a, b in expected}
        terms = {term for block in load_blocks().values() for term in block}
        self.assertEqual(terms, expected)
        for kind in ('scopus', 'ieee', 'acm'):
            query = build(load_blocks(), kind)
            for term in terms:
                for variant in ([term] if kind == 'scopus' else expand(term)):
                    self.assertIn(variant, query)
    def test_templates_validation_and_formula(self):
        extraction = load_workbook(ROOT / 'extraction/extraction_TEMPLATE.xlsx')
        rob = load_workbook(ROOT / 'extraction/risk_of_bias_TEMPLATE.xlsx')
        self.assertGreater(len(extraction['studies'].data_validations.dataValidation), 0)
        self.assertGreater(len(extraction['results'].data_validations.dataValidation), 0)
        for name in ('R1', 'R2', 'consensus'):
            ws = rob[name]
            self.assertGreater(len(ws.data_validations.dataValidation), 0)
            self.assertTrue(ws.cell(3, ws.max_column).value.startswith('=IF('))
