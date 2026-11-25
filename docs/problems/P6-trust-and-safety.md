# P6 评价与举报的信任分析

- **负责人**：Yuan Xia（建议，可调整）
- **状态**：未开始
- **参考**：`mysql/queries.sql` 1.6（收到的评价）、5.4（我的举报）、5.5（举报队列）、7.9（举报统计）、7.10（被举报最多的用户）

## 1. 业务问题

平台上的评价质量如何？举报集中在哪些原因上？处理一条举报要多久？被举报最多的用户是否已经被停用？

## 2. 设计目标

1. 已发布评价（`PUBLISHED`）的评分分布（1–5 星）与平均分；被标记（`FLAGGED`）和被移除（`REMOVED`）的评价数。
2. 举报按原因（`reason`）计数，按状态（`status`）计数。
3. 已处理的举报（`RESOLVED`、`DISMISSED`）的平均处理天数，即 `handledAt` 与 `reportDate` 相差的天数。
4. 被举报次数 Top 5 的用户。被举报包括：商品举报中商品的卖家，以及订单举报中订单商品的卖家。输出每个用户的账号状态。
5. 所有查询只读，并用参数绑定传入 Top N。

## 3. 涉及的表

- `TransactionReview`：`rating`、`reviewStatus`、`recipientId`
- `BuyerReview`、`SellerReview`：评价的类型
- `Report`：`reason`、`status`、`reportDate`、`handledAt`
- `ItemReport`、`TransactionReport`：举报的对象
- `SecondhandItem`、`TransactionOrder`、`PurchaseRequest`：找到被举报的卖家
- `User`：`accountStatus`

## 4. 嵌入查询

| 编号 | 用途 | 参数 | 主要表 | 返回列 |
| --- | --- | --- | --- | --- |
| Q1 | 已发布评价的评分分布 | 无 | TransactionReview | rating, reviewCount |
| Q2 | 评价按状态计数 | 无 | TransactionReview | reviewStatus, reviewCount |
| Q3 | 举报按原因、状态计数 | 无 | Report | reason, status, reportCount |
| Q4 | 已处理举报的平均处理天数 | 无 | Report | status, avgDays |
| Q5 | 被举报最多的用户 Top N | N | ItemReport, TransactionReport, SecondhandItem, TransactionOrder, PurchaseRequest, User | userId, reportedCount, accountStatus |

Q5 用 `UNION ALL` 把两类举报的卖家合在一起，再按用户汇总。

## 5. 分析与输出

- 对 Q1 求平均分。Q3 与 Q4 直接输出。
- 对 Q5 的结果按被举报次数排序，同数时按用户 ID 排序。
- 输出：评价摘要（分布与平均分）、举报原因表、举报状态表、处理天数表、被举报用户 Top N 表。

## 6. 结果预期（种子数据）

- 评价 33 条：`PUBLISHED` 27，`FLAGGED` 6，`REMOVED` 0。
- 已发布评分：1 星 3 条，2 星 2 条，3 星 6 条，4 星 6 条，5 星 10 条。平均分 3.67（99 ÷ 27）。
- 举报 30 条，按原因：`SCAM` 11，`HARASSMENT` 6，`SPAM` 5，`WRONG_DESCRIPTION` 3，`COUNTERFEIT` 3，`INAPPROPRIATE_CONTENT` 2，`OTHER` 0。
- 举报状态：`RECEIVED` 9，`UNDER_REVIEW` 4，`RESOLVED` 8，`DISMISSED` 9。未处理（`RECEIVED` + `UNDER_REVIEW`）共 13 条。
- 已处理举报的平均天数：`RESOLVED` 为 5.13 天，`DISMISSED` 为 4.22 天。
- 用户 30 人：`ACTIVE` 28，`SUSPENDED` 2。
- 被举报次数 Top 5 的用户：由 Q5 计算，本次没有单独核对。

## 7. 验收标准

- 已发布评分的人数之和为 27；评价状态之和为 33。
- 举报原因计数之和为 30；举报状态计数之和为 30。
- 已处理举报的平均天数只统计 `handledAt` 不为空的记录。
- 平均分在两位小数上为 3.67。

## 8. 不做的事

- 不做自动封禁或修改评价、举报状态。
- 不做文本分析，不判断评价内容是否违规。

## 9. 参考

`queries.sql` 1.6、5.4、5.5、7.9、7.10。
