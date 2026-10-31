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
from urllib.parse import urlparse

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
    result = {'updated_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'articles': latest}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'Saved {len(latest)} articles to {OUTPUT}')

if __name__ == '__main__':
    main()
