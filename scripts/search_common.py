import argparse, json, subprocess, time, hashlib
from datetime import datetime
from pathlib import Path
import requests
from common import FIELDS, write_csv
ROOT=Path(__file__).resolve().parents[1]

def setup(db):
 p=argparse.ArgumentParser(); p.add_argument('--out',required=True); p.add_argument('--query-file',default=str(ROOT/'scripts/queries'/f'{db}.txt')); p.add_argument('--max-records',type=int); a=p.parse_args()
 if a.max_records is not None and a.max_records<1: p.error('--max-records must be positive')
 out=Path(a.out); (out/'raw').mkdir(parents=True,exist_ok=True)
 query=' '.join(line.strip() for line in Path(a.query_file).read_text(encoding='utf-8-sig').splitlines() if line.strip() and not line.lstrip().startswith('#'))
 return a,out,query
class Client:
 def __init__(self,delay): self.delay=delay; self.last=0
 def get(self,url,params):
  for attempt in range(4):
   time.sleep(max(0,self.delay-(time.monotonic()-self.last))); self.last=time.monotonic()
   try:
    r=requests.get(url,params=params,timeout=90); r.raise_for_status(); return r
   except requests.RequestException:
    if attempt==3: raise
    time.sleep(2**attempt)
def finish(out,db,query,args,total,records,extra=None):
 write_csv(out/'records.csv',records,FIELDS)
 try: version=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,stderr=subprocess.DEVNULL,text=True).strip()
 except (OSError,subprocess.CalledProcessError): version='uncommitted'
 expected=min(total,args.max_records) if args.max_records else total
 if len(records)!=expected: raise RuntimeError(f'Expected {expected} records, parsed {len(records)}; inspect raw responses')
 hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'scripts').glob('*.py')}
 log={'database':db,'query':query,'query_file_original':Path(args.query_file).read_text(encoding='utf-8-sig'),'script_sha256':hashes,'executed_at':datetime.now().astimezone().isoformat(),'api_total':total,'downloaded':len(records),'script_version':version,'parameters':vars(args)}
 if extra: log.update(extra)
 (out/'search_log.json').write_text(json.dumps(log,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(log,ensure_ascii=False,indent=2))
