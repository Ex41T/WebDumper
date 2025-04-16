from pathlib import Path
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from downloader import fetch_html_async, save_asset_async
from utils import normalize_url, is_internal_link
from logger import log_info
import config


# Tracks already visited pages to avoid redundant crawling
visited = set()


def extract_links(html: str, base_url: str) -> set:
    """

    Extracts all valid internal <a> tag href links from the given HTML.

    """

    soup = BeautifulSoup(html, 'html.parser')
    links = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith(('mailto:', 'tel:', '#', 'javascript:')):
            continue
        full_url = urljoin(base_url, href)
        links.add(full_url)
    return links


def save_html(content: str, output_dir: Path, filename: str):
    """

    Saves HTML content to the specified output directory.

    """

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / filename, 'w', encoding='utf-8') as f:
        f.write(content)


def save_headers(headers: dict, output_dir: Path):
    """

    Saves HTTP response headers to a file for debugging/inspection.

    """

    with open(output_dir / 'headers.txt', 'w', encoding='utf-8') as f:
        for k, v in headers.items():
            f.write(f"{k}: {v}\n")


async def parse_and_download_assets(html: str, base_url: str, output_dir: Path, session, seen_assets: set, tag_map=None):
    """
    Parses HTML and asynchronously downloads all discovered assets (CSS, JS, IMG).
    Skips fonts and already downloaded resources using 'seen_assets'.
    """

    soup = BeautifulSoup(html, 'html.parser')
    tags = tag_map or {
        'link': 'href',
        'script': 'src',
        'img': 'src'
    }

    for tag, attr in tags.items():
        for el in soup.find_all(tag):
            if tag == 'link':
                rel = el.get('rel')
                if rel is None or 'stylesheet' not in rel:
                    continue

            asset_url = el.get(attr)
            if not asset_url:
                continue

            full_url = urljoin(base_url, asset_url)

            if 'fonts.googleapis.com' in full_url or 'fonts.gstatic.com' in full_url:
                continue

            await save_asset_async(full_url, tag, output_dir, session, base_url, seen_assets)


async def crawl_page_async(
    url: str,
    base_url: str,
    output_dir: Path,
    base_netloc: str,
    index_list_file: Path,
    session,
    seen_assets: set
):
    """
    Recursively crawls and downloads internal pages and their assets.
    Prevents duplicate visits and tracks asset usage.
    """
    
    norm_url = normalize_url(url)
    if norm_url in visited:
        return
    visited.add(norm_url)

    log_info(f"[CRAWL] {url}")
    html, headers = await fetch_html_async(url, session)
    if not html:
        return

    parsed = urlparse(url)
    filename = 'index.html' if parsed.path in ('', '/') else parsed.path.strip('/').replace('/', '_') + '.html'

    save_html(html, output_dir, filename)
    save_headers(headers, output_dir)

    await parse_and_download_assets(html, base_url, output_dir, session, seen_assets)

    with open(index_list_file, 'a', encoding='utf-8') as f:
        f.write(filename + '\n')

    links = extract_links(html, url)
    for link in links:
        if is_internal_link(link, base_netloc):
            await crawl_page_async(link, base_url, output_dir, base_netloc, index_list_file, session, seen_assets)
