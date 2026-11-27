"""P1 and P4 against the seeded sandbox (skipped without DATABASE_URL).

Expected values come from docs/problems/P1-search-and-price.md and P4-pickup-and-cross-campus.md.
"""

from decimal import Decimal

import pytest

from ie6700 import db
from ie6700.analytics import p1_search_and_price as p1
from ie6700.analytics import p2_seller_report as p2
from ie6700.analytics import p3_request_funnel as p3
from ie6700.analytics import p4_pickup_and_cross_campus as p4
from ie6700.analytics import p5_messaging_activity as p5
from ie6700.analytics import p6_trust_and_safety as p6
from ie6700.analytics.common import average
from ie6700.course import COURSE_SCHEMA


@pytest.fixture
def course_conn(loaded_db):
    connection = db.connect(loaded_db, database=COURSE_SCHEMA)
    try:
        yield connection
    finally:
        connection.close()


# ---- P1 ----


def test_p1_unfiltered_search_returns_13_available_items_cheapest_first(course_conn):
    rows = p1.search_items(course_conn, p1.SearchFilters())
    assert len(rows) == 13
    prices = [row.askingPrice for row in rows]
    assert prices == sorted(prices)


def test_p1_category_filter_includes_subcategories(course_conn):
    rows = p1.search_items(course_conn, p1.SearchFilters(category="Electronics"))
    assert len(rows) == 4
    assert all(row.topCategory == "Electronics" for row in rows)
    assert {row.categoryName for row in rows} >= {"Computers"}


def test_p1_price_range_is_inclusive(course_conn):
    rows = p1.search_items(
        course_conn, p1.SearchFilters(min_price=Decimal(18), max_price=Decimal(18))
    )
    assert {row.itemId for row in rows} == {29, 34}


def test_p1_campus_tag_and_keyword_filters(course_conn):
    campus_rows = p1.search_items(course_conn, p1.SearchFilters(campus="Main Campus"))
    assert len(campus_rows) == 7
    assert all(row.campusName == "Main Campus" for row in campus_rows)

    tag_rows = p1.search_items(course_conn, p1.SearchFilters(tag="Negotiable"))
    assert len(tag_rows) == 4

    keyword_rows = p1.search_items(course_conn, p1.SearchFilters(keyword="monitor"))
    assert [row.itemId for row in keyword_rows] == [38]


def test_p1_benchmarks_describe_the_whole_market_even_when_filtered(course_conn):
    (row,) = p1.search_items(course_conn, p1.SearchFilters(keyword="monitor"))
    assert row.itemId == 38
    assert (row.categoryCount, row.priceRank) == (4, 4)
    assert row.categoryAvg == Decimal("33.25")
    assert row.diffFromAvg == Decimal("61.75")


def test_p1_category_summary_matches_the_brief(course_conn):
    rows = p1.search_items(course_conn, p1.SearchFilters())
    summaries = p1.summarize_categories([(r.topCategory, r.askingPrice) for r in rows])
    got = {s.category: (s.count, s.average, s.lowest, s.highest) for s in summaries}
    assert got == {
        "Electronics": (4, Decimal("33.25"), Decimal("0.00"), Decimal("95.00")),
        "Other": (2, Decimal("58.5"), Decimal("22.00"), Decimal("95.00")),
        "Sports & Outdoors": (2, Decimal("112.5"), Decimal("65.00"), Decimal("160.00")),
        "Furniture": (2, Decimal(44), Decimal("18.00"), Decimal("70.00")),
        "Clothing": (1, Decimal(8), Decimal("8.00"), Decimal("8.00")),
        "Kitchen & Dorm": (1, Decimal(40), Decimal("40.00"), Decimal("40.00")),
        "Textbooks": (1, Decimal(50), Decimal("50.00"), Decimal("50.00")),
    }
    assert sum(s.count for s in summaries) == 13


