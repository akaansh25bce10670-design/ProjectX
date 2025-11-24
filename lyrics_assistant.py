import os
import sys
import sqlite3
import json
import time
import difflib
import re
import html
try:
    import requests
    _HAS_REQUESTS = True
except:
    import urllib.request as _urllib
    import urllib.parse as _urlparse
    _HAS_REQUESTS = False

DB_PATH = os.path.expanduser("~/.lyrics_assistant_cache.db")
ITUNES_SEARCH_URL = "https://itunes.apple.com/search"
LYRICS_OVH_URL = "https://api.lyrics.ovh/v1/{artist}/{title}"
GENIUS_BASE = "https://api.genius.com"
GENIUS_TOKEN = os.environ.get("GENIUS_TOKEN", "").strip()

def http_get(url, params=None, timeout=10, as_json=False):
    if _HAS_REQUESTS:
        r = requests.get(url, params=params, timeout=timeout, headers={"User-Agent":"LyricsAssistant/1.0"})
        r.raise_for_status()
        return r.json() if as_json else r.text
    else:
        if params:
            url = f"{url}?{_urlparse.urlencode(params)}"
        req = _urllib.Request(url, headers={"User-Agent":"LyricsAssistant/1.0"})
        with _urllib.urlopen(req, timeout=timeout) as fh:
            data = fh.read().decode()
            return json.loads(data) if as_json else data

def init_db(path=DB_PATH):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS lyrics_cache (id INTEGER PRIMARY KEY, artist TEXT COLLATE NOCASE, title TEXT COLLATE NOCASE, lyrics TEXT, ts INTEGER, UNIQUE(artist, title))")
    conn.commit()
    return conn

def get_cached_lyrics(conn, artist, title):
    cur = conn.cursor()
    cur.execute("SELECT lyrics FROM lyrics_cache WHERE artist = ? AND title = ?", (artist, title))
    row = cur.fetchone()
    return row[0] if row else None

def cache_lyrics(conn, artist, title, lyrics):
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO lyrics_cache (artist, title, lyrics, ts) VALUES (?, ?, ?, ?)", (artist, title, lyrics, int(time.time())))
    conn.commit()

def search_itunes(query, limit=10):
    params = {"term": query, "limit": limit, "media": "music"}
    try:
        data = http_get(ITUNES_SEARCH_URL, params=params, as_json=True)
    except Exception as e:
        print("iTunes search error:", e)
        return []
    out = []
    for r in data.get("results", []):
        out.append({
            "trackName": r.get("trackName"),
            "artistName": r.get("artistName"),
            "collectionName": r.get("collectionName"),
            "trackViewUrl": r.get("trackViewUrl"),
            "previewUrl": r.get("previewUrl"),
            "trackTimeMillis": r.get("trackTimeMillis")
        })
    return out

def _url_safe(s):
    return s.replace(" ", "%20").replace("#", "%23").replace("?", "%3F").strip()

def fetch_lyrics_ovh(artist, title):
    a = _url_safe(artist)
    t = _url_safe(title)
    url = LYRICS_OVH_URL.format(artist=a, title=t)
    try:
        data = http_get(url, as_json=True)
        lyrics = data.get("lyrics")
        if lyrics and lyrics.strip():
            return lyrics.strip()
    except Exception:
        return None
    return None

