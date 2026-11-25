# MySQL Local Test Environment

This phase merges the two SQL sets provided by teammates into one schema script that conforms to `RelationalModel.md`, and prepares sample data and a standalone MySQL Docker test node.
Starting and resetting initialize only MySQL's built-in system databases; they do not create the database or import data automatically. For creating the database and importing, see "Import" below.

## File Structure

```text
03 MySQL Implementation/
├── marketplace.sql         # Merged schema script (23 tables, structure only)
├── queries.sql             # Common queries, grouped by use-case number
├── delete_rules.sql        # Delete-rule tests (27 checks, output PASS/FAIL)
├── db.sh                   # Import, query, test, and open a client inside the container
├── finals/
│   └── MySQL Implementation.pdf   # PDF deliverable for this phase
├── seed/                   # Sample data, imported in numeric order
│   ├── 01_identity.sql                  # Campuses, roles, users (adapted from archive/02_data.sql)
│   ├── 02_marketplace.sql               # Items, purchase requests, pickup points, orders (newly written)
│   └── 03_messaging_reviews_reports.sql # Messages, reviews, reports (adapted from archive/02_data.sql)
├── archive/                # Originals provided by teammates, archived, no longer modified
│   ├── 01_schema.sql
│   ├── 02_data.sql
│   ├── 03_queries.sql
│   └── seattle_marketplace_updated_with_sample_data.sql
├── docker-compose.yaml
├── reset.sh                # Reset the container and data volume; --load also imports data
├── import_local.sh         # Non-Docker: one-shot import into a local MySQL 8.x instance
├── .env.example
└── .gitignore
```

The originals come from the raw SQL files provided by teammates. They are kept unchanged in `archive/` and mounted read-only into the container at `/workspace/archive/`.
`marketplace.sql` and `seed/` are likewise mounted read-only at `/workspace/`.

## Merge Notes

The two original script sets could not be run one after the other: `01_schema.sql` creates `secondhand_marketplace` (users, messages, reviews, reports),
and `seattle_marketplace_updated_with_sample_data.sql` creates `seattle_marketplace` (items, purchase requests, orders).
Both define `Campus` and `User`, one calls the role table `UserRole` and the other `Role`, and the id types differ. What `marketplace.sql` does:

- Unify on the `seattle_marketplace` database; `Campus`, `User`, and `Role` use the seattle version, `UserHasRole` references `Role`, and all ids are `INT`.
- Cross-graph relationships that were only written as comments in 01 become real foreign keys (conversations, reports, and reviews pointing to items and orders).
- `Report` gains `resolutionNote`, `handledAt`, and `handledById` as designed, and `status` is restricted to
  `RECEIVED`, `UNDER_REVIEW`, `RESOLVED`, `DISMISSED`; `reviewDate` and `reportDate` are `DATE`.
- Useful unique constraints from the originals that the design does not mention are kept: `uq_email`, `uq_roleName`, `uq_buyer_transaction`, `uq_seller_transaction`.

Sample data (23 tables, about 1000 rows in total):

- `01_identity.sql`: adapted from `archive/02_data.sql`. Adds `emailDomain` and `accountStatus` (2 users are `SUSPENDED`), changes `UserRole` to `Role`, and changes `dateJoined` to `DATE`.
- `02_marketplace.sql` (newly written): 40 items, 10 categories, 43 purchase requests, 29 orders, 10 addresses, 28 pickup points.
  Pickup points belong to sellers: every seller has their own usual pickup point, and some have a second one (one of which is closed); every order uses the pickup point of that order's own seller.
  Orders 1–17 and 20–25 are completed, 18, 26, and 27 are awaiting pickup, and 19, 28, and 29 are cancelled; item status matches order status (completed is `SOLD`, awaiting pickup is `RESERVED`, cancelled goes back to `AVAILABLE`).
  Every available item has at least one purchase request and one favorite.
- `03_messaging_reviews_reports.sql`: adapted from `archive/02_data.sql` and extended, with 59 conversations, 324 messages, 33 reviews, and 30 reports.
  Corrections made to the original data:
  - Message, conversation, and report times are not earlier than the item and order involved, nor earlier than the user's join date;
  - Every conversation includes the item's seller (where missing, a participant and a reply were added);
  - The author and subject of a review match the order's buyer and seller; reviews 25–30, which were not attached to any order, became buyer reviews for orders 20–25;
  - The reporter of an item report is not the item's seller, and the reporter of an order report is the order's buyer or seller;
  - `Report.status`, `Report.reason`, and `reviewStatus` use uppercase enum values; for `RECEIVED` all handling fields are empty, `UNDER_REVIEW` has only a handler, and `RESOLVED` and `DISMISSED` have a handler, a time, and a note, where the handler is an admin user.
  Added: one conversation for each order and for each of the 10 pending requests, seller reviews 31–33, and reports 25–30.
- The 2 users and 3 items in the seattle original were not imported because their user ids conflict with `02_data.sql`; they remain in `archive/`.

