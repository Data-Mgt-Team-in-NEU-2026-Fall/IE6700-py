# MySQL 本地测试环境

这一阶段把同学提供的两套 SQL 合并成一个符合 `RelationalModel.md` 的建库脚本，并准备样例数据和独立的 MySQL Docker 测试节点。
启动和 reset 都只初始化 MySQL 自带的系统数据库，不会自动建库或导入数据；建库和导入见下文"导入"。

## 文件结构

```text
03 MySQL Implementation/
├── marketplace.sql         # 合并后的建库脚本（23 张表，只含结构）
├── queries.sql             # 常用查询，按用例编号分组
├── delete_rules.sql        # 删除规则测试（27 条，输出 PASS/FAIL）
├── db.sh                   # 在容器里导入、查询、测试、进入客户端
├── finals/
│   └── MySQL Implementation.pdf   # 本阶段的 PDF 交付物
├── seed/                   # 样例数据，按编号顺序导入
│   ├── 01_identity.sql                  # 校园、角色、用户（改编自 archive/02_data.sql）
│   ├── 02_marketplace.sql               # 商品、购买请求、取货点、订单（新写）
│   └── 03_messaging_reviews_reports.sql # 消息、评价、举报（改编自 archive/02_data.sql）
├── archive/                # 同学提供的原件，已归档，内容不再修改
│   ├── 01_schema.sql
│   ├── 02_data.sql
│   ├── 03_queries.sql
│   └── seattle_marketplace_updated_with_sample_data.sql
├── docker-compose.yaml
├── reset.sh                # 重置容器和数据卷，--load 同时导入数据
├── import_local.sh         # 非 Docker：一次性导入到本地 MySQL 8.x 实例
├── .env.example
└── .gitignore
```

原件来自 `/home/newbe36524/Downloads/`，原样放在 `archive/`，以只读方式挂载到容器的 `/workspace/archive/`。
`marketplace.sql` 和 `seed/` 同样只读挂载到 `/workspace/`。

## 合并说明

原来两套脚本不能依次运行：`01_schema.sql` 建 `secondhand_marketplace`（用户、消息、评价、举报），
`seattle_marketplace_updated_with_sample_data.sql` 建 `seattle_marketplace`（商品、购买请求、订单），
两边都有 `Campus`、`User`，角色表一个叫 `UserRole`、一个叫 `Role`，id 类型也不同。`marketplace.sql` 的处理：

- 统一成 `seattle_marketplace` 库，`Campus`、`User`、`Role` 用 seattle 版，`UserHasRole` 引用 `Role`，所有 id 为 `INT`。
- 01 里只写成注释的跨图关联改成真实外键（会话、举报、评价指向商品和订单）。
- `Report` 按设计增加 `resolutionNote`、`handledAt`、`handledById`，`status` 限定为
  `RECEIVED`、`UNDER_REVIEW`、`RESOLVED`、`DISMISSED`；`reviewDate`、`reportDate` 为 `DATE`。
- 保留原件中设计没有写、但有用的唯一约束：`uq_email`、`uq_roleName`、`uq_buyer_transaction`、`uq_seller_transaction`。

样例数据（共 23 张表、约 1000 行）：

- `01_identity.sql`：由 `archive/02_data.sql` 改编。补 `emailDomain`、`accountStatus`（2 个用户为 `SUSPENDED`），`UserRole` 改 `Role`，`dateJoined` 改 `DATE`。
- `02_marketplace.sql`（新写）：40 件商品、10 个分类、43 个购买请求、29 笔订单、10 个地址、28 个取货点。
  取货点属于卖家：每个卖家都有自己常用的取货点，有的还有第二个（其中一个已关闭）；每笔订单使用该订单卖家自己的取货点。
  订单 1–17、20–25 已完成，18、26、27 待取货，19、28、29 已取消；商品状态和订单状态对应（已完成为 `SOLD`，待取货为 `RESERVED`，已取消回到 `AVAILABLE`）。
  每件在售商品至少有一个购买请求和收藏。
