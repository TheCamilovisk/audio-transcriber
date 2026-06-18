---
name: implement-plan-on-branch
description: >-
  Read an approved plan/slice from a file, analyze it, create a fresh branch
  from main, implement the code changes, and verify the suite stays green —
  then stop without committing or pushing. Use when a plan or slice needs
  implementing as a new branch for review.
license: MIT
metadata:
  version: 1.0.0
  authoring-spec: agent-skills (portable SKILL.md)
---

# Implement an approved plan on a branch

Turn a written plan or slice into code on a dedicated branch, then stop so the
user can review before any commit lands. Harness-agnostic.

## When to use

- A plan or slice in `.resources/plans/` is approved and ready to implement.
- The user asks to "implement this plan" or "code this slice".
- You need to create a clean branch from `main` for reviewable changes.

Skip when the user explicitly says to commit and push — that's the
**commit-and-push-reviewed-branch** skill's job.

## Process

### 1. Preflight

- Read `git status` and `git branch --show-current`.
- If there are uncommitted user changes (not files staged by you), STOP and
  ask how to proceed — do not stash or discard without confirmation.
- Confirm the plan file exists at the path the user referenced.

### 2. Start from main

```bash
git checkout main
```

- Only pull (`git pull`) if the user explicitly requested it.
- Otherwise, do not pull — work against the local main as-is.

### 3. Read and analyze the plan

- Read the plan file and any dependencies it links (sibling slices, parent
  plans, or referenced source files).
- Inspect current code, tests, and configuration relevant to the plan's
  "Changes" section. Know the before-state before editing.
- Understand the verification commands the plan specifies.

### 4. Create a branch

```bash
git checkout -b <branch-name>
```

- Derive the branch name from the plan/slice title, e.g. `002-singleton-transcriber`.
- Base it on the current `main` (already checked out in step 2).
- If the branch already exists, ask the user whether to delete and recreate,
  switch to it, or pick a different name.

### 5. Implement

- Make **only** the changes listed in the plan's "Changes" section. Do not
  expand scope.
- Prefer existing project conventions and reuse existing seams.
- Every file and test the plan mentions must be addressed.
- When editing, keep diff minimal — precise targeted replacements.

### 6. Verify

Run the plan's verification commands. Typical project defaults:

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

- If failures are caused by the implementation, fix them immediately.
- If failures are pre-existing, note them and move on.
- The suite must be green before stopping.

### 7. Stop — do not commit or push

- Do **not** stage, commit, or push changes.
- Report:
  - Branch name
  - Files changed
  - Verification results (test count, lint/format status)
  - Anything the user should focus on during review
