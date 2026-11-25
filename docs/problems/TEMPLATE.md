# P<number> <Problem title>

- **Owner**: Unassigned
- **Status**: Not started

## 1. Business Question

One or two sentences: who wants to know what.

## 2. Data Needed

Describe in words what the single query must return: one row per what, which columns, and the optional parameters. Do not put SQL here; the owner writes it in the Python module.

## 3. Python Analysis

Bullets: the metrics Python computes from the returned rows, the output, and the error behavior (message, exit status). A zero denominator prints `-`.

## 4. Expected Results (Seed Data, verified)

Numbers checked on the sandbox after `./mysql/reset.sh --load`.

## 5. Acceptance Criteria

Three or four checks that can become tests, for example "the group counts add up to the total".
