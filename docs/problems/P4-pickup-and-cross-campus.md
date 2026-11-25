# P4 取货点与跨校园交易

- **负责人**：Kun Yu（建议，可调整）
- **状态**：未开始
- **参考**：`mysql/queries.sql` 1.4（订单的跨校园标记）、3.2（卖家的取货点）、7.4（校园对比）

## 1. 业务问题

买卖双方是否来自同一所校园？交易集中在哪些取货点？取货点是否都由卖家自己提供？

## 2. 设计目标

1. 统计跨校园订单数与占比：买家所在校园不等于卖家所在校园。
2. 校园交易矩阵：买家校园 × 卖家校园，每格为订单数。
3. 取货点使用次数 Top N（N 为参数，默认 5）。统计按 `pickupPointId`，不按名称，因为同名的取货点可能属于不同卖家。输出每个取货点是否启用。
4. 检查取货点是否属于该商品的卖家（`PickupPoint.ownerId = SecondhandItem.sellerId`）。
5. 所有校园与用户的关联都通过外键 JOIN，不靠名称匹配。

## 3. 涉及的表

- `TransactionOrder`：`pickupPointId`、`purchaseRequestId`
- `PickupPoint`：`pickupPointName`、`ownerId`、`activeStatus`
- `PurchaseRequest`、`SecondhandItem`：找到商品和卖家
- `User`：买家与卖家，各自的 `campusId`
- `Campus`：校园名称

## 4. 嵌入查询

| 编号 | 用途 | 参数 | 主要表 | 返回列 |
| --- | --- | --- | --- | --- |
| Q1 | 跨校园订单数与总数 | 无 | TransactionOrder, PurchaseRequest, SecondhandItem, User, Campus | crossCampus, total |
| Q2 | 校园交易矩阵 | 无 | 同上 | buyerCampus, sellerCampus, orderCount |
| Q3 | 取货点使用次数 Top N | N | TransactionOrder, PickupPoint | pickupPointId, pickupPointName, activeStatus, orderCount |
| Q4 | 取货点归属检查 | 无 | TransactionOrder, PickupPoint, PurchaseRequest, SecondhandItem | ownedBySeller, total |

## 5. 分析与输出

- Q1 算出跨校园占比。Q2 的结果在 Python 里整理成矩阵。
- Q3 按使用次数排序，同数时按名称排序。
- 输出：跨校园摘要、校园矩阵、取货点 Top N 表、归属检查的一行结论。

## 6. 结果预期（种子数据）

- 订单 29 笔，其中跨校园 22 笔，占 75.9%。
- 取货点使用 Top 5（按 ID 统计）：
  - Library entrance (Ethan)：3 笔，启用
  - Student Union lobby (Sophia)：3 笔，启用
  - Library entrance (Leo)、Library entrance (Max)、Library entrance (Noah)：各 2 笔，启用
- 29 笔订单使用的取货点全部启用（`activeStatus = 1`）。
- 29 笔订单的取货点全部属于该商品的卖家（29 ÷ 29）。
- 校园矩阵各格之和为 29。

## 7. 验收标准

- 矩阵各格之和等于订单总数 29；跨校园数 + 同校园数 = 29。
- 同名取货点在输出中分开显示，不合并计数。
- 归属检查的结果为 29 ÷ 29。

## 8. 不做的事

- 不做地图、距离计算。`Address` 虽然有经纬度，本题不用。
- 不修改取货点或订单。

## 9. 参考

`queries.sql` 1.4、3.2、7.4。
