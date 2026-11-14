import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from import_records import parse_bibtex, parse_ris, deduplicate, abstracts
class ImportTests(unittest.TestCase):
 def test_bibtex(self):
  r=parse_bibtex((Path(__file__).parent/'fixtures/nested.bib').read_text(encoding='utf-8-sig'))
  self.assertEqual(r[0]['title'],'Test Title Alpha'); self.assertIn('second nested line',r[0]['abstract'])
 def test_ris(self):
  r=parse_ris((Path(__file__).parent/'fixtures/sample.ris').read_text(encoding='utf-8-sig'))
  self.assertEqual(r[0]['title'],'Test Title Alpha'); self.assertEqual(r[0]['abstract'],'line one line two')
 def test_rules_and_distinct_doi(self):
  rows=[dict(title='Test Alpha',year='2024',doi='10/a',pmid='1'),dict(title='Different',year='2024',doi='10/a',pmid=''),dict(title='Other',year='2024',doi='',pmid='1'),dict(title='Test Beta',year='2024',doi='',pmid=''),dict(title='Test Beta',year='2025',doi='',pmid=''),dict(title='Test Gamma',year='2024',doi='10/b',pmid=''),dict(title='Test Gamma',year='2024',doi='10/c',pmid='')]
  groups,log,possible=deduplicate(rows)
  self.assertEqual(sorted(map(len,groups)),[1,1,2,3]); self.assertEqual({x['match_rule'] for x in log},{'doi','pmid','title'})

 def test_pubmed_numbered_abstract_and_no_affiliations(self):
  text="1. Journal. 2024.\n\nTest Title.\n\nChen D.\n\nINTRO: Test text.\n1. Numbered item.\n\nDOI: 10/a\nPMID: 111\n\n2. Journal. 2024.\n\nOther Title.\n\nDoe J.\n\nTest abstract.\n\nPMID: 222\n"
  a=abstracts(text); self.assertIn('Numbered item',a['111']); self.assertEqual(a['222'],'Test abstract.')

 def test_pubmed_language_note_before_authors(self):
  text="1. Journal. 2024.\n\nTest Title.\n\n[Article in German]\n\nChen D(1).\n\nAuthor information:\n(1) Test University.\n\nBACKGROUND: Test abstract.\n\nPMID: 333\n"
  self.assertEqual(abstracts(text)['333'],'BACKGROUND: Test abstract.')
