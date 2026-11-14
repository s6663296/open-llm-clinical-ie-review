import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

class PairingTests(unittest.TestCase):
    def test_pairing_requires_same_dataset_metric_and_level(self):
        from analyze import pair_results
        common = {'study_id': 'S001', 'task': 'NER', 'dataset': 'TestSet', 'metric': 'F1', 'eval_level': 'entity'}
        rows = [dict(common, model='TestModel-A', is_best_open='yes', value=.8), dict(common, model='TestModel-B', model_class='closed LLM', is_best_comparator='yes', value=.7), dict(common, model='Wrong', model_class='BERT-type', is_best_comparator='yes', value=.5, eval_level='document')]
        pairs, unpaired = pair_results(rows)
        self.assertEqual(len(pairs), 1)
        self.assertAlmostEqual(pairs[0]['difference'], .1)
        self.assertEqual(len(unpaired), 1)
