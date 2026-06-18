---
name: vertical-slice-plan
description: >-
  Decompose an approved implementation plan into vertical slices — small,
  dependency-ordered, independently mergeable units that each cut through all
  layers and carry their own tests. Use when a plan is too big to ship at once,
  when the user asks to break work into slices/increments/PRs, or to sequence a
  large change so every step leaves the suite green. Consumes a plan produced by
  the create-implementation-plan skill.
license: MIT
metadata:
  version: 1.0.0
  authoring-spec: agent-skills (portable SKILL.md)
---

# Decompose a plan into vertical slices

A vertical slice is the smallest change that delivers working, tested behavior on
its own. "Vertical" means it cuts through every layer it touches (code + tests +
docs) rather than landing one horizontal layer at a time. This skill turns one
big plan into an ordered set of slice plans. Harness-agnostic.

## When to use

- An approved implementation plan is large or multi-component.
- The user asks to "break this into slices / increments / smaller PRs", or to
  sequence the work safely.
- You want each merge to leave the build and test suite green.

## Principles

- **Don't re-design — decompose.** Start from the approved plan's scope. The
  union of all slices must equal that scope exactly: nothing added, nothing
  dropped.
- **Dependency-ordered.** Slice N+1 builds on slice N. Foundational utilities
  first; integration last.
- **Each slice ends green.** After any single slice merges, the build passes,
  tests pass, and the app still runs.
- **Each slice is vertical.** It carries its own unit/integration tests — the
  "units that ensure code quality" — not deferred to a final test slice.
- **Introduce-with-use.** Prefer landing a new component together with its first
  caller in the same slice, so no slice leaves dead/unused code behind. Split a
  component from its wiring only when the user explicitly wants smaller PRs.

## Process

1. **Read the parent plan** and confirm its full scope and any confirmed
   decisions. Note its house style — your slices should match it.
2. **Identify slice boundaries.** Walk the dependency order: shared foundations
   → components that use them → end-to-end wiring + docs. Each boundary must be
   independently mergeable and green.
3. **Confirm granularity with the user** when there's a real trade-off (e.g.
   "introduce component + wiring together" vs "split into two PRs"). This changes
   the deliverable, so ask rather than assume.
4. **Write one file per slice.** Place them in a folder named after the parent
   plan file: `.resources/plans/<parent-plan-name>/NNN-slice-title.md`, slices
   numbered sequentially from `001`. Each slice file mirrors the parent's style:
   - **Context** — what this slice delivers and why it is safe to merge alone:
     what it depends on (link sibling slices), what stays green.
   - **Changes** — concrete files to add/edit with the relevant snippets copied
     from the parent plan; reuse existing seams (cite `path:line`).
   - **Tests** — the unit/integration tests this slice adds.
   - **Verification** — the per-slice green check plus standard build/lint/test
     commands; a manual smoke test on the final integration slice.
   - **Notes** (final slice) — carry forward the parent's deferred/future work.
   Cross-link slices and back to the parent plan with relative links.
5. **Verify coverage.** Confirm the union of slices equals the parent scope —
   list each parent change and the slice that owns it; no orphans.

## Conventions

- Slice folder name == parent plan filename (without extension).
- Slices: zero-padded sequential numbers, dependency-ordered.
- Every slice file is self-contained and executable from the file alone.
- No production code is written by this skill — it only produces the slice plans.

## Quality bar

- Each slice, merged alone, leaves the suite green and the app runnable.
- Each slice carries its own tests; none defers quality checks downstream.
- The slice set is collectively exhaustive and mutually exclusive vs the parent
  plan — full coverage, no overlap.
