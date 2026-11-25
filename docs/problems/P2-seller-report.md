# P2 卖家经营报告

- **负责人**：Eduardo Gonzalez（建议，可调整）
- **状态**：未开始
- **参考**：`mysql/queries.sql` 1.2（我的商品）、1.4（我的订单）、1.6（收到的评价）、3.1（待处理请求）、3.3（需要处理的商品）

## 1. 业务问题

卖家想看一份自己的经营报告：商品处于什么状态，成交了多少钱，买家给了什么评分，还有哪些购买请求等待回复。

## 2. 设计目标

1. 输入一个卖家的 `userId`。不存在的卖家报错并以非零状态退出。
2. 报告包括：商品按状态计数；已完成订单数与成交额；已发布卖家评价的条数与平均分；待处理的购买请求数（只统计该卖家自己的商品）。
3. 分析：成交率 = `SOLD` 商品数 ÷（全部商品数 − `REMOVED` 商品数）；已完成订单的平均成交额；评分的 1–5 星分布。
4. 评价只统计 `reviewStatus = 'PUBLISHED'` 的记录。
5. 所有查询都用参数绑定传入 `userId`。

## 3. 涉及的表

- `User`：卖家是否存在
- `SecondhandItem`：商品状态与 `sellerId`
- `PurchaseRequest`：购买请求与状态
- `TransactionOrder`：订单状态与 `agreedPrice`
- `TransactionReview`、`SellerReview`：卖家评价的评分、状态与收件人（`recipientId`）

## 4. 嵌入查询

| 编号 | 用途 | 参数 | 主要表 | 返回列 |
| --- | --- | --- | --- | --- |
| Q1 | 商品按状态计数 | sellerId | SecondhandItem | status, itemCount |
| Q2 | 已完成订单数与成交额 | sellerId | TransactionOrder, PurchaseRequest, SecondhandItem | completedCount, revenue |
| Q3 | 已发布卖家评价的条数、平均分、分布 | sellerId | SellerReview, TransactionReview | rating, reviewCount |
| Q4 | 待处理购买请求数 | sellerId | PurchaseRequest, SecondhandItem | pendingCount |

## 5. 分析与输出

- Python 计算成交率、平均成交额，以及评分的平均分。
- 输出一份报告：商品状态表、成交摘要、评分分布、待处理请求数。
- 卖家不存在时输出一行错误并以状态 1 退出。

## 6. 结果预期（种子数据）

- **卖家 27（Ethan）**：商品全部为 `SOLD`，3 件；已完成订单 3 笔，成交额 70.00；已发布卖家评价 1 条，平均分 1.00；成交率 3 ÷ 3 = 100%。
- **卖家 29（Noah）**：商品全部为 `SOLD`，2 件；已完成订单 2 笔，成交额 480.00；没有已发布的卖家评价。
- 按已完成订单数（同数则按成交额）排名前三：27（3 笔，70.00）、29（2 笔，480.00）、23（2 笔，160.00）。
- 待处理请求数：由 Q4 计算，结果以沙箱查询为准（本次没有单独核对）。

## 7. 验收标准

- 卖家 27 的报告必须显示成交额 70.00、平均分 1.00。
- 商品状态计数之和等于该卖家的商品总数。
- 成交额等于该卖家已完成订单 `agreedPrice` 之和。
- 只有 `PUBLISHED` 的评价参与平均分计算。

## 8. 不做的事

- 不做收入趋势图、按月的预测。
- 不修改任何订单或请求状态。

## 9. 参考

`queries.sql` 1.2、1.4、1.6、3.1、3.3。
