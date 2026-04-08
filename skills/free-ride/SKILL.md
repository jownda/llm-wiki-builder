---
name: freeride
description: Manages free AI models from OpenRouter for CoPaw. Automatically ranks models by quality, configures fallbacks for rate-limit handling, and updates CoPaw agent.json. Use when the user mentions free AI, OpenRouter, model switching, rate limits, or wants to reduce AI costs.
---

# FreeRide - Free AI for CoPaw

## What This Skill Does

Configures CoPaw to use **free** AI models from OpenRouter. Sets the best free model as primary, adds ranked fallbacks so rate limits don't interrupt your session, and preserves existing CoPaw config.

> Original skill was built for OpenClaw. This version has been adapted for **CoPaw** — it reads/writes `agent.json` and `config.json` in CoPaw's workspace structure.

## Prerequisites

Before running any FreeRide command, ensure:

1. **OPENROUTER_API_KEY is set.** Check with `echo %OPENROUTER_API_KEY%` (Windows). If empty, get a free key at https://openrouter.ai/keys and set it:
   ```cmd
   set OPENROUTER_API_KEY=sk-or-v1-...
   ```
   On Linux/macOS:
   ```bash
   export OPENROUTER_API_KEY="sk-or-v1-..."
   ```

2. **Python + requests available.** The CoPaw Python runtime is used:
   ```
   # Windows CoPaw embedded Python:
   "C:\Users\Administrator\AppData\Local\CoPaw\python.exe" skills\free-ride\copaw_freeride.py --help
   ```

## Primary Workflow

When the user wants free AI, run these steps:

```cmd
:: Step 1: Set API key (if not already set)
set OPENROUTER_API_KEY=sk-or-v1-xxxxx

:: Step 2: Auto-configure best free model + fallbacks
"C:\Users\Administrator\AppData\Local\CoPaw\python.exe" "%COPAW_WORKING_DIR%\workspaces\<agent_id>\skills\free-ride\copaw_freeride.py" auto

:: Step 3: Restart CoPaw (or start a new session) for changes to take effect
```

That's it. You now have free AI with automatic fallback switching.

Verify by running:
```cmd
"C:\Users\Administrator\AppData\Local\CoPaw\python.exe" "...\skills\free-ride\copaw_freeride.py" status
```

## Commands Reference

| Command | When to use it |
|---------|----------------|
| `copaw_freeride.py auto` | User wants free AI set up (most common) |
| `copaw_freeride.py auto -f` | User wants fallbacks but wants to keep current primary model |
| `copaw_freeride.py auto -c 10` | User wants more fallbacks (default is 5) |
| `copaw_freeride.py list` | User wants to see available free models |
| `copaw_freeride.py list -n 30` | User wants to see more models |
| `copaw_freeride.py switch <model>` | User wants a specific model (e.g. `switch qwen3-coder`) |
| `copaw_freeride.py switch <model> -f` | Add specific model as fallback only |
| `copaw_freeride.py status` | Check current FreeRide configuration |
| `copaw_freeride.py fallbacks` | Update only the fallback models |
| `copaw_freeride.py refresh` | Force refresh the cached model list |

**After any config-changing command, start a new CoPaw session for changes to take effect.**

## What It Writes to Config

FreeRide updates only these keys in `~/.copaw/workspaces/<agent_id>/agent.json`:

- `active_model.provider_id` — set to `"openrouter"`
- `active_model.model` — e.g. `"openrouter/qwen/qwen3-coder:free"`
- `active_model.fallbacks` — e.g. `["openrouter/free", "meta-llama/llama-3.1-8b-instruct:free", ...]`

If `llm_routing` exists, it also updates:
- `llm_routing.local.provider_id`
- `llm_routing.local.model`

Everything else (channels, mcp, tools, security, running, etc.) is preserved.

The first fallback is always `openrouter/free` — OpenRouter's smart router that auto-picks the best available free model based on the request.

## Model Ranking

FreeRide scores each free model on:
- **Context length** (40% weight) — prefers models with more tokens
- **Capabilities** (30% weight) — parameter support count
- **Recency** (20% weight) — newer models score higher
- **Provider trust** (10% weight) — Google, Meta, Mistral, DeepSeek, Qwen, etc. rank higher

Cache is refreshed every 6 hours automatically, or use `refresh` to force.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `OPENROUTER_API_KEY not set` | User needs a key from https://openrouter.ai/keys |
| No free models found | Check API key is valid; try `refresh` |
| Changes not taking effect | Start a new CoPaw session |
| `copaw_freeride.py: command not found` | Use full Python path + script path |
| `requests` not installed | `"COPAW_PYTHON" -m pip install requests` |

## Files

| File | Purpose |
|------|---------|
| `copaw_freeride.py` | CoPaw-adapted CLI entry point |
| `main.py` | Original OpenClaw version (reference) |
| `watcher.py` | Original auto-rotation watcher (OpenClaw-specific, not adapted) |
| `SKILL.md` | This file |
