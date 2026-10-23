# Prompt log — Assignment 1, Part 4

Tool: Claude Code in VS Code, with `CLAUDE.md` in the folder. Prompts I typed in Chinese are translated into English. Claude helped me write this log, and I checked it.

---

## 1. (a) All 50 pages with a cache

**Prompt:** "extend the scraper to all 50 pages with a re-run cache — checkpoint 1,000 books"

**Produced:**
- `scrape.py`:
  - It follows the site's "next" link.
  - It caches each page in `data/raw/`, using the URL as the file name.
  - It logs failed pages to `errors.log`, waits 1 s per request, and checks for 1,000 books at the end.
- First run took 54 s. A cached rerun took 1.8 s.

**Wrong:** Nothing broke. I still had to decide two things: what to do on a failed page (stop the loop, or skip and continue), and the output file name (`books_all.csv`, not `books_silver.csv`).

**Changed:** Nothing yet. I asked for a proper check first (prompt 2).

---

## 2. Verify (a)

**Prompt:** "confirm 1,000 unique books across 50 pages, pagination follows next links, and a cached rerun makes zero network requests. Check error handling and request delays too."

**Produced:** An offline test script. It swaps out `requests.get` so it can count requests and fake failures. Results:
- 1,000 unique URLs, 20 books on each of 50 pages.
- Pagination: requests went to page-1 … page-50 in order, and stopped because page 50 has no "next" link. No page URLs are hard-coded.
- Cached rerun: 0 requests. `requests.get` was set to raise an error if called, and it was never called.
- Delay: 1.02–1.11 s between requests. The User-Agent was sent and `timeout=20` was used.
- Errors:
  - A 404 on page 7 and a timeout on page 3 were both logged. The run returned the pages before the failure and did not crash.
  - A rerun downloaded only the missing pages.

**Wrong:** Only network errors are caught. A page that downloads fine but has broken HTML (for example, a book with no price) crashes `parse_page()` with an `AttributeError`.

**Changed:** I asked Claude to fix it (prompt 3).

---

## 3. Fix the parse crash

**Prompt:** "Fix it: when parsing a page fails, write the error to the log and stop, the same way as a network error."

**Produced:**
- In `scrape_pages()`, `parse_page()` and `next_url()` now run inside a `try`.
- If parsing fails (`AttributeError`, `KeyError`, `IndexError` or `TypeError`), the error is logged and the loop stops.

**Wrong:** Nothing. Here is how it was checked, offline:
- A cached page 3 with no price was logged and the run stopped. It returned pages 1–2 (40 rows) and did not crash.
- A page 3 whose "next" link had no `href` was handled the same way.
- All the checks from prompt 2 still pass.

One limit is left: a broken page stays in the cache, so a rerun hits the same error until I delete that file.

**Changed:** —

---

## 4. (b) Category and UPC

**Prompt:** "add category and UPC from each book's own page"

**Produced:**
- `parse_book()`:
  - category = the 3rd breadcrumb item. The 2nd one is always "Books".
  - UPC = the table row whose header is "UPC".
- Each book's page is cached in `data/raw/books/`, 1 request per second.
- `add_details()`: a failed book is logged and skipped (its category/UPC are NaN). It does not stop the run.
- New checkpoint: no missing category or UPC, and every UPC is unique.
- Tested on 3 books first: Poetry / Historical Fiction / Fiction. These match the website.
- Full run: 18 min, 1,000 detail pages, 50 categories, 0 books missing category or UPC. A cached rerun took 6 s.

**Wrong:** Nothing broke. I checked the result properly in prompt 5.

**Changed:** —

---

## 5. Verify (b)

**Prompt:** "confirm there are still 1,000 unique books, with category and UPC extracted from each book's detail page. Report missing values, verify UPC is stored as text, and compare five sample records against their saved detail-page HTML."

**Produced:** A check script. It reads the saved HTML in a different way from `parse_book()`: the last breadcrumb link for category, and a regex for UPC.
- 1,000 rows, 1,000 unique URLs, 50 pages. 0 missing values in any column. 1,000 cached detail pages.
- UPC is text: dtype `object`, all 16-character hex strings. It is still text when the CSV is read back with default settings.
- 5 random books: category, UPC, title and price all match the saved HTML (5/5).
- No book got "Books" as its category. Our 50 categories are exactly the 50 in the site's sidebar.