def test_p1_campus_counts_and_top_tags_match_the_brief(course_conn):
    rows = p1.search_items(course_conn, p1.SearchFilters())
    counts = dict(p1.campus_counts(rows))
    assert counts == {
        "Main Campus": 7,
        "West Campus": 2,
        "South Campus": 2,
        "East Campus": 1,
        "North Campus": 1,
    }
    assert sum(counts.values()) == 13
    assert p1.top_tags(rows) == [
        ("Like new", 5),
        ("Negotiable", 4),
        ("Free campus pickup", 3),
        ("Student deal", 3),
        ("Needs repair", 1),
    ]


def test_p1_keyword_is_bound_not_concatenated(course_conn):
    rows = p1.search_items(course_conn, p1.SearchFilters(keyword="'; DROP TABLE Campus; --"))
    assert rows == []
    assert "Campus" in db.base_table_names(course_conn, COURSE_SCHEMA)


def test_p1_does_not_change_the_database(course_conn):
    before = db.table_counts(course_conn, COURSE_SCHEMA)
    p1.report(course_conn, p1.SearchFilters())
    assert db.table_counts(course_conn, COURSE_SCHEMA) == before


# ---- P3 ----


def test_p3_funnel_totals_match_the_brief(course_conn):
    rows = p3.fetch_funnel(course_conn)
    assert len(rows) == 11  # 2025-12 to 2026-10
    assert [r.requestMonth for r in rows] == [
        "2025-12", "2026-01", "2026-02", "2026-03", "2026-04", "2026-05",
        "2026-06", "2026-07", "2026-08", "2026-09", "2026-10",
    ]
    totals = p3.funnel_totals(rows)
    assert totals == p3.FunnelTotals(
        requests=43,
        acceptedRequests=29,
        orders=29,
        completedOrders=23,
        cancelledOrders=3,
        pendingOrders=3,
        daysToOrderSum=23,
        discountSum=Decimal("2.011766"),
    )
    assert p3.average_days(totals.daysToOrderSum, totals.completedOrders) == Decimal("1.00")
    assert p3.average_discount(totals.discountSum, totals.completedOrders) == Decimal("0.0875")


def test_p3_month_rows_match_the_brief(course_conn):
    rows = {r.requestMonth: r for r in p3.fetch_funnel(course_conn)}
    february = rows["2026-02"]
    assert (february.requests, february.orders, february.completedOrders) == (6, 6, 6)
    september = rows["2026-09"]
    assert (september.requests, september.acceptedRequests, september.orders) == (3, 2, 2)
    assert september.completedOrders == 0 and september.cancelledOrders == 2
    assert september.daysToOrderSum is None and september.discountSum is None


def test_p3_month_filter_returns_one_month(course_conn):
    (row,) = p3.fetch_funnel(course_conn, "2026-02")
    assert row.requestMonth == "2026-02" and row.requests == 6
    assert p3.fetch_funnel(course_conn, "2026-11") == []


def test_p3_month_filter_is_bound_not_concatenated(course_conn):
    rows = p3.fetch_funnel(course_conn, "'; DROP TABLE Campus; --")
    assert rows == []
    assert "Campus" in db.base_table_names(course_conn, COURSE_SCHEMA)


def test_p3_does_not_change_the_database(course_conn):
    before = db.table_counts(course_conn, COURSE_SCHEMA)
    p3.report(course_conn, None)
    assert db.table_counts(course_conn, COURSE_SCHEMA) == before


# ---- P6 ----


def test_p6_overall_matches_the_brief(course_conn):
    rows = p6.fetch_user_trust(course_conn)
    assert len(rows) == 30
    stats = p6.overall(rows)
    assert stats == p6.Overall(
        users=30,
        activeUsers=28,
        suspendedUsers=2,
        reports=30,
        handledReports=17,
        handledDaysSum=79,
        publishedReviews=27,
        ratingSum=99,
        flaggedReviews=6,
        averageRating=Decimal("3.67"),
        averageHandlingDays=Decimal("4.65"),
    )
    assert {r.userId for r in rows if r.accountStatus == "SUSPENDED"} == {25, 26}


