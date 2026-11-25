# P1 Item Search and Price Overview

- **Owner**: Kun Yu (suggested, can be changed)
- **Status**: Not started

## 1. Business Question

Buyers want to find available items by category, price, campus, tag, or keyword, and to see whether an asking price is high or low for its category.

## 2. Data Needed

A single query returns one row per **available** item with: item id, title, asking price, top-level category, subcategory, seller campus, the item's tags as one comma-separated text, and three market benchmarks computed over *all* available items (so they stay the same when filters are applied): the number of items in its top-level category, the category's average price, and the item's price rank inside the category. The difference between the asking price and the category average is also returned (`diffFromAvg`).

Optional filters, each given as `NULL` when absent: top-level category (includes subcategories), minimum price, maximum price, seller campus, tag, and a title keyword (matched literally). Rows are sorted by price, then item id. The SQL is written in `src/ie6700/analytics/p1_search_and_price.py`.

## 3. Python Analysis

- Print the result rows as the search table.
- Group the rows by `topCategory`: count, average, lowest, and highest price, sorted by count.
- Split `tags` and count the 5 most common tags; count rows per `campusName`.
- If the minimum price is greater than the maximum, exit with status 2 before querying.

## 4. Expected Results (Seed Data, verified)

- No filters: 13 rows (the available items), cheapest first.
- By top-level category (count / average / range): Electronics 4 / 33.25 / 0.00–95.00; Other 2 / 58.50 / 22.00–95.00; Sports & Outdoors 2 / 112.50 / 65.00–160.00; Furniture 2 / 44.00 / 18.00–70.00; Clothing 1 / 8.00; Kitchen & Dorm 1 / 40.00; Textbooks 1 / 50.00.
- By campus: Main 7, West 2, South 2, East 1, North 1.
- Top tags: Like new 5, Negotiable 4, Free campus pickup 3, Student deal 3, Needs repair 1.
- Item 38 (portable monitor, 95.00) has `priceRank` 4 in Electronics and `diffFromAvg` 61.75.

## 5. Acceptance Criteria

- 13 rows without filters; the category counts and the campus counts each sum to 13.
- With category Electronics, every row has `topCategory = 'Electronics'`.
- A price range with minimum above maximum exits with a non-zero status.
