# P1 商品搜索与价格概览

- **负责人**：Kun Yu（建议，可调整）
- **状态**：未开始
- **参考**：`mysql/queries.sql` 2.2（浏览与筛选）、2.3（商品详情）、7.6（类别统计）

## 1. 业务问题

买家想按类别、价格、校园、标签或关键词找在售商品；同时想知道每个类别的价格水平，判断一件商品的标价是否合理。

## 2. 设计目标

1. 搜索支持可选条件：顶层类别（包含子类）、价格下限、价格上限、卖家所在校园、标签名、标题关键词。没有给出的条件不参与过滤。
2. 只返回 `status = 'AVAILABLE'` 的商品，结果按价格从低到高排列。
3. 分析：每个顶层类别的在售数量、均价、最低价、最高价；在售商品中最常见的 5 个标签。
4. 价格下限大于上限时报错，不静默返回空结果。
5. 所有用户输入都通过参数绑定传入。

## 3. 涉及的表

- `SecondhandItem`：`itemId`、`title`、`askingPrice`、`status`、`categoryId`、`sellerId`
- `ItemCategory`：`categoryId`、`categoryName`、`parentCategoryId`（自关联，用来找顶层类别）
- `ItemTags`、`ItemTag`：标签关联与标签名
- `User`、`Campus`：卖家所在校园

## 4. 嵌入查询

| 编号 | 用途 | 参数 | 主要表 | 返回列 |
| --- | --- | --- | --- | --- |
| Q1 | 搜索在售商品，可选条件用 `(%s IS NULL OR …)` 形式 | 类别、价格下限、价格上限、校园、标签、关键词 | SecondhandItem, ItemCategory, User, Campus, ItemTags, ItemTag | itemId, title, askingPrice, categoryName, campusName |
| Q2 | 每个在售商品及其顶层类别，供 Python 聚合 | 无 | SecondhandItem, ItemCategory（自关联） | topCategory, askingPrice |
| Q3 | 在售商品的标签使用次数 | 返回条数 N | ItemTags, ItemTag, SecondhandItem | tagName, useCount |
| Q4 | 在售商品按卖家校园计数 | 无 | SecondhandItem, User, Campus | campusName, itemCount |

顶层类别的写法：`COALESCE(parent.categoryName, child.categoryName)`，用 `LEFT JOIN` 连到父类别。

## 5. 分析与输出

- Q2 的结果在 Python 里按顶层类别分组，算出在售数、均价、最低价、最高价，按在售数从多到少排序。
- Q3 的 N 固定为 5。Q4 的结果直接输出。
- 搜索结果以表格输出；分析部分输出类别汇总表和标签、校园两个小表。

## 6. 结果预期（种子数据）

- 商品共 40 件：`AVAILABLE` 13，`RESERVED` 3，`SOLD` 23，`REMOVED` 1。在售商品为 13 件。
- 按顶层类别（在售数 / 均价 / 最低–最高）：

| 顶层类别 | 在售数 | 均价 | 价格范围 |
| --- | --- | --- | --- |
| Electronics | 4 | 33.25 | 0.00–95.00 |
| Other | 2 | 58.50 | 22.00–95.00 |
| Sports & Outdoors | 2 | 112.50 | 65.00–160.00 |
| Furniture | 2 | 44.00 | 18.00–70.00 |
| Clothing | 1 | 8.00 | 8.00 |
| Kitchen & Dorm | 1 | 40.00 | 40.00 |
| Textbooks | 1 | 50.00 | 50.00 |

- 按卖家校园计数：Main Campus 7，West Campus 2，South Campus 2，East Campus 1，North Campus 1。
- 不带任何条件的搜索返回 13 行。

## 7. 验收标准

- 不带条件的搜索返回 13 行，且按价格升序。
- 类别在售数之和等于 13；校园计数之和等于 13。
- 设置类别为 Electronics 时，结果都属于 Electronics 或它的子类。
- 价格下限大于上限时，程序报错并以非零状态退出。

## 8. 不做的事

- 不做分页界面、图片展示。
- 关键词搜索用 `LIKE` 即可，不建全文索引。

## 9. 参考

`queries.sql` 2.2、2.3、7.6。