def test_p6_top_reported_matches_the_brief(course_conn):
    rows = p6.fetch_user_trust(course_conn)
    top = p6.top_reported(rows, 5)
    assert [r.userId for r in top] == [18, 22, 23, 26, 27]
    assert all(r.reportedCount == 3 for r in top)
    assert [r for r in top if r.userId == 26][0].accountStatus == "SUSPENDED"


def test_p6_users_without_reports_or_reviews_show_zero(course_conn):
    rows = {r.userId: r for r in p6.fetch_user_trust(course_conn)}
    assert rows[6] == p6.UserTrustRow(6, "ACTIVE", 0, 0, 0, 0, 0, 0)
    assert p6.user_average_rating(rows[6]) is None
    assert p6.user_average_rating(rows[22]) == Decimal("4.33")


def test_p6_reported_users_average_higher_than_never_reported(course_conn):
    rows = p6.fetch_user_trust(course_conn)
    reported, never_reported = p6.compare_reported(rows)
    assert reported == p6.RatingGroup(users=8, publishedReviews=11, ratingSum=43, averageRating=Decimal("3.91"))
    assert never_reported == p6.RatingGroup(users=13, publishedReviews=9, ratingSum=30, averageRating=Decimal("3.33"))


def test_p6_does_not_change_the_database(course_conn):
    before = db.table_counts(course_conn, COURSE_SCHEMA)
    p6.report(course_conn, 5)
    assert db.table_counts(course_conn, COURSE_SCHEMA) == before


# ---- P4 ----


def test_p4_cross_campus_share_matches_the_brief(course_conn):
    groups = p4.fetch_order_groups(course_conn)
    assert p4.cross_campus(groups) == p4.CrossCampus(crossCampus=22, total=29)


def test_p4_campus_matrix_sums_to_all_orders(course_conn):
    matrix = p4.build_matrix(p4.campus_cells(p4.fetch_order_groups(course_conn)))
    assert sum(matrix.counts.values()) == 29
    same_campus = sum(n for (b, s), n in matrix.counts.items() if b == s)
    assert 29 - same_campus == 22


def test_p4_top_pickup_points_match_the_brief(course_conn):
    top = p4.top_pickup_points(p4.fetch_order_groups(course_conn), 5)
    assert [(p.pickupPointName, p.orderCount) for p in top] == [
        ("Library entrance (Ethan)", 3),
        ("Student Union lobby (Sophia)", 3),
        ("Library entrance (Leo)", 2),
        ("Library entrance (Max)", 2),
        ("Library entrance (Noah)", 2),
    ]
    assert all(p.activeStatus for p in top)


def test_p4_same_named_pickup_points_stay_separate(course_conn):
    everything = p4.top_pickup_points(p4.fetch_order_groups(course_conn), 100)
    names = [p.pickupPointName for p in everything]
    assert names.count("Library entrance (Max)") == 2
    assert len({p.pickupPointId for p in everything}) == len(everything)


def test_p4_ownership_and_activity_are_29_of_29(course_conn):
    owned = p4.ownership(p4.fetch_order_groups(course_conn))
    assert owned == p4.Ownership(ownedBySeller=29, activeOrders=29, total=29)


def test_p4_does_not_change_the_database(course_conn):
    before = db.table_counts(course_conn, COURSE_SCHEMA)
    p4.report(course_conn, 5)
    assert db.table_counts(course_conn, COURSE_SCHEMA) == before


# ---- P2 (docs/problems/P2-seller-report.md) ----


def test_p2_has_23_sellers_and_the_top_three(course_conn):
    rows = p2.fetch_sellers(course_conn)
    assert len(rows) == 23
    assert [(r.sellerId, r.completedOrders, r.revenue) for r in rows[:3]] == [
        (27, 3, Decimal("70.00")),
        (29, 2, Decimal("480.00")),
        (23, 2, Decimal("160.00")),
    ]