def genius_search_and_lyrics(artist, title):
    if not GENIUS_TOKEN:
        return None, "No GENIUS_TOKEN provided"
    headers = {"Authorization": f"Bearer {GENIUS_TOKEN}"}
    q = f"{artist} {title}"
    try:
        if _HAS_REQUESTS:
            r = requests.get(GENIUS_BASE + "/search", params={"q": q}, headers=headers, timeout=8)
            r.raise_for_status()
            data = r.json()
        else:
            url = GENIUS_BASE + "/search?" + _urlparse.urlencode({"q": q})
            req = _urllib.Request(url, headers=headers)
            with _urllib.urlopen(req, timeout=8) as fh:
                data = json.loads(fh.read().decode())
        hits = data.get("response", {}).get("hits", [])
        if not hits:
            return None, "Genius search returned no hits"
        for hit in hits:
            result = hit.get("result", {})
            path = result.get("path")
            if not path:
                continue
            page_url = "https://genius.com" + path
            try:
                html_text = http_get(page_url)
            except Exception as e:
                continue
            lyrics = scrape_genius_html(html_text)
            if lyrics:
                return lyrics, f"Found on Genius: {page_url}"
        return None, "No lyrics scraped from Genius pages"
    except Exception as e:
        return None, f"Genius API/search error: {e}"

def scrape_genius_html(html_text):
    m = re.findall(r'<div[^>]+data-lyrics-container="true"[^>]*>(.*?)</div>', html_text, flags=re.S)
    if m:
        parts = []
        for block in m:
            block = re.sub(r'<[^>]+>', '', block)
            parts.append(html.unescape(block).strip())
        lyrics = "\n".join(p for p in parts if p)
        if lyrics.strip():
            return lyrics.strip()
    m2 = re.search(r'<div class="lyrics">(.+?)</div>', html_text, flags=re.S)
    if m2:
        text = re.sub(r'<[^>]+>', '', m2.group(1))
        text = html.unescape(text).strip()
        if text:
            return text
    return None

def scrape_azlyrics(html_text):
    m = re.search(r'<!-- Usage of azlyrics.com content by any third-party.*?-->(.*?)</div>', html_text, flags=re.S)
    if m:
        text = re.sub(r'<[^>]+>', '', m.group(1))
        text = html.unescape(text).strip()
        if text:
            return text
    m2 = re.search(r'<div class="col-xs-12 col-lg-8 text-center">(.*?)</div>\s*<div class="ringtone">', html_text, flags=re.S)
    if m2:
        text = re.sub(r'<[^>]+>', '', m2.group(1))
        text = html.unescape(text).strip()
        if text:
            return text
    return None

def scrape_lyricsfreak(html_text):
    blocks = re.findall(r'<div class="lyrictxt jshare">(.*?)</div>', html_text, flags=re.S)
    if blocks:
        text = "\n".join(html.unescape(re.sub(r'<[^>]+>', '', b)).strip() for b in blocks)
        if text.strip():
            return text
    return None

