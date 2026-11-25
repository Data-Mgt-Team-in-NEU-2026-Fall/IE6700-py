"""P1 Item search and price overview (owner: Kun Yu). Design brief: docs/problems/P1-search-and-price.md.

Usage::

    python -m ie6700.analytics.p1_search_and_price
    python -m ie6700.analytics.p1_search_and_price --category Electronics --max-price 50
    python -m ie6700.analytics.p1_search_and_price --campus "Main Campus" --tag Vintage --keyword lamp

One SELECT returns the matching AVAILABLE items together with market benchmarks per top-level
category. Python then summarises the returned rows. Every user value is bound as a query parameter.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation
from typing import NamedTuple

from .common import (
    EXIT_OK,
    EXIT_USAGE,
    Connection,
    InvalidInput,
    money,
    print_table,
    run_with_connection,
)

TOP_TAG_LIMIT = 5  # how many tags the tag analysis lists; fixed by the problem brief

# The one query, built from several CTEs, each with a single job:
#   item_base      available items with their top-level category (the parent's name when there is
#                  one, otherwise their own) and the seller's campus
#   item_tags      each item's tags as one comma-separated text
#   category_stats market benchmarks per top-level category: item count and average price
#   available      the above joined together, plus each item's price rank inside its category
# The final SELECT applies the optional filters as "(%s IS NULL OR …)", so an absent filter does
# nothing and the benchmarks never depend on the filters.
SEARCH_SQL = """
WITH item_base AS (
  SELECT i.itemId, i.title, i.askingPrice,
         COALESCE(p.categoryName, c.categoryName) AS topCategory,
         c.categoryName, cp.campusName
  FROM SecondhandItem i
  JOIN ItemCategory c ON c.categoryId = i.categoryId
  LEFT JOIN ItemCategory p ON p.categoryId = c.parentCategoryId
  JOIN `User` u ON u.userId = i.sellerId
  JOIN Campus cp ON cp.campusId = u.campusId
  WHERE i.status = 'AVAILABLE'
),
item_tags AS (
  SELECT it.itemId, GROUP_CONCAT(t.tagName ORDER BY t.tagName) AS tags
  FROM ItemTags it
  JOIN ItemTag t ON t.tagId = it.tagId
  GROUP BY it.itemId
),
category_stats AS (
  SELECT topCategory, COUNT(*) AS categoryCount, AVG(askingPrice) AS categoryAvg
  FROM item_base
  GROUP BY topCategory
),
available AS (
  SELECT b.itemId, b.title, b.askingPrice, b.topCategory, b.categoryName, b.campusName,
         tg.tags, cs.categoryCount, cs.categoryAvg,
         RANK() OVER (PARTITION BY b.topCategory ORDER BY b.askingPrice) AS priceRank
  FROM item_base b
  JOIN category_stats cs ON cs.topCategory = b.topCategory
  LEFT JOIN item_tags tg ON tg.itemId = b.itemId
)
SELECT a.itemId, a.title, a.askingPrice, a.topCategory, a.categoryName, a.campusName,
       a.tags, a.categoryCount, ROUND(a.categoryAvg, 2) AS categoryAvg, a.priceRank,
       ROUND(a.askingPrice - a.categoryAvg, 2) AS diffFromAvg
FROM available a
WHERE (%s IS NULL OR a.topCategory = %s)
  AND (%s IS NULL OR a.askingPrice >= %s)
  AND (%s IS NULL OR a.askingPrice <= %s)
  AND (%s IS NULL OR a.campusName = %s)
  AND (%s IS NULL OR EXISTS (SELECT 1 FROM ItemTags it JOIN ItemTag t ON t.tagId = it.tagId
                              WHERE it.itemId = a.itemId AND t.tagName = %s))
  AND (%s IS NULL OR a.title LIKE %s)