- `03_messaging_reviews_reports.sql`：由 `archive/02_data.sql` 改编并补充，共 59 个会话、324 条消息、33 条评价、30 条举报。
  对原数据的修正：
  - 消息、会话、举报的时间不早于所涉商品和订单，也不早于用户加入时间；
  - 每个会话都包含商品的卖家（原来缺的补了参与者和一条回复）；
  - 评价的作者和被评人与订单的买家、卖家一致；原来没挂在任何订单上的评价 25–30，改为订单 20–25 的买家评价；
  - 商品举报的举报人不是该商品的卖家，订单举报的举报人是该订单的买家或卖家；
  - `Report.status`、`Report.reason`、`reviewStatus` 换成大写枚举值；`RECEIVED` 的处理字段都为空，`UNDER_REVIEW` 只有处理人，`RESOLVED`、`DISMISSED` 有处理人、时间和备注，处理人是管理员用户。
  新增：每笔订单和 10 个待处理请求各一个会话，卖家评价 31–33，举报 25–30。
- seattle 原件里的 2 个用户和 3 件商品样例与 `02_data.sql` 的用户编号冲突，没有导入；它们仍在 `archive/` 中。

## 查询

`queries.sql` 按 `00 init/user-cases.md` 的用例编号组织，开头的参数用 `SET @变量` 设置，整份文件可直接运行（参数可以改）：

```bash
./db.sh queries
```

| 部分 | 内容 |
| --- | --- |
| 1 | 登录与个人记录：校园邮箱登录、我的商品、请求、订单、收藏、收到和写出的评价 |
| 2 | 浏览与筛选（分类含子类、价格、校园、标签、关键词）、商品详情、收藏、购买请求 |
| 3 | 卖家：待处理请求、常用交接地点、需要处理的商品 |
| 4 | 会话：我的会话和是否可发言、消息列表、参与者、查找已有会话 |
| 5 | 订单详情、缺少的评价、举报记录、管理员举报队列 |
| 6 | 写入：发布商品、收藏、提购买请求、接受请求并生成订单、确认完成、取消订单、评价、举报、下架、处理举报、停用标签 |
| 7 | 管理员概览：状态统计、按月活跃度、校园对比、热门卖家和分类、转化率、举报统计 |
| 8 | 数据健康检查，每条应返回 0 |

第 6 部分的每个例子都放在 `START TRANSACTION … ROLLBACK` 中，运行后数据不变，只是自增编号会往后走；
要保留某项改动，把 `ROLLBACK` 改成 `COMMIT`。评价方向：`BuyerReview` 是对买家的评价（卖家写），`SellerReview` 是对卖家的评价（买家写）。

## 类型与枚举

课程项目只处理 ASCII 数据，服务器和数据库的字符集与排序规则统一为 `utf8mb4` / `utf8mb4_0900_ai_ci`
（`docker-compose.yaml` 和 `CREATE DATABASE` 都显式写明）。邮箱和域名列保持原样。

| 类别 | 列 | 类型 |
| --- | --- | --- |
| 主键和外键 | 所有 `…Id` | `INT UNSIGNED` |
| 金额 | `askingPrice`、`offeredPrice`、`agreedPrice` | `DECIMAL(8,2)`，最大 999,999.99 |
| 小整数 | `rating`、`displayOrder` | `TINYINT UNSIGNED`（评分另有 1–5 的 CHECK） |
| 年份 | `yearAcquired` | `YEAR` |
| 布尔 | `activeStatus` | `BOOLEAN NOT NULL DEFAULT TRUE` |
| 地址 | `state` / `zipCode` / `city` / 街道 | `CHAR(2)` / `VARCHAR(10)` / `VARCHAR(50)` / `VARCHAR(100)` |
| 姓名和电话 | `firstName`、`lastName` / `phone` | `VARCHAR(50)` / `VARCHAR(20)` |
| 名称 | 校园、分类、标签、角色、取货点、商品标题 | `VARCHAR(80)`、`(50)`、`(30)`、`(30)`、`(80)`、`(120)` |
| 文本 | 商品描述、消息 / 评价、举报说明和处理备注 / 请求留言 / 分类和取货点说明 | `VARCHAR(2000)` / `(1000)` / `(500)` / `(255)`，不再使用 `TEXT` |