## Queries

`queries.sql` is organized by the use-case numbers in `00 init/user-cases.md`. The parameters at the top are set with `SET @variable`, and the whole file can be run as is (the parameters can be changed):

```bash
./db.sh queries
```

| Section | Content |
| --- | --- |
| 1 | Login and personal records: campus email login, my items, requests, orders, favorites, reviews received and written |
| 2 | Browse and filter (category including subcategories, price, campus, tag, keyword), item detail, favorites, purchase requests |
| 3 | Seller: pending requests, usual handoff locations, items needing action |
| 4 | Conversations: my conversations and whether I can post, message list, participants, find an existing conversation |
| 5 | Order detail, missing reviews, report history, admin report queue |
| 6 | Writes: post an item, favorite, make a purchase request, accept a request and create an order, confirm completion, cancel an order, review, report, remove an item, handle a report, deactivate a tag |
| 7 | Admin overview: status counts, monthly activity, campus comparison, popular sellers and categories, conversion rate, report statistics |
| 8 | Data health checks, each of which should return 0 |

Every example in section 6 is wrapped in `START TRANSACTION … ROLLBACK`, so the data is unchanged after running and only the auto-increment counters move forward;
to keep a change, replace `ROLLBACK` with `COMMIT`. Review direction: `BuyerReview` is a review of the buyer (written by the seller), and `SellerReview` is a review of the seller (written by the buyer).

## Types and Enums

The course project handles only ASCII data. The server and database character set and collation are unified as `utf8mb4` / `utf8mb4_0900_ai_ci`
(stated explicitly in both `docker-compose.yaml` and `CREATE DATABASE`). Email and domain columns are kept as they are.

| Category | Columns | Type |
| --- | --- | --- |
| Primary and foreign keys | all `…Id` | `INT UNSIGNED` |
| Money | `askingPrice`, `offeredPrice`, `agreedPrice` | `DECIMAL(8,2)`, maximum 999,999.99 |
| Small integers | `rating`, `displayOrder` | `TINYINT UNSIGNED` (rating also has a 1–5 CHECK) |
| Year | `yearAcquired` | `YEAR` |
| Boolean | `activeStatus` | `BOOLEAN NOT NULL DEFAULT TRUE` |
| Address | `state` / `zipCode` / `city` / street | `CHAR(2)` / `VARCHAR(10)` / `VARCHAR(50)` / `VARCHAR(100)` |
| Name and phone | `firstName`, `lastName` / `phone` | `VARCHAR(50)` / `VARCHAR(20)` |
| Names | campus, category, tag, role, pickup point, item title | `VARCHAR(80)`, `(50)`, `(30)`, `(30)`, `(80)`, `(120)` |
| Text | item description, message / review, report description and handling note / request message / category and pickup point description | `VARCHAR(2000)` / `(1000)` / `(500)` / `(255)`; `TEXT` is no longer used |

Values that can be enumerated use `ENUM`, so invalid values are rejected, and the duplicated status `CHECK` constraints have been removed:

| Column | Values | Default |
| --- | --- | --- |
| `SecondhandItem.status` | `AVAILABLE`, `RESERVED`, `SOLD`, `REMOVED` | `AVAILABLE` |
| `SecondhandItem.condition` | `NEW`, `LIKE_NEW`, `GOOD`, `FAIR`, `POOR` | required |
| `PurchaseRequest.status` | `PENDING`, `ACCEPTED`, `REJECTED` | `PENDING` |
| `TransactionOrder.status` | `PENDING`, `COMPLETED`, `CANCELLED` | `PENDING` |
| `User.accountStatus` | `ACTIVE`, `SUSPENDED` | `ACTIVE` |
| `TransactionReview.reviewStatus` | `PUBLISHED`, `FLAGGED`, `REMOVED` | `PUBLISHED` |
| `Report.status` | `RECEIVED`, `UNDER_REVIEW`, `RESOLVED`, `DISMISSED` | `RECEIVED` |
| `Report.reason` | `SCAM`, `SPAM`, `INAPPROPRIATE_CONTENT`, `HARASSMENT`, `WRONG_DESCRIPTION`, `COUNTERFEIT`, `OTHER` | `OTHER` |

Note: in MySQL, a `NOT NULL` enum without a default silently takes its first value when omitted, instead of raising an error,
so `condition` is written as a nullable enum plus `CHECK (condition IS NOT NULL)`; an omitted value raises an error and is not treated as `NEW`.
Roles, categories, and tags are data that gets maintained, so they stay in their own tables and are not made into enums.

## Delete Rules

All 36 foreign keys state `ON DELETE` explicitly; `ON UPDATE` stays at the default `RESTRICT` (the primary keys are surrogate ids that never change).
Principle: history data and base data may never be deleted, and when something is no longer used its status is changed instead; only dependent rows that "exist because of the parent row and are meaningless without it" are deleted by cascade.

