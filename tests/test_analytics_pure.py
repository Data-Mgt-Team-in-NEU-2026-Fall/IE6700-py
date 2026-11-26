"""Pure checks for the analytics modules: no database needed."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from ie6700.analytics import p1_search_and_price as p1
from ie6700.analytics import p2_seller_report as p2
from ie6700.analytics import p4_pickup_and_cross_campus as p4
from ie6700.analytics import p5_messaging_activity as p5
from ie6700.analytics.common import InvalidInput, average, money, percent


def test_min_price_above_max_price_is_rejected():
    with pytest.raises(InvalidInput):
        p1.SearchFilters(min_price=Decimal(50), max_price=Decimal(10))


def test_equal_min_and_max_price_is_allowed():
    filters = p1.SearchFilters(min_price=Decimal(20), max_price=Decimal(20))
    assert filters.min_price == filters.max_price == Decimal(20)


def test_cli_exits_with_usage_status_for_inverted_price_range(capsys):
    status = p1.main(["--min-price", "50", "--max-price", "10"])
    assert status == 2
    assert "greater than maximum price" in capsys.readouterr().err


def test_cli_rejects_a_negative_price():
    with pytest.raises(SystemExit):
        p1.build_parser().parse_args(["--max-price", "-1"])


def test_like_pattern_matches_wildcards_literally():
    assert p1.like_pattern("50%") == "%50\\%%"
    assert p1.like_pattern("a_b") == "%a\\_b%"
    assert p1.like_pattern("c\\d") == "%c\\\\d%"


def test_summarize_categories_counts_and_prices():
    rows = [
        ("Electronics", Decimal(0)),
        ("Electronics", Decimal(95)),
        ("Electronics", None),
        ("Furniture", Decimal(18)),
    ]
    summaries = p1.summarize_categories(rows)

    electronics = summaries[0]
    assert electronics.category == "Electronics"
    assert electronics.count == 3  # the item without a price still counts
    assert electronics.average == Decimal("47.5")
    assert electronics.lowest == Decimal(0)
    assert electronics.highest == Decimal(95)
    assert summaries[1].category == "Furniture"


def test_summarize_categories_orders_by_count_then_name():
    rows = [("B", Decimal(1)), ("A", Decimal(1)), ("A", Decimal(2)), ("C", Decimal(3))]
    assert [s.category for s in p1.summarize_categories(rows)] == ["A", "B", "C"]


def test_summarize_category_with_no_prices_has_no_price_figures():
    (summary,) = p1.summarize_categories([("Books", None)])
    assert summary.count == 1
    assert summary.average is None and summary.lowest is None and summary.highest is None


def test_build_matrix_fills_missing_cells_with_zero_totals():
    cells = [("East Campus", "Main Campus", 3), ("West Campus", "West Campus", 4)]
    matrix = p4.build_matrix(cells)
    assert matrix.buyerCampuses == ["East Campus", "West Campus"]
    assert matrix.sellerCampuses == ["Main Campus", "West Campus"]

    rows = p4.matrix_rows(matrix)
    assert rows[0] == ["East Campus", 3, 0, 3]
    assert rows[1] == ["West Campus", 0, 4, 4]
    assert rows[-1] == ["total", 3, 4, 7]


def test_money_and_percent_formatting():
    assert money(Decimal(0)) == "0.00"
    assert money(Decimal("33.2")) == "33.20"
    assert money(None) == "-"
    assert percent(22, 29) == "75.9%"
    assert percent(0, 0) == "-"


def _item(item_id, campus, tags):
    return p1.ItemRow(item_id, "x", Decimal(1), "Cat", "Cat", campus, tags, 1, Decimal(1), 1, Decimal(0))


def test_top_tags_counts_splits_and_breaks_ties_by_name():
    rows = [_item(1, "A", "b,a"), _item(2, "A", "b"), _item(3, "B", None)]
    assert p1.top_tags(rows) == [("b", 2), ("a", 1)]
    assert p1.top_tags(rows, limit=1) == [("b", 2)]


def test_campus_counts_orders_by_count_then_name():
    rows = [_item(1, "B", None), _item(2, "A", None), _item(3, "B", None)]
    assert p1.campus_counts(rows) == [("B", 2), ("A", 1)]


def _group(buyer, seller, pid, name, orders, owned=None, active=True, owner=1):
    return p4.OrderGroup(buyer, seller, pid, name, owner, active, orders, orders if owned is None else owned)


def test_p4_rollups_from_order_groups():
    groups = [
        _group("East", "East", 1, "Lobby", 2),
        _group("East", "West", 1, "Lobby", 1),
        _group("West", "East", 2, "Lobby", 4, owned=3, active=False),
    ]
    assert p4.cross_campus(groups) == p4.CrossCampus(crossCampus=5, total=7)
    assert p4.campus_cells(groups) == [("East", "East", 2), ("East", "West", 1), ("West", "East", 4)]
    assert p4.ownership(groups) == p4.Ownership(ownedBySeller=6, activeOrders=3, total=7)


def test_p4_top_pickup_points_merge_by_id_not_by_name():
    groups = [
        _group("A", "A", 1, "Lobby", 2),
        _group("B", "A", 1, "Lobby", 1),
        _group("A", "B", 2, "Lobby", 3),
    ]
    top = p4.top_pickup_points(groups, limit=5)
    assert [(p.pickupPointId, p.orderCount) for p in top] == [(1, 3), (2, 3)]  # same name, two points
    assert p4.top_pickup_points(groups, limit=1)[0].pickupPointId == 1  # tie broken by id


def test_p4_empty_groups_give_zero_totals():
    assert p4.cross_campus([]) == p4.CrossCampus(0, 0)
    assert p4.ownership([]) == p4.Ownership(0, 0, 0)
    assert p4.top_pickup_points([]) == []


def test_each_module_runs_exactly_one_query():
    assert p1.SEARCH_SQL.lstrip().upper().startswith("WITH") and ";" not in p1.SEARCH_SQL
    assert p4.ORDER_GROUPS_SQL.lstrip().upper().startswith("WITH") and ";" not in p4.ORDER_GROUPS_SQL
    for sql in (p1.SEARCH_SQL, p4.ORDER_GROUPS_SQL):
        assert not any(word in sql.upper() for word in ("INSERT ", "UPDATE ", "DELETE ", "DROP "))


# ---- average helper ----


def test_average_formats_and_handles_zero_count():
    assert average(Decimal(70), 3) == "23.33"
    assert average(1, 0) == "-"
    assert average(567, 3, 1) == "189.0"


# ---- P2 ----


def _seller(**kw):
    base = dict(
        sellerId=1, firstName="A", items=4, soldItems=2, removedItems=1, completedOrders=2,
        revenue=Decimal("100"), reviews=2, ratingSum=9, star1=0, star2=0, star3=0, star4=1, star5=1,
        pendingRequests=1,
    )
    base.update(kw)
    return p2.SellerRow(**base)


def test_p2_metrics_from_counts():
    row = _seller()
    assert p2.sell_through(row) == "66.7%"  # 2 sold of 4 - 1 removed
    assert p2.revenue_per_order(row) == "50.00"
    assert p2.average_rating(row) == "4.50"


def test_p2_zero_denominators_print_a_dash():
    row = _seller(items=1, removedItems=1, completedOrders=0, revenue=Decimal(0), reviews=0, ratingSum=0)
    assert p2.sell_through(row) == "-"
    assert p2.revenue_per_order(row) == "-"
    assert p2.average_rating(row) == "-"


def test_p2_top_sellers_order_and_pending_total():
    rows = [
        _seller(sellerId=3, completedOrders=2, revenue=Decimal(10), pendingRequests=2),
        _seller(sellerId=2, completedOrders=2, revenue=Decimal(10), pendingRequests=0),
        _seller(sellerId=1, completedOrders=2, revenue=Decimal(50), pendingRequests=1),
    ]
    assert [r.sellerId for r in p2.top_sellers(rows)] == [1, 2, 3]
    assert p2.total_pending(rows) == 3


def test_p2_rejects_a_bad_seller_id():
    for bad in ("0", "-3", "abc"):
        with pytest.raises(SystemExit):
            p2.build_parser().parse_args(["--seller", bad])


# ---- P5 ----


def _conv(cid, msgs=2, started=False, mins=10, seller_first=datetime(2026, 1, 1)):
    return p5.ConversationRow(cid, 1, 2, 3, msgs, datetime(2026, 1, 1), seller_first, started, mins)


def test_p5_volume_and_reply_stats_exclude_unmeasurable_rows():
    rows = [
        _conv(1, mins=10),
        _conv(2, mins=30),
        _conv(3, mins=-5),  # seller wrote first
        _conv(4, mins=None),  # creator never wrote
        _conv(5, started=True, mins=0),  # seller started it
        _conv(6, mins=0),  # replied in the same minute: counts
    ]
    assert p5.volume(rows) == p5.Volume(6, 12)
    assert p5.reply_stats(rows) == p5.ReplyStats(count=3, totalMinutes=40)


def test_p5_unanswered_are_rows_without_a_seller_message():
    rows = [_conv(1), _conv(2, seller_first=None, mins=None, msgs=0)]
    assert [r.conversationId for r in p5.unanswered(rows)] == [2]
    assert p5.reply_stats([]) == p5.ReplyStats(0, 0)


def test_p2_p5_each_run_exactly_one_read_only_query():
    for sql in (p2.SELLER_SQL, p5.CONVERSATION_SQL):
        assert sql.lstrip().upper().startswith(("WITH", "SELECT")) and ";" not in sql
        assert not any(word in sql.upper() for word in ("INSERT ", "UPDATE ", "DELETE ", "DROP "))
