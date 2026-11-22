# Bangla News public data

Public RSS aggregation for https://banglanewsbd.web.app/. This separate repository contains no website application source, Firebase configuration, Firebase credentials or LMS data. It does not deploy Firebase or require a computer, database, Apps Script, Cloudflare or paid API.

## Run

Python 3.13, standard library only:

```sh
python -m unittest discover -s tests
python scripts/collect_news.py
python scripts/collect_news.py --validate
```

## Automation

`.github/workflows/update-news.yml` runs at minute 7 and 37 of each UTC hour and supports manual Run workflow. Standard GitHub-hosted Ubuntu, 6-minute timeout, one concurrent run, data-only commits, no push trigger (no commit loop), no uploaded artifacts/cache. Private repositories skip this job to prevent surprise usage charges. The built-in repository-scoped `GITHUB_TOKEN` needs contents write; no personal tokens or Firebase secrets.

The schedule must be on default branch `main`. GitHub schedules may be delayed. Public scheduled workflows can be disabled after 60 days without repository activity; normal data commits provide activity, but no synthetic keep-alive commits are made.

## Data contract

`news-data/latest.json` contains at most 3000 articles from the last 30 days. `sources.json` reports source state. `categories/*.json` contains article IDs referring to latest.json (no repeated article bodies). `news.schema.json` documents the format; `--validate` checks data and category indexes without external dependencies.

Articles contain original source URL, source name, title, at most 160 characters of excerpt, publication time (null when unknown), category, GUID where present and a stable identifier. No full articles or downloaded publisher images. Breaking labels require explicit publisher metadata/title; recency alone is not breaking news. Deduplication uses canonical URL, publisher-scoped GUID, content hash and same-publisher/day headline. Different publishers' reporting is preserved.

Retention removes expired records from current JSON only, not prior Git commits. Git history can grow; review repository size periodically. Original site data was backed up and was not deleted during migration.

If one source fails, retain eligible old articles and report cached/unavailable status. If every enabled source fails, stop without writing files. Identical data does not create a new commit; `generatedAt` records dataset changes, while workflow logs show each actual check time. Files are staged then atomically replaced; publication is one Git commit.

## Verified sources

Official publisher-domain RSS/Atom responses were checked during setup. Verification is connectivity/content validation, not a publisher licensing grant; retain attribution and check publisher terms for your use. Disabled entries are not fetched until a new official feed is verified and enabled. BBC Bangla is disabled because no current official feed was verified.

| Publisher | State | RSS URL | Verification result |
|---|---|---|---|
| প্রথম আলো | Enabled | https://www.prothomalo.com/feed | Verified official-domain RSS/Atom with recent articles |
| The Daily Star | Enabled | https://www.thedailystar.net/news/bangladesh/rss.xml | Verified official-domain RSS/Atom with recent articles |
| ইত্তেফাক | Enabled | https://www.ittefaq.com.bd/feed/ | Verified official-domain RSS/Atom with recent articles |
| যুগান্তর | Disabled | https://www.jugantor.com/feed/rss.xml | HTTPError: 403 |
| সমকাল | Disabled | https://samakal.com/rss.xml | ValueError |
| কালের কণ্ঠ | Disabled | https://www.kalerkantho.com/rss.xml | HTTPError: 403 |
| বাংলাদেশ প্রতিদিন | Disabled | https://www.bd-pratidin.com/rss.xml | HTTPError: 403 |
| Dhaka Tribune | Enabled | https://www.dhakatribune.com/feed/ | Verified official-domain RSS/Atom with recent articles |
| বাংলা ট্রিবিউন | Enabled | https://www.banglatribune.com/feed/ | Verified official-domain RSS/Atom with recent articles |
| The Business Standard | Enabled | https://www.tbsnews.net/bangladesh/rss.xml | Verified official-domain RSS/Atom with recent articles |
| bdnews24.com | Disabled | https://bdnews24.com/?widgetName=rssfeed&widgetId=1150&getXmlFeed=true | ValueError |
| জাগো নিউজ ২৪ | Enabled | https://www.jagonews24.com/rss/rss.xml | Verified official-domain RSS/Atom with recent articles |
| বাংলানিউজটোয়েন্টিফোর | Disabled | https://www.banglanews24.com/rss/rss.xml | HTTPError: 404 |
| ঢাকা পোস্ট | Disabled | https://www.dhakapost.com/rss.xml | HTTPError: 404 |
| মানবজমিন | Disabled | https://mzamin.com/rss.php | HTTPError: 404 |
| নয়া দিগন্ত | Disabled | https://dailynayadiganta.com/rss.xml | ValueError |
| বণিক বার্তা | Disabled | https://bonikbarta.com/feed | ValueError |
| দেশ রূপান্তর | Enabled | https://www.deshrupantor.com/feed/ | Verified official-domain RSS/Atom with recent articles |
| আজকের পত্রিকা | Enabled | https://www.ajkerpatrika.com/feed | Verified official-domain RSS/Atom with recent articles |
| কালবেলা | Disabled | https://www.kalbela.com/rss.xml | HTTPError: 403 |
| আমার দেশ | Disabled | Not verified | Pending live RSS verification |
| দৈনিক ইনকিলাব | Disabled | https://dailyinqilab.com/rss.xml | HTTPError: 404 |
| NEW AGE | Disabled | https://www.newagebd.net/rss.xml | HTTPError: 404 |
| The Financial Express | Disabled | https://thefinancialexpress.com.bd/feed | HTTPError: 404 |
| daily sun | Disabled | https://www.daily-sun.com/rss.xml | HTTPError: 403 |
| The Daily Observer | Disabled | https://www.observerbd.com/rss.php | HTTPError: 415 |
| দৈনিক পূর্বকোণ | Enabled | https://dainikpurbokone.net/feed/ | Verified official-domain RSS/Atom with recent articles |
| দৈনিক আজাদী | Enabled | https://dainikazadi.net/feed/ | Verified official-domain RSS/Atom with recent articles |
| সিলেটের ডাক | Enabled | https://sylheterdak.com.bd/feed/ | Verified official-domain RSS/Atom with recent articles |
| সংবাদ | Disabled | Not verified | Pending live RSS verification |
| BBC News | Enabled | https://feeds.bbci.co.uk/news/rss.xml | Verified official-domain RSS/Atom with recent articles |
| বিবিসি বাংলা | Disabled | Not verified | No current official Bangla RSS URL verified; original publisher link remains available. |

## Free-plan estimate (checked 2026-11-22)

48 scheduled runs/day = 1440 runs in 30 days. At 1–2 minutes each, 1440–2880 minutes/month. Current GitHub Free billing documentation lists $12 monthly included compute; standard private Linux is $0.006/minute ($8.64–$17.28 for this estimate, before other usage). Public standard runners remain free. Therefore this dedicated public data repository is recommended for the requested 30-minute schedule. No billing or paid plan should be enabled. No artifact/cache uploads are used. Actual GitHub-hosted runtime must be measured after the first run.

Raw GitHub responded with `Access-Control-Allow-Origin: *` during setup; verify the actual latest.json after upload. The frontend must allow `https://raw.githubusercontent.com` in connect-src and configure the real public endpoint without credentials.

References: https://docs.github.com/en/billing/concepts/product-billing/github-actions · https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows · https://support.bbc.co.uk/platform/feeds/NewsFeeds.htm
