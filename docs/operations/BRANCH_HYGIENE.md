# KUEPER Branch Hygiene

## Purpose

Reduce branch clutter across KUEPER repositories without treating branch names as an archive. Git commit history, merged pull requests, decisions and release tags remain the historical record.

## Current mode: dry run only

`tools/branch_hygiene/branch_hygiene.py` performs metadata-only classification and **never deletes a branch ref**.

Scope is all enabled GitHub repositories in `registry/projects.json` plus explicitly configured metadata-only extras in `config/branch-hygiene.json`. `buecherwelten` is included only for branch/PR metadata hygiene; this does not ingest manuscript content or enable public export.

## Classification

- `KEEP`: default branch, protected branch, head of an open PR, or base of an open/stacked PR.
- `DELETE`: branch is tied to at least one merged PR and no open PR uses it as head or base.
- `REVIEW`: deletion cannot be proven safe. This includes closed-unmerged work, branches without a PR association, ephemeral-looking leftovers without a merged PR, and all `research/*` branches.

Research branches deliberately remain `REVIEW` even after merge because branch metadata alone cannot prove that downstream candidate/follow-up processing is complete.

## Automation

`.github/workflows/branch-hygiene-dry-run.yml` runs weekly and on manual dispatch. It uses the normal cross-repository read credential (`KUEPER_BOT_TOKEN`), runs deterministic safety tests, emits Markdown and JSON reports, and uploads them as a 14-day artifact.

The workflow has no branch-delete permission and no deletion code path.

## Promotion to cleanup mode

A future deletion mode must be a separate reviewed change. It should re-fetch repository and PR state immediately before each deletion, reject default/protected/open-head/open-base branches again at execution time, keep research branches outside automatic deletion until their lifecycle can be proven, and produce an audit record of every deleted ref.
