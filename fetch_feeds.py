#!/usr/bin/env python3
"""Fetch selected public RSS/Atom feeds into data/articles.json (stdlib only)."""
import concurrent.futures
import datetime as dt
import email.utils
import html
import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse, urlencode

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / 'data' / 'articles.json'
FEEDS = [
    ('OpenAI', 'AI', 'https://openai.com/news/rss.xml'),
    ('Google DeepMind', 'AI', 'https://deepmind.google/blog/rss.xml'),
    ('Hugging Face', 'AI', 'https://huggingface.co/blog/feed.xml'),
    ('TechCrunch AI', 'AI', 'https://techcrunch.com/category/artificial-intelligence/feed/'),
    ('The Decoder', 'AI', 'https://the-decoder.com/feed/'),
    ('MIT Technology Review', 'Emerging', 'https://www.technologyreview.com/feed/'),
    ('Microsoft Power BI', 'Analytics', 'https://powerbi.microsoft.com/en-us/blog/feed/'),
    ('Databricks', 'Analytics', 'https://www.databricks.com/feed'),
    ('Google Cloud', 'Cloud', 'https://cloud.google.com/feeds/blog.xml'),
    ('AWS News', 'Cloud', 'https://aws.amazon.com/blogs/aws/feed/'),
    ('GitHub Blog', 'Development', 'https://github.blog/feed/'),
    ('Hacker News', 'Development', 'https://news.ycombinator.com/rss'),
    ('Wired Security', 'Security', 'https://www.wired.com/feed/category/security/latest/rss'),
    ('The Hacker News', 'Security', 'https://feeds.feedburner.com/TheHackersNews'),
    ('The Verge', 'Emerging', 'https://www.theverge.com/rss/tech/index.xml'),
    ('IEEE Spectrum', 'Emerging', 'https://spectrum.ieee.org/feeds/feed.rss'),
    ('Microsoft Fabric', 'Analytics', 'https://blog.fabric.microsoft.com/en-us/blog/feed/'),
    ('Google AI', 'AI', 'https://blog.google/technology/ai/rss/'),
]
ATOM = '{http://www.w3.org/2005/Atom}'
CONTENT = '{http://purl.org/rss/1.0/modules/content/}'
DC = '{http://purl.org/dc/elements/1.1/}'

def clean(value):
    value = re.sub(r'<[^>]*>', ' ', value or '')
    value = html.unescape(value)
    return re.sub(r'\s+', ' ', value).strip()

def iso_date(value):
    if not value:
        return None
    try:
        date = email.utils.parsedate_to_datetime(value)
        if date:
            return date.astimezone(dt.timezone.utc).isoformat()
    except (TypeError, ValueError, OverflowError):
        pass
    try:
        return dt.datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(dt.timezone.utc).isoformat()
    except (ValueError, TypeError):
        return None

def first_text(element, paths):
    for path in paths:
        found = element.find(path)
        if found is not None and found.text:
            return found.text.strip()
    return ''

def extract(source, category, url):
    req = urllib.request.Request(url, headers={'User-Agent': 'TechPulseRSSReader/1.0 (public news aggregation)', 'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml, */*'})
    try:
        with urllib.request.urlopen(req, timeout=14) as response:
            raw = response.read(2_500_000)
        root = ET.fromstring(raw)
        is_atom = root.tag.endswith('feed')
        entries = root.findall(f'{ATOM}entry') if is_atom else root.findall('.//item')
        items = []
        for entry in entries[:35]:
            title = clean(first_text(entry, [f'{ATOM}title', 'title']))
            description = clean(first_text(entry, [f'{ATOM}summary', f'{ATOM}content', 'description', f'{CONTENT}encoded']))[:230]
            link = first_text(entry, ['link'])
            if is_atom:
                for node in entry.findall(f'{ATOM}link'):
                    if node.attrib.get('rel', 'alternate') == 'alternate':
                        link = node.attrib.get('href', '')
                        break
            date = iso_date(first_text(entry, [f'{ATOM}published', f'{ATOM}updated', 'pubDate', f'{DC}date']))
            if not title or not link or not date or urlparse(link).scheme not in ('http','https'):
                continue
            items.append({'title': title[:200], 'summary': description, 'url': link, 'source': source, 'category': category, 'published': date})
        print(f'{source}: {len(items)} articles')
        return items
    except Exception as exc:
        print(f'{source}: failed: {exc}')
        return []

