# P6 Trust Analysis of Reviews and Reports

- **Owner**: Yuan Xia (suggested, can be changed)
- **Status**: Not started

## 1. Business Question

How good are the reviews, how quickly are reports handled, and are the most-reported users also the lowest rated or already suspended?

## 2. Data Needed

A single query returns one row per user: account status; the number of reports against the user (reports on the user's items plus reports on orders for the user's items); how many of those were handled (`RESOLVED` or `DISMISSED` with `handledAt` set) and the total days they took; and the user's received reviews: published count, rating total, flagged count. Users without reports or reviews show 0. No parameters. Rows are sorted by reports, then user id.

## 3. Python Analysis

- Overall average rating = total `ratingSum` ÷ total `publishedReviews`; total flagged reviews.
- Average handling days = total `handledDaysSum` ÷ total `handledCount`.
- Top N most-reported users (default 5, option `--top`), ties by user id, with account status and own average rating (`-` when they have no published reviews).
- Compare the average rating of users reported at least twice with that of users never reported.

## 4. Expected Results (Seed Data, verified)

- 30 users (28 `ACTIVE`, 2 `SUSPENDED`: users 25 and 26); 30 reports, all attached to a seller.
- 27 published reviews with 99 rating points, average 3.67; 6 flagged reviews.
- 17 handled reports (`RESOLVED` or `DISMISSED`) with 79 days in total, average 4.65 days.
- Top 5 most reported (3 reports each, ties by id): users 18, 22, 23, 26, 27. User 26 is `SUSPENDED`.

## 5. Acceptance Criteria

- `reportedCount` adds up to 30; `publishedReviews` adds up to 27.
- Average rating is 3.67 to two decimal places; average handling days is 4.65.
- Only reports with `handledAt` set count toward handling days.
