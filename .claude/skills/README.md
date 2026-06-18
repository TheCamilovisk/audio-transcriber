# Skills

## `create-implementation-plan` + `vertical-slice-plan`

These two skills are a pair, used in sequence:

1. **[create-implementation-plan](create-implementation-plan/SKILL.md)** —
   explore the codebase, design one recommended approach, clarify only genuine
   decisions, and write a reviewable plan to `.resources/plans/NNN-kebab-title.md`
   before any code is touched.
2. **[vertical-slice-plan](vertical-slice-plan/SKILL.md)** — once a plan from
   step 1 is approved and is too large to ship as one change, decompose it into
   small, dependency-ordered, independently mergeable slices (each carrying its
   own tests, each leaving the suite green) under
   `.resources/plans/<parent-plan-name>/NNN-slice-title.md`.

Use just the first skill for changes small enough to ship in one go. Use both
for anything that benefits from being split into separate, safely-mergeable
steps.

## Format

Both are written in the portable **Agent Skills** format: a `SKILL.md` per
folder with agent-agnostic frontmatter (`name`, `description`). They're meant to
work in any skill-aware agent — Claude Code, OpenAI Codex CLI, etc. — not just
this harness. Where a skill mentions a harness-specific capability (parallel
search agents, a plan-approval step), it says to use your harness's equivalent
or skip it.

## Claude Code shortcuts

For convenience in Claude Code specifically, `/plan` and `/slice` slash commands
(see [.claude/commands/](../commands/)) invoke these two skills directly. They
are optional wrappers, not required — the skills are picked up automatically by
description-matching even without them, and other agents won't have these
slash commands at all.
