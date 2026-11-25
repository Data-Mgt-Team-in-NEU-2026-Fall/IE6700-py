import datetime
import io
import json
from decimal import Decimal

from ie6700.render import cell_text, csv_text, json_value, render_results, results_json, table_text, write_text
from ie6700.runner import ResultSet


def test_null_is_shown_as_null():
    assert cell_text(None) == "NULL"
    assert json_value(None) is None


def test_decimal_keeps_its_precision_in_text_and_json():
    value = Decimal("1234.50")
    assert cell_text(value) == "1234.50"
    assert json_value(value) == "1234.50"


def test_dates_and_datetimes_are_iso_text():
    assert cell_text(datetime.date(2026, 1, 2)) == "2026-01-02"
    assert cell_text(datetime.datetime(2026, 1, 2, 3, 4, 5)) == "2026-01-02 03:04:05"
    assert json_value(datetime.datetime(2026, 1, 2, 3, 4, 5)) == "2026-01-02 03:04:05"
    assert json_value(datetime.date(2026, 1, 2)) == "2026-01-02"


def test_bytes_are_decoded_as_utf8_text():
    assert cell_text("café".encode("utf-8")) == "café"


def test_table_has_header_rule_and_rows_with_null():
    text = table_text(["id", "name"], [(1, "Ann"), (2, None)])
    lines = text.splitlines()
    assert lines[0].split() == ["id", "name"]
    assert set(lines[1].replace(" ", "")) == {"-"}
    assert lines[2].split() == ["1", "Ann"]
    assert lines[3].split() == ["2", "NULL"]


def test_numeric_looking_text_is_not_reformatted():
    text = table_text(["code"], [("00123",)])
    assert "00123" in text


def test_empty_result_still_prints_its_header():
    text = table_text(["a", "b"], [])
    assert text.splitlines()[0].split() == ["a", "b"]


def test_csv_has_header_and_quotes_commas():
    text = csv_text(["id", "note"], [(1, "a, b"), (2, None)])
    assert text == 'id,note\n1,"a, b"\n2,NULL\n'


def test_json_document_has_metadata_and_rows():
    result = ResultSet(
        columns=("n", "price"),
        rows=[(1, Decimal("2.50")), (None, datetime.date(2026, 1, 2))],
        source="/x/queries.sql",
        line=12,
        heading="1.1 UC-1101 Sign in",
    )
    document = json.loads(results_json([result]))
    assert document == [
        {
            "source": "/x/queries.sql",
            "line": 12,
            "heading": "1.1 UC-1101 Sign in",
            "section": None,
            "columns": ["n", "price"],
            "row_count": 2,
            "rows": [[1, "2.50"], [None, "2026-01-02"]],
        }
    ]


def test_table_render_prints_title_and_row_count():
    result = ResultSet(columns=("x",), rows=[(1,), (2,)], heading="2.1 Something")
    stream = io.StringIO()
    render_results([result], "table", stream)
    assert stream.getvalue().startswith("== 2.1 Something (2 rows)\n")


def test_non_ascii_text_on_a_cp1252_stream_does_not_crash():
    buffer = io.BytesIO()
    stream = io.TextIOWrapper(buffer, encoding="cp1252", newline="\n")
    write_text(stream, "café — 北京\n")
    stream.flush()
    data = buffer.getvalue()
    assert data.startswith("café".encode("cp1252"))
    assert b"?" in data  # characters cp1252 cannot hold are replaced


def test_table_output_on_a_cp1252_stream_does_not_crash():
    buffer = io.BytesIO()
    stream = io.TextIOWrapper(buffer, encoding="cp1252", newline="\n")
    result = ResultSet(columns=("名前",), rows=[("Zoë 北京",)], heading="Names")
    render_results([result], "table", stream)
    stream.flush()
    assert "Zoë".encode("cp1252") in buffer.getvalue()
