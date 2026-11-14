import xml.etree.ElementTree as ET
from search_common import setup,Client,finish
from common import first_author,normalize_doi,write_csv
BASE='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
def txt(e,path):
 x=e.find(path); return ' '.join(''.join(x.itertext()).split()) if x is not None else ''
def parse_book(article):
 doc=article.find('./BookDocument'); book=doc.find('./Book'); pmid=txt(doc,'./PMID'); names=[]
 for author in book.findall('./AuthorList/Author'):
  name=' '.join(x for x in [txt(author,'./LastName'),txt(author,'./Initials')] if x) or txt(author,'./CollectiveName')
  if name: names.append(name)
 authors='; '.join(names); abstract=[]
 for part in doc.findall('./Abstract/AbstractText'):
  label=part.get('Label',''); abstract.append((label+': ' if label else '')+' '.join(''.join(part.itertext()).split()))
 doi=next((''.join(x.itertext()) for x in doc.findall('./ArticleIdList/ArticleId') if x.get('IdType')=='doi'),'')
 return dict(source_db='PubMed',source_id=pmid,pmid=pmid,title=txt(doc,'./ArticleTitle') or txt(book,'./BookTitle'),abstract=' '.join(abstract),authors=authors,first_author=first_author(authors),year=txt(book,'./PubDate/Year'),venue=txt(book,'./CollectionTitle') or txt(book,'./BookTitle'),doi=normalize_doi(doi),pub_type=txt(doc,'./PublicationType'),language=txt(doc,'./Language'),url='https://pubmed.ncbi.nlm.nih.gov/'+pmid+'/',source_file='API')
def main():
 a,out,q=setup('pubmed'); c=Client(.4); tool={'tool':'sr-clinical-ie'}
 mesh=c.get(BASE+'esearch.fcgi',dict(tool,db='mesh',term='"Large Language Models"[MeSH Terms]',retmode='json')); (out/'raw'/'mesh.json').write_bytes(mesh.content); mesh_count=int(mesh.json()['esearchresult']['count']); exists=mesh_count>0
 if not exists: print('Warning: Large Language Models MeSH term not found; query unchanged')
 response=c.get(BASE+'esearch.fcgi',dict(tool,db='pubmed',term=q,usehistory='y',retmode='json',retmax=0)); (out/'raw'/'esearch.json').write_bytes(response.content); result=response.json()['esearchresult']; total=int(result['count']); count=min(total,a.max_records) if a.max_records else total; rows=[]; details=[]
 for start in range(0,count,200):
  res=c.get(BASE+'efetch.fcgi',dict(tool,db='pubmed',query_key=result['querykey'],WebEnv=result['webenv'],retstart=start,retmax=min(200,count-start),retmode='xml')); (out/'raw'/f'page_{start//200+1:04}.xml').write_bytes(res.content); root=ET.fromstring(res.content)
  for article in root.findall('.//PubmedArticle'):
   cit=article.find('./MedlineCitation'); art=cit.find('./Article'); pmid=txt(cit,'./PMID'); au=[]
   for author in art.findall('./AuthorList/Author'):
    name=' '.join(x for x in [txt(author,'./LastName'),txt(author,'./Initials')] if x) or txt(author,'./CollectiveName');
    if name: au.append(name)
   abstracts=[]
   for part in art.findall('./Abstract/AbstractText'):
    label=part.get('Label',''); v=' '.join(''.join(part.itertext()).split()); abstracts.append((label+': ' if label else '')+v)
   authors='; '.join(au); year=txt(art,'./Journal/JournalIssue/PubDate/Year') or txt(cit,'./ArticleDate/Year') or txt(art,'./Journal/JournalIssue/PubDate/MedlineDate')[:4]; doi=next(((''.join(x.itertext())) for x in article.findall('.//ArticleId') if x.get('IdType')=='doi'),''); types='; '.join(''.join(x.itertext()) for x in art.findall('./PublicationTypeList/PublicationType')); lang='; '.join((x.text or '') for x in art.findall('./Language')); meshterms='; '.join(''.join(x.itertext()) for x in cit.findall('./MeshHeadingList/MeshHeading/DescriptorName'))
   rows.append(dict(source_db='PubMed',source_id=pmid,pmid=pmid,title=txt(art,'./ArticleTitle'),abstract=' '.join(abstracts),authors=authors,first_author=first_author(authors),year=year,venue=txt(art,'./Journal/Title'),doi=normalize_doi(doi),pub_type=types,language=lang,keywords=meshterms,url='https://pubmed.ncbi.nlm.nih.gov/'+pmid+'/',source_file='API')); details.append(dict(pmid=pmid,mesh=meshterms))
  for article in root.findall('./PubmedBookArticle'):
   r=parse_book(article); rows.append(r); details.append(dict(pmid=r['pmid'],mesh=''))
 if len(rows)!=count: raise RuntimeError(f'Expected {count} records, parsed {len(rows)}; inspect raw files')
 write_csv(out/'details.csv',details,['pmid','mesh']); finish(out,'PubMed',q,a,total,rows,{'mesh_check':{'term':'Large Language Models','exists':exists,'count':mesh_count}})
if __name__=='__main__': main()
