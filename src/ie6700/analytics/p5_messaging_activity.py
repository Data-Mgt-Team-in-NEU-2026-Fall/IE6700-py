"""P5 Conversation and message activity (owner: Eduardo Gonzalez). Design brief: docs/problems/P5-messaging-activity.md.

Usage::

    python -m ie6700.analytics.p5_messaging_activity
    python -m ie6700.analytics.p5_messaging_activity --item 10

Read-only. One query returns one row per conversation with its message count and the time of the
creator's and the seller's first messages; Python measures the reply time and finds unanswered chats.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from datetime import datetime
from typing import NamedTuple

from .common import EXIT_OK, Connection, average, print_table, run_with_connection

# The one query. Each output row is one conversation (item, creator, the item's seller), joined to its messages:
#   messageCount   number of messages in the conversation
#   creatorFirst   time of the creator's first message (NULL if the creator never wrote)
#   sellerFirst    time of the seller's first message (NULL if the seller never wrote)
#   sellerStarted  1 when the creator is the item's seller, else 0
#   minutesToReply minutes from creatorFirst to sellerFirst (negative when the seller wrote first)
# Parameter: itemId or NULL (all conversations), given twice.
CONVERSATION_SQL = """
SELECT c.conversationId, c.itemId, c.creatorId, s.sellerId,
       COUNT(m.messageId) AS messageCount,
       MIN(CASE WHEN m.authorId = c.creatorId THEN m.sentAt END) AS creatorFirst,
       MIN(CASE WHEN m.authorId = s.sellerId THEN m.sentAt END) AS sellerFirst,
       s.sellerId = c.creatorId AS sellerStarted,
       TIMESTAMPDIFF(MINUTE, MIN(CASE WHEN m.authorId = c.creatorId THEN m.sentAt END), MIN(CASE WHEN m.authorId = s.sellerId THEN m.sentAt END)) AS minutesToReply
FROM Conversation c, SecondhandItem s, Message m
WHERE s.itemId = c.itemId
  AND c.conversationId = m.conversationId
  AND (%s IS NULL OR c.itemId = %s)
GROUP BY c.conversationId
ORDER BY c.conversationId
"""


class ConversationRow(NamedTuple):
    conversationId: int
    itemId: int
    creatorId: int
    sellerId: int
    messageCount: int
    creatorFirst: datetime | None
    sellerFirst: datetime | None
    sellerStarted: bool
    minutesToReply: int | None


class Volume(NamedTuple):
    conversations: int
    messages: int


class ReplyStats(NamedTuple):
    count: int
    totalMinutes: int


def fetch_conversations(conn: Connection, item_id: int | None = None) -> list[ConversationRow]:
    with conn.cursor() as cur:
        cur.execute(CONVERSATION_SQL, (item_id, item_id))
        return [
            ConversationRow(
                conversationId=int(r[0]),
                itemId=int(r[1]),
                creatorId=int(r[2]),
                sellerId=int(r[3]),
                messageCount=int(r[4]),
                creatorFirst=r[5],
                sellerFirst=r[6],
                sellerStarted=bool(r[7]),
                minutesToReply=None if r[8] is None else int(r[8]),
            )
            for r in cur.fetchall()
        ]


def volume(rows: Sequence[ConversationRow]) -> Volume:
    return Volume(conversations=len(rows), messages=sum(r.messageCount for r in rows))


def reply_rows(rows: Sequence[ConversationRow]) -> list[ConversationRow]:
    """Rows that measure a reply delay: started by a buyer, with a non-negative minutesToReply.

    A negative value means the seller wrote first, so there was no delay to measure.
    """
    return [r for r in rows if not r.sellerStarted and r.minutesToReply is not None and r.minutesToReply >= 0]


def reply_stats(rows: Sequence[ConversationRow]) -> ReplyStats:
    used = reply_rows(rows)
    return ReplyStats(count=len(used), totalMinutes=sum(r.minutesToReply or 0 for r in used))


def unanswered(rows: Sequence[ConversationRow]) -> list[ConversationRow]:
    """Conversations in which the seller never wrote."""
    return [r for r in rows if r.sellerFirst is None]


def report(conn: Connection, item_id: int | None) -> int:
    rows = fetch_conversations(conn, item_id)
    vol = volume(rows)

    print("== Volume ==")
    print(
        f"{vol.conversations} conversations, {vol.messages} messages, "
        f"{average(vol.messages, vol.conversations)} messages per conversation."
    )

    stats = reply_stats(rows)
    print("\n== Seller reply time ==")
    print(
        f"{stats.count} conversations qualify; average {average(stats.totalMinutes, stats.count, 1)} minutes "
        f"from the buyer's first message to the seller's first message."
    )
    print(f"Excluded: {vol.conversations - stats.count} (the seller wrote first, or a side never wrote).")

    missing = unanswered(rows)
    print(f"\n== Unanswered conversations: {len(missing)} ==")
    if missing:
        print_table(
            ["conversationId", "itemId", "creatorId", "sellerId", "messages"],
            [(r.conversationId, r.itemId, r.creatorId, r.sellerId, r.messageCount) for r in missing],
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
        prog="p5_messaging_activity", description="Conversation and message activity (P5)."
    )
    parser.add_argument("--item", type=_positive_int, help="only conversations about this itemId")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return run_with_connection(lambda conn: report(conn, args.item))


if __name__ == "__main__":
    raise SystemExit(main())
