"""P1 and P4 against the seeded sandbox (skipped without DATABASE_URL).

Expected values come from docs/problems/P1-search-and-price.md and P4-pickup-and-cross-campus.md.
"""

from decimal import Decimal

import pytest

from ie6700 import db
from ie6700.analytics import p1_search_and_price as p1
from ie6700.analytics import p4_pickup_and_cross_campus as p4
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
