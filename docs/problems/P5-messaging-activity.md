# P5 会话与消息活跃度

- **负责人**：Eduardo Gonzalez（建议，可调整）
- **状态**：未开始
- **参考**：`mysql/queries.sql` 4.1（我的会话）、4.2（消息列表）、4.4（商品的会话）、4.5（查找已有会话）

## 1. 业务问题

买家咨询一件商品后，卖家多久回复？有没有买家发起的会话始终没有等到卖家回复？

## 2. 设计目标

1. 统计会话数、消息数，以及每个会话的平均消息数。
2. 首次回复时间：对会话创建者不是卖家的会话，计算创建者的首条消息到卖家首条消息之间的分钟数。
3. 未回复的会话：卖家在该会话中从未发言的会话。
4. 列出某件商品的会话，每个会话带消息数（商品 ID 作为参数）。
5. 只读，不创建会话，不发消息。

## 3. 涉及的表

- `Conversation`：`conversationId`、`itemId`、`creatorId`、`createdAt`
- `Message`：`conversationId`、`authorId`、`sentAt`
- `SecondhandItem`：`sellerId`
- `ConversationParticipant`：参与者（用于核对，不是必需）

## 4. 嵌入查询

| 编号 | 用途 | 参数 | 主要表 | 返回列 |
| --- | --- | --- | --- | --- |
| Q1 | 会话数、消息数、每会话平均消息数 | 无 | Conversation, Message | conversations, messages |
| Q2 | 每个会话里，创建者的首条消息与卖家的首条消息 | 无 | Conversation, SecondhandItem, Message | conversationId, creatorFirst, sellerFirst |
| Q3 | 卖家从未发言的会话 | 无 | Conversation, SecondhandItem, Message（`NOT EXISTS`） | conversationId, itemId |
| Q4 | 某件商品的会话及消息数 | itemId | Conversation, Message | conversationId, creatorId, messageCount |

Q2 可以用 `WITH` 公共表表达式，每个会话一行，用 `MIN(CASE WHEN … END)` 取首条消息时间。

## 5. 分析与输出

- Q2 的结果在 Python 里筛掉创建者本人就是卖家的会话，然后计算首次回复的平均分钟数（取整到一位小数）。
- 输出：会话与消息摘要、首次回复摘要、未回复会话列表、按商品查询的结果表。

## 6. 结果预期（种子数据）

- 会话 59 个，消息 326 条，每个会话平均 5.53 条（326 ÷ 59）。
- 会话创建者不是卖家的会话有 58 个，且全部由买家发起。这 58 个会话中，卖家都有回复（58 ÷ 58）。
- 这 58 个会话的首次回复平均时间为 178.3 分钟（约 3 小时）。
- 未回复的会话（Q3）：对于买家发起的会话，应该为 0。

## 7. 验收标准

- 会话数为 59，消息数为 326。
- 平均消息数为 5.53。
- 首次回复的统计只包含创建者不是卖家的会话，数量为 58。
- 按商品查询时，返回的会话都属于该商品。

## 8. 不做的事

- 不做情感分析、关键词分析。
- 首次回复时间只输出平均值，不做分布或分位数。

## 9. 参考

`queries.sql` 4.1、4.2、4.4、4.5。
