"""P6 Trust analysis of reviews and reports (owner: Yuan Xia). Design brief: docs/problems/P6-trust-and-safety.md.

Usage::

    python -m ie6700.analytics.p6_trust_and_safety
    python -m ie6700.analytics.p6_trust_and_safety --top 10

Read-only. One query returns one row per user: account status; reports against the user
(reports on the user's items plus reports on orders for the user's items), how many of
those were handled and the total days they took; and the user's received reviews
(published count, rating total, flagged count). Users without reports or reviews show 0.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from decimal import ROUND_HALF_UP, Decimal
from typing import NamedTuple

from .common import EXIT_OK, Connection, print_table, run_with_connection

DEFAULT_TOP = 5

# The one query, built from CTEs, each with a single job (everything is linked through ids, never names):
#   report_targets  each report with the user it is against: the seller of the reported item,
#                   or the seller of the item in the reported order
#   user_reports    per user: report count, handled count and handled days; handled means
#                   RESOLVED or DISMISSED with handledAt set, days are handledAt - reportDate
#   user_reviews    per user (as review recipient): published count, rating total over
#                   published reviews only, and flagged count
# The final SELECT lists every user, most reported first, ties by user id.
TRUST_SQL = """
WITH report_targets AS (
  SELECT ir.reportId, i.sellerId AS userId
  FROM ItemReport ir
  JOIN SecondhandItem i ON i.itemId = ir.itemId
  UNION ALL
  SELECT tr.reportId, i.sellerId
  FROM TransactionReport tr
  JOIN TransactionOrder t ON t.transactionId = tr.transactionId
  JOIN PurchaseRequest pr ON pr.purchaseRequestId = t.purchaseRequestId
  JOIN SecondhandItem i ON i.itemId = pr.itemId
),
user_reports AS (
  SELECT rt.userId, COUNT(*) AS reportedCount,
         SUM(r.status IN ('RESOLVED', 'DISMISSED') AND r.handledAt IS NOT NULL) AS handledCount,
         SUM(CASE WHEN r.status IN ('RESOLVED', 'DISMISSED') AND r.handledAt IS NOT NULL
                  THEN DATEDIFF(r.handledAt, r.reportDate) END) AS handledDaysSum
  FROM report_targets rt
  JOIN Report r ON r.reportId = rt.reportId
  GROUP BY rt.userId
),
user_reviews AS (
  SELECT recipientId AS userId,
         SUM(reviewStatus = 'PUBLISHED') AS publishedReviews,
         SUM(CASE WHEN reviewStatus = 'PUBLISHED' THEN rating END) AS ratingSum,
         SUM(reviewStatus = 'FLAGGED') AS flaggedReviews
  FROM TransactionReview
  GROUP BY recipientId
)
SELECT u.userId, u.accountStatus,
       COALESCE(ur.reportedCount, 0) AS reportedCount,
       COALESCE(ur.handledCount, 0) AS handledCount,
       COALESCE(ur.handledDaysSum, 0) AS handledDaysSum,
       COALESCE(uv.publishedReviews, 0) AS publishedReviews,
       COALESCE(uv.ratingSum, 0) AS ratingSum,
       COALESCE(uv.flaggedReviews, 0) AS flaggedReviews
FROM `User` u
LEFT JOIN user_reports ur ON ur.userId = u.userId
LEFT JOIN user_reviews uv ON uv.userId = u.userId
ORDER BY reportedCount DESC, u.userId
"""


class UserTrustRow(NamedTuple):
    userId: int
    accountStatus: str
    reportedCount: int
    handledCount: int
    handledDaysSum: int
    publishedReviews: int
    ratingSum: int
    flaggedReviews: int


class Overall(NamedTuple):
    users: int
    activeUsers: int
    suspendedUsers: int
    reports: int
    handledReports: int
    handledDaysSum: int
    publishedReviews: int
    ratingSum: int
    flaggedReviews: int
    averageRating: Decimal | None
    averageHandlingDays: Decimal | None


class RatingGroup(NamedTuple):
    users: int
    publishedReviews: int
    ratingSum: int
    averageRating: Decimal | None


def fetch_user_trust(conn: Connection) -> list[UserTrustRow]:
    """Run the query: one trust row per user, most reported first, ties by user id."""
    with conn.cursor() as cur:
        cur.execute(TRUST_SQL)
        return [
            UserTrustRow(
                userId=int(user_id),
                accountStatus=str(status),
                reportedCount=int(reported),
                handledCount=int(handled),
                handledDaysSum=int(days),
                publishedReviews=int(published),
                ratingSum=int(rating_sum),
                flaggedReviews=int(flagged),
            )
            for user_id, status, reported, handled, days, published, rating_sum, flagged in cur.fetchall()
        ]


def average_rating(published_reviews: int, rating_sum: int) -> Decimal | None:
    """Average rating to two decimals, or ``None`` with no published reviews."""
    if published_reviews == 0:
        return None
    return (Decimal(rating_sum) / Decimal(published_reviews)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def average_handling_days(handled_reports: int, handled_days_sum: int) -> Decimal | None:
    """Average handling days to two decimals, or ``None`` with no handled reports."""
    if handled_reports == 0:
        return None
    return (Decimal(handled_days_sum) / Decimal(handled_reports)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def user_average_rating(row: UserTrustRow) -> Decimal | None:
    """One user's average received rating, or ``None`` with no published reviews."""
    return average_rating(row.publishedReviews, row.ratingSum)


