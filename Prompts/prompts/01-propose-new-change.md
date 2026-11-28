# Prompt 1: Create the change (OpenSpec propose)

- **When:** 2026-11-25 05:47
- **Stage:** Proposal. Creates the change directory and shows the first artifact template.
- **Source:** The user's change description is the part after `Change Description`; the rest is the OpenSpec workflow template that the tool added.

The text below the line is the prompt exactly as it was sent, without edits.

---

``````text
**Input**: The workflow context provides the change name (kebab-case), OR a description of what the user wants to build.

**Change Name**: cross-platform-python-sql-cli
**Change Description**: Create a Cross-Platform Python CLI for Course SQL: ## Involved Repositories

### Repos

| Repository Name | Path | Edit Permission | Purpose |
| --- | --- | --- | --- |
| IE6700-py | repos/IE6700-py | [editable] | Build a Python project for running course SQL and displaying results. |

## Context

The project needs a basic Python setup that users can install and run with a local `.venv`. Users will configure the database connection string through `.env` and use a CLI to execute course SQL and view results. The project should support Windows, macOS, and Linux.

## Problem

Users need a consistent way to set up the Python environment, configure database connectivity, execute the three course SQL files, and inspect results across supported operating systems. GitHub Actions should verify that the SQL runs correctly and produces the expected results.

## Solution

Create a basic Python project with instructions and commands for creating and using a `.venv`. Add `.env`-based connection string configuration and a CLI for executing the three course SQL files and displaying their results. Configure GitHub Actions to validate SQL execution and result correctness.

## Impact

Users can set up and run the course SQL workflow on Windows, macOS, and Linux. Automated checks provide a repeatable way to verify the SQL and its results.

**No Background Research Constraint**:
- You MUST NOT perform background research. Do NOT spawn sub-agents, and do NOT use any out-of-session retrieval or generation mechanism to gather or produce content.
- You MUST NOT delegate artifact generation to sub-agents or any detached generation path.
- The proposal result MUST be generated directly in the current session, using only the context already present in the conversation.
---
**Stage Boundary Constraint (strictly exclusive)**:
- You are in the "proposal generation" stage. You may only create or update proposal artifacts under `changeRoot`, the change directory the CLI resolves.
- You MUST NOT execute the implementation: do NOT modify, add, or delete any source code, configuration, test, or documentation files (proposal artifacts excepted), do NOT run build, test, or migration commands to land the change, do NOT tick tasks in tasks.md as `- [x]`, and do NOT run `openspec instructions apply` or any implementation flow.
- You MUST NOT execute archiving: do NOT run `openspec archive`, do NOT move the change directory into `openspec/changes/archive/`, and do NOT sync delta specs into `openspec/specs/`.
- You MUST NOT perform Git commit-style operations: do NOT run `git add`, `git commit`, or `git push`, and do NOT create a PR.
- Proposal artifacts describe only the implementation of the change itself: proposal, design, specs, and tasks MUST NOT contain requirements or tasks beyond implementation, such as archiving the change, syncing main specs, committing or pushing code, creating a PR, deploying, or releasing. Those belong to later, separate stages that the user triggers independently.
- Exception: only when the change itself is about modifying archive, sync, Git, or release logic (for example, editing prompts like this one) may these be referenced as **descriptive content**, never as tasks to be executed by this change.
---
Start a new change using the experimental artifact-driven approach.
## Planning Directions For This Run
Apply the following planning directions for this generation run:
- Change map: include structured file-impact views so readers can immediately see which files or modules change, why they change, and where the implementation work lands. Typical outputs: a proposal code change table plus a design code change inventory.

### `change-map` direction
If enabled, `proposal.md` should include a structured code change table, and `design.md` can expand it into a more detailed inventory.
**Example Code Change Table**:
| File Path | Change Type | Change Reason | Impact Scope |
|-----------|-------------|---------------|--------------|
|           |             |               |              |
**Example Detailed Code Change Inventory**:
| File Path | Change Type | Change Description | Affected Module |
|-----------|-------------|-------------------|-----------------|
|           |             |                   |                 |
- Prototype: when UI changes are involved, include an ASCII interface prototype in the proposal artifact so layout, controls, and interaction shape are visible early.

