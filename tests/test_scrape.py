"""Tests for scrape.py against saved HTML in tests/fixtures/ — no network."""
import shutil

import pandas as pd
import pytest
import requests

import scrape
from conftest import FIXTURES

PAGE1 = scrape.BASE + "page-1.html"


# --- parse_page: the saved page-1 HTML ---------------------------------------------------

def test_page1_has_20_books(page1_html):
    assert len(scrape.parse_page(page1_html)) == 20


def test_page1_first_book(page1_html):
    assert scrape.parse_page(page1_html)[0] == {
        "title": "A Light in the Attic",
        "price": "£51.77",
        "rating": "Three",
        "availability": "In stock",
        "url": scrape.BASE + "a-light-in-the-attic_1000/index.html",
    }


def test_page1_full_title_not_truncated(page1_html):
    # the link text is cut to "A Light in the ..."; the title attribute has the full title
    titles = [b["title"] for b in scrape.parse_page(page1_html)]
    assert "Sapiens: A Brief History of Humankind" in titles
    assert not any(t.endswith("...") for t in titles)


def test_page1_fields_look_right(page1_html):
    books = scrape.parse_page(page1_html)
    assert all(b["price"].startswith("£") and "Â" not in b["price"] for b in books)
    assert all(b["rating"] in scrape.RATING for b in books)
    assert all(b["url"].startswith(scrape.BASE) for b in books)
    assert len({b["url"] for b in books}) == 20


# --- next_url ----------------------------------------------------------------------------

def test_next_url_from_page1(page1_html):
    assert scrape.next_url(page1_html, PAGE1) == scrape.BASE + "page-2.html"


def test_next_url_none_on_last_page(page1_html):
    last_page = page1_html.replace('<li class="next"><a href="page-2.html">next</a></li>', "")
    assert scrape.next_url(last_page, PAGE1) is None


# --- cache, scrape_pages and errors ------------------------------------------------------

def test_cached_page_makes_no_request(tmp_data, monkeypatch):
    (tmp_data / "raw").mkdir()
    shutil.copy(FIXTURES / "page-1.html", tmp_data / "raw")
    monkeypatch.setattr(scrape, "get", lambda *a, **k: pytest.fail("cache was not used"))
    df = scrape.scrape_pages(PAGE1, max_pages=1)
    assert len(df) == 20
    assert (df.dtypes == object).all()          # still all strings before cleaning


def test_failed_download_is_logged_not_fatal(tmp_data, monkeypatch):
    def fail(*a, **k):
        raise requests.ConnectionError("no connection")
    monkeypatch.setattr(scrape, "get", fail)
    df = scrape.scrape_pages(PAGE1, max_pages=1)
    assert df.empty
    assert "page-1.html" in (tmp_data / "errors.log").read_text()


def test_broken_html_is_logged_not_fatal(tmp_data, page1_html):
    (tmp_data / "raw").mkdir()
    broken = page1_html.replace('class="price_color"', 'class="x"', 1)
    (tmp_data / "raw" / "page-1.html").write_text(broken, encoding="utf-8")
    df = scrape.scrape_pages(PAGE1, max_pages=1)
    assert df.empty
    assert "parse error" in (tmp_data / "errors.log").read_text()


# --- clean -------------------------------------------------------------------------------

def test_clean_types(page1_html):
    raw = pd.DataFrame(scrape.parse_page(page1_html)).assign(page="1")
    books = scrape.clean(raw)
    assert books["price"].dtype == "float64" and books.loc[0, "price"] == 51.77
    assert str(books["rating"].dtype) == "Int64" and books.loc[0, "rating"] == 3
    assert books["in_stock"].dtype == bool
    assert str(books["scraped_at"].dt.tz) == "UTC"


# --- parse_book: one saved detail page ---------------------------------------------------

def test_parse_book(book_html):
    assert scrape.parse_book(book_html) == {"category": "Poetry", "upc": "a897fe39b1053632"}


def test_book_cache_path():
    url = scrape.BASE + "a-light-in-the-attic_1000/index.html"
    assert scrape.book_cache_path(url).name == "a-light-in-the-attic_1000.html"
