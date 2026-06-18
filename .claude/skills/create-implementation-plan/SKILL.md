---
name: create-implementation-plan
description: >-
  Produce a written implementation plan before coding a non-trivial change.
  Use when the user asks to plan a feature/refactor, when a task needs design
  before edits, or before starting any multi-file change. Explores the codebase
  for reusable patterns, clarifies genuine decisions, and writes a structured,
  reviewable plan file. Pairs with the vertical-slice-plan skill to break a big
  plan into mergeable slices.
license: MIT
metadata:
  version: 1.0.0
  authoring-spec: agent-skills (portable SKILL.md)
---

# Create an implementation plan

A plan is a written artifact you produce *before* editing code, so the approach
can be reviewed and the design pinned down. It is not the code; it is the
contract for the code. This skill is harness-agnostic — where it names a tool
(search agents, plan-approval steps), use your harness's equivalent or skip it.

## When to use

- A change spans multiple files, introduces new components, or has real design
  choices.
- The user asks to "plan", "design", or "figure out how" before implementing.
- You are unsure of scope and need to explore before committing to an approach.

Skip for typo fixes, single-line changes, and trivial renames — just do those.

## Process

### 1. Understand the request and the code

Read any existing related plans or docs first. Then **explore the codebase to
find what already exists** — functions, utilities, patterns, and extension seams
you can reuse. Actively avoid proposing new code when a suitable implementation
already exists. If your harness has parallel read-only search agents, fan out
(scope uncertain → a few agents in parallel; isolated/known files → one). Capture
exact file paths, constructor/function signatures, and `file:line` references.

### 2. Design the approach

Decide the approach from what you found. Prefer reusing existing seams over
inventing new ones. If your harness offers a planning/architect agent, use it to
validate the approach and weigh alternatives; otherwise reason it through
yourself. Settle on **one recommended approach** — not a survey of every option.

### 3. Clarify only genuine decisions

Ask the user only about choices you cannot resolve from the request, the code, or
sensible defaults — and where the answer changes what you build (e.g. mechanism,
library, granularity). Pick obvious defaults silently and state them. Do not ask
for approval-to-proceed as a "question"; that is what step 5 is for.

### 4. Write the plan file

Write to `.resources/plans/NNN-kebab-title.md` where `NNN` is the next zero-padded
sequence number (`001`, `002`, …) and the title is a short kebab-case summary.
Structure (keep it scannable but executable):

- **Context** — why this change is being made: the problem/need, what prompted
  it, the intended outcome, and any decisions already confirmed with the user.
- **Changes** — the concrete files to add/edit, each with the relevant code
  snippet. Reference existing functions/utilities to reuse with their paths and
  `file:line`. For a pattern repeated across many files, describe it once and
  list a few representative paths — do not enumerate every line.
- **Verification** — how to test end-to-end: exact commands (build, lint, tests)
  and a manual smoke test where relevant.
- **Notes / future work** — explicitly deferred scope and known follow-ups.

Include only the recommended approach, not rejected alternatives.

### 5. Request approval before implementing

Present the plan and get explicit approval before writing production code. Use
your harness's plan-approval step if it has one. Do not start editing until the
plan is accepted.

## Conventions

- Plan files live in `.resources/plans/`, zero-padded sequential numbers.
- One plan file per coherent change. To split a large plan into independently
  mergeable units, hand it to the **vertical-slice-plan** skill.
- Reference code as clickable `path:line`; copy real signatures, don't paraphrase.

## Quality bar

- Every "Changes" item names a real file and reuses existing seams where they
  exist.
- The Verification section actually proves the change works (not just "run
  tests" — say which, and what green looks like).
- A reader who didn't explore the codebase could execute the plan from the file
  alone.
