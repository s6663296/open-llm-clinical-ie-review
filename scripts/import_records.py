import argparse, json, re, html
from pathlib import Path
from collections import defaultdict
from difflib import SequenceMatcher
from common import FIELDS, normalize_doi, normalize_title, first_author, read_csv, write_csv
ROOT=Path(__file__).resolve().parents[1]

def clean(x): return ' '.join(re.sub(r'[{}]', '', x).split())
def parse_bibtex(text):
    entries=[]; pos=0
    while m:=re.search(r'@\w+\s*\{\s*([^,]+),',text[pos:]):
        i=pos+m.end(); fields={}; key=m.group(1).strip()
        while i<len(text):
            m2=re.match(r'\s*,?\s*([\w-]+)\s*=\s*',text[i:])
            if not m2: break
            name=m2.group(1).lower(); i+=m2.end()
            if i>=len(text): break
            opening=text[i]; i+=1; start=i
            if opening=='{':
                depth=1
                while i<len(text) and depth:
                    if text[i]=='{' and (i==0 or text[i-1]!='\\'): depth+=1
                    elif text[i]=='}' and (i==0 or text[i-1]!='\\'): depth-=1
                    i+=1
                val=text[start:i-1]
            elif opening=='"':
                while i<len(text) and (text[i]!='"' or text[i-1]=='\\'): i+=1
                val=text[start:i]; i+=1
            else:
                i-=1; start=i
                while i<len(text) and text[i] not in ',}': i+=1
                val=text[start:i]
            fields[name]=clean(val)
        fields['_key']=key; entries.append(fields); pos=max(i,pos+m.end())
    return entries

def parse_ris(text):
    records=[]; rec={}; last=None
    for line in text.splitlines():
        m=re.match(r'^([A-Z0-9]{2})  - ?(.*)$',line)
        if m:
            tag,v=m.groups(); last=tag
            if tag=='TY': rec={}
            elif tag=='ER':
                records.append({'title':' '.join(rec.get('TI',rec.get('T1',[]))), 'abstract':' '.join(rec.get('AB',[])), 'authors':'; '.join(rec.get('AU',[])), 'year':' '.join(rec.get('PY',rec.get('Y1',[])))[:4], 'doi':' '.join(rec.get('DO',[])), 'venue':' '.join(rec.get('JO',rec.get('T2',[]))), 'keywords':'; '.join(rec.get('KW',[]))})
                rec={}; last=None
            else: rec.setdefault(tag,[]).append(v.strip())
        elif last and line.strip() and rec.get(last): rec[last][-1]+=' '+line.strip()
    return records

def deduplicate(rows):
    n=len(rows); parent=list(range(n)); dois=[{normalize_doi(r.get('doi',''))}-{''} for r in rows]; log=[]
    def find(i):
        while parent[i]!=i: parent[i]=parent[parent[i]]; i=parent[i]
        return i
    def union(i,j,rule):
        a,b=find(i),find(j)
        if a==b: return
        if rule=='title' and dois[a] and dois[b] and dois[a]!=dois[b]: return
        if a>b: a,b=b,a
        parent[b]=a; dois[a]|=dois[b]
        log.append({'group_id':'','kept_seq':a+1,'removed_seq':b+1,'match_rule':rule,'title_kept':rows[a].get('title',''),'title_removed':rows[b].get('title','')})
    for field,rule in [('doi','doi'),('pmid','pmid')]:
        seen={}
        for i,r in enumerate(rows):
            v=normalize_doi(r.get(field,'')) if field=='doi' else r.get(field,'').strip()
            if v:
                if v in seen: union(seen[v],i,rule)
                else: seen[v]=i
    def year(r):
        try: return int(str(r.get('year',''))[:4])
        except ValueError: return None
    def near(i,j):
        a,b=year(rows[i]),year(rows[j]); return a is not None and b is not None and abs(a-b)<=1
    titles=[normalize_title(r.get('title','')) for r in rows]; exact=defaultdict(list)
    for i,t in enumerate(titles):
        if t:
            for j in exact[t]:
                if near(i,j): union(i,j,'title')
            exact[t].append(i)
    blocks=defaultdict(list); possible=[]
    for i,t in enumerate(titles):
        if not t: continue
        block=' '.join(t.split()[:3])
        for j in blocks[block]:
            if find(i)==find(j) or not near(i,j): continue
            sim=SequenceMatcher(None,t,titles[j]).ratio()
            if sim>=.93: possible.append({'seq_a':j+1,'seq_b':i+1,'similarity':round(sim,4),'title_a':rows[j].get('title',''),'title_b':rows[i].get('title',''),'year_a':rows[j].get('year',''),'year_b':rows[i].get('year','')})
        blocks[block].append(i)
    groups=defaultdict(list)
    for i in range(n): groups[find(i)].append(i)
    for x in log: x['group_id']='G'+str(find(x['kept_seq']-1)+1).zfill(4)
    return list(groups.values()),log,possible

