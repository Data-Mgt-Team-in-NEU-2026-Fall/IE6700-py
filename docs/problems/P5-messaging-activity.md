# P5 Conversation and Message Activity

- **Owner**: Eduardo Gonzalez (suggested, can be changed)
- **Status**: Implemented

## 1. Business Question

After a buyer asks about an item, how long does the seller take to reply, and do any conversations never get a seller reply?

## 2. Data Needed

A single query returns one row per conversation: item, creator, the item's seller, message count, the time of the creator's first message, the time of the seller's first message, whether the creator is the seller, and the minutes from the creator's first message to the seller's first message.

Optional filter: one item's `itemId` (`NULL` for all conversations). Rows are sorted by conversation id.

## 3. Python Analysis

- Conversations, messages, and average messages per conversation (`messageCount`).
- Reply time: use only rows where `sellerStarted = 0` and `minutesToReply` is not null and not negative (a negative value means the seller wrote first, so there was no reply delay). Print the count and the average.
- Unanswered conversations: rows where `sellerFirst` is null.

## 4. Expected Results (Seed Data, verified)

- 59 conversations, 326 messages, 5.53 messages per conversation. All 59 were started by buyers and all 59 have a seller message, so there are 0 unanswered conversations.
- 56 conversations qualify for the reply time, with an average of 189.0 minutes. Three are excluded: conversation 2 (the creator never wrote), and conversations 3 and 15 (the seller wrote first).

## 5. Acceptance Criteria

- 59 conversations and 326 messages; average 5.53.
- Reply statistics use 56 conversations.
- With an `itemId`, every returned row has that `itemId`.