ORDER BY a.askingPrice, a.itemId
"""


class ItemRow(NamedTuple):
    itemId: int
    title: str | None
    askingPrice: Decimal | None
    topCategory: str
    categoryName: str
    campusName: str
    tags: str | None
    categoryCount: int
    categoryAvg: Decimal | None
    priceRank: int
    diffFromAvg: Decimal | None


class CategorySummary(NamedTuple):
    category: str
    count: int
    average: Decimal | None
    lowest: Decimal | None
    highest: Decimal | None


class SearchFilters:
    """The optional search conditions. Absent conditions (None) do not filter."""

    def __init__(
        self,
        category: str | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        campus: str | None = None,
        tag: str | None = None,
        keyword: str | None = None,
    ) -> None:
        if min_price is not None and max_price is not None and min_price > max_price:
            raise InvalidInput(
                f"minimum price {min_price} is greater than maximum price {max_price}"
            )
        self.category = category
        self.min_price = min_price
        self.max_price = max_price
        self.campus = campus
        self.tag = tag
        self.keyword = keyword


def like_pattern(keyword: str) -> str:
    """Turn user text into a LIKE pattern that matches it literally, anywhere in the title."""
    escaped = keyword.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def search_items(conn: Connection, filters: SearchFilters) -> list[ItemRow]:
    """Run the query: the available items that match ``filters``, cheapest first."""
    keyword = None if filters.keyword is None else like_pattern(filters.keyword)
    params = (
        filters.category, filters.category,
        filters.min_price, filters.min_price,
        filters.max_price, filters.max_price,
        filters.campus, filters.campus,
        filters.tag, filters.tag,
        keyword, keyword,
    )  # fmt: skip
    with conn.cursor() as cur:
        cur.execute(SEARCH_SQL, params)
        return [ItemRow(*row) for row in cur.fetchall()]


def summarize_categories(rows: Sequence[tuple[str, Decimal | None]]) -> list[CategorySummary]:
    """Count, average, lowest and highest price per category, most items first.

    ``rows`` are ``(category, asking price)`` pairs. Items without a price count towards
    ``count`` but not towards the price figures.
    """
    grouped: dict[str, list[Decimal | None]] = {}
    for category, price in rows:
        grouped.setdefault(category, []).append(price)

    summaries: list[CategorySummary] = []
    for category, prices in grouped.items():
        known = [price for price in prices if price is not None]
        average = sum(known, Decimal(0)) / len(known) if known else None
        summaries.append(
            CategorySummary(
                category=category,
                count=len(prices),
                average=average,
                lowest=min(known, default=None),
                highest=max(known, default=None),
            )
        )
    summaries.sort(key=lambda summary: (-summary.count, summary.category))
    return summaries


def top_tags(rows: Sequence[ItemRow], limit: int = TOP_TAG_LIMIT) -> list[tuple[str, int]]:
    """The most common tags in ``rows``: most items first, ties by name."""
    counts = Counter(tag for row in rows if row.tags for tag in row.tags.split(","))
    return sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))[:limit]


def campus_counts(rows: Sequence[ItemRow]) -> list[tuple[str, int]]:
    """Items per seller campus: most items first, ties by name."""
    counts = Counter(row.campusName for row in rows)
    return sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))


def report(conn: Connection, filters: SearchFilters) -> int:
    matches = search_items(conn, filters)
    print(f"== Search results: {len(matches)} item(s), cheapest first ==")
    if not matches:
        print("No matching items.\n")
        return EXIT_OK
    print_table(
        ["itemId", "title", "price", "category", "subcategory", "campus", "rank", "vs category avg"],
        [
            (
                r.itemId, r.title, money(r.askingPrice), r.topCategory, r.categoryName,
                r.campusName, f"{r.priceRank}/{r.categoryCount}", money(r.diffFromAvg),
            )
            for r in matches
        ],
    )  # fmt: skip

    print("== Results by top-level category ==")
    print_table(
        ["category", "items", "average", "lowest", "highest"],
        [
            (s.category, s.count, money(s.average), money(s.lowest), money(s.highest))
            for s in summarize_categories([(r.topCategory, r.askingPrice) for r in matches])
        ],
    )

    print(f"== Top {TOP_TAG_LIMIT} tags in the results ==")
    print_table(["tag", "items"], top_tags(matches))

    print("== Results by seller campus ==")
    print_table(["campus", "items"], campus_counts(matches))
    return EXIT_OK


def _price(text: str) -> Decimal:
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise argparse.ArgumentTypeError(f"not a price: {text!r}") from None
    if not value.is_finite() or value < 0:
        raise argparse.ArgumentTypeError(f"a price must be a finite number of 0 or more: {text!r}")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="p1_search_and_price",
        description="Search available marketplace items and summarise prices (P1).",
    )
    parser.add_argument("--category", help="top-level category name; includes its subcategories")
    parser.add_argument("--min-price", type=_price, help="lowest asking price, inclusive")
    parser.add_argument("--max-price", type=_price, help="highest asking price, inclusive")
    parser.add_argument("--campus", help="campus of the seller, e.g. 'Main Campus'")
    parser.add_argument("--tag", help="tag name")
    parser.add_argument("--keyword", help="text that must appear in the title (literal match)")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        filters = SearchFilters(
            category=args.category,
            min_price=args.min_price,
            max_price=args.max_price,
            campus=args.campus,
            tag=args.tag,
            keyword=args.keyword,
        )
    except InvalidInput as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    return run_with_connection(lambda conn: report(conn, filters))


if __name__ == "__main__":
    raise SystemExit(main())
