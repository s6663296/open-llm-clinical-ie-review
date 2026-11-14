import argparse, random, re
from pathlib import Path
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from common import read_csv
from record_matching import match_rows
ROOT=Path(__file__).resolve().parents[1]
TA='record_id title abstract year venue doi sources calibration R1_decision R1_code R1_note R2_decision R2_code R2_note agreement final_decision final_code resolved_by agent_suggestion agent_reason'.split()
FT='record_id title doi sources pdf_path fulltext_retrieved R1_decision R1_code R1_page_evidence R2_decision R2_code R2_page_evidence agreement final_decision final_code resolved_by agent_suggestion agent_reason'.split()

def main():
 p=argparse.ArgumentParser(); p.add_argument('--records',required=True); p.add_argument('--out',required=True); p.add_argument('--stage',required=True,choices=['title_abstract','full_text']); p.add_argument('--from-screening'); p.add_argument('--agent-suggestions'); p.add_argument('--seed',type=int,default=20261114); p.add_argument('--calibration-n',type=int,default=50); p.add_argument('--force',action='store_true'); a=p.parse_args(); out=Path(a.out)
 if out.exists() and not a.force: p.error('output exists; use --force to overwrite')
 rows=read_csv(a.records)
 if a.stage=='full_text':
  if not a.from_screening: p.error('--from-screening required for full_text')
  wb0=load_workbook(a.from_screening,read_only=True,data_only=True); it=wb0['screening'].iter_rows(values_only=True); headers=next(it); ids={str(r.get('record_id')) for line in it if (r:=dict(zip(headers,line))) and str(r.get('final_decision') or '').strip().lower()=='include'}; wb0.close(); rows=[r for r in rows if r['record_id'] in ids]
 else:
  chosen=set(random.Random(a.seed).sample(range(len(rows)),min(a.calibration_n,len(rows))))
  for i,r in enumerate(rows): r['calibration']='yes' if i in chosen else ''
 if a.agent_suggestions:
  suggestions=read_csv(a.agent_suggestions)
  matches=match_rows(rows,suggestions,arxiv=True)
  for r,match in zip(rows,matches):
   if match is not None:
    s=suggestions[match]
    r['agent_suggestion']=s.get('agent_suggestion','')
    signals=s.get('agent_signals','')
    r['agent_reason']=s.get('agent_reason','') + (f' [signals: {signals}]' if signals else '')
  print(f'agent suggestions matched: {sum(m is not None for m in matches)}; unmatched: {sum(m is None for m in matches)}')
 wb=Workbook(); ws=wb.active; ws.title='screening'; cols=TA if a.stage=='title_abstract' else FT; ws.append(cols)
 for n,r in enumerate(rows,2):
  ws.append([r.get(c,'') for c in cols]); x=get_column_letter(cols.index('R1_decision')+1); y=get_column_letter(cols.index('R2_decision')+1); ws.cell(n,cols.index('agreement')+1,f'=IF(OR({x}{n}="",{y}{n}=""),"",IF({x}{n}={y}{n},"agree","disagree"))')
 for col in cols:
  vals = ('include,exclude,unsure' if a.stage=='title_abstract' else 'include,exclude') if col in ('R1_decision','R2_decision') else 'include,exclude' if col=='final_decision' else ','.join('X'+str(i) for i in range(1,9)) if col in ('R1_code','R2_code','final_code') else 'yes,no' if col=='fulltext_retrieved' else None
  if vals:
   dv=DataValidation(type='list',formula1='"'+vals+'"'); dv.errorTitle='Invalid'; dv.error='Choose from the list'; dv.showErrorMessage=True; ws.add_data_validation(dv); letter=get_column_letter(cols.index(col)+1); dv.add(f'{letter}2:{letter}{max(2,len(rows)+1)}')
 ws.freeze_panes='A2'; ws.auto_filter.ref=ws.dimensions
 for cell in ws[1]: cell.font=Font(bold=True)
 for i,c in enumerate(cols,1):
  ws.column_dimensions[get_column_letter(i)].width=75 if c=='abstract' else 48 if c=='title' else 20
  if c in ('abstract','title'):
   for cells in ws.iter_rows(min_row=2,min_col=i,max_col=i): cells[0].alignment=Alignment(wrap_text=True,vertical='top')
 protocol=(ROOT/'protocol/protocol.md').read_text(encoding='utf-8')
 for name,section,nextsec,prefix in [('criteria','### 3.1','### 3.2','I'),('codes','### 3.2','### 3.3','X')]:
  sheet=wb.create_sheet(name); sheet.append(['code','criterion','operational definition'] if name=='criteria' else ['code','description'])
  part=protocol.split(section,1)[1].split(nextsec,1)[0]
  for line in part.splitlines():
   if re.match(r'^\|\s*'+prefix+r'\d\s*\|',line): sheet.append([s.strip() for s in line.strip().strip('|').split('|')])
  sheet.freeze_panes='A2'
  for cell in sheet[1]: cell.font=Font(bold=True)
  for col,width in [('A',12),('B',55),('C',100)]: sheet.column_dimensions[col].width=width
  for row in sheet.iter_rows(min_row=2):
   for c in row: c.alignment=Alignment(wrap_text=True,vertical='top')
 out.parent.mkdir(parents=True,exist_ok=True); wb.save(out); print(f'{out}: {len(rows)} records')
if __name__=='__main__': main()
