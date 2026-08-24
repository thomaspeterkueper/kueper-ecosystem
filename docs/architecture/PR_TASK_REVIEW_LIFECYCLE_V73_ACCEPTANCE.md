# V7.3 acceptance checks

- Repository implementation that opens a PR transitions to `review_pending`, not `completed`.
- One persisted review generation exists per originating task + PR head SHA.
- Unchanged PR heads do not create repeated review spend or REVIEW_FIX tasks.
- PASS is invalid when any blocking finding exists.
- CHANGES_REQUIRED creates exactly one idempotent REVIEW_FIX task for the reviewed head.
- REVIEW_FIX updates the existing PR branch and never opens a second PR.
- A stale REVIEW_FIX does not overwrite a newer PR head.
- A changed PR head is reviewed again.
- Only a PASS recorded for the current reviewed head can complete the originating task.
- V0.1 has no auto-merge authority.
