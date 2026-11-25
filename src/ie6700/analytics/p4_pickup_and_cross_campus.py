"""P4 Pickup points and cross-campus orders (owner: Kun Yu). Design brief: docs/problems/P4-pickup-and-cross-campus.md.

Usage::

    python -m ie6700.analytics.p4_pickup_and_cross_campus
    python -m ie6700.analytics.p4_pickup_and_cross_campus --top 10

Read-only. One query (built from CTEs) returns the orders grouped by (buyer campus, seller campus, pickup point);
Python rolls those groups up. Pickup points are counted by pickupPointId, so two points with the
same name stay apart.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from collections.abc import Sequence
from typing import NamedTuple

from .common import EXIT_OK, Connection, percent, print_table, run_with_connection

DEFAULT_TOP = 5

# The one query, built from CTEs, each with a single job (everything is linked through ids, never names):
#   order_parties  each order with the buyer's campus, the seller's campus and the item's seller
#   order_facts    adds the campus names and the pickup point, and flags whether that pickup point
#                  is owned by the item's seller
# The final SELECT counts the orders per (buyer campus, seller campus, pickup point).
ORDER_GROUPS_SQL = """
WITH order_parties AS (
  SELECT t.transactionId, t.pickupPointId, i.sellerId,
         b.campusId AS buyerCampusId, s.campusId AS sellerCampusId
  FROM TransactionOrder t
  JOIN PurchaseRequest pr ON pr.purchaseRequestId = t.purchaseRequestId
  JOIN SecondhandItem i ON i.itemId = pr.itemId
  JOIN `User` b ON b.userId = pr.buyerId
  JOIN `User` s ON s.userId = i.sellerId
),
order_facts AS (
  SELECT op.transactionId,
         op.buyerCampusId, bc.campusName AS buyerCampus,
         op.sellerCampusId, sc.campusName AS sellerCampus,
         pp.pickupPointId, pp.pickupPointName, pp.ownerId, pp.activeStatus,
         pp.ownerId = op.sellerId AS ownedBySeller
  FROM order_parties op
  JOIN Campus bc ON bc.campusId = op.buyerCampusId
  JOIN Campus sc ON sc.campusId = op.sellerCampusId
  JOIN PickupPoint pp ON pp.pickupPointId = op.pickupPointId
)
SELECT buyerCampus, sellerCampus, pickupPointId, pickupPointName, ownerId, activeStatus,
       COUNT(*) AS orders,
       SUM(ownedBySeller) AS ownedBySeller
FROM order_facts
GROUP BY buyerCampusId, buyerCampus, sellerCampusId, sellerCampus,
         pickupPointId, pickupPointName, ownerId, activeStatus
