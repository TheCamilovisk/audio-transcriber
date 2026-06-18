---
name: commit-and-push-reviewed-branch
description: >-
  Commit reviewed changes on the current feature branch and push to the remote
  repository. Use only after the user has reviewed the implementation and
  explicitly asks to commit and push. Does not create a PR.
license: MIT
metadata:
  version: 1.0.0
  authoring-spec: agent-skills (portable SKILL.md)
---

# Commit and push a reviewed branch

Land the reviewed implementation by committing and pushing the current branch.
Does **not** create a pull request unless asked. Harness-agnostic.

## When to use

- The user says "create the necessary commits" or "commit and push".
- The user has already reviewed the changes and explicitly asks to land them.
- You are on the branch containing the reviewed work.

Skip when the user says to create a PR — that is a different operation.

## Process

### 1. Preflight

- Check `git status` and `git branch --show-current`.
- **Refuse if on `main`** — ask the user to confirm they really want to commit
  directly to main.
- If there are uncommitted user changes that you did not add, ask before staging.
- Do **not** pull unless explicitly requested.
- Do **not** force push (`--force`/`--force-with-lease`) unless explicitly
  requested.

### 2. Review changed files

```bash
git status
```

- Show the list of changed/untracked files to the user.
- If files are already staged, preserve the staging as-is.
- If files are unstaged and should be included, stage them.

### 3. Stage and commit

```bash
git add <relevant files>
```

- Stage only the files relevant to the implementation (not build artifacts,
  caches, or unrelated changes).
- Craft a commit message following the project's conventions:
  - First line: a short summary matching the plan/slice title.
  - Body: bullet list of the key changes, one per file or concern.
- Use `git commit -m "..."` or `git commit -m "summary" -m "body..."`.

### 4. Push

```bash
git push -u origin <branch>    # first push (no upstream)
git push                        # subsequent pushes
```

- If the branch has no upstream, use `-u origin <branch>`.
- If an upstream already exists, plain `git push` is sufficient.

### 5. Report

- Commit hash (full or short).
- Branch name.
- Remote tracking branch.
- If the remote prints a PR creation URL, include it for convenience — but
  do **not** create a PR unless explicitly asked.