可以枚举的取值都用 `ENUM`，非法值会被拒绝，原来重复的状态 `CHECK` 已去掉：

| 列 | 取值 | 默认值 |
| --- | --- | --- |
| `SecondhandItem.status` | `AVAILABLE`、`RESERVED`、`SOLD`、`REMOVED` | `AVAILABLE` |
| `SecondhandItem.condition` | `NEW`、`LIKE_NEW`、`GOOD`、`FAIR`、`POOR` | 必须填写 |
| `PurchaseRequest.status` | `PENDING`、`ACCEPTED`、`REJECTED` | `PENDING` |
| `TransactionOrder.status` | `PENDING`、`COMPLETED`、`CANCELLED` | `PENDING` |
| `User.accountStatus` | `ACTIVE`、`SUSPENDED` | `ACTIVE` |
| `TransactionReview.reviewStatus` | `PUBLISHED`、`FLAGGED`、`REMOVED` | `PUBLISHED` |
| `Report.status` | `RECEIVED`、`UNDER_REVIEW`、`RESOLVED`、`DISMISSED` | `RECEIVED` |
| `Report.reason` | `SCAM`、`SPAM`、`INAPPROPRIATE_CONTENT`、`HARASSMENT`、`WRONG_DESCRIPTION`、`COUNTERFEIT`、`OTHER` | `OTHER` |

注意：MySQL 里不带默认值的 `NOT NULL` 枚举，漏填时会悄悄取第一个值而不报错，
所以 `condition` 写成可空枚举加 `CHECK (condition IS NOT NULL)`，漏填会报错，不会被当成 `NEW`。
角色、分类、标签是会被维护的数据，仍然放在各自的表里，没有做成枚举。

## 删除规则

所有 36 个外键都写明 `ON DELETE`；`ON UPDATE` 保持默认的 `RESTRICT`（主键都是不会改的代理 id）。
原则：历史数据和基础数据一律禁止删除，不再使用时改状态；只有"随父行存在、离开父行没有意义"的从属行才级联删除。

| 规则 | 外键 | 原因 |
| --- | --- | --- |
| 禁止删除（`RESTRICT`，25 个） | 校园、角色、分类、标签、商品、购买请求、订单、地址、有消息的会话、评价和举报所引用的一切；用户被商品、请求、消息、评价、举报引用 | 交易、会话、评价、举报要保留供追溯；下架用 `REMOVED`，封禁用 `SUSPENDED`，标签用 `activeStatus = 0`，订单用 `CANCELLED` |
| 级联删除（`CASCADE`，11 个） | 商品 → 图片、标签关联；商品 → 收藏；用户 → 收藏、角色关联、自己的取货点；空会话 → 参与者；评价 → `BuyerReview`/`SellerReview` 行；举报 → `ItemReport`/`TransactionReport` 行 | 这些行只因父行存在，没有父行就没有意义 |

两个要点：取货点随用户级联，但被订单引用的取货点仍然禁止删除，所以用过的取货点不会丢；会话里有消息时不能删除，保证历史消息保留。
`delete_rules.sql` 对每条规则做一次删除并判断结果，在事务里运行，最后回滚：

```bash
./db.sh test
```

## 启动、重置和使用

数据库运行在 Docker 容器里，镜像为 `mysql:8.4`（8.x 长期支持版），宿主机不需要安装 MySQL。
不想用 Docker 时，见下文"非 Docker 环境"。
需要 Docker Engine、Docker Compose v2.20 或更高版本以及 Bash。所有命令在本目录执行：

