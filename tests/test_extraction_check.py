import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts' / 'extraction'))
from check_batch import check  # noqa: E402
from fields import RESULT_FIELDS, STUDY_FIELDS  # noqa: E402

STUDY = dict(zip(STUDY_FIELDS, [
    'S001', 'R0001', 'Smith', '2025', 'journal', 'English', 'p.1', 'radiology report', 'p.1', 'oncology',
    'in-house', 'p.1', 'NER', 'tumour size', 'p.1', 'Llama-3-8B', 'p.1', 'no', 'GPT-4o', 'none', 'none',
    'p.2', 'zero-shot', 'p.1', 'local', 'p.1', '', 'codex']))
OPEN = dict(zip(RESULT_FIELDS, [
    'S001-R01', 'S001', 'tumour', 'NER', 'in-house', '200 reports', 'Llama-3-8B', 'open LLM', 'Llama', '8',
    'no', 'zero-shot', '', 'no', 'F1', 'micro', '91.2', 'percent', '0.912', 'entity', 'strict', 'yes', 'no',
    'p.2 Table 1', 'Table 1 Llama 91.2 GPT-4o 93.0', '', 'codex']))
CLOSED = dict(OPEN, result_id='S001-R02', model='GPT-4o', model_class='closed LLM', model_family='NA',
              params_b='NR', is_best_open='no', is_best_comparator='yes', value_reported='93.0', value='0.93')
TRIVIAL = dict(OPEN, value_reported='0', value='0', metric_scale_original='0-1')


class CheckBatchTests(unittest.TestCase):
    def run_check(self, results, page2='Table 1 Llama 91.2 GPT-4o 93.0'):
        d = Path(tempfile.mkdtemp())
        (d / 'b.list').write_text('S001\tR0001\tTitle\n', encoding='utf-8')
        (d / 'R0001.txt').write_text(f'=== p.1 ===\nmethods\n=== p.2 ===\n{page2}\n', encoding='utf-8')
        for name, fields, rows in (('s.csv', STUDY_FIELDS, [STUDY]), ('r.csv', RESULT_FIELDS, results)):
            with open(d / name, 'w', newline='', encoding='utf-8') as f:
                w = csv.DictWriter(f, fields)
                w.writeheader()
                w.writerows(rows)
        return check(d / 'b.list', d / 's.csv', d / 'r.csv', d)[0]

    def test_valid(self):
        self.assertEqual(self.run_check([OPEN, CLOSED]), [])

    def test_value_not_on_page(self):
        errs = self.run_check([OPEN], page2='Table 1 nothing here')
        self.assertTrue(any('not found verbatim' in e for e in errs))

    def test_trivial_value_rejected(self):
        errs = self.run_check([TRIVIAL])
        self.assertTrue(any('too trivial' in e for e in errs))

    def test_context_must_be_on_page(self):
        errs = self.run_check([dict(OPEN, value_context='Llama reached 91.2 F1 on the test set')])
        self.assertTrue(any('not found verbatim' in e for e in errs))

    def test_scale_mismatch(self):
        errs = self.run_check([dict(OPEN, value='0.812')])
        self.assertTrue(any('!= value_reported' in e for e in errs))

    def test_missing_best_open(self):
        errs = self.run_check([dict(OPEN, is_best_open='no')])
        self.assertTrue(any('exactly one is_best_open' in e for e in errs))

    def test_bad_controlled_value(self):
        errs = self.run_check([dict(OPEN, metric='F-score')])
        self.assertTrue(any('metric=' in e for e in errs))


if __name__ == '__main__':
    unittest.main()
