# Contributing

This repository contains multiple apps in one monorepo:

- `apps/api`
- `apps/admin-web`
- `apps/mobile`

Git branches and pull requests protect work better than local folder-by-folder changes. Use the workflow below for both humans and coding agents.

## Core Rules

- Never work directly on `main`.
- Always start new work from the latest `main`.
- Use one branch per task.
- Open pull requests before merging to `main`.
- Keep commits scoped to the task you are doing.
- Do not use `git reset --hard`, force-push shared branches, or rebase recovery branches unless you fully understand the impact.
- If work was recovered or restored, integrate it on a separate branch first.

## Standard Workflow

1. Update local refs.
2. Move to `main`.
3. Pull the latest remote changes.
4. Create a fresh feature branch.
5. Make only the task-specific changes.
6. Run the narrowest relevant checks locally.
7. Push the branch.
8. Open a pull request.
9. Review the changed file list before merging.

Example:

```bash
git fetch origin
git checkout main
git pull origin main
git checkout -b feature/admin-web-dashboard-filters
```

## Branching Guidance

- Admin web work: branch from updated `main`, keep changes mostly under `apps/admin-web` unless the task explicitly needs shared or root files.
- API work: branch from updated `main`, keep changes under `apps/api` unless the task explicitly needs shared or root files.
- Mobile work: branch from updated `main`, keep changes under `apps/mobile` unless the task explicitly needs shared or root files.
- Recovery work: create a dedicated integration branch from the authoritative base, then cherry-pick or merge the missing work into that branch.

## Pull Request Rules

Before opening a PR:

- Confirm the branch was created from the latest `main`.
- Check `git status` is clean.
- Review `git diff --stat main...HEAD`.
- Review the PR file list in GitHub.
- Confirm you did not accidentally include unrelated files.
- Mention any known follow-up issues in the PR description.

## Local Validation

Run only the checks relevant to the area you changed.

Admin web:

```bash
pnpm --filter admin-web lint
pnpm --filter admin-web typecheck
pnpm --filter admin-web test
pnpm --filter admin-web build
```

API:

```bash
cd apps/api
PYTHONPATH=. pytest tests -m "not integration"
```

Mobile:

```bash
pnpm --filter @ml-workflow/mobile typecheck
```

## Current CI Behavior

GitHub Actions currently runs repository checks defined in `.github/workflows/checks.yml`.

- `api-checks` runs when API-related files change.
- `admin-web-checks` runs when admin-web or related workspace files change.

CI is still defined at the repository level, but the jobs are scoped to relevant file changes so unrelated app work does not fail on another app's checks.

## Guidance For Coding Agents

If you use an AI coding agent or Copilot workflow, include these instructions in the prompt:

- Work on a feature branch, not `main`.
- Fetch and inspect the current branch state before editing.
- Do not overwrite unrelated work.
- Prefer additive recovery on a separate integration branch when restoring missing work.
- Use the narrowest relevant validation after changes.
- Stop before merge and let a human review the PR.

## Recovery Checklist

If something appears missing:

1. Stop and avoid merging more branches immediately.
2. Run `git fetch --all --prune`.
3. Check whether the work exists on `origin/main`, another branch, or in an open PR.
4. Create backup branches before attempting recovery.
5. Create a dedicated integration branch.
6. Bring work forward with `merge`, `cherry-pick`, or `git restore --source ...` depending on scope.
7. Validate on the integration branch.
8. Open a PR and review before merging.