ORDER BY orders DESC, pickupPointName, pickupPointId
"""


class OrderGroup(NamedTuple):
    buyerCampus: str
    sellerCampus: str
    pickupPointId: int
    pickupPointName: str
    ownerId: int
    activeStatus: bool
    orders: int
    ownedBySeller: int


class CrossCampus(NamedTuple):
    crossCampus: int
    total: int


class PickupRow(NamedTuple):
    pickupPointId: int
    pickupPointName: str
    ownerId: int
    activeStatus: bool
    orderCount: int


class Ownership(NamedTuple):
    ownedBySeller: int
    activeOrders: int
    total: int


class Matrix(NamedTuple):
    buyerCampuses: list[str]
    sellerCampuses: list[str]
    counts: dict[tuple[str, str], int]


def fetch_order_groups(conn: Connection) -> list[OrderGroup]:
    """Run the query: order counts per (buyer campus, seller campus, pickup point)."""
    with conn.cursor() as cur:
        cur.execute(ORDER_GROUPS_SQL)
        return [
            OrderGroup(
                buyerCampus=str(buyer),
                sellerCampus=str(seller),
                pickupPointId=int(pid),
                pickupPointName=str(name),
                ownerId=int(owner),
                activeStatus=bool(active),
                orders=int(orders),
                ownedBySeller=int(owned),
            )
            for buyer, seller, pid, name, owner, active, orders, owned in cur.fetchall()
        ]


def cross_campus(groups: Sequence[OrderGroup]) -> CrossCampus:
    """Orders whose buyer and seller are on different campuses, and the order total."""
    total = sum(g.orders for g in groups)
    cross = sum(g.orders for g in groups if g.buyerCampus != g.sellerCampus)
    return CrossCampus(crossCampus=cross, total=total)


def campus_cells(groups: Sequence[OrderGroup]) -> list[tuple[str, str, int]]:
    """``(buyer campus, seller campus, order count)`` for each pair that has orders."""
    counts: dict[tuple[str, str], int] = defaultdict(int)
    for g in groups:
        counts[(g.buyerCampus, g.sellerCampus)] += g.orders
    return [(buyer, seller, n) for (buyer, seller), n in sorted(counts.items())]


def build_matrix(cells: Sequence[tuple[str, str, int]]) -> Matrix:
    """Arrange the cells into a matrix with sorted row and column labels."""
    buyers = sorted({buyer for buyer, _, _ in cells})
    sellers = sorted({seller for _, seller, _ in cells})
    counts: dict[tuple[str, str], int] = {}
    for buyer, seller, count in cells:
        counts[(buyer, seller)] = counts.get((buyer, seller), 0) + count
    return Matrix(buyers, sellers, counts)


def matrix_rows(matrix: Matrix) -> list[list[object]]:
    """Table rows for the matrix, with a row total and a final row of column totals."""
    rows: list[list[object]] = []
    column_totals = [0] * len(matrix.sellerCampuses)
    for buyer in matrix.buyerCampuses:
        values = [matrix.counts.get((buyer, seller), 0) for seller in matrix.sellerCampuses]
        column_totals = [total + value for total, value in zip(column_totals, values, strict=True)]
        rows.append([buyer, *values, sum(values)])
    rows.append(["total", *column_totals, sum(column_totals)])
    return rows


def top_pickup_points(groups: Sequence[OrderGroup], limit: int = DEFAULT_TOP) -> list[PickupRow]:
    """The pickup points used most, top ``limit``. Ties are ordered by name, then id."""
    counts: dict[int, int] = defaultdict(int)
    first: dict[int, OrderGroup] = {}
    for g in groups:
        counts[g.pickupPointId] += g.orders
        first.setdefault(g.pickupPointId, g)
    rows = [
        PickupRow(
            pickupPointId=pid,
            pickupPointName=first[pid].pickupPointName,
            ownerId=first[pid].ownerId,
            activeStatus=first[pid].activeStatus,
            orderCount=count,
        )
        for pid, count in counts.items()
    ]
    rows.sort(key=lambda p: (-p.orderCount, p.pickupPointName, p.pickupPointId))
    return rows[:limit]


def ownership(groups: Sequence[OrderGroup]) -> Ownership:
    """How many orders use a pickup point owned by the seller, and how many use an active one."""
    return Ownership(
        ownedBySeller=sum(g.ownedBySeller for g in groups),
        activeOrders=sum(g.orders for g in groups if g.activeStatus),
        total=sum(g.orders for g in groups),
    )


def report(conn: Connection, top: int) -> int:
    groups = fetch_order_groups(conn)

    cross = cross_campus(groups)
    print("== Cross-campus orders ==")
    print(
        f"{cross.crossCampus} of {cross.total} orders "
        f"({percent(cross.crossCampus, cross.total)}) have a buyer and seller on different campuses.\n"
    )

    matrix = build_matrix(campus_cells(groups))
    print("== Campus matrix: order count by buyer campus (rows) and seller campus (columns) ==")
    print_table(["buyer \\ seller", *matrix.sellerCampuses, "total"], matrix_rows(matrix))

    print(f"== Top {top} pickup points by order count ==")
    print_table(
        ["pickupPointId", "name", "ownerId", "active", "orders"],
        [
            (p.pickupPointId, p.pickupPointName, p.ownerId, "yes" if p.activeStatus else "no", p.orderCount)
            for p in top_pickup_points(groups, top)
        ],
    )

    owned = ownership(groups)
    print("== Pickup point checks ==")
    print(f"Pickup point belongs to the item's seller: {owned.ownedBySeller} of {owned.total} orders.")
    print(f"Pickup point is active: {owned.activeOrders} of {owned.total} orders.")
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
        prog="p4_pickup_and_cross_campus",
        description="Cross-campus orders, campus matrix and pickup point usage (P4).",
    )
    parser.add_argument(
        "--top", type=_positive_int, default=DEFAULT_TOP, help=f"how many pickup points to list (default {DEFAULT_TOP})"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return run_with_connection(lambda conn: report(conn, args.top))


if __name__ == "__main__":
    raise SystemExit(main())
