# Prompt 3: Implement the tasks (OpenSpec apply)

- **When:** 2026-11-25 05:57
- **Stage:** Implementation. Builds the Python project, the tests, the Docker sandbox use and the CI workflows from tasks.md.
- **Source:** OpenSpec apply workflow template for the change `cross-platform-python-sql-cli`.

The text below the line is the prompt exactly as it was sent, without edits.

---

``````text
**Input**: Optionally specify a change name (e.g., `add-auth`).

**Change Name**: cross-platform-python-sql-cli

**Stage Boundary Constraint (strictly exclusive)**:
- You are in the "proposal execution (implementation)" stage. You may only implement the implementation, testing, and documentation tasks in tasks.md that relate to the change itself, and tick the corresponding checkboxes once done.
- You MUST NOT execute archiving: do NOT run `openspec archive`, do NOT move the change directory into `openspec/changes/archive/`, do NOT sync (merge) delta specs into `openspec/specs/`, and do NOT create or run an archive commit.
- You MUST NOT regenerate the proposal: do NOT run `openspec new change`, do NOT create a new change, and do NOT rewrite the goals or scope of proposal.md, design.md, or specs; if implementation reveals a design issue, only suggest updating the artifacts and wait for guidance.
- If tasks.md contains non-implementation tasks such as archiving, syncing main specs, committing or pushing, creating a PR, or releasing (for example, left over from an older proposal), you MUST skip them: do not execute them, do not tick them, and list them in the status report as "out of scope for this stage, skipped". They do not affect whether this stage counts as complete.
- Once all implementation tasks are done, only report the result and stop; do NOT proceed into archiving on your own. Archiving is triggered separately by the user.
---
Implement tasks from an OpenSpec change.
**Input**: Optionally specify a change name (e.g., `add-auth`). If omitted, check if it can be inferred from conversation context. If vague or ambiguous you MUST prompt for available changes.
## Steps
**Store:** When a standalone store is selected for this run, append `--store <id>` to every `openspec` command in these steps. Otherwise add no `--store` flag.
**Project check:** Before the first write (ticking a task), run `openspec list --json` and read `root`. A root object means the project is set up. `root: null` means it is not: a write would create an `openspec/` root as a side effect.
- **Auto-selected** (you chose OpenSpec yourself, without the user naming it): stop using OpenSpec and answer the request normally, without mentioning OpenSpec setup.
- **Explicit OpenSpec request** (the user named OpenSpec): stop before writing and ask how to proceed: set this project up (`openspec init`), target a store they already have (`--store <id>`), or continue without OpenSpec for this request. Wait for their answer.
Never create the root as a side effect: do not run `openspec init` until the user asks for it, and do not hand-create `openspec/` files.
1. **Select change**
   If a name is provided, use it. Otherwise:
   - Infer from conversation context if the user mentioned a change
   - Auto-select if only one active change exists
   - **In interactive mode**: If ambiguous, ask the user to select
   - Always announce: "Using change: <name>" and how to override (e.g., by specifying a different change name).
2. **Check status to understand the schema**
   ```bash
   openspec status --change "<name>" --json
   ```
   Parse the JSON to understand:
   - `schemaName`: The workflow being used (e.g., "spec-driven")
   - `planningHome` and `changeRoot`: where the change lives. Do not assume a repo-local path.
   - `artifactPaths`: for each artifact, `existingOutputPaths` lists the files that already exist
   - Which artifact contains tasks (typically "tasks" for spec-driven, check status for others)
3. **Get apply instructions**
   ```bash
   openspec instructions apply --change "<name>" --json
   ```
   This returns:
   - Context file paths (varies by schema)
   - Progress (total, complete, remaining)
   - Task list with status
   - Dynamic instruction based on current state
   **Handle states:**
   - If `state: "blocked"` (missing artifacts): show message, suggest returning to the artifact creation flow first
   - If `state: "all_done"`: report that all tasks are complete and stop; do NOT archive
   - Otherwise: proceed to implementation
   - An artifact whose status is `skipped` is satisfied: do not create its files, and do not treat it as missing
4. **Read context files**
   Read the files listed in `contextFiles` from the apply instructions output, under `changeRoot`.
   The files depend on the schema being used:
   - **spec-driven**: proposal, specs, design, tasks
   - Other schemas: follow the contextFiles from CLI output
   Treat the `context` field from the apply instructions as required input: read it and apply it. If it conflicts with a controlling input (the task list, the resolved paths or the CLI result), do not follow it; report the conflict instead.
5. **Show current progress**
   Display:
   - Schema being used
   - Progress: "N/M tasks complete"
   - Remaining tasks overview
   - Dynamic instruction from CLI
   - Emit the `## Implementation Started` block once, as shown under Output format, before the first task
