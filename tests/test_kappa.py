import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from kappa import calculate
class KappaTests(unittest.TestCase):
    def test_perfect(self):
        self.assertEqual(calculate([('include','include'),('exclude','exclude')],['include','exclude'])['kappa'], 1)
    def test_known(self):
        pairs = [('include','include')]*20+[('include','exclude')]*5+[('exclude','include')]*10+[('exclude','exclude')]*15
        r=calculate(pairs,['include','exclude'])
        self.assertAlmostEqual(r['observed_agreement'], .7)
        self.assertAlmostEqual(r['kappa'], .4)
    def test_no_data(self):
        self.assertIsNone(calculate([],['include','exclude'])['kappa'])
