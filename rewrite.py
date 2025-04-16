from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urlparse
from logger import log_info

def rewrite_asset_paths(base_dir, index_list_file):
    """
    Rewrites HTML asset paths (CSS/JS/IMG) to local filesystem structure.
    """

    asset_paths = {
        'link': 'assets/css',
        'script': 'assets/js',
        'img': 'assets/img',
    }
    
    # Load all dumped HTML filenames
    with open(index_list_file, 'r', encoding='utf-8') as f:
        html_files = [line.strip() for line in f.readlines()]

    for file in html_files:
        file_path = base_dir / file
        if not file_path.exists():
            continue
        
        # Calculate relative path depth to use correct "../" prefix
        depth = len(file_path.relative_to(base_dir).parents) - 1
        prefix = '../' * depth if depth > 0 else ''

        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        for tag, subdir in asset_paths.items():
            attr = 'href' if tag == 'link' else 'src'
            for el in soup.find_all(tag):
                val = el.get(attr)
                if val and not val.startswith(('http', '//', 'data:')):
                    filename = Path(urlparse(val).path).name
                    local_path = Path(prefix) / subdir / filename
                    if (base_dir / local_path).exists():
                        el[attr] = str(local_path)
                    else:
                        log_info(f"[SKIP] Not found locally: {filename}")

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))

        log_info(f"[✔] Rewrote asset paths in: {file}")