6. **Implement tasks (loop until done or blocked)**
   For each pending task:
   - Show which task is being worked on
   - Make the code changes required
   - Keep changes minimal and focused
   - Tick the task at the file and line given by its `sourcePath` (`- [ ]` → `- [x]`), and only after the task's behavior is fully implemented. A partly implemented task stays unticked.
   - Continue to the next task
   **Tasks that name a slash command or skill** (for example `/impeccable polish`):
   - `/<name> <arguments>` in a task, and wording such as "execute the polish operation of the `impeccable` skill", are skill invocations, not shell commands and not a command-line tool (CLI). `/impeccable polish` is equivalent: the skill is `impeccable` and the operation is `polish`. The skill may also be provided as `hagi:impeccable`, which is the same skill as `impeccable`. Do not type it into the shell and do not conclude it is unavailable from that; read the skill's information and follow its instructions for that operation.
   - Skills are discoverable at run time, and no extra skills configuration is required. Invoke it through whatever skill mechanism your runtime provides, passing the rest of the command as its arguments. If it is not in the skill listing you were given, look for it before giving up: search the skill directories of the repository and of the user environment for a skill with that name, read its skill definition file, then follow those instructions.
   - Run the named skill. A manual check does not replace it. Only when the skill truly cannot be found or invoked after that search may you fall back to a manual check, and then say so in `### Notes (if any)` or the pause evidence, with the search you made.
   - When the task lists things to verify (rules, colours, breakpoints, test ids), check every listed item and keep the evidence for each. If one cannot be checked, the task stays unticked and that item is named under `### Issue Encountered`. Never tick a task, or narrow it, after covering only some of its items.
   - If a listed rule has a mechanical check, run it. For example, for a spacing rule that says the base class is the phone value, grep the changed files for the unprefixed and `sm:` utilities instead of judging by eye.
   **Pause if:**
   - Task is unclear → ask for clarification
   - A task asks for behavior beyond the specs → pause and report the gap with options. Do not implement a narrower version silently.
   - Implementation reveals a design issue → suggest updating artifacts
   - Error or blocker encountered → report and wait for guidance
   - User interrupts
7. **On completion or pause, show status**
   Display:
   - Tasks completed this session
   - Overall progress: "N/M tasks complete"
   - If all done: report completion and stop; do NOT archive
   - If paused: explain why and wait for guidance
## Output format
**Output at Start** (emitted once, before the first task)
```
## Implementation Started
**Change:** <change-name>
**Schema:** <schema-name>
**Progress:** 0/7 tasks complete
```
**Per-task progress** is plain narration, not a heading. Write each step as a line such as `Working on task 3/7: <task description>`, followed by `✓ Task complete`. Never repeat the start heading.
### Output On Completion
```
## Implementation Complete
**Change:** <change-name>
**Schema:** <schema-name>
**Progress:** 7/7 tasks complete ✓
### Completed This Session
- [x] Task 1
- [x] Task 2
...
### Notes (if any)
- <deviation or side effect, one per line>
All implementation tasks complete! This stage ends here; archiving was not performed.
```
The completion block holds only completed content: the facts, `### Completed This Session`, and optionally `### Notes (if any)` for deviations and side effects. It never holds a reason, unfinished work or a decision request. Tasks that are out of scope for this stage are listed as skipped, not as unfinished, and they do not turn the run into a pause.
### Output On Pause
```
## Implementation Paused
**Change:** <change-name>
**Schema:** <schema-name>
**Progress:** 4/7 tasks complete
**Reason:** <one line: why the run stopped>
### Completed This Session
- [x] Task 1
- [x] Task 2
### Not Done
- 3.2, 3.3 (blocked: <one line>)
### Issue Encountered
<the evidence behind the reason>
### Decision Needed
1. <option 1>: <what happens next>
2. <option 2>: <what happens next>
```
The facts come first, and `**Reason:**` is one line. `### Completed This Session` appears only when work was done. The reason is never part of the heading and never mixed into the completed part. `### Not Done` lists the unfinished and blocked tasks by id. `### Issue Encountered` holds the evidence behind the reason. `### Decision Needed` lists numbered options, and each one says what the executor does next.
### Closing rules
- A run that stops on its own ends with exactly one `## Implementation Complete` or `## Implementation Paused` block. A free-form summary or a conversational report never replaces it.
- Write each lifecycle heading exactly as shown for this prompt's locale, with nothing appended. The stop reason and the conversation language never change the heading; the body follows the user's language.
## Guardrails
- Keep going through tasks until done or blocked
- Always read context files before starting (from the apply instructions output)
- If a task is ambiguous, pause and ask before implementing
- If implementation reveals issues, pause and suggest artifact updates
- Keep code changes minimal and scoped to each task
- Update the task checkbox immediately after completing each task, at its `sourcePath` line, and never before the behavior is fully implemented
- Pause on errors, blockers, or unclear requirements - don't guess
- Use the contextFiles from CLI output, don't assume specific file names
- Never archive: do not run `openspec archive`, do not move to the archive directory, do not sync main specs, do not make an archive commit
### Fluid Workflow Integration
This skill supports an "actions on a change" model:
- **Can be invoked anytime**: Before all artifacts are done (if tasks exist), after partial implementation, interleaved with other actions
- **Allows artifact updates**: If implementation reveals design issues, suggest updating artifacts - not phase-locked, work fluidly
``````