```bash
# 可选：自定义本地密码和端口。
cp .env.example .env

# 重置并导入：删除旧容器和数据卷，启动 MySQL，在容器内导入建库脚本和样例数据。
./reset.sh --load

./db.sh status     # 版本、表和行数
./db.sh queries    # 运行 queries.sql
./db.sh test       # 运行 delete_rules.sql，27 条规则各输出 PASS 或 FAIL
./db.sh shell      # 进入容器里的 mysql 客户端（已选中 seattle_marketplace）
```

| 命令 | 作用 |
| --- | --- |
| `./reset.sh` | 重置为空的 MySQL（不建库、不导入） |
| `./reset.sh --load` | 重置并导入 `marketplace.sql` 和 `seed/` |
| `./db.sh load` | 向空的节点导入；库已存在时会报"表已存在"，先重置 |
| `./db.sh queries` / `test` / `status` / `shell` | 查询、测试、状态、客户端 |

`marketplace.sql`、`seed/`、`queries.sql`、`delete_rules.sql`、`archive/` 以只读方式挂载到容器的 `/workspace/`，
`db.sh` 直接读取容器里的文件，不经过宿主机。首次运行会下载 `mysql:8.4` 镜像。
若数据卷是用其他版本（例如之前的 9.7）创建的，重置时会一并删除；MySQL 不能把数据目录降回旧版本，所以不要换镜像版本后复用旧卷。

重置脚本固定操作 `neu-ie6700-mysql` Compose 项目：先检查 Docker、配置及所需镜像，
再移除该项目的容器和 `mysql_data` 数据卷，重新启动 MySQL，并等待真实 SQL 健康检查通过。
这会删除本测试节点中的所有数据库和数据；`archive/` 原件保留。脚本不执行全局 Docker 清理命令，也不处理其他 Compose 项目。
脚本根据自身位置定位配置，也可以从仓库根目录运行：`"./03 MySQL Implementation/reset.sh"`。

从宿主机连接：地址 `127.0.0.1:3307`，用户名 `root`，密码为 `.env.example` 中的本地测试密码；
端口被占用时在 `.env` 里改 `MYSQL_PORT`。查看日志：`docker compose logs --tail 100 mysql`。

## 非 Docker 环境：导入本地 MySQL 8.x

已有本地 MySQL 8.x 服务器（8.0 及以上的 8.x 版本）时，可以不用 Docker，用 `import_local.sh` 一次性导入：

```bash
# 连接本地 127.0.0.1:3306，用户 root；密码未设置时脚本会提示输入一次。
./import_local.sh

# 指定主机、端口、用户；用 MYSQL_PWD 传入密码（不会出现在进程参数里）。
MYSQL_PWD='你的密码' ./import_local.sh -h 127.0.0.1 -P 3306 -u root

# 库已存在时替换它（会删除 seattle_marketplace 里的全部数据）。
./import_local.sh --drop-existing
```

脚本需要本机有 `mysql` 客户端。执行顺序与 `db.sh load` 相同：先 `marketplace.sql`，再 `seed/` 三个文件，
最后检查库里是否恰好有 23 张基础表。它做了以下保护：

- **版本检查**：服务器必须是 MySQL 8.x。MariaDB 会被拒绝，因为 `utf8mb4_0900_ai_ci` 排序规则只有 MySQL 8.x 提供。
- **不覆盖已有数据**：`seattle_marketplace` 已存在时直接停止，什么都不改；只有加 `--drop-existing` 才会删除重建。
- **出错即停**：导入中途出错时，脚本以非零状态退出，并提示数据库可能只导入了一部分，需要用 `--drop-existing` 重来。

脚本只导入，不运行 `queries.sql` 和 `delete_rules.sql`；要测试删除规则，可在导入后用客户端运行 `delete_rules.sql`。

## 停止

```bash
# 停止节点，保留数据库数据。
docker compose stop

# 删除容器与网络，保留数据库数据卷。
docker compose down
```
