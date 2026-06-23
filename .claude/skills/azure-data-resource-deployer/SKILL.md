---
name: azure-data-resource-deployer
description: Provision and deploy Azure data-engineering resources from scratch or incrementally - resource group, ADLS/Blob storage with containers, Azure Data Factory, managed-identity RBAC, and ADF artifacts (linked services, datasets, pipelines, config manifests). Use when asked to create/deploy/provision Azure data resources, stand up a medallion (bronze/silver/gold) landing zone, wire ADF to storage via managed identity, or push ADF JSON artifacts to a live factory.
---

# Azure Data Resource Deployer

## Overview

A repeatable, verify-as-you-go method for standing up the Azure pieces of a data-engineering pipeline. Deploy in dependency order, prefer managed identity over keys, make every step idempotent, and confirm each resource exists before building the next thing on top of it.

## Principles

- **Dependency order, never skip ahead.** A role assignment needs the identity; a container needs the account; an ADF artifact needs its linked service.
- **Idempotent by default.** Re-running the deploy should not error or duplicate. Check-then-create, or use create commands that tolerate existing resources.
- **Managed identity > keys.** Wire ADF → storage with the factory's system-assigned MI and an RBAC role. Do not bake account keys or connection strings into linked services or files.
- **Verify each step before the next.** A "command returned 0" is not proof; query the resource back.

## Deploy order

```bash
AZ="C:/Program Files/Microsoft SDKs/Azure/CLI2/wbin/az.cmd"   # az is often NOT on PATH on Windows
RG=<rg>; LOC=<region>; ACCT=<storage>; FACTORY=<factory>
```

### 1. Resource group
```bash
"$AZ" group create --name "$RG" --location "$LOC"
```

### 2. Storage account (+ ADLS Gen2 if needed)
```bash
"$AZ" storage account create --name "$ACCT" --resource-group "$RG" --location "$LOC" \
  --sku Standard_LRS --kind StorageV2 --hns true   # --hns true = ADLS Gen2 hierarchical namespace
```
Storage account names: 3–24 chars, lowercase letters+digits, globally unique. Add a short random suffix to avoid collisions.

### 3. Containers (medallion + config)
```bash
for c in bronze silver gold config; do
  "$AZ" storage container create --name "$c" --account-name "$ACCT" --auth-mode login
done
```

### 4. Data Factory
```bash
"$AZ" datafactory create --resource-group "$RG" --factory-name "$FACTORY" --location "$LOC"
```

### 5. Grant the factory's managed identity access to storage
```bash
MI=$("$AZ" datafactory show -g "$RG" -n "$FACTORY" --query identity.principalId -o tsv)
SCOPE=$("$AZ" storage account show -g "$RG" -n "$ACCT" --query id -o tsv)
"$AZ" role assignment create --assignee "$MI" \
  --role "Storage Blob Data Contributor" --scope "$SCOPE"
```
RBAC propagation can lag a few minutes — if the first pipeline run fails on auth, retry before assuming misconfiguration (but rule out path/404 bugs first — those are far more common).

### 6. Deploy ADF artifacts (in order: linked services → datasets → pipelines)
```bash
"$AZ" datafactory linked-service create -g "$RG" --factory-name "$FACTORY" \
  --linked-service-name <name> --properties @ADF-Script/linkedService/<name>.json
"$AZ" datafactory dataset create -g "$RG" --factory-name "$FACTORY" \
  --dataset-name <name> --properties @ADF-Script/dataset/<name>.json
"$AZ" datafactory pipeline create -g "$RG" --factory-name "$FACTORY" \
  --name <name> --pipeline @ADF-Script/pipeline/<name>.json
```

### 7. Upload config/manifest blobs the pipeline reads at runtime
```bash
"$AZ" storage blob upload --account-name "$ACCT" --auth-mode key \
  --container-name config --name git.json --file ADF-Script/git.json --overwrite
```

## Verify after deploy
```bash
"$AZ" group show -n "$RG" --query properties.provisioningState -o tsv
"$AZ" storage container list --account-name "$ACCT" --auth-mode login --query "[].name" -o tsv
"$AZ" datafactory linked-service list -g "$RG" --factory-name "$FACTORY" --query "[].name" -o tsv
"$AZ" datafactory dataset list      -g "$RG" --factory-name "$FACTORY" --query "[].name" -o tsv
"$AZ" datafactory pipeline list     -g "$RG" --factory-name "$FACTORY" --query "[].name" -o tsv
"$AZ" role assignment list --assignee "$MI" --scope "$SCOPE" --query "[].roleDefinitionName" -o tsv
```
Then trigger the pipeline and verify the sink (see the `adf-pipeline-doctor` skill for run + sink verification).

## Windows / auth gotchas
- `az` is frequently not on PATH — use the full path `C:/Program Files/Microsoft SDKs/Azure/CLI2/wbin/az.cmd`.
- The interactive login user often lacks **data-plane** RBAC (`Storage Blob Data Contributor`), so `--auth-mode login` fails on blob upload/list while management-plane commands still work. Use `--auth-mode key` for blob data ops — az fetches the account key via ARM. **Never persist keys/SAS/connection strings to a file.**
- Assigning the MI a data role does **not** grant your own login that role; they are separate principals.

## Out of scope / cautions
- This stands up infrastructure and is outward-facing and billable. Confirm region, SKU, and naming before creating anything; deletion/recreation is not free or instant.
- Do not embed secrets in artifacts or commit them. Keep linked-service auth on managed identity.

## This project (concrete values)
- RG `rg-adventureworks` (`westeurope`), storage `stadventurewksicop2a` (Standard_LRS, StorageV2), factory `adf-adventureworks-35chlk`.
- Containers: `bronze`, `config`. MI granted `Storage Blob Data Contributor` on the storage account.
- Artifacts under `ADF-Script/{linkedService,dataset,pipeline}/`; manifest `config/git.json`.
- Related: `adf-pipeline-doctor` (diagnose/verify the pipeline once deployed).
