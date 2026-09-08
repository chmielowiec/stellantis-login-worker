---
name: merge-upstream-pr
description: 'Merge an upstream pull request into this fork, publish a new GHCR image, and avoid the multi-account/SSH auth pitfalls of this repo. Use when: merge PR into fork, fetch pull head, trigger GHCR build, refusing to allow an OAuth App to update workflow, wrong gh account, git push rejected workflow scope.'
---

# Merge an upstream PR into this fork

## Fetching and merging

```bash
git remote add upstream git@github.com:andreadegiovine/homeassistant-stellantis-vehicles-worker-v2.git   # once
git fetch upstream
git fetch upstream "refs/pull/<N>/head:pr-<N>"
git merge-base main pr-<N>          # sanity check: should be a real ancestor of main
git checkout main
git merge pr-<N> --no-edit
python3 -m py_compile main.py && echo OK
```

If `git merge-base main pr-<N>` is far behind `main`, the PR branch is stale relative to
your fork and the merge may pull in unrelated commits — check `git log --oneline
upstream/main..pr-<N>` first to see exactly what the PR itself adds.

## Auth gotchas in this environment

- Multiple `gh` accounts are logged in. Use `GH_TOKEN=$(gh auth token --user chmielowiec)`
  before any `gh api`/`gh run` call against this fork, or it may resolve to the wrong account.
- Push over SSH with the dedicated key, not the default `gh`-issued HTTPS token — the
  HTTPS token can lack the `workflow` OAuth scope and gets rejected with *"refusing to
  allow an OAuth App to create or update workflow ... without workflow scope"* the moment a
  commit touches `.github/workflows/*.yml`:
  ```bash
  git remote set-url origin git@github.com:chmielowiec/stellantis-login-worker.git
  git config core.sshCommand 'ssh -i ~/.ssh/id_ed25519_priv -F /dev/null'
  git config user.email 'robert+github@chmielowiec.net'
  git config user.name 'Robert Chmielowiec'
  ```

## After pushing to main

The `docker-publish.yml` workflow builds and tags `ghcr.io/chmielowiec/stellantis-login-worker:sha-<short>`
automatically. Watch it before treating the fix as live:
```bash
GH_TOKEN=$(gh auth token --user chmielowiec) gh run list --repo chmielowiec/stellantis-login-worker --limit 1 --json databaseId --jq '.[0].databaseId'
GH_TOKEN=$(gh auth token --user chmielowiec) gh run watch <id> --repo chmielowiec/stellantis-login-worker --exit-status
```
Then use the `bump-stack-image` skill (in `homelab-infra`) to pin the new tag and redeploy.

## Debugging a failed login/OAuth flow

Every request logs `[<process_id>]` lines and, on failure, saves
`/tmp/stellantis-<process_id>-{exception,missing-code}.{png,html}` inside the container.
The `logger.warning(...)` line with `current=<url> body=<page text>` is the single most
useful diagnostic — get it before guessing at selector/flow changes.

**Known pitfall (found the hard way):** the Gigya login widget can render inside a child
`<iframe>` rather than the top-level page, so selectors must search `page.frames`, not just
`page.locator()` (which only sees the main frame). But when doing that, don't search for
email, password, and the submit button as three **independent** cross-frame searches — if
more than one frame matches the generic fallback selectors, each field can silently resolve
to a *different* frame, producing a mismatched/incomplete submit that Peugeot legitimately
rejects as "invalid login/password" even with correct credentials. Find the frame once (via
the email selector), then scope password/submit lookups to that exact same frame.
