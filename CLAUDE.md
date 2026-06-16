# OxChief Client (public) — agent guide

This is the **open-source / customer-facing mirror** of the OxChief mower Raspberry Pi autopilot
client. The actively-developed client lives in the private sibling repo `oxchief-client-private`;
changes flow here as a curated mirror. Trunk: **`main`**.

> ⚠️ This repo is **public**. Internal cross-repo + infrastructure facts (server topology, where
> production runs, host addresses, integration contracts) are intentionally **NOT** documented here —
> they live in the **private** `oxchief-server` repo (`docs/REPOS.md`). Do not add internal infra
> details (host IPs, prod endpoints, credentials) to anything committed in this repo.

## Conventions
- Branch naming: `wt/<type>-<ticket>-<slug>` (type ∈ feat/fix/sec/safety/ops/docs/chore); short-lived,
  squash-merge, delete on merge. Agent worktrees stay under `.claude/worktrees/` (gitignored).
