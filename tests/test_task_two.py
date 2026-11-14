import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

class TaskTwoTests(unittest.TestCase):
    def test_html_entities_normalized(self):
        from common import normalize_title
        self.assertEqual(normalize_title('A &amp; B'), 'a b')

    def test_form_tables(self):
        from form_common import codebook_tables, questions
        tables = codebook_tables()
        self.assertIn('pub_type', [r[0] for r in tables['studies']])
        self.assertIn('value_src', [r[0] for r in tables['results']])
        self.assertIn('1.1', dict(questions()))
        self.assertIn('4.4', dict(questions()))

    def test_rob_judgement(self):
        from make_rob_form import overall
        self.assertEqual(overall(['Low'] * 4), 'Low')
        self.assertEqual(overall(['Low', 'High', 'Low', 'Low']), 'High')
        self.assertEqual(overall(['Low', '', 'Low', 'High']), '')

    def test_query_blocks_match_protocol(self):
        from build_queries import protocol_blocks, load_blocks, expand
        self.assertEqual(load_blocks(), protocol_blocks())
        self.assertEqual(expand('discharge summar*'), ['discharge summary', 'discharge summaries'])

    def test_abstract_reconstruction(self):
        from citation_search import abstract_text
        self.assertEqual(abstract_text({'world': [1], 'hello': [0]}), 'hello world')

    def test_substitution(self):
        from fill_manuscript import substitute
        text, missing = substitute('{{N}} {{X}}', {'N': 0})
        self.assertEqual(text, '0 {{X}}')
        self.assertEqual(missing, ['X'])
