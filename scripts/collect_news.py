"""Official RSS/Atom -> bounded public JSON. Python standard library only."""
import argparse, concurrent.futures, datetime as dt, email.utils, hashlib, html, json, os, pathlib, re, tempfile, unicodedata, urllib.parse, urllib.request, xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parents[1]
UTC=dt.timezone.utc
MAX_BYTES=4_000_000
CATEGORIES={'national':'জাতীয়','international':'আন্তর্জাতিক','politics':'রাজনীতি','economy':'অর্থনীতি','sports':'খেলা','technology':'প্রযুক্তি','entertainment':'বিনোদন','education':'শিক্ষা','health':'স্বাস্থ্য'}
RULES=[('sports',['sports','sport','খেলা','ক্রিকেট','ফুটবল']),('education',['education','শিক্ষা','বিশ্ববিদ্যালয়','ভর্তি','পরীক্ষা']),('health',['health','স্বাস্থ্য','চিকিৎসা','হাসপাতাল']),('technology',['technology','science','প্রযুক্তি','বিজ্ঞান']),('entertainment',['entertainment','বিনোদন','চলচ্চিত্র','সিনেমা']),('economy',['economy','business','অর্থনীতি','বাণিজ্য','ব্যাংক']),('politics',['politics','রাজনীতি','নির্বাচন']),('international',['world','international','আন্তর্জাতিক'])]
def iso(value):return value.astimezone(UTC).isoformat().replace('+00:00','Z')
def parse_date(value):
 if not value:return None
 try:parsed=email.utils.parsedate_to_datetime(value)
 except (ValueError,TypeError,IndexError):
  try:parsed=dt.datetime.fromisoformat(str(value).replace('Z','+00:00'))
  except (ValueError,TypeError):return None
 return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)
def clean(value,limit=500):
 text=re.sub(r'<(script|style)\b[^>]*>.*?</\1>','',str(value or ''),flags=re.I|re.S)
 text=html.unescape(re.sub(r'<[^>]*>','',text))
 text=unicodedata.normalize('NFC',re.sub(r'\s+',' ',text).strip())
 return text if len(text)<=limit else text[:limit-1].rstrip()+'…'
def allowed_host(host,domains):return bool(host) and any(host==d or host.endswith('.'+d) for d in domains)
def article_url(value,source):
 url=urllib.parse.urljoin(source['url'],html.unescape(str(value or '').strip()))
 try:
  parts=urllib.parse.urlsplit(url);host=(parts.hostname or '').lower().removeprefix('www.')
  if parts.scheme not in ('https','http') or parts.username or parts.password or parts.port not in (None,80,443) or not allowed_host(host,source['articleDomains']) or parts.path in ('','/') or re.search(r'[\x00-\x20]',url):return ''
 except ValueError:return ''
 return urllib.parse.urlunsplit(('https',parts.hostname.lower(),parts.path,parts.query,''))
def canonical_url(url):
 parts=urllib.parse.urlsplit(url)
 query=sorted((k,v) for k,v in urllib.parse.parse_qsl(parts.query,keep_blank_values=True) if not k.lower().startswith('utm_') and k.lower() not in ('fbclid','gclid','dclid','mc_cid','mc_eid'))
 return urllib.parse.urlunsplit(('https',parts.netloc.lower().removeprefix('www.'),parts.path.rstrip('/') or '/',urllib.parse.urlencode(query),''))
def digest(value):return hashlib.sha256(value.encode('utf-8')).hexdigest()
def local_name(tag):return tag.rsplit('}',1)[-1]
def category_for(title,url,tags,default='national'):
 text=(' '.join(tags)+' '+title+' '+url).lower()
 return next((cat for cat,words in RULES if any(word in text for word in words)),default if default in CATEGORIES else 'national')
