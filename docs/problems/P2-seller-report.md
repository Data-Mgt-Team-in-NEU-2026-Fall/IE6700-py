# P2 Seller Performance Report

- **Owner**: Eduardo Gonzalez (suggested, can be changed)
- **Status**: Implemented

## 1. Business Question

For each seller (or one chosen seller): how many items are in each state, how much has been sold, what do buyers rate them, and how many requests await a reply?

## 2. Data Needed

A single query returns one row per seller (a user with at least one item): item count and counts of `SOLD` and `REMOVED` items; number of completed orders and their revenue (sum of `agreedPrice`); number and rating total of published seller reviews, with the count of each star rating 1–5; and the number of pending purchase requests on the seller's items. Sellers without orders or reviews show 0.

Optional filter: one seller's `userId` (`NULL` for all sellers). Rows are sorted by completed orders, then revenue, then id.

## 3. Python Analysis

- Sell-through rate = `soldItems ÷ (items − removedItems)`; average revenue per order = `revenue ÷ completedOrders`; average rating = `ratingSum ÷ reviews`. Print `-` when a denominator is 0.
- Print one report per returned row: item counts, sales, rating distribution (`star1`–`star5`), pending requests.
- With a seller id and no returned row, print one error line and exit with status 1.

## 4. Expected Results (Seed Data, verified)

- 23 sellers have posted items. Top three by completed orders, ties by revenue: 27 (3 orders, 70.00), 29 (2, 480.00), 23 (2, 160.00).
- **Seller 27 (Ethan)**: 3 items, all `SOLD`; 3 orders, revenue 70.00; 1 published review, average 1.00; sell-through 100%; 0 pending requests.
- **Seller 29 (Noah)**: 2 items, all `SOLD`; 2 orders, revenue 480.00; no published reviews.
- Pending requests across all sellers add up to 10.

## 5. Acceptance Criteria

- Seller 27 shows revenue 70.00 and average rating 1.00.
- `revenue` for each seller equals the sum of `agreedPrice` of that seller's completed orders.
- Only `PUBLISHED` reviews count; seller 9999 exits with status 1.