def test_p2_seller_27(course_conn):
    (row,) = p2.fetch_sellers(course_conn, 27)
    assert (row.items, row.soldItems, row.removedItems) == (3, 3, 0)
    assert (row.completedOrders, row.revenue) == (3, Decimal("70.00"))
    assert row.reviews == 1
    assert p2.average_rating(row) == "1.00"
    assert p2.sell_through(row) == "100.0%"
    assert row.pendingRequests == 0


def test_p2_seller_29_has_no_reviews(course_conn):
    (row,) = p2.fetch_sellers(course_conn, 29)
    assert (row.items, row.soldItems, row.completedOrders, row.revenue) == (2, 2, 2, Decimal("480.00"))
    assert row.reviews == 0
    assert p2.average_rating(row) == "-"


def test_p2_pending_requests_add_up_to_10(course_conn):
    assert p2.total_pending(p2.fetch_sellers(course_conn)) == 10


def test_p2_revenue_equals_completed_order_sum_per_seller(course_conn):
    with course_conn.cursor() as cur:
        cur.execute(
            "SELECT i.sellerId, SUM(t.agreedPrice) FROM TransactionOrder t "
            "JOIN PurchaseRequest pr ON pr.purchaseRequestId = t.purchaseRequestId "
            "JOIN SecondhandItem i ON i.itemId = pr.itemId WHERE t.status = 'COMPLETED' GROUP BY i.sellerId"
        )
        expected = {int(s): Decimal(total) for s, total in cur.fetchall()}
    got = {r.sellerId: r.revenue for r in p2.fetch_sellers(course_conn) if r.completedOrders}
    assert got == expected


def test_p2_unknown_seller_exits_with_status_1(course_conn, capsys):
    assert p2.fetch_sellers(course_conn, 9999) == []
    assert p2.report(course_conn, 9999) == 1
    assert "9999" in capsys.readouterr().err


def test_p2_seller_filter_is_bound_not_concatenated(course_conn):
    assert p2.fetch_sellers(course_conn, "'; DROP TABLE Campus; --") == []  # type: ignore[arg-type]
    assert "Campus" in db.base_table_names(course_conn, COURSE_SCHEMA)


def test_p2_does_not_change_the_database(course_conn):
    before = db.table_counts(course_conn, COURSE_SCHEMA)
    p2.report(course_conn, None)
    assert db.table_counts(course_conn, COURSE_SCHEMA) == before


# ---- P5 (docs/problems/P5-messaging-activity.md) ----


def test_p5_volume(course_conn):
    rows = p5.fetch_conversations(course_conn)
    vol = p5.volume(rows)
    assert (vol.conversations, vol.messages) == (59, 326)
    assert average(vol.messages, vol.conversations) == "5.53"


def test_p5_all_started_by_buyers_and_none_unanswered(course_conn):
    rows = p5.fetch_conversations(course_conn)
    assert not any(r.sellerStarted for r in rows)
    assert p5.unanswered(rows) == []


def test_p5_reply_time_uses_56_conversations(course_conn):
    rows = p5.fetch_conversations(course_conn)
    stats = p5.reply_stats(rows)
    assert stats.count == 56
    assert average(stats.totalMinutes, stats.count, 1) == "189.0"
    excluded = {r.conversationId for r in rows} - {r.conversationId for r in p5.reply_rows(rows)}
    assert excluded == {2, 3, 15}


def test_p5_item_filter_returns_only_that_item(course_conn):
    rows = p5.fetch_conversations(course_conn, 10)
    assert rows and all(r.itemId == 10 for r in rows)


def test_p5_item_is_bound_not_concatenated(course_conn):
    assert p5.fetch_conversations(course_conn, "'; DROP TABLE Campus; --") == []  # type: ignore[arg-type]
    assert "Campus" in db.base_table_names(course_conn, COURSE_SCHEMA)


def test_p5_does_not_change_the_database(course_conn):
    before = db.table_counts(course_conn, COURSE_SCHEMA)
    p5.report(course_conn, None)
    assert db.table_counts(course_conn, COURSE_SCHEMA) == before
