"""P2 Seller performance report (owner: Eduardo Gonzalez). Design brief: docs/problems/P2-seller-report.md.

Usage::

    python -m ie6700.analytics.p2_seller_report
    python -m ie6700.analytics.p2_seller_report --seller 27

Read-only. One query returns one row per seller (a user with at least one item); Python computes
sell-through, revenue per order and average rating from those counts.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from decimal import Decimal
from typing import NamedTuple

from .common import EXIT_FAILURE, EXIT_OK, Connection, average, money, percent, print_table, run_with_connection

# The one query, built from CTEs that each aggregate one subject per seller, so the joins never multiply rows:
#   item_stats     item count and the SOLD / REMOVED counts
#   order_stats    COMPLETED orders and their revenue (sum of agreedPrice)
#   review_stats   PUBLISHED seller reviews: count, rating total and the count of each star rating
#   pending_stats  PENDING purchase requests on the seller's items
# Each output row is one seller (a user with at least one item); missing orders, reviews or requests show 0.
# Parameter: seller id (NULL = all sellers), given twice.
SELLER_SQL = """
WITH item_stats AS (
  SELECT sellerId, COUNT(*) AS items,
         SUM(status = 'SOLD') AS soldItems,
         SUM(status = 'REMOVED') AS removedItems
  FROM SecondhandItem
  GROUP BY sellerId
),
order_stats AS (
  SELECT s.sellerId, COUNT(*) AS completedOrders, SUM(tro.agreedPrice) AS revenue
  FROM SecondhandItem AS s, TransactionOrder AS tro, PurchaseRequest AS pr
  WHERE s.itemId = pr.itemId
    AND pr.purchaseRequestId = tro.purchaseRequestId
    AND tro.status = 'COMPLETED'
  GROUP BY s.sellerId
),
review_stats AS (
  SELECT s.sellerId, COUNT(*) AS reviews, SUM(tr.rating) AS ratingSum,
         SUM(tr.rating = 1) AS star1, SUM(tr.rating = 2) AS star2, SUM(tr.rating = 3) AS star3,
         SUM(tr.rating = 4) AS star4, SUM(tr.rating = 5) AS star5
  FROM SecondhandItem AS s, TransactionOrder AS tro, PurchaseRequest AS pr,
       TransactionReview AS tr, SellerReview AS sr
  WHERE s.itemId = pr.itemId
    AND pr.purchaseRequestId = tro.purchaseRequestId
    AND tro.transactionId = sr.transactionId
    AND sr.reviewId = tr.reviewId
    AND tr.reviewStatus = 'PUBLISHED'
  GROUP BY s.sellerId
),
pending_stats AS (
  SELECT s.sellerId, COUNT(*) AS pendingRequests
  FROM SecondhandItem AS s, PurchaseRequest AS pr
  WHERE s.itemId = pr.itemId AND pr.status = 'PENDING'
  GROUP BY s.sellerId
)
SELECT u.userId AS sellerId, u.firstName,
       it.items, it.soldItems, it.removedItems,
       COALESCE(o.completedOrders, 0) AS completedOrders,
       COALESCE(o.revenue, 0) AS revenue,
       COALESCE(rv.reviews, 0) AS reviews,
       COALESCE(rv.ratingSum, 0) AS ratingSum,
       COALESCE(rv.star1, 0) AS star1, COALESCE(rv.star2, 0) AS star2, COALESCE(rv.star3, 0) AS star3,
       COALESCE(rv.star4, 0) AS star4, COALESCE(rv.star5, 0) AS star5,
       COALESCE(p.pendingRequests, 0) AS pendingRequests
