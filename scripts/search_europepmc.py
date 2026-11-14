import re, html
from search_common import setup,Client,finish
from common import first_author,normalize_doi,write_csv
URL='https://www.ebi.ac.uk/europepmc/webservices/rest/search'
def main():
 a,out,q=setup('europepmc'); c=Client(.4); cursor='*'; rows=[]; details=[]; total=None; page=0; med=[]
 while total is None or len(rows)<total:
  limit=min(1000,(a.max_records-len(rows)) if a.max_records else 1000)
  if limit<=0: break
  response=c.get(URL,{'query':q,'format':'json','resultType':'core','pageSize':limit,'cursorMark':cursor}); page+=1; (out/'raw'/f'page_{page:04}.json').write_bytes(response.content); data=response.json(); total=data['hitCount']; results=data['resultList']['result']
  if not results: break
  for d in results:
   authors='; '.join(x.get('fullName','') for x in d.get('authorList',{}).get('author',[])); pub=d.get('bookOrReportDetails',{}).get('publisher',''); doi=d.get('doi',''); id=d.get('id',''); src=d.get('source',''); abstract=html.unescape(re.sub('<[^>]+>',' ',d.get('abstractText',''))); abstract=' '.join(abstract.split()); venue=d.get('journalTitle',''); url='https://europepmc.org/article/'+src+'/'+id
   r=dict(source_db='Europe PMC',source_id=id,title=d.get('title',''),abstract=abstract,authors=authors,first_author=first_author(authors),year=str(d.get('pubYear','')),venue=venue,doi=normalize_doi(doi),pmid=d.get('pmid',''),url=url,source_file='API'); rows.append(r)
   # medRxiv DOI prefix is assigned by the server; publisher and journal metadata are additional explicit evidence.
   ismed=doi.lower().startswith(('10.1101/','10.64898/')) and ('medrxiv' in (pub+' '+venue+' '+str(d.get('journalInfo',{}))).lower())
   details.append(dict(id=id,source=src,publication_date=d.get('firstPublicationDate',''),publisher=pub,journal=venue,doi=doi,medrxiv=ismed))
   if ismed: med.append(r)
  nxt=data.get('nextCursorMark');
  if not nxt or nxt==cursor: break
  cursor=nxt
 write_csv(out/'details.csv',details,['id','source','publication_date','publisher','journal','doi','medrxiv']); write_csv(out/'medrxiv_records.csv',med,list(rows[0]) if rows else __import__('common').FIELDS); finish(out,'Europe PMC',q,a,total,rows,{'medrxiv_before':len(rows),'medrxiv_after':len(med),'medrxiv_rule':'publisher or journal metadata contains medRxiv and DOI prefix 10.1101/ or 10.64898/'})
if __name__=='__main__': main()
