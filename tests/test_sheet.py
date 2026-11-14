import subprocess,sys,tempfile,unittest,csv
from pathlib import Path
from openpyxl import load_workbook
ROOT=Path(__file__).resolve().parents[1]
class SheetTests(unittest.TestCase):
 def test_screening_validation_and_no_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   records=Path(d)/'records.csv'; out=Path(d)/'sheet.xlsx'
   with records.open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['record_id','title','abstract']); w.writeheader(); w.writerow({'record_id':'R0001','title':'Test Title Alpha','abstract':'Test abstract'})
   cmd=[sys.executable,str(ROOT/'scripts/make_screening_sheet.py'),'--records',str(records),'--out',str(out),'--stage','title_abstract']
   subprocess.run(cmd,check=True,capture_output=True); before=out.read_bytes(); w=load_workbook(out); self.assertEqual(len(w['screening'].data_validations.dataValidation),6); self.assertEqual(w['screening']['H2'].value,'yes'); self.assertTrue(w['screening']['O2'].value.startswith('=IF(')); w.close()
   self.assertNotEqual(subprocess.run(cmd,capture_output=True).returncode,0); self.assertEqual(out.read_bytes(),before)
