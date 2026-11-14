import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from common import normalize_doi, normalize_title, first_author

class NormalizationTests(unittest.TestCase):
    def test_doi(self):
        self.assertEqual(normalize_doi(' https://doi.org/10.1234/ABC '), '10.1234/abc')
    def test_title(self):
        self.assertEqual(normalize_title('Café: Test—Title!'), 'cafe test title')
    def test_authors(self):
        for author, expected in [('Chen D','Chen'), ('A. Latif','Latif'), ('Alfaifi, Abeer','Alfaifi')]:
            with self.subTest(author=author): self.assertEqual(first_author(author), expected)
