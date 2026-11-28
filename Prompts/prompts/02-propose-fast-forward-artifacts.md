# Prompt 2: Generate all proposal artifacts (OpenSpec fast-forward)

- **When:** 2026-11-25 05:48
- **Stage:** Proposal. Generates proposal.md, design.md, the specs and tasks.md in one run.
- **Source:** Same change description as Prompt 1, with the fast-forward workflow template.

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

**Stage Boundary Constraint (strictly exclusive)**:
- You are in the "proposal generation" stage. You may only create or update proposal artifacts under `changeRoot` (proposal.md, design.md, specs, tasks.md).
- You MUST NOT execute the implementation: do NOT modify, add, or delete any source code, configuration, test, or documentation files (proposal artifacts excepted), do NOT run build, test, or migration commands to land the change, do NOT tick tasks in tasks.md as `- [x]`, and do NOT run `openspec instructions apply` or any implementation flow. "Generate everything needed to start implementation" means writing the proposal artifacts only, not performing the implementation itself.
- You MUST NOT execute archiving: do NOT run `openspec archive`, do NOT move the change directory into `openspec/changes/archive/`, and do NOT sync delta specs into `openspec/specs/`.
- You MUST NOT perform Git commit-style operations: do NOT run `git add`, `git commit`, or `git push`, and do NOT create a PR.
- Proposal artifacts describe only the implementation of the change itself: proposal, design, specs, and tasks MUST NOT contain requirements or tasks beyond implementation, such as archiving the change, syncing main specs, committing or pushing code, creating a PR, deploying, or releasing. Those belong to later, separate stages that the user triggers independently.
- Exception: only when the change itself is about modifying archive, sync, Git, or release logic (for example, editing prompts like this one) may these be referenced as **descriptive content**, never as tasks to be executed by this change.
---
Fast-forward through artifact creation - generate everything needed to start implementation.
**Input**: The current workflow input can be the change name (kebab-case), OR a description of what the user wants to build.
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
Generate all natural-language proposal artifacts in `en-US`. Preserve code identifiers, file paths, commands, and protocol literals exactly when technical syntax requires them.
## Steps
**Store:** When a standalone store is selected for this run, append `--store <id>` to every `openspec` command in these steps. Otherwise add no `--store` flag.
1. **If no input provided, use reasonable defaults**
   The current workflow input can be the change name (kebab-case), OR a description of what the user wants to build.
   If `changeDescription` or `changeName` is provided in the input context, use it.
   - Ask the user: "What change do you want to work on? Describe what you want to build or fix."
   - From their description, derive a kebab-case name (e.g., "add user authentication" → `add-user-auth`)
   **IMPORTANT**: Do NOT proceed without understanding what the user wants to build.
2. **Check the project root**
   ```bash
   openspec list --json
   ```
   Read `root` before the first write. A root object means the project is set up. `root: null` means it is not: there is no `openspec/` root here, and `openspec new change` would create one as a side effect.
   - **Auto-selected** (you chose OpenSpec yourself, without the user naming it): stop using OpenSpec and answer the request normally, without mentioning OpenSpec setup.
   - **Explicit OpenSpec request** (the user named OpenSpec): stop before writing. Ask how to proceed: set this project up (`openspec init`), target a store they already have (`--store <id>`), or continue without OpenSpec for this request. Wait for their answer.
   Never create the root as a side effect: do not run `openspec init` until the user asks for it, do not hand-create `openspec/` files, and do not let `openspec new change` create one.
3. **Create the change directory**
   ```bash
   openspec new change "<name>"
   ```
   This creates a scaffolded change in the planning home the CLI resolves (`planningHome`). Never create the change directory by hand.
4. **Get the artifact build order**
   ```bash
   openspec status --change "<name>" --json
   ```
   Parse the JSON to get:
   - `planningHome` and `changeRoot`: where the change lives. Do not assume a repo-local path.
   - `artifactPaths`: for each artifact, `resolvedOutputPath` (where its file is written) and `existingOutputPaths` (files that already exist)
   - `applyRequires`: array of artifact IDs needed before implementation (e.g., `["tasks"]`)
   - `artifacts`: list of all artifacts with their status, `requires` edges and dependencies
