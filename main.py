import asyncio
import sys
from pathlib import Path
from urllib.parse import urlparse
from core import crawl_page_async
from rewrite import rewrite_asset_paths
from logger import log_info, log_fail
import config
import time
import aiohttp

# 🔧 Fix dla aiodns na Windows
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def get_file_stats(output_dir: Path) -> dict:
    """Returns count and size of files by type."""
    stats = {
        'css': 0,
        'js': 0,
        'img': 0,
        'other': 0,
        'total_files': 0,
        'total_size': 0.0  # in MB
    }

    for file in output_dir.rglob('*'):
        if file.is_file():
            ext = file.suffix.lower()
            stats['total_files'] += 1
            stats['total_size'] += file.stat().st_size / (1024 * 1024)

            if ext in ['.css']:
                stats['css'] += 1
            elif ext in ['.js']:
                stats['js'] += 1
            elif ext in ['.png', '.jpg', '.jpeg', '.svg', '.gif', '.webp']:
                stats['img'] += 1
            else:
                stats['other'] += 1

    return stats


async def run_webdumper():
    print("============================")
    print("     WebDumper PRO v2.0     ")
    print("============================")

    url = input("URL >>> ").strip()
    if not url.startswith("http"):
        log_fail("URL must start with http:// or https://")
        return

    parsed = urlparse(url)
    base_url = url if url.endswith('/') else url + '/'
    host = parsed.netloc.replace(':', '_')
    target = Path(config.OUTPUT_DIR) / host
    index_file = target / 'index_list.txt'

    if index_file.exists():
        index_file.unlink()

    start_time = time.time()
    log_info(f"Starting crawl for: {url}")

    async with aiohttp.ClientSession() as session:
        seen_assets = set()
        await crawl_page_async(url, base_url, target, parsed.netloc, index_file, session, seen_assets)  

    log_info("Rewriting asset paths...")
    rewrite_asset_paths(target, index_file)

    elapsed = time.time() - start_time
    stats = get_file_stats(target)

    print("\n[✔] Dump complete. Saved to:", target.resolve())
    print(f"\n[📊] Dump Stats:")
    print(f"   • Duration        : {elapsed:.2f} seconds")
    print(f"   • Total files     : {stats['total_files']}")
    print(f"   • Total size      : {stats['total_size']:.2f} MB")
    print(f"   • CSS files       : {stats['css']}")
    print(f"   • JS files        : {stats['js']}")
    print(f"   • Image files     : {stats['img']}")
    print(f"   • Other files     : {stats['other']}")


if __name__ == "__main__":
    asyncio.run(run_webdumper())