def parse_feed(payload,source,now=None):
 now=now or dt.datetime.now(UTC)
 if len(payload)>MAX_BYTES or b'<!DOCTYPE' in payload.upper() or b'<!ENTITY' in payload.upper():raise ValueError('Unsafe or oversized XML')
 root=ET.fromstring(payload.lstrip(b'\xef\xbb\xbf'))
 if local_name(root.tag) not in ('rss','feed','RDF'):raise ValueError('Not RSS or Atom')
 articles=[]
 for item in root.iter():
  if local_name(item.tag) not in ('item','entry'):continue
  values={};link='';tags=[]
  for child in item:
   key=local_name(child.tag);text=''.join(child.itertext());values.setdefault(key,text)
   if key=='link' and child.attrib.get('rel','alternate')=='alternate':link=child.attrib.get('href') or child.text or link
   if key=='category':tags.append(child.attrib.get('term') or text)
  title=clean(values.get('title'));guid=clean(values.get('guid') or values.get('id'),500)
  url=article_url(link or (guid if guid.startswith(('http://','https://')) else ''),source)
  if not title or not url:continue
  published=parse_date(values.get('pubDate') or values.get('published') or values.get('date') or values.get('updated'))
  if published and (now-published>dt.timedelta(days=30) or published-now>dt.timedelta(minutes=15)):continue
  description=clean(values.get('description') or values.get('summary') or values.get('encoded'),160)
  canonical=canonical_url(url);cat=category_for(title,url,tags,source.get('defaultCategory','national'))
  articles.append({'id':digest(source['id']+'|'+(guid or canonical))[:24],'sourceId':source['id'],'sourceName':source['name'],'title':title,'description':description,'url':url,'canonicalUrl':canonical,'guid':guid or None,'publishedAt':iso(published) if published else None,'firstSeenAt':iso(now),'category':cat,'categoryName':CATEGORIES[cat],'isBreaking':bool(re.search(r'^(breaking\b|ব্রেকিং\b|জরুরি সংবাদ)',title,re.I) or any(t.lower() in ('breaking','breaking news','ব্রেকিং') for t in tags)),'contentHash':digest(source['id']+'|'+title+'|'+description)})
 return sorted(articles,key=lambda a:a['publishedAt'] or '',reverse=True)[:80]
def keys(article):
 day=(article.get('publishedAt') or article.get('firstSeenAt') or '')[:10]
 title=re.sub(r'[\W_]+','',unicodedata.normalize('NFC',article['title']).casefold())
 out=['url:'+canonical_url(article['url']),'hash:'+article['sourceId']+':'+article['contentHash']+':'+day,'title:'+article['sourceId']+':'+title+':'+day]
 if article.get('guid'):out.append('guid:'+article['sourceId']+':'+article['guid'])
 return out
def merge_articles(previous,incoming,now,maximum=3000):
 old_keys={k:a for a in previous for k in keys(a)};seen=set();merged=[];duplicates=0
 for raw in incoming+previous:
  a=dict(raw);matches=[old_keys[k] for k in keys(a) if k in old_keys]
  if matches:a['firstSeenAt']=matches[0].get('firstSeenAt') or a['firstSeenAt'];a['id']=matches[0]['id']
  timestamp=parse_date(a.get('publishedAt') or a.get('firstSeenAt'))
  if not timestamp or timestamp<now-dt.timedelta(days=30) or timestamp>now+dt.timedelta(minutes=15):continue
  identities=keys(a)+['id:'+a['id']]
  if any(k in seen for k in identities):duplicates+=1;continue
  seen.update(identities);merged.append(a)
 merged.sort(key=lambda a:(a.get('publishedAt') or '',a['firstSeenAt'],a['id']),reverse=True)
 return merged[:maximum],duplicates

def fetch_source(source,now):
 if not source.get('enabled'):return [],{'id':source['id'],'name':source['name'],'url':source['url'],'status':'disabled','reason':source.get('reason','Not verified')}
 try:
  request=urllib.request.Request(source['feed'],headers={'User-Agent':'BanglaNewsRSS/2.0 (+https://banglanewsbd.web.app/)','Accept':'application/rss+xml, application/atom+xml, application/xml, text/xml'})
  with urllib.request.urlopen(request,timeout=18) as response:
   host=urllib.parse.urlsplit(response.url).hostname or ''
   allowed=source['articleDomains']+[urllib.parse.urlsplit(source['feed']).hostname]
   if not allowed_host(host.removeprefix('www.'),allowed):raise ValueError('Unexpected feed redirect domain')
   payload=response.read(MAX_BYTES+1)
  articles=parse_feed(payload,source,now)
  if not articles:raise ValueError('No eligible articles')
  return articles,{'id':source['id'],'name':source['name'],'url':source['url'],'status':'ok','reason':''}
 except Exception as error:
  return [],{'id':source['id'],'name':source['name'],'url':source['url'],'status':'unavailable','reason':type(error).__name__+(': '+str(error.code) if hasattr(error,'code') else '')}