def main():
    with concurrent.futures.ThreadPoolExecutor(max_workers=9) as pool:
        results = list(pool.map(lambda row: extract(*row), FEEDS))
    all_items = [article for items in results for article in items]
    dedup = {}
    for article in all_items:
        key = re.sub(r'[^a-z0-9]', '', article['title'].lower())
        if key and key not in dedup:
            dedup[key] = article
    latest = sorted(dedup.values(), key=lambda a: a['published'], reverse=True)[:450]
    if not latest:
        print('No feeds returned articles; keeping prior data unchanged.')
        return
    now = dt.datetime.now(dt.timezone.utc)
    # These are relevance/freshness signals, NOT measured social popularity.
    terms = ('ai', 'agent', 'model', 'power bi', 'fabric', 'databricks', 'security', 'cloud', 'github', 'python', 'release', 'launch')
    def signal(a):
        age = max(0, (now - dt.datetime.fromisoformat(a['published'])).total_seconds() / 3600)
        keywords = sum(1 for term in terms if term in a['title'].lower())
        return round(max(0, 7 - age / 18) + min(3, keywords) + (1 if a['source'] in ('OpenAI', 'Google DeepMind', 'Microsoft Power BI', 'Microsoft Fabric', 'Databricks') else 0), 2)
    fresh = [a for a in latest if (now - dt.datetime.fromisoformat(a['published'])).days <= 7]
    trend = sorted(fresh, key=lambda a: (signal(a), a['published']), reverse=True)[:6]
    ai_words = re.compile(r'\b(ai|agent|model|reasoning|research|gpt|gemini|claude|llm|deepmind|openai)\b', re.I)
    release_words = re.compile(r'\b(release|released|launch|launched|update|updated|upgrade|version|feature|generally available|rollout|preview|introducing|announced|now available)\b', re.I)
    ai = [a for a in latest if a['category'] == 'AI' and ai_words.search(a['title'])][:6]
    releases = [a for a in latest if release_words.search(a['title'])][:6]
    result = {'updated_at': now.isoformat(), 'ranking_method': 'freshness + topic matching + source signal; not verified popularity', 'articles': latest}
    insights = {'updated_at': now.isoformat(), 'trending': trend, 'ai_breakthroughs': ai, 'technology_releases': releases}
    (ROOT / 'data').mkdir(parents=True, exist_ok=True)
    (ROOT / 'data' / 'insights.json').write_text(json.dumps(insights, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'Saved {len(latest)} articles and new intelligence sections')

def refresh_github_projects():
    target = ROOT / 'data' / 'github-trending.json'
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=21)).date().isoformat()
    query = urlencode({'q': f'created:>={since} stars:>=10 fork:false', 'sort': 'stars', 'order': 'desc', 'per_page': 12})
    headers = {'User-Agent': 'TechPulse/2.0', 'Accept': 'application/vnd.github+json'}
    token = os.getenv('GITHUB_TOKEN', '').strip()
    if token:
        headers['Authorization'] = f'Bearer {token}'
    try:
        req = urllib.request.Request('https://api.github.com/search/repositories?' + query, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as response:
            result = json.load(response)
        repos = []
        for r in result.get('items', []):
            if not r.get('html_url', '').startswith('https://github.com/'):
                continue
            repos.append({'name': r.get('full_name', ''), 'description': (r.get('description') or '')[:220],
                          'url': r['html_url'], 'language': r.get('language') or 'Open source',
                          'stars': r.get('stargazers_count', 0), 'created_at': r.get('created_at', '')})
        if repos:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps({'updated_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'method': 'GitHub search: repositories created in last 21 days, sorted by total stars', 'repositories': repos}, indent=2) + '\n', encoding='utf-8')
            print(f'Saved {len(repos)} GitHub repositories')
        else:
            print('GitHub API returned no projects; keeping previous results.')
    except Exception as error:
        print(f'GitHub repository discovery unavailable ({error}); keeping previous results.')

if __name__ == '__main__':
    main()
    refresh_github_projects()
