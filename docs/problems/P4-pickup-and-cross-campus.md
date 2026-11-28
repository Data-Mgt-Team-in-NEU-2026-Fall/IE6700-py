# P4 Pickup Points and Cross-Campus Transactions

- **Owner**: Kun Yu (suggested, can be changed)
- **Status**: Implemented

## 1. Business Question

Do buyers and sellers come from the same campus? Which pickup points are used most, and does every order use an active pickup point owned by the item's seller?

## 2. Data Needed

A single query returns the orders grouped by buyer campus, seller campus, and pickup point (id, name, owner, active flag), with the number of orders and the number of orders whose pickup point is owned by the item's seller. Campuses, users, and pickup points are linked through ids, never names. No parameters. The SQL is written in `src/ie6700/analytics/p4_pickup_and_cross_campus.py`.

## 3. Python Analysis

- Cross-campus orders = sum of `orders` where `buyerCampus` differs from `sellerCampus`; print the count and share.
- Campus matrix = sum of `orders` by (`buyerCampus`, `sellerCampus`), with row and column totals.
- Top N pickup points (default 5, option `--top`) = sum of `orders` by `pickupPointId`, ties by name; show whether each is active. Never merge points that share a name.
- Ownership check = sum of `ownedBySeller` ÷ sum of `orders`.

## 4. Expected Results (Seed Data, verified)

- 29 orders; 22 cross-campus (75.9%); the matrix cells add up to 29.
- Top 5 by `pickupPointId`: Library entrance (Ethan) 3, Student Union lobby (Sophia) 3, then Library entrance (Leo), Library entrance (Max), Library entrance (Noah) with 2 each. All are active.
- All 29 orders use an active pickup point owned by the item's seller.

## 5. Acceptance Criteria
    
- The matrix total, the cross-campus plus same-campus count, and the ownership denominator are all 29.
- Same-named pickup points stay separate in the Top N table.
- Ownership result is 29 ÷ 29.