def validate_document(data):
 if data.get('schemaVersion')!=1 or not isinstance(data.get('articles'),list) or len(data['articles'])>3000 or not isinstance(data.get('sources'),list):raise ValueError('Invalid news document')
 if not parse_date(data.get('generatedAt')):raise ValueError('Invalid generation time')
 ids=set()
 for a in data['articles']:
  if not isinstance(a.get('id'),str) or a['id'] in ids:raise ValueError('Duplicate/invalid ID')
  ids.add(a['id'])
  if not isinstance(a.get('title'),str) or not 1<=len(a['title'])<=500 or not isinstance(a.get('description'),str) or len(a['description'])>160 or a.get('category') not in CATEGORIES:raise ValueError('Invalid article fields')
  u=urllib.parse.urlsplit(a['url'])
  if u.scheme!='https' or not u.hostname or u.username or u.password:raise ValueError('Unsafe article URL')
  if not parse_date(a.get('firstSeenAt')) or (a.get('publishedAt') is not None and not parse_date(a['publishedAt'])):raise ValueError('Invalid date')
 return True

def write_bundle(folder,data):
 validate_document(data);folder.mkdir(parents=True,exist_ok=True)
 documents={'latest.json':data,'sources.json':{'schemaVersion':1,'generatedAt':data['generatedAt'],'sources':data['sources']}}
 for cat in CATEGORIES:documents['categories/'+cat+'.json']={'schemaVersion':1,'category':cat,'label':CATEGORIES[cat],'generatedAt':data['generatedAt'],'articleIds':[a['id'] for a in data['articles'] if a['category']==cat]}
 changed=[]
 # All files are staged and validated before atomic replacements; Git publishes one commit.
 with tempfile.TemporaryDirectory(prefix='.news-stage-',dir=folder.parent) as temporary:
  for name,document in documents.items():
   content=json.dumps(document,ensure_ascii=False,indent=2)+'\n';json.loads(content)
   target=folder/name
   if target.exists() and target.read_text(encoding='utf-8')==content:continue
   staged=pathlib.Path(temporary)/name;staged.parent.mkdir(parents=True,exist_ok=True);staged.write_text(content,encoding='utf-8');changed.append((staged,target))
  for staged,target in changed:target.parent.mkdir(parents=True,exist_ok=True);os.replace(staged,target)
 return len(changed)

def collect(root=ROOT,now=None):
 now=now or dt.datetime.now(UTC);sources=json.loads((root/'config/sources.json').read_text(encoding='utf-8'))
 target=root/'news-data/latest.json'
 previous=json.loads(target.read_text(encoding='utf-8')) if target.exists() else {'articles':[],'sources':[]}
 if target.exists():validate_document(previous)
 incoming=[];statuses=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
  for items,status in pool.map(lambda source:fetch_source(source,now),sources):
   incoming.extend(items);statuses.append(status);print(json.dumps({'feed':status['id'],'status':status['status'],'fetched':len(items),'error':status['reason']},ensure_ascii=False))
 if not any(s['status']=='ok' for s in statuses):raise RuntimeError('All enabled feeds failed; all existing JSON preserved.')
 articles,duplicates=merge_articles(previous['articles'],incoming,now)
 for status in statuses:
  status['count']=sum(a['sourceId']==status['id'] for a in articles)
  if status['status']=='unavailable' and status['count']:status['status']='cached'
 data={'schemaVersion':1,'generatedAt':iso(now),'articles':articles,'sources':statuses}
 if previous.get('articles')==articles and previous.get('sources')==statuses:data['generatedAt']=previous['generatedAt']
 changes=write_bundle(root/'news-data',data)
 old_ids={a['id'] for a in previous['articles']}
 print(json.dumps({'checkedAt':iso(now),'newArticles':sum(a['id'] not in old_ids for a in articles),'duplicates':duplicates,'retained':len(articles),'filesChanged':changes},ensure_ascii=False))
 return data

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--validate',action='store_true');args=parser.parse_args()
 if args.validate:
  data=json.loads((ROOT/'news-data/latest.json').read_text(encoding='utf-8'));validate_document(data)
  for category in CATEGORIES:
   index=json.loads((ROOT/'news-data/categories'/f'{category}.json').read_text(encoding='utf-8'))
   if index['articleIds']!=[a['id'] for a in data['articles'] if a['category']==category]:raise ValueError('Category index mismatch')
  print('All news JSON and category indexes valid.')
 else:collect()
if __name__=='__main__':main()
