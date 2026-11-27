"""P3 Purchase request conversion funnel (owner: Yuan Xia). Design brief: docs/problems/P3-request-funnel.md.

Usage::

    python -m ie6700.analytics.p3_request_funnel
    python -m ie6700.analytics.p3_request_funnel --month 2026-02

Read-only. One SELECT returns one row per request month (``YYYY-MM``) with only counts and
sums, so Python can add the months together. An optional month filter (``NULL`` for all
months) is bound twice, once for the ``IS NULL`` check and once for the comparison.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Sequence
from decimal import ROUND_HALF_UP, Decimal
from typing import NamedTuple

from .common import (
    EXIT_OK,
    EXIT_USAGE,
    Connection,
    InvalidInput,
    percent,
    print_table,
    run_with_connection,
)

_MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

# The one query: one row per request month. ``daysToOrderSum`` and ``discountSum`` only
# cover completed orders, so a month with no completed orders returns NULL for both.
# The ``%%`` in the DATE_FORMAT pattern is a literal ``%`` for PyMySQL's parameter formatting.
# ``discountSum`` is the sum of ``1 - agreedPrice / askingPrice``; asking prices of 0
# are guarded out (no completed order has one, but division by zero must stay NULL).
FUNNEL_SQL = """
SELECT DATE_FORMAT(pr.purchaseRequestDate, '%%Y-%%m') AS requestMonth,
       COUNT(*) AS requests,
       SUM(pr.status = 'ACCEPTED') AS acceptedRequests,
       COUNT(t.transactionId) AS orders,
       SUM(t.status = 'COMPLETED') AS completedOrders,
       SUM(t.status = 'CANCELLED') AS cancelledOrders,
       SUM(CASE WHEN t.status = 'COMPLETED'
                THEN DATEDIFF(t.transactionDate, pr.purchaseRequestDate) END) AS daysToOrderSum,
       SUM(CASE WHEN t.status = 'COMPLETED' AND i.askingPrice > 0
                THEN 1 - t.agreedPrice / i.askingPrice END) AS discountSum
FROM PurchaseRequest pr
LEFT JOIN TransactionOrder t ON t.purchaseRequestId = pr.purchaseRequestId
JOIN SecondhandItem i ON i.itemId = pr.itemId
WHERE (%s IS NULL OR DATE_FORMAT(pr.purchaseRequestDate, '%%Y-%%m') = %s)
GROUP BY requestMonth
ORDER BY requestMonth
"""


class MonthRow(NamedTuple):
    requestMonth: str
    requests: int
    acceptedRequests: int
    orders: int
    completedOrders: int
    cancelledOrders: int
    daysToOrderSum: int | None
    discountSum: Decimal | None


class FunnelTotals(NamedTuple):
    requests: int
    acceptedRequests: int
    orders: int
    completedOrders: int
    cancelledOrders: int
    pendingOrders: int
    daysToOrderSum: int
    discountSum: Decimal


def validate_month(text: str) -> str:
    """Return ``text`` if it is a ``YYYY-MM`` month, otherwise raise :class:`InvalidInput`."""
    if not _MONTH_RE.match(text):
        raise InvalidInput(f"not a month (expected YYYY-MM): {text!r}")
    return text


def fetch_funnel(conn: Connection, month: str | None = None) -> list[MonthRow]:
    """Run the query: one funnel row per request month (``month`` filters to a single month)."""
    with conn.cursor() as cur:
        cur.execute(FUNNEL_SQL, (month, month))
        return [
            MonthRow(
                requestMonth=str(request_month),
                requests=int(requests),
                acceptedRequests=int(accepted),
                orders=int(orders),
                completedOrders=int(completed),
                cancelledOrders=int(cancelled),
                daysToOrderSum=None if days is None else int(days),
                discountSum=None if discount is None else Decimal(discount),
            )
            for request_month, requests, accepted, orders, completed, cancelled, days, discount in cur.fetchall()
        ]


def funnel_totals(rows: Sequence[MonthRow]) -> FunnelTotals:
    """Add the monthly columns together; pending orders are orders neither completed nor cancelled."""
    requests = sum(r.requests for r in rows)
    accepted = sum(r.acceptedRequests for r in rows)
    orders = sum(r.orders for r in rows)
    completed = sum(r.completedOrders for r in rows)
    cancelled = sum(r.cancelledOrders for r in rows)
    return FunnelTotals(
        requests=requests,
        acceptedRequests=accepted,
        orders=orders,
        completedOrders=completed,
        cancelledOrders=cancelled,
        pendingOrders=orders - completed - cancelled,
        daysToOrderSum=sum(r.daysToOrderSum or 0 for r in rows),
        discountSum=sum((r.discountSum or Decimal(0) for r in rows), Decimal(0)),
    )


def average_days(days_sum: int, completed_orders: int) -> Decimal | None:
    """Average days from request to order, to two decimals, or ``None`` with no completed orders."""
    if completed_orders == 0:
        return None
    return (Decimal(days_sum) / Decimal(completed_orders)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def average_discount(discount_sum: Decimal, completed_orders: int) -> Decimal | None:
    """Average discount (``1 - agreedPrice / askingPrice``), to four decimals, or ``None`` with no completed orders."""
    if completed_orders == 0:
        return None
    return (discount_sum / Decimal(completed_orders)).quantize(
        Decimal("0.0001"), rounding=ROUND_HALF_UP
    )


def _format_days(value: Decimal | None) -> str:
    return "-" if value is None else f"{value:.2f}"


def _format_discount(value: Decimal | None) -> str:
    if value is None:
        return "-"
    return f"{(value * 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}%"


def report(conn: Connection, month: str | None) -> int:
    rows = fetch_funnel(conn, month)
    print("== Purchase request funnel by month ==")
    print_table(
        ["month", "requests", "accepted", "orders", "completed", "cancelled", "pending", "avg days", "avg discount"],
        [
            (
                r.requestMonth,
                r.requests,
                r.acceptedRequests,
                r.orders,
                r.completedOrders,
                r.cancelledOrders,
                r.orders - r.completedOrders - r.cancelledOrders,
                _format_days(average_days(r.daysToOrderSum or 0, r.completedOrders)),
                _format_discount(average_discount(r.discountSum or Decimal(0), r.completedOrders)),
            )
            for r in rows
        ],
    )

    totals = funnel_totals(rows)
    print("== Funnel ==")
    print(
        f"{totals.requests} requests -> {totals.acceptedRequests} accepted "
        f"({percent(totals.acceptedRequests, totals.requests)}) -> {totals.orders} orders -> "
        f"{totals.completedOrders} completed ({percent(totals.completedOrders, totals.orders)}), "
        f"{totals.cancelledOrders} cancelled ({percent(totals.cancelledOrders, totals.orders)}), "
        f"{totals.pendingOrders} pending.\n"
    )

    days = average_days(totals.daysToOrderSum, totals.completedOrders)
    discount = average_discount(totals.discountSum, totals.completedOrders)
    print("== Completed orders ==")
    print(f"Average days from request to order: {_format_days(days)}.")
    if discount is None:
        print("Average discount on completed orders: -.")
    else:
        print(f"Average discount on completed orders: {_format_discount(discount)} ({discount}).")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="p3_request_funnel",
        description="Purchase request conversion funnel by month (P3).",
    )
    parser.add_argument("--month", help="one request month (YYYY-MM); all months when omitted")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        month = None if args.month is None else validate_month(args.month)
    except InvalidInput as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    return run_with_connection(lambda conn: report(conn, month))


if __name__ == "__main__":
    raise SystemExit(main())