5. **Create artifacts in sequence until the required set is complete**
   Use the **TodoWrite tool** to track progress through the artifacts.
   Before creating the first artifact, check for project design guidelines. Look for `DESIGN.md` and `.impeccable/design.json` at the project root and, when a repository scope contract is present, at the root of each repository it names. Only when **both** files exist in the same location, read both and follow the design requirements and guidelines they declare in every artifact you write. When only one exists, or neither, skip this silently. These files are read-only guidance: never modify them, and the Stage Boundary Constraint still applies to anything they suggest. Record work they imply as implementation tasks in `tasks.md`.
   Loop through artifacts in dependency order (artifacts with no pending dependencies first):
   a. **For each artifact that is `ready` (dependencies satisfied)**:
      - Get instructions:
        ```bash
        openspec instructions <artifact-id> --change "<name>" --json
        ```
      - The instructions JSON includes:
        - `context`: Project background (constraints for you - do NOT include in output)
        - `rules`: Artifact-specific rules (constraints for you - do NOT include in output)
        - `template`: The structure to use for your output file
        - `instruction`: Schema-specific guidance for this artifact type
        - `outputPath`: Schema hint only; write to the `artifactPaths` entry from the status output instead
        - `dependencies`: Completed artifacts to read for context
      - Read any completed dependency files for context
      - Choose the write target from `artifactPaths.<artifact-id>.resolvedOutputPath`. If that path is a glob, pick the concrete file first, then resolve symlinks. If the resolved path is outside `changeRoot`, stop and report without writing. Run this check before delegating any write to another skill.
      - Create the artifact file using `template` as the structure
      - Apply `context` and `rules` as constraints - but do NOT copy them into the file
      - **Apply any enabled planning-direction output requirements (use the instructions and examples of the enabled directions in the direction block above)**
      - Show brief progress: "✓ Created <artifact-id>"
   b. **After creating each artifact, verify enabled planning-direction output**:
      For **proposal.md**:
      - [ ] Are the proposal-stage outputs of the enabled directions represented?
      For **design.md**:
      - [ ] Are the design-stage outputs of the enabled directions represented?
      For **tasks.md**:
      - [ ] Are the tasks required by the enabled directions present? If any is missing, **MUST** supplement `tasks.md` before writing it.
      If any enabled direction is missing: **MUST** supplement the artifact before writing it.
      For **every artifact** when both design files were found:
      - [ ] Does UI-facing content (layout, controls, styling, interaction) match the design guidelines? If not, **MUST** correct it before writing the artifact.
   c. **Continue until the required set is complete**
      - The required set is `applyRequires` plus every artifact reachable from it by following the `requires` edges in the status output. Compute it from the status JSON, not from memory.
      - After creating each artifact, re-run `openspec status --change "<name>" --json` and recompute readiness from the file system; do not rely on a cached state
      - Stop when every artifact in the required set has status `done` or `skipped`
      - An artifact with status `skipped` is not created and counts as satisfied; it never blocks the stage
      - Only the `skipped` status skips an artifact. Never skip `specs` on your own judgment
      - When the change alters no spec-level behavior (a maintenance change), declare `skip_specs: true` in `.openspec.yaml` instead of inventing a requirement
      - When the change removes every requirement of a capability, declare `retire_capabilities: true` in `.openspec.yaml`
      - An artifact whose own instruction marks it optional may be skipped on that basis only; skipping a conditional dependency does not stop a required artifact from being written
   d. **If an artifact requires user input** (unclear context):
      - In interactive mode: clarify with the user
      - Then continue with creation
6. **Show final status**
   ```bash
   openspec status --change "<name>" --json
   ```
## Output format
After completing all artifacts, summarize:
- Change name and location
- List of artifacts created with brief descriptions
- What's ready: "All artifacts created! Ready for implementation."
- Prompt: "Enter the implementation stage to start implementing."
Report the outcome under this heading, with the labeled key facts first:
```
## Artifacts Ready
**Change:** <change-name> (`openspec/changes/<change-name>/`)
**Progress:** <N>/<N> artifacts complete
**Apply requires:** <artifact IDs from applyRequires>
### Assumptions (if any)
- **Assumption:** <one sentence>
  - **Reason:** <one sentence>
  - **Impact:** <one sentence>
### Next step
Enter the implementation stage to start implementing.
```
## Artifact Creation Guidelines
- Follow the `instruction` field from `openspec instructions` for each artifact type
- The schema defines what each artifact should contain - follow it
- Read dependency artifacts for context before creating new ones
- Use the `template` as a starting point, filling in based on context
## Special Note: tasks.md Content Scope
- tasks.md should focus on business logic and technical implementation tasks
- Should NOT include Git version control operations (git add, git commit, git push)
- Should NOT include archive-stage operations such as archiving or syncing main specs
- See the "tasks.md Content Scope Constraints" section below for detailed rules
### tasks.md Content Scope Constraints
When creating the `tasks.md` artifact, you **MUST** adhere to the following content scope constraints:
**MUST Include**:
- Business logic tasks (code implementation, feature development)
- Technical implementation tasks (component integration, API development)
- Testing tasks (unit tests, integration tests)
- Documentation tasks (updating docs, adding comments)
**MUST NOT Include**:
- Git commit operations (git add, git commit, git push)
- Version control management workflows
- Deployment and release operations
- Archive operations (`openspec archive`, moving to `openspec/changes/archive/`, syncing delta specs into `openspec/specs/`)
- Procedural tasks unrelated to the implementation itself, such as creating a PR
**Exception**:
When the change itself is about modifying Git command or archive logic in prompt templates, Git commands or archive steps may be referenced as **descriptive content** (e.g., "Locate the git add command in step 5", "Adjust the sync step in the archive prompt"), not as **operational instructions** (e.g., "Execute git add . && git commit", "Run openspec archive").
**Decision Criteria**:
- If the change's goal is to modify Git command or archive logic in prompts → Descriptive references allowed
- Otherwise → Actual Git or archive operation steps should NOT be included in tasks
## Guardrails
- Create ALL artifacts in the required set (`applyRequires` plus its `requires` closure); leave `skipped` artifacts uncreated
- Always read dependency artifacts before creating a new one
- Never create the change directory by hand: only `openspec new change` creates it
- If context is critically unclear, ask the user - but prefer making reasonable decisions to keep momentum
- If a change with that name already exists, ask if the user wants to continue it or create a new one
- Verify each artifact file exists after writing before proceeding to the next
- Generate proposal artifacts only: stop right after the summary output, and do NOT proceed into implementation or archiving on your own
``````
