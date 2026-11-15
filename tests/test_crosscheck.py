import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts' / 'extraction'))
import crosscheck

class CrosscheckTests(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(crosscheck.normalize_model('Llama3.3-70B'), crosscheck.normalize_model('llama 3.3_70b'))

    def test_model_variants(self):
        cases = [
            ('LLaMA 3.2', 'LLaMA 3.2 (RAG)'),
            ('MedGemma 27B', 'MedGemma-27B-it (Q4_K_XL)'),
            ('DeepSeek-R1', 'DeepSeek-R1 (UD-IQ1_S)'),
            ('DeepSeek', 'DeepSeek NR'),
            ('Meta-Llama-3.1-8B-Instruct', 'Llama-3.1-8B-Instruct'),
            ('Llama 3.1 405B', 'Llama-3.1-405B-Instruct'),
            ('Llama 3 8B', 'Llama-3-8B-Instruct'),
            ('Llama-3.3-70B-Instruct', 'Llama-3.3-70B'),
            ('Qwen 2.5', 'Qwen-2.5-7B'),
            ('Qwen2.5-72B', 'Qwen2.5-72B with dynamic RAG few-shot'),
            ('Qwen2.5-7B-FT', 'Qwen2.5-7B (fine-tuned)'),
        ]
        for a, b in cases:
            with self.subTest(a=a, b=b):
                self.assertTrue(crosscheck.models_match(a, b)[0])
        self.assertEqual(crosscheck.models_match('Qwen 2.5', 'Qwen-2.5-7B'), (True, True))
        for a, b in [('Flan-T5-XXL', 'Mixtral-8x7B-Instruct-v0.1'),
                     ('Llama-3.1-70B-Instruct', 'Qwen2.5-32B-Instruct'),
                     ('DeepSeek', 'DeepSeek-R1')]:
            with self.subTest(a=a, b=b):
                self.assertFalse(crosscheck.models_match(a, b)[0])

    def test_prefix_variant_detail(self):
        a = {'model': 'Qwen 2.5', 'value': '0.9'}
        b = {'model': 'Qwen 2.5 7B', 'value': '0.9'}
        self.assertEqual(crosscheck.determine_status(a, b), 'agree')
        self.assertIn('??????????????', crosscheck.describe('agree', a, b, None, None, []))

    def test_choose_preserves_source_value(self):
        row = {'model': 'X', 'value': '0.9470000000000001', 'is_best_open': 'yes'}
        self.assertEqual(crosscheck.choose([row], 'open')[0]['value'], '0.9470000000000001')

    def test_values(self):
        self.assertEqual(crosscheck.compare_values('0.940', '94'), (True, True))
        self.assertEqual(crosscheck.compare_values('0.940', '0.945'), (True, False))
        self.assertEqual(crosscheck.compare_values('0.940', '0.946'), (False, False))

    def test_statuses(self):
        def row(model='Llama', value='0.9'):
            return {'model': model, 'value': value}
        cases = [
            (row(), row(), None, None, 'agree'),
            (row(), row(value='0.8'), None, None, 'differ_value'),
            (row(), row(model='Qwen'), None, None, 'differ_model'),
            (row(), row(), row('GPT', '0.8'), row('GPT', '0.7'), 'differ_closed'),
            (row(), None, None, None, 'missing_174'),
            (None, row(), None, None, 'missing_62'),
        ]
        for a, b, c, d, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(crosscheck.determine_status(a,b,c,d), expected)

if __name__ == '__main__':
    unittest.main()
