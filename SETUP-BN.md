# বাংলা নিউজ: GitHub-এ অটো আপডেট

Repository: https://github.com/rudro8915-colla/banglanews-

## একবারের setup

1. এই folder-এর **ভেতরের ফাইলগুলো** repository root-এ রাখুন। `.github/workflows/update-news.yml` অবশ্যই থাকবে। পুরো website project, `.firebase`, `.automation`, credentials বা LMS-এর কিছু upload করবেন না।
2. Repository public, default branch `main` রাখুন। Settings → Actions → General-এ Actions অনুমোদিত থাকা প্রয়োজন। Workflow contents-write permission চায়; organization policy আটকালে সেটি না বুঝে broad access দেবেন না।
3. Actions → **Update public news JSON** → **Run workflow** → branch main। সব ধাপ সবুজ হওয়া পর্যন্ত অপেক্ষা করুন। Failure হলে failed step-এর logs দেখুন; কোনো token chat-এ দেবেন না।
4. এই URL খুলে valid JSON ও সাম্প্রতিক `generatedAt` দেখুন: https://raw.githubusercontent.com/rudro8915-colla/banglanews-/main/news-data/latest.json
5. Website project-এর `data/news-config.json`-এ `newsDataUrl` হবে `https://raw.githubusercontent.com/rudro8915-colla/banglanews-/main/news-data/`। এই repository-তে website source নেই; website পরিবর্তন আলাদা project-এ প্রস্তুত।
6. মালিকের explicit Firebase deployment approval পাওয়ার পরে website folder-এ `npm test`, `npm run build`, তারপর `npx firebase-tools@15 deploy --only hosting --project pata-newsroom-bd --non-interactive`। আগে `firebase.json`-এ hosting.site ঠিক `banglanewsbd` কি না দেখুন। LMS project `porashona-2eaee` ব্যবহার করবেন না।
7. Browser-এ headline, source/category/search, archive, fallback ও original links পরীক্ষা করুন। Browser network response-এ public JSON/CORS কাজ করছে কি না যাচাই করুন।

## প্রতিদিনের কাজ

প্রতি ঘণ্টার ৭ ও ৩৭ মিনিটে GitHub-এর server চেষ্টা করবে; exact-minute guarantee নয়। PC/CMD/Codex খোলা রাখতে হবে না। New data GitHub-এ commit হলে website refresh/খবর refresh button দিয়ে পড়বে—প্রতি update-এ Firebase deploy লাগবে না।

## সমস্যা হলে

- 404: workflow upload হয়েছে কি না, repository public কি না এবং URL-এ owner/repository/branch spelling মিলছে কি না দেখুন।
- 403 push: workflow token write permission অথবা branch protection বাধা দিচ্ছে। Rule না মুছে প্রয়োজনীয় সীমিত অনুমতি review করুন।
- RSS failure: একটি source ব্যর্থ হলে অন্যগুলো চলবে। Disabled source শুধু `config/sources.json`-এ verified official feed দিয়ে enable করুন; paywall/restriction bypass করবেন না।
- সব source ব্যর্থ: run fail হবে, আগের JSON থাকবে।
- Schedule চলেনি: main branch-এ workflow আছে কি না, Actions enabled কি না ও GitHub status দেখুন। ৬০ দিন repository activity না থাকলে public schedule বন্ধ হতে পারে।
- বন্ধ করতে: Actions → workflow menu → Disable workflow। Site শেষ পাওয়া data দেখাবে।

## খরচ ও সুরক্ষা

Standard public GitHub runner ব্যবহার করা হয়েছে; private repository-তে job চলবে না। Paid runner, billing, artifact upload বা external credentials নেই। Full articles/images রাখা হয় না। সর্বোচ্চ ৩০ দিন/৩০০০ খবর; category ফাইলে শুধু ID। Git history-তে পুরোনো commit থাকে, সেটি আলাদা size consideration। Firebase শুধু website shell host করবে; তার Spark traffic/storage limits প্রযোজ্য। Google Apps Script ও Windows scheduler ব্যবহার করা হবে না।

প্রথম manual run ও public JSON পরীক্ষা পাস না হওয়া পর্যন্ত automation live দাবি করবেন না। Firebase frontend deploy-ও আলাদা অনুমোদনের কাজ।
