import sys,unittest,xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from search_pubmed import parse_book
class BookTests(unittest.TestCase):
 def test_book(self):
  e=ET.fromstring("<PubmedBookArticle><BookDocument><PMID>123</PMID><Book><BookTitle>Test Title Alpha</BookTitle><PubDate><Year>2024</Year></PubDate><AuthorList><Author><LastName>Chen</LastName><Initials>D</Initials></Author></AuthorList></Book><Abstract><AbstractText Label=\"BACKGROUND\">Test abstract</AbstractText></Abstract></BookDocument></PubmedBookArticle>")
  r=parse_book(e); self.assertEqual(r["pmid"],"123"); self.assertEqual(r["abstract"],"BACKGROUND: Test abstract"); self.assertEqual(r["first_author"],"Chen")
