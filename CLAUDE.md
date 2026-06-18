# CLAUDE.md — Claude-specific Configuration

This file configures Claude's behavior in this repository.
All project rules are defined in `AGENTS.md`. This file does not duplicate them — it only adds Claude-specific settings on top.

**Read `AGENTS.md` first. Follow it fully. Everything below is additive.**

---

## Model

Use `claude-opus-4-5` with `thinking` budget set to `medium` (this corresponds to effort: mid).

In API terms:
```json
{
  "model": "claude-opus-4-5",
  "thinking": { "type": "enabled", "budget_tokens": 8000 }
}
```

---

## Claude-specific Behavior

- When running the Evil Duck commit protocol (defined in `AGENTS.md`), invoke it with the exact prompt pattern from `.claude/SKILL.md`:
  > *"Use Evil Duck. Critique this proposal as an adversarial discussion partner. Be blunt and sarcastic where useful, but keep every criticism actionable. End with the strongest improved solution."*

- After Evil Duck critique, summarize the verdict into one sentence for the commit message body as required by `AGENTS.md`.

- For Azure jokes in commit messages: generate them using your own reasoning, do not repeat jokes across commits in the same session.

---

## What This File Does NOT Do

- It does not redefine commit rules — those live in `AGENTS.md`.
- It does not redefine project context — that lives in `AGENTS.md`.
- It does not override any rule from `AGENTS.md`.

If there is ever a conflict between this file and `AGENTS.md`, `AGENTS.md` wins.