def duckduckgo_search_links(query):
    q = query + " lyrics"
    url = "https://duckduckgo.com/html/"
    try:
        if _HAS_REQUESTS:
            r = requests.post(url, data={"q": q}, timeout=8, headers={"User-Agent":"LyricsAssistant/1.0"})
            r.raise_for_status()
            html_text = r.text
        else:
            data = _urlparse.urlencode({"q": q}).encode()
            req = _urllib.Request(url, data=data, headers={"User-Agent":"LyricsAssistant/1.0"})
            with _urllib.urlopen(req, timeout=8) as fh:
                html_text = fh.read().decode()
        links = re.findall(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"', html_text)
        if not links:
            links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*rel="nofollow"', html_text)
        return links
    except Exception:
        return []

def try_scrape_common_sites(artist, title):
    q = f"{artist} {title}"
    links = duckduckgo_search_links(q)
    tried = []
    for link in links:
        low = link.lower()
        tried.append(link)
        try:
            html_text = http_get(link)
        except Exception:
            continue
        if "genius.com" in low:
            lyrics = scrape_genius_html(html_text)
            if lyrics:
                return lyrics, f"Scraped Genius page: {link}"
        if "azlyrics.com" in low:
            lyrics = scrape_azlyrics(html_text)
            if lyrics:
                return lyrics, f"Scraped AZLyrics page: {link}"
        if "lyricsfreak.com" in low or "lyricsfreak." in low:
            lyrics = scrape_lyricsfreak(html_text)
            if lyrics:
                return lyrics, f"Scraped LyricsFreak: {link}"
    return None, f"Tried links: {tried[:5]}"

def clean_title_artist(s):
    s = s.strip()
    s = re.sub(r'\(.*?version.*?\)', '', s, flags=re.I)
    s = re.sub(r'\(.*?remix.*?\)', '', s, flags=re.I)
    s = re.sub(r'\(.*?feat[^\)]*\)', '', s, flags=re.I)
    s = re.sub(r'feat\..*', '', s, flags=re.I)
    s = re.sub(r'ft\..*', '', s, flags=re.I)
    s = re.sub(r'[\[\]\"]', '', s)
    return s.strip()

def find_lyrics(conn, artist, title):
    cached = get_cached_lyrics(conn, artist, title)
    if cached:
        return cached, "cached"
    artist_c = clean_title_artist(artist)
    title_c = clean_title_artist(title)
    sources_tried = []
    l = fetch_lyrics_ovh(artist_c, title_c)
    sources_tried.append("lyrics.ovh")
    if l:
        cache_lyrics(conn, artist, title, l)
        return l, "lyrics.ovh"
    if GENIUS_TOKEN:
        l, info = genius_search_and_lyrics(artist_c, title_c)
        sources_tried.append("genius_api")
        if l:
            cache_lyrics(conn, artist, title, l)
            return l, info
    l, info = try_scrape_common_sites(artist_c, title_c)
    sources_tried.append("scrape_search")
    if l:
        cache_lyrics(conn, artist, title, l)
        return l, info
    return None, f"No lyrics found. Sources tried: {sources_tried}. Last info: {info}"

def best_matches(results, query):
    def score(r):
        txt = (r.get("trackName","") + " " + r.get("artistName","")).lower()
        return difflib.SequenceMatcher(None, query.lower(), txt).ratio()
    scored = [(score(r), r) for r in results]
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored

def pretty_print(scored):
    for i, (score, r) in enumerate(scored, 1):
        title = r.get("trackName") or ""
        artist = r.get("artistName") or ""
        album = r.get("collectionName") or ""
        dur = r.get("trackTimeMillis")
        dur = f"{int(dur/60000)}:{int((dur%60000)/1000):02d}" if dur else "--:--"
        print(f"{i}. {title} — {artist} [{album}] ({dur}) score={score:.2f}")

def interactive(conn):
    print("Lyrics Assistant (stronger). Type 'exit' to quit.")
    while True:
        q = input("\nEnter song title or artist or both: ").strip()
        if not q:
            continue
        if q.lower() in ("exit", "quit"):
            return
        results = search_itunes(q, limit=20)
        if not results:
            print("iTunes returned no results; trying a direct search fallback.")
            artist = ""
            title = q
            lyrics, info = find_lyrics(conn, artist, title)
            if lyrics:
                print(f"\n--- Lyrics (source: {info}) ---\n{lyrics}\n")
            else:
                print("No lyrics found. Info:", info)
            continue
        scored = best_matches(results, q)
        pretty_print(scored[:8])
        sel = input("Pick a number to fetch lyrics (or '0' to search again): ").strip()
        if not sel.isdigit():
            print("Invalid input")
            continue
        num = int(sel)
        if num == 0:
            continue
        if num < 1 or num > len(scored):
            print("Number out of range")
            continue
        _, r = scored[num-1]
        artist = r.get("artistName","")
        title = r.get("trackName","")
        print(f"\nAttempting lyrics for: {title} — {artist}")
        lyrics, info = find_lyrics(conn, artist, title)
        if lyrics:
            print(f"\n--- Lyrics (source: {info}) ---\n{lyrics}\n")
        else:
            print("No lyrics found. Info:", info)

def main():
    conn = init_db()
    try:
        interactive(conn)
    finally:
        conn.close()

if __name__ == "__main__":
    main()