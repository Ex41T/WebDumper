# config.py

from aiohttp import ClientTimeout

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
    ),
    "Accept": "*/*",
    "Connection": "keep-alive",
    "DNT": "1"
}

RETRY_COUNT = 3

# aiohttp timeout
TIMEOUT = ClientTimeout(total=30)

# attribute req for main.py
OUTPUT_DIR = "output"