**Wrong:** Not a code bug, but a data issue. 152 books are in the category "Default" and 67 in "Add a comment". These are real categories on the site (placeholder data), so 22% of books have no meaningful category. I need to say this in the README and data dictionary.

**Changed:** —

---

## 6. (c) pytest tests, no network

**Prompt:** "write pytest tests against the saved page-1 HTML, no network"

**Produced:**
- `tests/test_scrape.py`: 12 tests.
  - `parse_page`: 20 books; the exact first book; full titles that are not cut off; £ prices; ratings; unique URLs.
  - `next_url`: page 1 points to page 2, and there is no next link on the last page.
  - Cache: no request is made when the page is already saved.
  - Errors: a failed download and broken HTML are both logged, and the run does not crash.
  - `clean()`: the dtypes are right.
  - `parse_book`: Poetry and the right UPC.
- `tests/conftest.py`: blocks every socket connection, so any test that tries to use the network fails.
- Claude asked before installing pytest, and I said yes. 12 passed in 0.7 s.

**Wrong:**
- No failures, but Claude found a problem in my prompt: `data/raw/` is not submitted, so tests that read `data/raw/page-1.html` would fail on the grader's machine. It copied page-1 into `tests/fixtures/` instead.
- It also added one saved book page that I did not ask for, so `parse_book` from (b) is tested too.
- How Claude checked the tests are real:
  - They pass in a copy of the project that has no `data/` folder.
  - Four planted bugs each made at least one test fail: the wrong breadcrumb item, the wrong rating class, the cache turned off, and parse errors no longer caught.
  - A live `requests.get` inside a test is blocked.
- One limit: the `utf-8` fix in `get()` is not tested, because that needs a real response.

**Changed:** Nothing in the code. I ran the tests myself in my own terminal: 12 passed in 0.64 s (screenshot for Part 5).

---

## 7. (d) README and data dictionary

**Prompt:** "write the README and update the data dictionary — then correct what it got wrong."

**Produced:**
- `README.md`:
  - what the project does, setup and run order;
  - what `scrape.py` does: next links, cache, delays, error handling, cleaning;
  - the tests, a file table and known limitations.
- `Data_Dictionary.md`: rewritten for the 1,000-row `books_silver` file (10 columns, now including `category` and `upc`), with notes. The Open Library columns from my notebook are in a separate section.
- Claude found three things while it collected the facts:
  - All 1,000 books are "In stock", so `in_stock` is always True.
  - *The Star-Touched Queen* appears twice as two different books (different URL and UPC). This is why `url` is the key, not `title`.
  - Read back from the CSV, `scraped_at` becomes a string. Only Parquet keeps the dtypes.

**Wrong:** Claude checked every claim against the data and ran the README commands (`scrape.py` 5 s from cache, pytest 12 passed). Two things in its own README were wrong or vague:
- It said a failed book page makes the final check fail, but not that **no output file is written** in that case, or that a rerun downloads only the missing pages.
- It said the notebook takes "about 1 minute", but that was never measured.

**Changed:** Claude fixed both. The README now explains what happens when a book page fails, and the timing line now says "about 30 requests, one per second" instead of a guessed time.

---

## 8. Checking the 1,000 rows in my notebook

**Prompt:** "This failed. Is it because I didn't run scrape.py?" (I sent a screenshot of a notebook cell. It ran `pd.read_csv("data/books_all.csv")` and got `FileNotFoundError`.)

**Produced:** Claude explained the cause. When I chose the 1,000-row version as the final file, `scrape.py`'s output was renamed from `books_all.csv` to `books_silver.csv`, and the old file was deleted. So my cell pointed to a file that no longer exists. Not running `scrape.py` was not the problem.

**Wrong:** Changing only the file name is not enough. My check cell comes after Part 3 in the notebook, and Part 3 writes a 100-row `books_silver.csv`. With Restart & Run All, the cell would read 100 rows, not 1,000.

**Changed:** I deleted that check cell from my notebook. Instead, I run the notebook first (Restart & Run All) and then `scrape.py` last in the terminal, so the final `books_silver.csv` has 1,000 rows. Then I check the row count with `pd.read_csv("data/books_silver.csv").shape`, which shows `(1000, 10)`.
