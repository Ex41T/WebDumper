from utils import extract_imported_css
from urllib.parse import urlparse, urljoin
from logger import log_info, log_warn, log_fail
from aiohttp import ClientSession
from pathlib import Path
import asyncio
import config


async def fetch_html_async(url: str, session: ClientSession):
    """
    Fetches HTML or CSS content from a URL asynchronously.
    Skips files that are not 'text/html' or 'text/css'.
    """
    headers = config.HEADERS

    try:
        async with session.get(url, headers=headers, timeout=config.TIMEOUT, ssl=False) as response:
            content_type = response.headers.get('Content-Type', '') if hasattr(response.headers, 'get') else ''
            if 'text/html' in content_type or 'text/css' in content_type:
                text = await response.text()
                return text, dict(response.headers)
            else:
                log_warn(f"[SKIP] Non-text content at {url} ({content_type})")
                return None, None
    except Exception as e:
        log_fail(f"[ERROR] Failed to fetch {url}: {e}")
        return None, None


async def save_asset_async(
    url: str,
    tag: str,
    output_dir: Path,
    session: ClientSession,
    base_url: str = None,
    seen_assets: set = None
):
    """
    Downloads an asset (CSS, JS, IMG...) and saves it to disk.
    Prevents duplicate downloads using 'seen_assets'.
    Also handles nested CSS @import calls recursively.
    """
    if url.startswith("data:"):
        log_warn(f"[SKIP] Skipping base64 asset: {url[:40]}...")
        return

    # check if asset exists already
    if seen_assets is not None:
        parsed_url = urlparse(url)
        clean_url = parsed_url._replace(query="", fragment="").geturl()

        if clean_url in seen_assets:
            return
        seen_assets.add(clean_url)

    headers = config.HEADERS
    parsed = urlparse(url)
    file_name = Path(parsed.path).name or 'asset'

    subdir = {
        'link': 'assets/css',
        'script': 'assets/js',
        'img': 'assets/img'
    }.get(tag, 'assets/other')

    full_path = output_dir / subdir / file_name
    full_path.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(config.RETRY_COUNT):
        try:
            async with session.get(url, headers=headers, timeout=config.TIMEOUT, ssl=False) as response:
                response.raise_for_status()
                content_type = response.headers.get('Content-Type', '') if hasattr(response.headers, 'get') else ''
                content = await response.read()

                with open(full_path, 'wb') as f:
                    f.write(content)

                log_info(f"[ASSET] Saved {file_name} ({tag})")

                # Handle @import inside CSS
                if tag == 'link' and full_path.suffix == '.css' and 'text/css' in content_type:
                    css_text = content.decode('utf-8', errors='ignore')
                    imported_urls = extract_imported_css(css_text)
                    for rel_url in imported_urls:
                        abs_url = urljoin(base_url or url, rel_url)
                        await save_asset_async(abs_url, 'link', output_dir, session, url, seen_assets)

                break 

        except Exception as e:
            log_warn(f"[WARN] Attempt {attempt+1}/{config.RETRY_COUNT} failed for {url}: {e}")
            await asyncio.sleep(2)

    else:
        log_fail(f"[FAIL] Could not download: {url}")
