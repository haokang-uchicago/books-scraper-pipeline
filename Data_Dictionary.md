# Data dictionary — books_silver.csv / .parquet

1,000 rows, one per book (`url` is unique). Built by `scrape.py` from all 50 catalogue pages
of books.toscrape.com plus each book's own page. The dtypes below are the Parquet dtypes.

| column | dtype | meaning | source |
|---|---|---|---|
| `page` | int64 | Catalogue page (1–50) the book was listed on | counted by `scrape_pages()` while following "next" links |
| `title` | object | Full book title (not unique: *The Star-Touched Queen* appears twice as two different books) | catalogue page: `h3 > a`, `title` attribute |
| `price` | float64 | Price in GBP, £ removed (10.00–59.99) | catalogue page: `p.price_color`, cast to float |
| `rating` | Int64 | Star rating, 1–5 | catalogue page: second class of `p.star-rating`, mapped One→1 … Five→5 |
| `availability` | object | Availability text as shown on the catalogue page | catalogue page: `p.instock.availability` |
| `url` | object | Full URL of the book's own page; the unique key | catalogue page: `h3 > a`, `href`, joined to `BASE` |
| `in_stock` | bool | True if `availability` contains "In stock" | derived from `availability` |
| `scraped_at` | datetime64[us, UTC] | Time the data was cleaned (UTC); one value for the whole run | set in `clean()` with `pd.Timestamp.now(tz="UTC")` |
| `category` | object | Book category, e.g. "Poetry" (50 values) | book page: 3rd item of `ul.breadcrumb` (Home › Books › *category*) |
| `upc` | object | Universal Product Code, 16-character hex string; unique per book | book page: product table row whose `th` is "UPC" |

## Notes

- **Missing values:** none. Every column is filled for all 1,000 books.
- **`category` has placeholder values:** 152 books are "Default" and 67 are "Add a comment". These are real categories on the site, but they say nothing about the book. So 22% of books have no meaningful category.
- **`in_stock` is always True:** all 1,000 books say "In stock" on the catalogue page, so this column does not separate books. The book page shows a stock count, e.g. "In stock (22 available)", but we do not scrape it.
- **`upc` is text, not a number:** keep it as a string. All UPCs are hex (they contain letters), so they read back as text from the CSV too.
- **CSV vs Parquet:** the CSV does not store dtypes. Read back with plain `pd.read_csv`, `scraped_at` becomes a string and `rating` becomes int64. Use the Parquet file, or `pd.read_csv(..., parse_dates=["scraped_at"])`.

## Notebook version (Parts 1–3)

`assignment_1.ipynb` writes a 100-row `books_silver.csv` to the same path: pages 1–5 only, without `category` and `upc`. It adds these Open Library columns for the first 20 books (LEFT join on `title`):

| column | dtype | meaning | source |
|---|---|---|---|
| `ol_title` | object | Title of the best Open Library match; compare with `title` | Open Library search: `docs[0].title` |
| `author` | object | First listed author of the match | `docs[0].author_name[0]` |
| `first_publish_year` | float64 | Year the work was first published | `docs[0].first_publish_year` |
| `edition_count` | float64 | Number of editions Open Library knows | `docs[0].edition_count` |
| `n_subjects` | float64 | Number of subject tags on the match | `len(docs[0].subject)` |
| `first_publish_decade` | Int64 | Decade of first publication, e.g. 1980 | `first_publish_year // 10 * 10` |

- **Why 85 of 100 rows are empty:** only 20 books were looked up, and 5 of those had no match.
- **Why these whole numbers are float64:** `first_publish_year`, `edition_count` and `n_subjects` are whole numbers, but they are NaN for 85 books. A normal int64 column cannot hold NaN, so pandas stores them as float64 (e.g. 1981.0). `first_publish_decade` was cast to the nullable `Int64` on purpose, so it stays an integer and shows missing values as `<NA>`.
- **Match quality:** matches are by title only. The hand-check in Part 2 found wrong matches (summary books, a book of critical essays), so the author and year can be wrong even when a match exists.
- **Run order:** both the notebook and `scrape.py` write `data/books_silver.*`. The file you keep is from whichever ran last. The submitted file is the 1,000-row version, so run the notebook first and `scrape.py` second.