def abstracts(text):
    out={}; markers=list(re.finditer(r'(?m)^(\d+)\. ',text)); starts=[]; expected=1; previous=0
    for m in markers:
        if int(m.group(1))==expected and (expected==1 or re.search(r'(?m)^PMID:\s*\d+',text[previous:m.start()])):
            starts.append(m.start()); previous=m.start(); expected+=1
    for n,start in enumerate(starts):
        block=text[start:starts[n+1] if n+1<len(starts) else len(text)]
        m=re.search(r'(?m)^PMID:\s*(\d+)',block)
        if not m: continue
        paras=re.split(r'\n\s*\n',block[:m.start()]); candidates=[]
        # Citation, title, authors precede optional author information.
        info=next((i for i,p in enumerate(paras) if p.startswith('Author information:')),None)
        if info is not None: remaining=paras[info+1:]
        else:
            offset=3 + (1 if len(paras)>2 and paras[2].lstrip().startswith('[Article in ') else 0)
            remaining=paras[offset:]
        for para in remaining:
            t=' '.join(para.split())
            if not t or re.match(r'^(?:\u00a9|Copyright|DOI:|PMCID:|Conflict of interest|Published by|Update (?:in|of)\b|Comment (?:in|on)\b|Erratum\b)',t,re.I): continue
            candidates.append(t)
        out[m.group(1)]=' '.join(candidates)
    return out

def main():
    p=argparse.ArgumentParser(); p.add_argument('--config',required=True); p.add_argument('--out',required=True); a=p.parse_args(); config=json.loads(Path(a.config).read_text(encoding='utf-8-sig')); rows=[]; counts={}; missing_pub=0
    for spec in config['sources']:
        db=spec['db']; fmt=spec['format']; counts.setdefault(db,0); absmap=abstracts((ROOT/spec['abstract_file']).read_text(encoding='utf-8-sig')) if spec.get('abstract_file') else {}
        for name in spec['files']:
            path=ROOT/name
            if fmt=='bibtex': data=parse_bibtex(path.read_text(encoding='utf-8-sig'))
            elif fmt=='ris': data=parse_ris(path.read_text(encoding='utf-8-sig'))
            else: data=read_csv(path)
            for d in data:
                if fmt=='pubmed_csv':
                    pmid=d.get('PMID',''); au=d.get('Authors','').replace(', ','; '); abstract=absmap.get(pmid,''); missing_pub+=not bool(abstract)
                    r=dict(source_id=pmid,pmid=pmid,title=d.get('Title',''),abstract=abstract,authors=au,year=d.get('Publication Year',''),venue=d.get('Journal/Book',''),doi=d.get('DOI',''))
                elif fmt=='scopus_csv': r=dict(source_id=d.get('EID',''),title=d.get('Title',''),abstract=d.get('Abstract',''),authors=d.get('Authors',''),year=d.get('Year',''),venue=d.get('Source title',''),doi=d.get('DOI',''),pmid=d.get('PubMed ID',''),keywords=d.get('Author Keywords',''),pub_type=d.get('Document Type',''),language=d.get('Language of Original Document',''))
                elif fmt=='ieee_csv': r=dict(title=d.get('Document Title',''),abstract=d.get('Abstract',''),authors=d.get('Authors','').replace(';','; '),year=d.get('Publication Year',''),venue=d.get('Publication Title',''),doi=d.get('DOI',''),keywords=d.get('Author Keywords',''))
                elif fmt=='bibtex': r=dict(source_id=d.get('_key',''),title=d.get('title',''),abstract=d.get('abstract',''),authors=d.get('author','').replace(' and ','; '),year=d.get('year',''),venue=d.get('journal',d.get('booktitle','')),doi=d.get('doi',''),keywords=d.get('keywords',''),url=d.get('url',''))
                else: r=dict(d)
                r={k: html.unescape(v) if isinstance(v, str) else v for k, v in r.items()}; r['source_db']=r.get('source_db') or db; r['source_file']=name; r['doi']=normalize_doi(r.get('doi','')); r['first_author']=r.get('first_author') or first_author(r.get('authors','')); r['record_seq']=len(rows)+1; rows.append(r); counts[db]+=1
    groups,log,possible=deduplicate(rows); merged=[]
    for group in groups:
        r={k:(next((rows[i].get(k,'') for i in group if rows[i].get(k,'')), '') if k in ('doi','pmid') else max((rows[i].get(k,'') or '' for i in group),key=len)) for k in FIELDS}
        r['sources']='; '.join(sorted({rows[i]['source_db'] for i in group})); r['n_sources']=len(set(rows[i]['source_db'] for i in group)); r['merged_seqs']='; '.join(str(i+1) for i in group); merged.append(r)
    merged.sort(key=lambda r:(-int(r['year'][:4]) if r['year'][:4].isdigit() else 0,normalize_title(r['title'])))
    for i,r in enumerate(merged,1): r['record_id']=f'R{i:04}'
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    write_csv(out/'records_raw.csv',rows,FIELDS+['record_seq']); write_csv(out/'records_dedup.csv',merged,FIELDS+['record_id','sources','n_sources','merged_seqs']); write_csv(out/'dedup_log.csv',log,['group_id','kept_seq','removed_seq','match_rule','title_kept','title_removed']); write_csv(out/'possible_duplicates.csv',possible,['seq_a','seq_b','similarity','title_a','title_b','year_a','year_b'])
    summary={'source_counts':counts,'total_raw':len(rows),'duplicates_removed':len(rows)-len(merged),'total_dedup':len(merged),'possible_duplicate_pairs':len(possible),'missing_abstract':sum(not r['abstract'] for r in merged),'pubmed_missing_abstract':missing_pub}; (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