FROM `User` u
JOIN item_stats it ON it.sellerId = u.userId
LEFT JOIN order_stats o ON o.sellerId = u.userId
LEFT JOIN review_stats rv ON rv.sellerId = u.userId
LEFT JOIN pending_stats p ON p.sellerId = u.userId
WHERE (%s IS NULL OR u.userId = %s)
ORDER BY completedOrders DESC, revenue DESC, u.userId
"""


class SellerRow(NamedTuple):
    sellerId: int
    firstName: str | None
    items: int
    soldItems: int
    removedItems: int
    completedOrders: int
    revenue: Decimal
    reviews: int
    ratingSum: int
    star1: int
    star2: int
    star3: int
    star4: int
    star5: int
    pendingRequests: int


def fetch_sellers(conn: Connection, seller_id: int | None = None) -> list[SellerRow]:
    """Run the query for one seller, or for every seller when ``seller_id`` is None."""
    with conn.cursor() as cur:
        cur.execute(SELLER_SQL, (seller_id, seller_id))
        return [
            SellerRow(
                sellerId=int(r[0]),
                firstName=r[1],
                items=int(r[2]),
                soldItems=int(r[3]),
                removedItems=int(r[4]),
                completedOrders=int(r[5]),
                revenue=Decimal(r[6]),
                reviews=int(r[7]),
                ratingSum=int(r[8]),
                star1=int(r[9]),
                star2=int(r[10]),
                star3=int(r[11]),
                star4=int(r[12]),
                star5=int(r[13]),
                pendingRequests=int(r[14]),
            )
            for r in cur.fetchall()
        ]


def sell_through(row: SellerRow) -> str:
    """Sold items as a share of the items that were not removed (``-`` when there are none)."""
    return percent(row.soldItems, row.items - row.removedItems)


def revenue_per_order(row: SellerRow) -> str:
    return average(row.revenue, row.completedOrders)


def average_rating(row: SellerRow) -> str:
    return average(row.ratingSum, row.reviews)


def top_sellers(rows: Sequence[SellerRow], limit: int = 3) -> list[SellerRow]:
    """The first ``limit`` rows by completed orders, then revenue, then id (the query's own order)."""
    return sorted(rows, key=lambda r: (-r.completedOrders, -r.revenue, r.sellerId))[:limit]


def total_pending(rows: Sequence[SellerRow]) -> int:
    return sum(r.pendingRequests for r in rows)


def print_seller(row: SellerRow) -> None:
    print(f"== Seller {row.sellerId} ({row.firstName or '-'}) ==")
    print(
        f"Items: {row.items} (sold {row.soldItems}, removed {row.removedItems}); "
        f"sell-through {sell_through(row)}"
    )
    print(
        f"Sales: {row.completedOrders} completed orders, revenue {money(row.revenue)}, "
        f"average per order {revenue_per_order(row)}"
    )
    print(f"Reviews: {row.reviews} published, average rating {average_rating(row)}")
    print_table(
        ["star1", "star2", "star3", "star4", "star5", "pendingRequests"],
        [(row.star1, row.star2, row.star3, row.star4, row.star5, row.pendingRequests)],
    )


def report(conn: Connection, seller_id: int | None) -> int:
    rows = fetch_sellers(conn, seller_id)
    if seller_id is not None and not rows:
        print(f"error: seller {seller_id} has no items", file=sys.stderr)
        return EXIT_FAILURE

    if seller_id is None:
        print(f"== {len(rows)} sellers; {total_pending(rows)} pending requests in total ==")
        print_table(
            ["sellerId", "orders", "revenue", "sell-through", "avg rating"],
            [
                (r.sellerId, r.completedOrders, money(r.revenue), sell_through(r), average_rating(r))
                for r in top_sellers(rows, len(rows))
            ],
        )
    for row in rows if seller_id is not None else top_sellers(rows):
        print_seller(row)
    return EXIT_OK


def _positive_int(text: str) -> int:
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a whole number: {text!r}") from None
    if value < 1:
        raise argparse.ArgumentTypeError(f"must be at least 1: {text!r}")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="p2_seller_report", description="Seller performance report (P2)."
    )
    parser.add_argument("--seller", type=_positive_int, help="report on this seller's userId only")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return run_with_connection(lambda conn: report(conn, args.seller))


if __name__ == "__main__":
    raise SystemExit(main())
