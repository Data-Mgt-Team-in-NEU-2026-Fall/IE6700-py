# Prompts

This folder keeps the prompts and the OpenSpec documents that were used to generate the structure of this application. It is part of the AI Usage record in the Python Application milestone report (section 5, stage 1 and stage 2). Nothing in this folder is needed to run the application.

## What is here

```text
Prompts/
├── README.md                              this file
├── prompts/                               the prompts, exactly as they were sent
│   ├── 01-propose-new-change.md           OpenSpec: create the change
│   ├── 02-propose-fast-forward-artifacts.md   OpenSpec: generate proposal, design, specs, tasks
│   ├── 03-implement-tasks.md              OpenSpec: implement the tasks
│   ├── 04-six-problems.md                 our request: six problems instead of a direct implementation
│   └── 05-python-only.md                  our correction: Python only, no R
└── openspec/                              what OpenSpec generated from prompts 01 and 02
    ├── config.yaml                        workflow schema (spec-driven)
    └── cross-platform-python-sql-cli/
        ├── proposal.md                    why, what changes, code change table
        ├── design.md                      design decisions
        ├── tasks.md                       the implementation checklist
        └── specs/                         five capability specs
            ├── python-environment-setup/
            ├── database-connection-config/
            ├── sql-script-execution/
            ├── course-sql-cli/
            └── sql-ci-validation/
```

## The order in which they were used

| Step | Prompt | Result |
| --- | --- | --- |
| 1 | `prompts/01` and `prompts/02` | `openspec/cross-platform-python-sql-cli/` (proposal, design, tasks, five specs) |
| 2 | `prompts/03` | The base of the application: `pyproject.toml`, `src/ie6700/` (the `ie6700` command), `tests/`, the Docker sandbox use, `.github/workflows/` |
| 3 | `prompts/04` and `prompts/05` | The six problem briefs in `docs/problems/` (`P1` to `P6` and `TEMPLATE.md`) |

Prompts 01 to 03 consist of two parts: our change description (the text after `Change Description` in prompt 01 and prompt 02), and the standard OpenSpec workflow template that the tool adds around it. Prompts 04 and 05 are short requests typed by us in Chinese; each file also has an English translation.

## How the specs map to the code

| Spec | Where it is implemented |
| --- | --- |
| `python-environment-setup` | `pyproject.toml`, `README.md` (setup for Windows, macOS and Linux) |
| `database-connection-config` | `src/ie6700/config.py`, `.env.example` |
| `sql-script-execution` | `src/ie6700/sqlscript.py`, `src/ie6700/runner.py` |
| `course-sql-cli` | `src/ie6700/cli.py`, `src/ie6700/render.py`, `src/ie6700/course.py` |
| `sql-ci-validation` | `.github/workflows/ci.yml`, `.github/workflows/sql-validation.yml`, `tests/` |

The six analytics reports in `src/ie6700/analytics/` were not part of the OpenSpec change. They were designed from the problem briefs in `docs/problems/` and written by each member (see the report, section 5).
