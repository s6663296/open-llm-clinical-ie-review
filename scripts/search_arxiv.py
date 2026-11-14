import re, xml.etree.ElementTree as ET
from search_common import setup,Client,finish
from common import first_author,normalize_doi,write_csv
URL='http://export.arxiv.org/api/query'; NS={'a':'http://www.w3.org/2005/Atom','op':'http://a9.com/-/spec/opensearch/1.1/','arxiv':'http://arxiv.org/schemas/atom'}
def val(e,path): return ' '.join(''.join(e.find(path,NS).itertext()).split()) if e.find(path,NS) is not None else ''
def main():
 a,out,q=setup('arxiv'); c=Client(3); rows=[]; extras=[]; total=None; start=0
 while total is None or start<total:
  limit=min(100,(a.max_records-len(rows)) if a.max_records else 100)
  if limit<=0: break
  response=c.get(URL,{'search_query':q,'start':start,'max_results':limit}); (out/'raw'/f'page_{start//100+1:04}.xml').write_bytes(response.content); root=ET.fromstring(response.content); total=int(val(root,'op:totalResults')); entries=root.findall('a:entry',NS)
  if not entries: break
  for e in entries:
   ident=val(e,'a:id'); arxiv=ident.rsplit('/',1)[-1]; authors='; '.join(val(x,'a:name') for x in e.findall('a:author',NS)); published=val(e,'a:published'); doi=val(e,'arxiv:doi'); primary=e.find('arxiv:primary_category',NS); cat=primary.get('term','') if primary is not None else ''
   rows.append(dict(source_db='arXiv',source_id=arxiv,arxiv_id=arxiv,title=val(e,'a:title'),abstract=val(e,'a:summary'),authors=authors,first_author=first_author(authors),year=published[:4],doi=normalize_doi(doi),url=ident,source_file='API'))
   extras.append(dict(arxiv_id=arxiv,first_submitted=published,updated=val(e,'a:updated'),primary_category=cat,doi=doi,journal_ref=val(e,'arxiv:journal_ref')))
  start+=len(entries)
 write_csv(out/'details.csv',extras,['arxiv_id','first_submitted','updated','primary_category','doi','journal_ref']); finish(out,'arXiv',q,a,total,rows)
if __name__=='__main__': main()
