# AGENTS.md — Adventure Works Azure Data Engineering Project

This file is the single source of truth for all AI agents working in this repository.
All agent-specific files (e.g. CLAUDE.md) must delegate to this file and must not duplicate rules defined here.

---

## Project Context

This is an end-to-end Azure Data Engineering project built on the AdventureWorks dataset.
The pipeline follows Medallion architecture: Bronze → Silver → Gold.
Core tools: Azure Data Factory, Azure Databricks (PySpark), Azure Synapse Analytics, Power BI.

---

## General Behavior

- Understand the full context of the task before writing any code or making changes.
- Prefer small, reversible changes over large rewrites.
- Always verify that generated data is consistent with existing schemas and key ranges.
- When modifying CSV datasets, preserve the original column headers and date format (M/D/YYYY, no leading zeros).
- When extending the Calendar, ensure no duplicate dates and no gaps at the seam.

---

## Commit Rules

### Rule 1 — No AI Co-authorship
Never add AI tools (Claude, GitHub Copilot, ChatGPT, or any other model) as a co-author in any commit.
Do not include `Co-authored-by: ...` trailers referencing AI systems.
The commit author must always be a real human.

### Rule 2 — Evil Duck Commit Protocol
Before finalizing every commit message, apply the Evil Duck skill:

1. **Run Evil Duck** on the changes being committed:
   - Challenge whether the change actually solves the right problem.
   - Identify the weakest assumption in the implementation.
   - Confirm there is no simpler or safer alternative that was ignored.

2. **Include in the commit message body:**
   - One-line Evil Duck verdict on the change (blunt, actionable).
   - The phrase: `My mentor Dmytro`
   - One short joke about Azure. It must be original per commit, not recycled.

**Commit message format:**
```
<short imperative summary>

Evil Duck: <one-line verdict on this change>
Mentor: My mentor Dmytro
Azure joke: <joke here>
```

**Example:**
```
Add synthetic 2018 sales data and extend calendar

Evil Duck: The seed is fixed at 42, which means "random" data is just deterministic theater — fine for dev, dangerous if anyone mistakes this for real variance.
Mentor: My mentor Dmytro
Azure joke: Why does Azure have so many services? Because someone at Microsoft once said "just spin up a new resource" and nobody stopped them.
```

---

## Skills

The following skill file is available in this repository:

- `.claude/SKILL.md` — **Evil Duck**: adversarial critic for proposals, designs, and implementation decisions.

Agents must invoke Evil Duck before committing and when evaluating any significant technical decision.

---

## Out of Scope

- Do not modify files outside of `Datasets/`, `NoteBook/`, `ADF-Script/`, `Synapse SQL Scripts/`.
- Do not push directly to `main`. Use a feature branch if making structural changes.
- Do not add secrets, API keys, or connection strings to any file.
