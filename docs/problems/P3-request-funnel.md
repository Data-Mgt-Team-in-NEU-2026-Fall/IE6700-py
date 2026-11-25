# P3 购买请求转化漏斗

- **负责人**：Yuan Xia（建议，可调整）
- **状态**：未开始
- **参考**：`mysql/queries.sql` 1.3（我的购买请求）、6.3–6.6（请求、接受、完成、取消的写法）、7.2（状态统计）、7.7（请求到订单的转化率）

## 1. 业务问题

平台上有多少购买请求最终变成了订单？订单里有多少完成，有多少取消？成交价比标价低多少？

## 2. 设计目标

1. 统计漏斗：购买请求按状态计数；订单按状态计数；计算接受率、完成率、取消率。
2. 对已完成的订单计算：从购买请求日期到订单日期的天数；成交价相对标价的平均折扣，即 `1 − agreedPrice ÷ askingPrice` 的均值。
3. 支持按月份筛选（按请求日期）。不给月份时统计全部。
4. 分母为 0 时，比例输出 `—`，不报错。

## 3. 涉及的表

- `PurchaseRequest`：`purchaseRequestDate`、`status`、`itemId`
- `TransactionOrder`：`transactionDate`、`agreedPrice`、`status`、`purchaseRequestId`
- `SecondhandItem`：`askingPrice`

## 4. 嵌入查询

| 编号 | 用途 | 参数 | 主要表 | 返回列 |
| --- | --- | --- | --- | --- |
| Q1 | 购买请求按状态计数（可按月份筛选） | 月份（可空） | PurchaseRequest | status, requestCount |
| Q2 | 订单按状态计数 | 无 | TransactionOrder | status, orderCount |
| Q3 | 已完成订单的天数与折扣 | 无 | TransactionOrder, PurchaseRequest, SecondhandItem | purchaseRequestId, daysToOrder, discount |
| Q4 | 按月的请求数与订单数 | 无 | PurchaseRequest, TransactionOrder | month, requests, orders |

## 5. 分析与输出

- 接受率 = `ACCEPTED` 请求数 ÷ 全部请求数；完成率 = `COMPLETED` 订单数 ÷ 全部订单数；取消率 = `CANCELLED` 订单数 ÷ 全部订单数。
- 对 Q3 的结果求平均天数和平均折扣。
- 输出漏斗表（请求 → 接受 → 订单 → 完成 / 取消）、按月表、折扣与天数两行摘要。

## 6. 结果预期（种子数据）

- 购买请求 43 条：`PENDING` 10，`ACCEPTED` 29，`REJECTED` 4。接受率 29 ÷ 43 = 67.4%。
- 订单 29 条：`PENDING` 3，`COMPLETED` 23，`CANCELLED` 3。完成率 23 ÷ 29 = 79.3%，取消率 3 ÷ 29 = 10.3%。
- 已完成的 23 笔订单：从请求到下单平均 1.00 天；成交价相对标价的平均折扣为 8.75%（0.0875）。
- `ACCEPTED` 请求数（29）与订单数（29）相等。应用中应核对每笔订单都对应一条 `ACCEPTED` 请求，这一点需要在测试中确认。

## 7. 验收标准

- 请求状态计数之和为 43；订单状态计数之和为 29。
- 完成率在一位小数上为 79.3%。
- 没有订单的月份，比例显示 `—`，程序不报错。
- 不给月份参数时，结果与不做筛选的全量统计一致。

## 8. 不做的事

- 不做预测模型，只做历史比例。
- 不处理订单状态的修改。

## 9. 参考

`queries.sql` 1.3、6.3–6.6、7.2、7.7。