| Rule | Foreign keys | Reason |
| --- | --- | --- |
| Deletion forbidden (`RESTRICT`, 25) | Everything referenced by campuses, roles, categories, tags, items, purchase requests, orders, addresses, conversations that have messages, reviews, and reports; users referenced by items, requests, messages, reviews, and reports | Transactions, conversations, reviews, and reports must be kept for traceability; use `REMOVED` to take down an item, `SUSPENDED` to ban a user, `activeStatus = 0` for a tag, and `CANCELLED` for an order |
| Cascade delete (`CASCADE`, 11) | item → images and tag associations; item → favorites; user → favorites, role associations, and their own pickup points; empty conversation → participants; review → `BuyerReview`/`SellerReview` rows; report → `ItemReport`/`TransactionReport` rows | These rows exist only because of the parent row and are meaningless without it |

Two key points: pickup points cascade with their user, but a pickup point referenced by an order still cannot be deleted, so a pickup point that has been used is never lost; a conversation that has messages cannot be deleted, which keeps the message history.
`delete_rules.sql` runs one delete per rule and checks the outcome, inside a transaction that is rolled back at the end:

```bash
./db.sh test
```

## Start, Reset, and Use

The database runs in a Docker container using the image `mysql:8.4` (an 8.x long-term support release), so MySQL does not need to be installed on the host.
If you prefer not to use Docker, see "Non-Docker Environment" below.
Docker Engine, Docker Compose v2.20 or later, and Bash are required. Run all commands in this directory:

```bash
# Optional: customize the local password and port.
cp .env.example .env

# Reset and import: remove the old container and data volume, start MySQL, and import the schema script and sample data inside the container.
./reset.sh --load

./db.sh status     # Version, tables, and row counts
./db.sh queries    # Run queries.sql
./db.sh test       # Run delete_rules.sql; each of the 27 rules prints PASS or FAIL
./db.sh shell      # Open the mysql client in the container (seattle_marketplace already selected)
```

| Command | Effect |
| --- | --- |
| `./reset.sh` | Reset to an empty MySQL (no database created, nothing imported) |
| `./reset.sh --load` | Reset and import `marketplace.sql` and `seed/` |
| `./db.sh load` | Import into an empty node; if the database already exists you get a "table already exists" error, so reset first |
| `./db.sh queries` / `test` / `status` / `shell` | Queries, tests, status, client |

`marketplace.sql`, `seed/`, `queries.sql`, `delete_rules.sql`, and `archive/` are mounted read-only at `/workspace/` in the container,
and `db.sh` reads the files inside the container directly, without going through the host. The first run downloads the `mysql:8.4` image.
If the data volume was created with another version (for example the earlier 9.7), it is removed on reset; MySQL cannot downgrade a data directory to an older version, so do not change the image version and reuse an old volume.

The reset script always operates on the `neu-ie6700-mysql` Compose project: it first checks Docker, the configuration, and the required image,
then removes that project's container and `mysql_data` data volume, starts MySQL again, and waits for a real SQL health check to pass.
This deletes all databases and data on this test node; the originals in `archive/` are kept. The script does not run any global Docker cleanup command and does not touch other Compose projects.
The script locates its configuration from its own location, so it can also be run from the repository root: `"./03 MySQL Implementation/reset.sh"`.

To connect from the host: address `127.0.0.1:3307`, user `root`, and the local test password from `.env.example`;
if the port is in use, change `MYSQL_PORT` in `.env`. To view logs: `docker compose logs --tail 100 mysql`.

## Non-Docker Environment: Import into a Local MySQL 8.x

If you already have a local MySQL 8.x server (any 8.x release from 8.0 up), you can skip Docker and import in one shot with `import_local.sh`:

```bash
# Connect to local 127.0.0.1:3306 as root; if no password is set, the script prompts for it once.
./import_local.sh

# Specify host, port, and user; pass the password with MYSQL_PWD (it does not appear in the process arguments).
MYSQL_PWD='your-password' ./import_local.sh -h 127.0.0.1 -P 3306 -u root

# Replace the database if it already exists (this deletes all data in seattle_marketplace).
./import_local.sh --drop-existing
```

The script needs the `mysql` client on the local machine. The order is the same as `db.sh load`: `marketplace.sql` first, then the three files in `seed/`,
and finally a check that the database has exactly 23 base tables. It provides the following protections:

- **Version check**: the server must be MySQL 8.x. MariaDB is rejected because the `utf8mb4_0900_ai_ci` collation is available only in MySQL 8.x.
- **No overwriting existing data**: if `seattle_marketplace` already exists, the script stops and changes nothing; only with `--drop-existing` does it drop and recreate it.
- **Stop on error**: if an error occurs partway through the import, the script exits with a non-zero status and warns that the database may be only partly imported and must be redone with `--drop-existing`.

The script only imports; it does not run `queries.sql` or `delete_rules.sql`. To test the delete rules, run `delete_rules.sql` with a client after the import.

## Stop

```bash
# Stop the node and keep the database data.
docker compose stop

# Remove the container and network and keep the database data volume.
docker compose down
```
