# CLAUDE.md — Assignment 1 (ADSP 31011, Session 1)

## Project
Scrape books.toscrape.com, enrich with the Open Library Search API, clean with pandas.
Parts 1–3 are done by hand in `assignment_1.ipynb`. Part 4 extends that work in a standalone `scrape.py`.

## Files
- `assignment_1.ipynb` — Parts 1–3 (5 pages, 100 books). Do not edit unless asked.
- `Data_Dictionary.md` — one row per column of `books_silver.csv`: dtype, meaning, source.
- `data/raw/` — saved catalogue HTML (`page-1.html` …). Cache, not submitted.
- `data/api/` — saved Open Library JSON responses. Not submitted.
- `data/books_silver.csv`, `data/books_silver.parquet` — cleaned output.
- `data/errors.log` — one line per failed page or lookup.
- `prompts.md` — my prompt log (I write this; do not edit it).

## Environment
- Python: `/opt/miniconda3/bin/python` (3.13, has pandas, pyarrow, bs4, requests).
  Do not use the system Python 3.10 (no pyarrow).
- Use `requests` + `BeautifulSoup` (`html.parser`) + `pandas`. No new libraries without asking.

## Rules
- Be polite: one request per second (`time.sleep(1)`), a User-Agent header, `timeout=20`.
- Set `r.encoding = "utf-8"` on books.toscrape.com responses (otherwise £ becomes Â£).
- Follow the site's own "next" link (`li.next > a`) with `urljoin`; never hard-code page URLs.
- A failed request is logged to `data/errors.log` and skipped — it must never crash the run.
- Cache: if a page's HTML already exists in `data/raw/`, read it from disk instead of downloading.
- `url` is the unique key for a book (titles can repeat).
- Keep the cleaning rules from the notebook: `price` float (no £), `rating` Int64 1–5,
  `in_stock` bool, `scraped_at` UTC timestamp.
- Tests must run offline: read only saved HTML files, no network calls.
- **No keys, passwords or tokens anywhere in code, prompts or files.**
- Keep changes small and explain what you changed; do not rewrite files you were not asked to touch.
