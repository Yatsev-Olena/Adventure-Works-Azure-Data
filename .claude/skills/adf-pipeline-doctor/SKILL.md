---
name: adf-pipeline-doctor
description: Diagnose and fix failed or no-op Azure Data Factory ingestion pipelines (especially manifest-driven Lookup -> ForEach -> Copy bronze ingestion). Use when an ADF pipeline run failed, the sink/bronze container is empty, a Copy activity errors (404/auth/path), or you need to verify a pipeline actually moved data rather than just reporting "Succeeded".
---

# ADF Pipeline Doctor

## Overview

A disciplined method for debugging Azure Data Factory pipelines: read the real error before guessing, run the cheapest checks first, fix at the layer that actually runs, then verify against the sink — not the status badge. Built for the common `Lookup (manifest) -> ForEach -> Copy` ingestion pattern, but the workflow generalizes.

## Core principle

A green "Succeeded" is not proof of success. A ForEach over an empty list succeeds and moves nothing. Verify **files/bytes at the sink**, not the run status.

## Workflow

### 1. Map the artifacts before touching anything
Read the pipeline JSON and every artifact it references:
- Pipeline → activities, dependencies, `@item()` / `@activity()` expressions.
- Datasets (source + sink) → linked service, parameters, location/path expressions.
- Linked services → base URL / endpoint, auth type (anonymous, MI, key).
- **The manifest/config the Lookup reads** (e.g. `git.json`). This is the data contract — most ingestion bugs live here (wrong base path, stale repo, typo'd filename/extension).

### 2. Read the actual error — do not theorize first
```bash
AZ="C:/Program Files/Microsoft SDKs/Azure/CLI2/wbin/az.cmd"   # az is often NOT on PATH on Windows
# Most recent runs + top-level message
"$AZ" datafactory pipeline-run query-by-factory \
  --resource-group <rg> --factory-name <factory> \
  --last-updated-after <ISO> --last-updated-before <ISO> \
  --filters operand=PipelineName operator=Equals values=<pipeline>
# Per-activity error / counters for a specific run
"$AZ" datafactory activity-run query-by-pipeline-run \
  --resource-group <rg> --factory-name <factory> --run-id <runId> \
  --last-updated-after <ISO> --last-updated-before <ISO>
```
The activity-level `error` and `output` tell you exactly which activity failed and why. Read it before proposing a cause.

### 3. Run the cheapest external check first
For HTTP/REST sources, probe the source directly — no Azure needed:
```bash
curl -s -o /dev/null -w "%{http_code}\n" "<full source URL>"
```
A `404` means the source path is dead (renamed repo, wrong branch, moved folder) — no amount of rerunning or role propagation fixes it. Confirm the **replacement** URL returns `200` before editing the manifest, so you don't trade one 404 for another.

### 4. Distinguish real success from a no-op
For each Copy activity, pull its `output`:
- `filesWritten` / `filesRead` > 0 and `dataRead == dataWritten` → real movement.
- All zero but status Succeeded → empty input (check the Lookup output / ForEach `items`).
- Copies **without schema mapping report bytes** (`dataRead`/`dataWritten`), not rows — `rowsRead/rowsCopied` being blank is normal for a passthrough bronze copy.
- `dataConsistencyVerification: Unsupported` on an HTTP source is expected, not a failure.

### 5. Fix at the layer that actually executes
A Lookup reads the **deployed config blob**, not the repo file. Fixing `ADF-Script/git.json` in git alone changes nothing at runtime. Update **both**:
```bash
"$AZ" storage blob upload --account-name <acct> --auth-mode key \
  --container-name <config-container> --name <manifest>.json --file <local> --overwrite
```
Keep edits minimal and reversible: repoint the broken URL, fix the obvious typo, leave working config alone.

### 6. Re-run and verify against the sink
```bash
"$AZ" datafactory pipeline create-run --resource-group <rg> --factory-name <factory> --name <pipeline>
# poll pipeline-run show until status != InProgress/Queued, then:
"$AZ" storage blob list --account-name <acct> --auth-mode key --container-name <sink> -o table
```
Confirm every expected file is present with **non-zero bytes**. Cross-check count == manifest length.

## Windows / auth gotchas
- `az` is frequently not on PATH — use the full path `C:/Program Files/Microsoft SDKs/Azure/CLI2/wbin/az.cmd`.
- The interactive login user often lacks **data-plane** RBAC (`Storage Blob Data Contributor`) even when it can manage the account. `--auth-mode login` then fails on blob read/write. Use `--auth-mode key` — az fetches the account key via ARM automatically.
- **Never** write account keys, SAS tokens, or connection strings into a file. Passing/auto-fetching a key transiently in a command is fine; persisting it is not.

## Common root causes (ranked)
1. Manifest points at a **stale/foreign source path** → 404 on every Copy.
2. Filename/extension typo in the manifest (e.g. `.cvsv`) → wrong sink artifact.
3. Source fixed in repo but **not redeployed** to the live config blob.
4. MI missing `Storage Blob Data Contributor` on the sink (real, but rarer than path bugs — don't reach for "role propagation" before ruling out 404s).
5. Empty Lookup output → ForEach iterates nothing → silent no-op "success".

## This project (concrete values)
- Factory `adf-adventureworks-35chlk`, RG `rg-adventureworks`, storage `stadventurewksicop2a`.
- Pipeline `pl_ingest_bronze`: `Lookup_git` (reads `config/git.json`) → `ForEach_files` → `Copy_to_bronze` (HTTP `raw.githubusercontent.com` → `bronze/<folder>/<file>`).
- Manifest must point at `Yatsev-Olena/Adventure-Works-Azure-Data/main/Datasets/*.csv`.
