import argparse, json
from pathlib import Path
from openpyxl import load_workbook

def calculate(pairs, labels):
    matrix = [[sum(a == x and b == y for a,b in pairs) for y in labels] for x in labels]
    n = len(pairs)
    if not n: return {'n':0,'observed_agreement':None,'kappa':None,'labels':labels,'confusion_matrix':matrix}
    observed = sum(matrix[i][i] for i in range(len(labels))) / n
    expected = sum(sum(matrix[i]) * sum(row[i] for row in matrix) for i in range(len(labels))) / (n*n)
    return {'n':n,'observed_agreement':observed,'kappa':(observed-expected)/(1-expected) if expected != 1 else None,'labels':labels,'confusion_matrix':matrix}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--sheet',required=True); p.add_argument('--stage',required=True,choices=['title_abstract','full_text']); p.add_argument('--subset',choices=['all','calibration'],default='all'); p.add_argument('--json'); a=p.parse_args()
    wb=load_workbook(a.sheet,read_only=True,data_only=True); ws=wb['screening']; it=ws.iter_rows(values_only=True); headers=next(it); rows=[dict(zip(headers,r)) for r in it]; wb.close()
    if a.subset=='calibration':
        if 'calibration' not in headers: p.error('calibration 欄位不存在')
        rows=[r for r in rows if str(r.get('calibration') or '').strip().lower()=='yes']
    allowed={'include','exclude','unsure'} if a.stage=='title_abstract' else {'include','exclude'}
    pairs=[]; incomplete=0
    for r in rows:
        x=str(r.get('R1_decision') or '').strip().lower(); y=str(r.get('R2_decision') or '').strip().lower()
        if x and x not in allowed or y and y not in allowed: raise ValueError(f"無效決策：{r.get('record_id')}: {x}, {y}")
        if x and y: pairs.append((x,y))
        else: incomplete+=1
    result={'stage':a.stage,'subset':a.subset,'incomplete':incomplete}
    if a.stage=='title_abstract': result['three_category']=calculate(pairs,['include','exclude','unsure'])
    result['binary']=calculate([( 'include' if x=='unsure' else x, 'include' if y=='unsure' else y) for x,y in pairs],['include','exclude'])
    text=json.dumps(result,ensure_ascii=False,indent=2); print(text)
    if a.json: Path(a.json).write_text(text+'\n',encoding='utf-8')
if __name__=='__main__': main()
