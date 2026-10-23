"""Part 4 — scrape all 50 catalogue pages of books.toscrape.com, with a re-run cache.

Run:  /opt/miniconda3/bin/python scrape.py
Pages already saved in data/raw/ are read from disk, so a second run makes no requests.
"""
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE = "http://books.toscrape.com/catalogue/"
HEADERS = {"User-Agent": "ADSP31011-assignment1 (student exercise)"}
DATA = Path("data")
RAW = DATA / "raw"
RATING = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def get(url: str, pause: float = 1.0) -> requests.Response:
    """One polite GET: wait a second, identify yourself, raise on HTTP errors."""
    time.sleep(pause)
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    r.encoding = "utf-8"            # the site sends no charset; without this £ becomes Â£
    return r


def log_error(msg: str) -> None:
    """Append one line to data/errors.log (and print it)."""
    line = f"{datetime.now().isoformat(timespec='seconds')}  {msg}"
    print("LOGGED:", line)
    DATA.mkdir(exist_ok=True)
    with open(DATA / "errors.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def fetch_page(url: str, path: Path | None = None) -> str:
    """HTML of one page: from the cache file if it exists, else download and save it.

    By default the cache file is named after the URL (…/page-7.html -> data/raw/page-7.html),
    so the cache can only ever return the page that was actually asked for.
    """
    path = path or RAW / url.rsplit("/", 1)[-1]
    if path.exists():
        return path.read_text(encoding="utf-8")
    html = get(url).text
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return html


def book_cache_path(url: str) -> Path:
    """…/catalogue/a-light-in-the-attic_1000/index.html -> data/raw/books/a-light-in-the-attic_1000.html"""
    return RAW / "books" / (url.rstrip("/").split("/")[-2] + ".html")


def parse_page(html: str) -> list[dict]:
    """All books on one catalogue page as a list of dicts (all values are strings)."""
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for pod in soup.select("article.product_pod"):
        rows.append({
            "title":        pod.h3.a["title"],
            "price":        pod.select_one("p.price_color").get_text(strip=True),
            "rating":       pod.select_one("p.star-rating")["class"][1],
            "availability": pod.select_one("p.instock.availability").get_text(strip=True),
            "url":          urljoin(BASE, pod.h3.a["href"]),
        })
    return rows


def parse_book(html: str) -> dict:
    """Category and UPC from one book's own page.

    Breadcrumb is Home > Books > <category> > <title>, so the category is the 3rd item
    (the 2nd is always "Books"). UPC is the product-table row whose header is "UPC".
    """
    soup = BeautifulSoup(html, "html.parser")
    category = soup.select("ul.breadcrumb li")[2].get_text(strip=True)
    upc = next(tr.td.get_text(strip=True) for tr in soup.select("table.table-striped tr")
               if tr.th.get_text(strip=True) == "UPC")
    return {"category": category, "upc": upc}


def next_url(html: str, current_url: str) -> str | None:
    """Full URL of the site's own "next" link, or None on the last page."""
    nxt = BeautifulSoup(html, "html.parser").select_one("li.next > a")
    return urljoin(current_url, nxt["href"]) if nxt else None


def scrape_pages(start_url: str = BASE + "page-1.html", max_pages: int = 50) -> pd.DataFrame:
    """Follow "next" from start_url for up to max_pages pages. A failed page is logged, not fatal.

    On failure we stop: the next page's URL lives inside the page that failed, so we cannot
    continue past it. Pages fetched so far are cached, so a re-run resumes where it stopped.
    """
    all_rows = []
    url, n = start_url, 1
    while url and n <= max_pages:
        try:
            html = fetch_page(url)
        except requests.RequestException as e:
            log_error(f"page {n}  {url}  {e}")
            break
        try:                                    # broken HTML is handled like a failed download
            rows = parse_page(html)
            nxt = next_url(html, url)
        except (AttributeError, KeyError, IndexError, TypeError) as e:
            log_error(f"page {n}  {url}  parse error: {type(e).__name__}: {e}")
            break
        for row in rows:
            row["page"] = str(n)
        all_rows.extend(rows)
        print(f"page {n}: {len(rows)} books")
        url, n = nxt, n + 1
    return pd.DataFrame(all_rows, columns=["page", "title", "price", "rating", "availability", "url"])


def add_details(books: pd.DataFrame) -> pd.DataFrame:
    """Add category and upc from each book's own page (cached in data/raw/books/).

    Books are independent, so a failed page is logged and skipped (its two columns stay NaN).
    """
    details = []
    for i, url in enumerate(books["url"], start=1):
        try:
            details.append(parse_book(fetch_page(url, book_cache_path(url))))
        except (requests.RequestException, AttributeError, KeyError, IndexError,
                TypeError, StopIteration) as e:
            log_error(f"book {i}  {url}  {type(e).__name__}: {e}")
            details.append({"category": None, "upc": None})
        if i % 100 == 0:
            print(f"details: {i}/{len(books)}")
    return pd.concat([books, pd.DataFrame(details, index=books.index)], axis=1)


def clean(raw: pd.DataFrame) -> pd.DataFrame:
    """Same cleaning rules as the notebook: typed columns, one row per url."""
    books = raw.copy()
    books["page"]       = books["page"].astype(int)
    books["price"]      = books["price"].str.replace("£", "", regex=False).astype(float)
    books["rating"]     = books["rating"].map(RATING).astype("Int64")
    books["in_stock"]   = books["availability"].str.contains("In stock", case=False)
    books["scraped_at"] = pd.Timestamp.now(tz="UTC")
    return books.drop_duplicates(subset="url").reset_index(drop=True)


if __name__ == "__main__":
    books = clean(scrape_pages())
    print(f"{len(books)} books from {books['page'].nunique()} pages")
    assert len(books) == 1000, f"expected 1000 books, got {len(books)}"   # Checkpoint 4a
    books = add_details(books)
    missing = books[["category", "upc"]].isna().any(axis=1).sum()
    print(f"{books['category'].nunique()} categories, {missing} books missing category/UPC")
    assert missing == 0, f"{missing} books have no category or UPC (see data/errors.log)"  # 4b
    assert books["upc"].is_unique, "UPC should be unique per book"
    books.to_csv(DATA / "books_silver.csv", index=False)
    books.to_parquet(DATA / "books_silver.parquet", index=False)
