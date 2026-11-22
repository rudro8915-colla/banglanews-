import datetime as dt, importlib.util, pathlib, tempfile, json, unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('collector',ROOT/'scripts/collect_news.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
NOW=dt.datetime(2026,11,22,8,tzinfo=dt.timezone.utc)
SOURCE={'id':'sample','name':'সংবাদ','url':'https://example.com','articleDomains':['example.com'],'defaultCategory':'national','enabled':True,'feed':'https://example.com/feed'}
def rss(title='বাংলা খবর',url='https://example.com/news/1',guid='one',date='Sun, 22 Nov 2026 07:00:00 GMT'):
 return f'<rss><channel><item><title>{title}</title><link>{url}</link><guid>{guid}</guid><pubDate>{date}</pubDate><description><![CDATA[<p>ছোট খবর</p><script>bad()</script>]]></description></item></channel></rss>'.encode()
class CollectorTests(unittest.TestCase):
 def test_rss_bangla_and_excerpt_sanitized(self):
  a=c.parse_feed(rss(),SOURCE,NOW)[0];self.assertEqual(a['title'],'বাংলা খবর');self.assertEqual(a['description'],'ছোট খবর');self.assertEqual(a['publishedAt'],'2026-11-22T07:00:00Z')
 def test_atom_and_missing_guid(self):
  xml=b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>News</title><link href="/article"/><updated>2026-11-22T07:00:00Z</updated></entry></feed>'
  a=c.parse_feed(xml,SOURCE,NOW)[0];self.assertIsNone(a['guid']);self.assertEqual(a['url'],'https://example.com/article')
 def test_invalid_xml_and_offsite_links(self):
  for payload in [b'<html/>',b'<!DOCTYPE rss><rss/>',b'<rss>']:
   with self.assertRaises(Exception):c.parse_feed(payload,SOURCE,NOW)
  for url in ['https://attacker.test/x','https://example.com@attacker.test/x','javascript:alert(1)']:
   self.assertFalse(c.parse_feed(rss(url=url),SOURCE,NOW))
 def test_canonical_tracking_dedup(self):
  self.assertEqual(c.canonical_url('http://www.example.com/a/?utm_source=x&amp=1#section'),'https://example.com/a?amp=1')
  a=c.parse_feed(rss(),SOURCE,NOW)[0];b={**a,'id':'other','guid':'other','url':a['url']+'?utm_source=x'}
  merged,n=c.merge_articles([], [a,b],NOW);self.assertEqual(len(merged),1);self.assertEqual(n,1)
 def test_guid_and_headline_duplicate_detection_preserves_other_publishers(self):
  a=c.parse_feed(rss(),SOURCE,NOW)[0];b={**a,'id':'second','url':'https://example.com/new-path'}
  self.assertEqual(len(c.merge_articles([], [a,b],NOW)[0]),1)
  b.update(guid='different',sourceId='different',url='https://other.example/a',id='third')
  self.assertEqual(len(c.merge_articles([], [a,b],NOW)[0]),2)
 def test_reimport_stable_first_seen_and_id(self):
  a=c.parse_feed(rss(),SOURCE,NOW)[0];b=c.parse_feed(rss(),SOURCE,NOW+dt.timedelta(hours=1))[0]
  result,_=c.merge_articles([a],[b],NOW+dt.timedelta(hours=1));self.assertEqual(result,[a])
 def test_retention_sort_and_limit(self):
  base=c.parse_feed(rss(),SOURCE,NOW)[0]
  articles=[{**base,'id':str(i),'guid':str(i),'title':'Title '+str(i),'url':'https://example.com/a/'+str(i),'contentHash':str(i),'publishedAt':c.iso(NOW-dt.timedelta(minutes=i))} for i in range(3005)]
  articles.append({**base,'publishedAt':'2020-01-01T00:00:00Z'})
  result,_=c.merge_articles([],articles,NOW);self.assertEqual(len(result),3000);self.assertEqual(result[0]['id'],'0')
 def test_missing_date_is_not_falsely_today(self):
  a=c.parse_feed(rss(date=''),SOURCE,NOW)[0];self.assertIsNone(a['publishedAt']);self.assertEqual(a['firstSeenAt'],c.iso(NOW))
 def test_semantic_no_change_does_not_rewrite_json(self):
  a=c.parse_feed(rss(),SOURCE,NOW)[0];data={'schemaVersion':1,'generatedAt':c.iso(NOW),'articles':[a],'sources':[]}
  with tempfile.TemporaryDirectory() as folder:
   target=pathlib.Path(folder)/'news-data';self.assertGreater(c.write_bundle(target,data),0);stamp=(target/'latest.json').stat().st_mtime_ns
   self.assertEqual(c.write_bundle(target,data),0);self.assertEqual((target/'latest.json').stat().st_mtime_ns,stamp)
 def test_all_failed_feeds_preserve_existing_files(self):
  with tempfile.TemporaryDirectory() as folder:
   root=pathlib.Path(folder);(root/'config').mkdir();(root/'config/sources.json').write_text(json.dumps([SOURCE]));a=c.parse_feed(rss(),SOURCE,NOW)[0]
   c.write_bundle(root/'news-data',{'schemaVersion':1,'generatedAt':c.iso(NOW),'articles':[a],'sources':[]});before=(root/'news-data/latest.json').read_bytes()
   with patch.object(c,'fetch_source',return_value=([],{'id':'sample','status':'unavailable','reason':'timeout'})):
    with self.assertRaises(RuntimeError):c.collect(root,NOW)
   self.assertEqual((root/'news-data/latest.json').read_bytes(),before)
 def test_category_and_breaking_are_source_grounded(self):
  a=c.parse_feed(rss(title='ক্রিকেট ম্যাচের খবর'),SOURCE,NOW)[0];self.assertEqual(a['category'],'sports');self.assertFalse(a['isBreaking'])
if __name__=='__main__':unittest.main()
