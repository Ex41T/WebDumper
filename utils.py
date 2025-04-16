from urllib.parse import urlparse
import re
from pathlib import Path


def get_asset_subdir(tag: str) -> str:
    return {
        'link': 'assets/css',
        'script': 'assets/js',
        'img': 'assets/img'
    }.get(tag, 'assets/other')

def extract_filename(url: str) -> str:
    return Path(urlparse(url).path).name or 'asset'


def normalize_url(url):
    """
    Remove trailing slash from URL if present.
    """
    return url.rstrip('/')


def is_internal_link(link, base_netloc):
    """
    Check whether a link is internal to the base domain.
    """
    parsed = urlparse(link)
    return parsed.netloc == '' or parsed.netloc == base_netloc


def extract_imported_css(content):
    """
    Extract URLs from @import statements in CSS.
    Accepts any @import url("...") pattern, not just ending with .css
    """
    return re.findall(r'@import\s+url\([\'"]?(.*?)[\'"]?\)', content)