import sys, tempfile, unittest
from pathlib import Path
from unittest.mock import Mock
from openpyxl import Workbook, load_workbook
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import fetch_fulltext as f

class FetchTests(unittest.TestCase):
    def test_arxiv_before_openalex_and_stop(self):
        client = Mock()
        client.pdf.return_value = b'%PDF-1.4 test'
        with tempfile.TemporaryDirectory() as d:
            result = f.fetch_record({'record_id':'A', 'arxiv_id':'2401.12345', 'doi':'10.1/example'}, Path(d), client)
            self.assertEqual(result['source'], 'arxiv')
            client.json.assert_not_called()

    def test_non_pdf_response_fails(self):
        response = Mock(status_code=200, content=b'<html>login</html>', headers={'Content-Type':'text/html'})
        response.raise_for_status.return_value = None
        client = f.Client(); client.request = Mock(return_value=response)
        self.assertIsNone(client.pdf('https://example.org/file'))

    def test_sheet_changes_only_two_columns_and_backs_up(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'sheet.xlsx'
            wb=Workbook(); ws=wb.active; ws.title='screening'; ws.append(['record_id','title','pdf_path','fulltext_retrieved','final_decision']); ws.append(['R1','Title','old','no','include']); wb.save(path)
            f.update_sheet(path, [{'record_id':'R1','status':'downloaded'}], Path(d))
            self.assertTrue((Path(d)/'sheet.bak.xlsx').exists())
            wb=load_workbook(path); vals=list(wb['screening'].values)
            self.assertEqual(vals[1][:2], ('R1','Title'))
            self.assertEqual(vals[1][3:], ('yes','include'))
            self.assertTrue(vals[1][2].endswith('R1.pdf'))

    def test_openalex_oa_locations_then_europe_pmc(self):
        client=Mock(); client.json.side_effect=[{'best_oa_location':{'pdf_url':'https://oa/best'},'locations':[{'is_oa':True,'pdf_url':'https://oa/other'}]}, {'resultList':{'result':[{'pmcid':'PMC123'}]}}]
        client.pdf.side_effect=[None,None,b'%PDF test']
        with tempfile.TemporaryDirectory() as d:
            result=f.fetch_record({'record_id':'R','doi':'10.1/x','pmid':'123'},Path(d),client)
            self.assertEqual(result['source'],'europe_pmc')
            self.assertEqual([x.args[0] for x in client.pdf.call_args_list], ['https://oa/best','https://oa/other','https://europepmc.org/articles/PMC123?pdf=render'])

    def test_explicit_arxiv_version_is_preserved(self):
        client=Mock(); client.pdf.return_value=b'%PDF data'
        with tempfile.TemporaryDirectory() as d:
            f.fetch_record({'record_id':'R', 'arxiv_id':'https://arxiv.org/abs/2401.12345v2'},Path(d),client)
            self.assertEqual(client.pdf.call_args.args[0], 'https://arxiv.org/pdf/2401.12345v2')
