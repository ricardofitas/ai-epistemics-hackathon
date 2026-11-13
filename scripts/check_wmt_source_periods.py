#!/usr/bin/env python3
"""Extract source-news periods from official WMT task descriptions."""
import argparse
import datetime as dt
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import urllib.request


class PageText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.pieces = []

    def handle_data(self, data):
        self.pieces.append(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rows = []
    for campaign in [2019, 2020]:
        url = f"https://www.statmt.org/wmt{campaign % 100}/translation-task.html"
        with urllib.request.urlopen(url, timeout=30) as response:
            data = response.read()
        page = PageText()
        page.feed(data.decode("utf-8"))
        text = " ".join(" ".join(page.pieces).split())
        matches = list(re.finditer(r"\bSeptember-November\s+(\d{4})\b", text))
        if len(matches) != 1:
            raise ValueError(f"Official source wording changed; manually inspect {url}")
        match = matches[0]
        rows.append({
            "benchmark": f"newstest{campaign}", "campaign_year": campaign,
            "source_news_start_month": 9, "source_news_end_month": 11,
            "source_news_year": int(match.group(1)), "source_url": url,
            "source_period_text": match.group(0),
            "html_sha256": hashlib.sha256(data).hexdigest(),
        })
    result = {
        "checked_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "sources": rows,
        "target": "English-to-German held-out online news from late 2019",
        "matching_source_period_benchmark": [r["benchmark"] for r in rows if r["source_news_year"] == 2019],
        "nonmatching_recommendation": "newstest2019",
        "scope": "Official documented source-news period only; no translation inference, score or model ranking change is measured.",
    }
    encoded = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded)
    print(encoded, end="")


if __name__ == "__main__":
    main()