### `prototype` direction
If enabled and the proposal changes UI, include an ASCII interface sketch in `proposal.md`.
**Example ASCII UI Prototype**:
```
┌─────────────────────────────────────────┐
│ User Login                         [×] │
├─────────────────────────────────────────┤
│  Email Address *                       │
│ ┌─────────────────────────────────────┐ │
│ │ user@example.com                   │ │
│ └─────────────────────────────────────┘ │
│  Password *                            │
│ ┌─────────────────────────────────────┐ │
│ │ ••••••••••••••••••••••••••••••••  │ │
│ └─────────────────────────────────────┘ │
│            [Login] [Register]            │
└─────────────────────────────────────────┘
```
- Repository scope: use the authoritative repository scope contract supplied for this run. For proposal.md, preserve its confirmed entries and permission markers exactly; do not infer repositories or permissions.
## Repository Scope Contract
The `repository-scope` direction is active. The authoritative contract below governs the single proposal repository section.
This repository scope comes from the current session's structured `targetRepositories` metadata and is the sole authority for permissions.
In `proposal.md`, generate exactly one `## Involved Repositories` section; do not generate this section in other artifacts.
That section must use these fixed columns: `| Repository Name | Path | Edit Permission | Purpose |`.
`[editable]` means confirmed `write` and `-` means confirmed `read`. Do not rewrite, upgrade, downgrade, or infer any permission, and do not add repositories not listed here.
Confirmed repository entries:
| Repository Name | Path | Edit Permission | Purpose |
| --- | --- | --- | --- |
| IE6700-py | repos/IE6700-py | [editable] | Current change context |
## Proposal Content Language
Generate all natural-language proposal content in `en-US`. Preserve code identifiers, file paths, commands, and protocol literals exactly when technical syntax requires them.
## Steps
**Store:** When a standalone store is selected for this run, append `--store <id>` to every `openspec` command in these steps. Otherwise add no `--store` flag.
1. **If no input provided, use reasonable defaults**
   If `changeDescription` or `changeName` is provided in the input context, use it.
   - Ask the user: "What change do you want to work on? Describe what you want to build or fix."
   - From their description, derive a kebab-case name (e.g., "add user authentication" → `add-user-auth`)
   **IMPORTANT**: Do NOT proceed without understanding what the user wants to build.
2. **Determine the workflow schema**
   Use the default schema (omit `--schema`) unless the user explicitly requests a different workflow.
   **Use a different schema only if the user mentions:**
   - A specific schema name → use `--schema <name>`
   - "show workflows" or "what workflows" → run `openspec schemas --json` and let them choose
   **Otherwise**: Omit `--schema` to use the default.
3. **Check the project root**
   ```bash
   openspec list --json
   ```
   Read `root` before the first write. A root object means the project is set up. `root: null` means it is not: there is no `openspec/` root here, and `openspec new change` would create one as a side effect.
   - **Auto-selected** (you chose OpenSpec yourself, without the user naming it): stop using OpenSpec and answer the request normally, without mentioning OpenSpec setup.
   - **Explicit OpenSpec request** (the user named OpenSpec): stop before writing. Ask how to proceed: set this project up (`openspec init`), target a store they already have (`--store <id>`), or continue without OpenSpec for this request. Wait for their answer.
   Never create the root as a side effect: do not run `openspec init` until the user asks for it, do not hand-create `openspec/` files, and do not let `openspec new change` create one.
4. **Create the change directory**
   ```bash
   openspec new change "<name>"
   ```
   Add `--schema <name>` only if the user requested a specific workflow.
   This creates a scaffolded change in the planning home the CLI resolves (`planningHome`), with the selected schema. Never create the change directory by hand.
5. **Show the artifact status**
   ```bash
   openspec status --change "<name>" --json
   ```
   Use the returned `planningHome`, `changeRoot`, `artifactPaths` and `nextSteps` instead of assuming repo-local paths. This shows which artifacts need to be created and which are ready (dependencies satisfied).
6. **Get instructions for the first artifact**
   The first artifact depends on the schema. Check the status output to find the first artifact with status "ready".
   ```bash
   openspec instructions <first-artifact-id> --change "<name>"
   ```
   This outputs the template and context for creating the first artifact.
## Output format
After completing the steps, summarize:
- Change name and location
- Schema/workflow being used and its artifact sequence
- Current status (0/N artifacts complete)
- The template for the first artifact
- Prompt: "Ready to create the first artifact? Continue the artifact creation flow, or just describe what this change is about and I'll draft it."
Report the outcome under this heading, with the labeled key facts first:
```
## Change Created
**Change:** <change-name> (`openspec/changes/<change-name>/`)
**Schema:** <schema-name>
**Progress:** 0/<N> artifacts complete
**Next artifact:** <first-artifact-id>
### Assumptions (if any)
- **Assumption:** <one sentence>
  - **Reason:** <one sentence>
  - **Impact:** <one sentence>
### Next step
<one sentence: the next action, for example creating the first artifact>
```
## Guardrails
- Do NOT create any artifacts yet - just show the instructions
- Do NOT advance beyond showing the first artifact template
- Create the change only through `openspec new change`; never create its directory by hand
- If the name is invalid (not kebab-case), ask for a valid name
- If a change with that name already exists, suggest continuing that change's artifact creation flow
- Pass --schema if using a non-default workflow
``````
