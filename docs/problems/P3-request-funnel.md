# P3 Purchase Request Conversion Funnel

- **Owner**: Yuan Xia (suggested, can be changed)
- **Status**: Implemented (in review)

## 1. Business Question

How many purchase requests become orders, how many orders complete or cancel, and how far below the asking price are completed orders?

## 2. Data Needed

A single query returns one row per request month (`YYYY-MM`) with only counts and sums, so Python can add the months together: requests, accepted requests, orders, completed orders, cancelled orders, the sum of days from request to order for completed orders, and the sum of `1 − agreedPrice ÷ askingPrice` for completed orders.

Optional filter: one month (`NULL` for all months). Rows are sorted by month.

## 3. Python Analysis

- Add the columns over all returned months, then compute: acceptance rate = accepted ÷ requests; completion rate = completed ÷ orders; cancellation rate = cancelled ÷ orders; average days = `daysToOrderSum ÷ completedOrders`; average discount = `discountSum ÷ completedOrders`.
- Print the monthly table, the funnel (requests → accepted → orders → completed / cancelled), and the two averages. A zero denominator prints `-`.
- An invalid month format exits with status 2.

## 4. Expected Results (Seed Data, verified)

- 43 requests, 29 accepted (67.4%); 29 orders, 23 completed (79.3%), 3 cancelled (10.3%), 3 pending.
- Completed orders: average 1.00 days from request to order; average discount 8.75% (0.0875).
- 11 months are returned (2025-12 to 2026-10). Month `2026-02`: 6 requests, 6 orders, 6 completed.

## 5. Acceptance Criteria

- The monthly columns add up to 43 requests and 29 orders.
- Completion rate is 79.3% to one decimal place.
- A month with no completed orders (for example `2026-09`) prints `-` for days and discount without an error.
- `ACCEPTED` requests equal orders (29 = 29).