def overall(rows: Sequence[UserTrustRow]) -> Overall:
    """Roll all user rows up into the headline figures."""
    published = sum(r.publishedReviews for r in rows)
    rating_sum = sum(r.ratingSum for r in rows)
    handled = sum(r.handledCount for r in rows)
    return Overall(
        users=len(rows),
        activeUsers=sum(1 for r in rows if r.accountStatus == "ACTIVE"),
        suspendedUsers=sum(1 for r in rows if r.accountStatus == "SUSPENDED"),
        reports=sum(r.reportedCount for r in rows),
        handledReports=handled,
        handledDaysSum=sum(r.handledDaysSum for r in rows),
        publishedReviews=published,
        ratingSum=rating_sum,
        flaggedReviews=sum(r.flaggedReviews for r in rows),
        averageRating=average_rating(published, rating_sum),
        averageHandlingDays=average_handling_days(handled, sum(r.handledDaysSum for r in rows)),
    )


def top_reported(rows: Sequence[UserTrustRow], limit: int = DEFAULT_TOP) -> list[UserTrustRow]:
    """The most-reported users, top ``limit``. Ties are ordered by user id."""
    return sorted(rows, key=lambda r: (-r.reportedCount, r.userId))[:limit]


def _rating_group(rows: Sequence[UserTrustRow]) -> RatingGroup:
    published = sum(r.publishedReviews for r in rows)
    rating_sum = sum(r.ratingSum for r in rows)
    return RatingGroup(
        users=len(rows),
        publishedReviews=published,
        ratingSum=rating_sum,
        averageRating=average_rating(published, rating_sum),
    )


def compare_reported(rows: Sequence[UserTrustRow]) -> tuple[RatingGroup, RatingGroup]:
    """Average rating of users reported at least twice, against users never reported."""
    reported = _rating_group([r for r in rows if r.reportedCount >= 2])
    never_reported = _rating_group([r for r in rows if r.reportedCount == 0])
    return reported, never_reported


def _format_rating(value: Decimal | None) -> str:
    return "-" if value is None else f"{value:.2f}"


def report(conn: Connection, top: int) -> int:
    rows = fetch_user_trust(conn)
    stats = overall(rows)

    print("== Reviews and reports overall ==")
    print(f"{stats.users} users ({stats.activeUsers} ACTIVE, {stats.suspendedUsers} SUSPENDED).")
    print(f"{stats.reports} reports, all attached to a seller.")
    print(
        f"{stats.publishedReviews} published reviews with {stats.ratingSum} rating points, "
        f"average {_format_rating(stats.averageRating)}; {stats.flaggedReviews} flagged reviews."
    )
    print(
        f"{stats.handledReports} handled reports (RESOLVED or DISMISSED) with "
        f"{stats.handledDaysSum} days in total, average {_format_rating(stats.averageHandlingDays)} days.\n"
    )

    print(f"== Top {top} most reported users ==")
    print_table(
        ["userId", "status", "reports", "handled", "published reviews", "avg rating"],
        [
            (
                r.userId,
                r.accountStatus,
                r.reportedCount,
                r.handledCount,
                r.publishedReviews,
                _format_rating(user_average_rating(r)),
            )
            for r in top_reported(rows, top)
        ],
    )

    reported, never_reported = compare_reported(rows)
    print("== Reported users vs never-reported users ==")
    print(
        f"Reported at least twice ({reported.users} users): "
        f"{reported.publishedReviews} published reviews, average rating {_format_rating(reported.averageRating)}."
    )
    print(
        f"Never reported ({never_reported.users} users): "
        f"{never_reported.publishedReviews} published reviews, average rating {_format_rating(never_reported.averageRating)}."
    )
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
        prog="p6_trust_and_safety",
        description="Trust analysis of reviews and reports (P6).",
    )
    parser.add_argument(
        "--top", type=_positive_int, default=DEFAULT_TOP, help=f"how many most-reported users to list (default {DEFAULT_TOP})"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return run_with_connection(lambda conn: report(conn, args.top))


if __name__ == "__main__":
    raise SystemExit(main())
