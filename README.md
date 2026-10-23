# Books Scraper Pipeline

**Scrape → enrich → clean: 1,000 books from a real paginated catalogue into a typed "silver" table, with a cache that turns a 20-minute crawl into a few seconds, and tests that never touch the network.**

[books.toscrape.com](http://books.toscrape.com) is a public practice site for scraping. This project crawls all 50 catalogue pages and every book's own page, enriches titles with the [Open Library Search API](https://openlibrary.org/dev/docs/api/search), and cleans the result with pandas into CSV + Parquet with a data dictionary.

## The idea in one picture

```
page-1 ──next──▶ page-2 ──next──▶ … ──▶ page-50 (no "next" → stop)
   │ 20 books each                          │
   ▼                                        ▼
 data/raw/page-N.html  (cache: read from disk if it exists)
   │
   ├─ each book's page ──▶ data/raw/books/<slug>.html ──▶ category + UPC
   ▼
 parse (strings) ──▶ clean (types) ──▶ data/books_silver.csv / .parquet   (1,000 rows, url = key)
                        failures ──▶ data/errors.log  (logged, never a crash)
```

Three rules make the crawler both polite and restartable:
1. **Follow the site's own "next" link** (`li.next > a` + `urljoin`). No page URL is hard-coded, so the crawl stops exactly where the site ends.
2. **Cache every page you download.** A saved page is read from disk, never fetched again. A crashed or interrupted run restarts where it stopped.
3. **One request per second, a User-Agent, `timeout=20`.** Failures are written to `data/errors.log` and skipped; they never crash the run.

## What's in here

| Part | File | What it does |
|---|---|---|
| Explore (5 pages, 100 books) | `assignment_1.ipynb` | Scrape by hand, call Open Library for the first 20 titles, clean, and aggregate: books and average price per rating, average price per first-publish decade |
| Production scraper (50 pages, 1,000 books) | `scrape.py` | Follows "next" links, caches pages, adds **category** and **UPC** from each book page, cleans, and asserts the result (1,000 books, all with a category and a unique UPC) |
| Tests | `tests/` | 12 pytest tests on saved HTML; `conftest.py` blocks every socket, so a test that tries to go online fails |
| Output | `data/books_silver.csv`, `.parquet` | The cleaned 1,000-row table |
| Documentation | `Data_Dictionary.md` | Every column: dtype, meaning, source selector |
| AI disclosure | `prompts.md`, `CLAUDE.md` | Every prompt I gave Claude Code, what came back, what was wrong, and the project rules I gave it |

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python scrape.py               # first run ≈ 20 min (50 catalogue + 1,000 book pages at 1 req/s); reruns: seconds, from cache
python -m pytest -v tests/     # offline: 12 passed
```

Run order matters if you also run the notebook: the notebook writes a 100-row `books_silver.csv`, so run `scrape.py` last to end with the 1,000-row version.

## Cleaning rules

| Column | Raw | Clean |
|---|---|---|
| `price` | `"£51.77"` | `51.77` (float) |
| `rating` | `class="star-rating Three"` | `3` (Int64, 1–5) |
| `in_stock` | `"In stock"` | `True` (bool) |
| `scraped_at` | — | UTC timestamp |
| `url` | relative `href` | absolute URL, the **unique key** (titles repeat: *The Star-Touched Queen* is two different books) |

## Things I hit that tutorials don't mention

- **£ turns into `Â£`.** The site sends no charset, so `requests` guesses Latin-1. Fix: `r.encoding = "utf-8"` before reading `.text`.
- **Catalogue titles are truncated** ("A Light in the …"). The full title lives in the link's `title` attribute, not its text.
- **The rating is a CSS class**, not text: `p.star-rating` → second class (`One`…`Five`).
- **Network errors were caught, broken HTML wasn't.** A page that downloads fine but has no price crashed `parse_page()` with `AttributeError`. Parsing now runs inside the same log-and-stop guard as downloading.
- **22% of categories are placeholders**: 152 books are "Default" and 67 are "Add a comment". These are real categories on the site, so they are documented, not "fixed".
- **CSV forgets types.** Read back with plain `pd.read_csv`, `scraped_at` is a string and `rating` is int64. Use the Parquet file, or `parse_dates=["scraped_at"]`.
- **pandas 3 changed the default string dtype** to `str`, which breaks one test's `object` check. `requirements.txt` pins `pandas<3` (all 12 tests pass on 2.x).

## Verified, not assumed

- 1,000 rows, 1,000 unique URLs, 50 pages, 50 categories (exactly the site's sidebar), 0 missing values; UPCs are 16-character hex text.
- A cached rerun makes **0** requests (`requests.get` replaced with a function that fails the test if called).
- A 404 on page 7 and a timeout on page 3 were logged; the run returned the earlier pages and did not crash; a rerun downloaded only the missing pages.
- Four planted bugs (wrong breadcrumb item, wrong rating class, cache off, parse errors not caught) each made at least one test fail.

## Known limitations

- Open Library matching is by title only, for the first 20 books, so some matches are the wrong book (checked by hand in the notebook). The 1,000-row file has no Open Library columns.
- `in_stock` is True for every book; the stock count on each book page is not scraped.
- The cache never expires: delete a file in `data/raw/` to re-download it.

## Repo layout

```
books-scraper-pipeline/
├── scrape.py               production scraper (Part 4)
├── assignment_1.ipynb      exploration, Open Library enrichment, aggregates (Parts 1–3)
├── tests/
│   ├── conftest.py         blocks all network access
│   ├── test_scrape.py      12 tests
│   └── fixtures/           saved page-1 + one book page
├── data/books_silver.csv / .parquet
├── Data_Dictionary.md
├── prompts.md              AI prompt log
├── CLAUDE.md               rules given to Claude Code
└── requirements.txt
```

## Context

Built for **ADSP 31011 Cloud-Native Data Engineering** (UChicago MS in Applied Data Science, Autumn 2026). Claude Code was used as a pair programmer under the rules in `CLAUDE.md`; every prompt, mistake and fix is in `prompts.md`. The repository is private under the course's academic-integrity policy and shared on request.

**Hao Kang** · [LinkedIn](https://www.linkedin.com/in/hao-kang-6654b5331/) · [GitHub](https://github.com/haokang-uchicago)
