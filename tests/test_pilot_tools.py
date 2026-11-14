import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


def write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


class PilotTests(unittest.TestCase):
    def test_matches_by_priority_and_arxiv_version(self):
        from record_matching import match_rows
        suggestions = [
            {'doi': '10/a', 'pmid': '2', 'arxiv_id': '', 'title': 'Other'},
            {'doi': '10/b', 'pmid': '1', 'arxiv_id': '1234.5678v2', 'title': 'Title'},
        ]
        matches = match_rows([{'doi': 'https://doi.org/10/a', 'pmid': '1'},
                              {'arxiv_id': '1234.5678v1'}, {'title': 'TITLE!'},
                              {'title': 'Missing'}], suggestions, arxiv=True)
        self.assertEqual(matches, [0, 1, 1, None])

    def test_validation_and_sheet_cli(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            records = base / 'pubmed' / 'records.csv'
            validation = base / 'validation.csv'
            suggestions = base / 'suggestions.csv'
            write(records, [{'record_id': 'R1', 'doi': '10/a', 'pmid': '', 'arxiv_id': '', 'title': 'Hello', 'abstract': 'Text'}])
            write(validation, [{'val_id': 'V1', 'doi': '10/a', 'pmid': '', 'title': 'Hello'}, {'val_id': 'V2', 'doi': '', 'pmid': '', 'title': 'Missing'}])
            write(suggestions, [{'doi': '10/a', 'pmid': '', 'arxiv_id': '', 'title': 'Hello', 'agent_suggestion': 'unsure', 'agent_reason': '待確認', 'agent_signals': 'Text'}])
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/check_validation.py'), '--validation', str(validation), '--records', str(records), '--out', str(base / 'out.csv')], capture_output=True, text=True, check=True)
            self.assertIn('pubmed: 1', result.stdout)
            with (base / 'out.csv').open(encoding='utf-8-sig', newline='') as stream:
                self.assertEqual([r['pubmed'] for r in csv.DictReader(stream)], ['yes', 'no'])
            subprocess.run([sys.executable, str(ROOT / 'scripts/make_screening_sheet.py'), '--records', str(records), '--out', str(base / 'sheet.xlsx'), '--stage', 'title_abstract', '--agent-suggestions', str(suggestions)], check=True, capture_output=True)
            book = load_workbook(base / 'sheet.xlsx')
            rows = list(book['screening'].values)
            record = dict(zip(rows[0], rows[1]))
            self.assertEqual(record['agent_suggestion'], 'unsure')
            self.assertEqual(record['agent_reason'], '待確認 [signals: Text]')
            book.close()

    def test_prisma_content_and_box_height(self):
        from prisma_flow import database_label, box_height
        label = database_label({'PubMed': 242, 'Scopus': 10})
        self.assertIn('Databases (n = 252):', label)
        self.assertIn('PubMed (n = 242)', label)
        self.assertGreater(box_height('a\nb\nc\nd\ne\nf'), box_height('a\nb'))


if __name__ == '__main__':
    unittest.main()
