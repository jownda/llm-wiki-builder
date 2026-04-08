#!/usr/bin/env python3
"""
CoPaw FreeRide - Free AI Models from OpenRouter for CoPaw
Adapted from OpenClaw's free-ride skill.

Manages free AI models from OpenRouter, ranks them by quality,
configures fallbacks for rate-limit handling, and updates CoPaw's
agent config (active_model + llm_routing).

Usage:
    copaw-freeride auto           - Auto-select best free model + fallbacks
    copaw-freeride list           - List available free models
    copaw-freeride switch <model> - Switch to a specific model
    copaw-freeride status         - Show current configuration
    copaw-freeride fallbacks      - Configure fallback models only
    copaw-freeride refresh        - Force refresh model cache
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests")
    sys.exit(1)


# ============================================================
# Constants - adapted for CoPaw
# ============================================================
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/models"

# CoPaw config paths (passed via env, or discovered)
COPAW_CONFIG_PATH = None       # Global: ~/.copaw/config.json
COPAW_AGENT_CONFIG_PATH = None # Per-agent: workspace/agent.json

# Cache
CACHE_FILE = None
CACHE_DURATION_HOURS = 6

# Model ranking weights
RANKING_WEIGHTS = {
    "context_length": 0.4,
    "capabilities": 0.3,
    "recency": 0.2,
    "provider_trust": 0.1
}

TRUSTED_PROVIDERS = [
    "google", "meta-llama", "mistralai", "deepseek",
    "nvidia", "qwen", "microsoft", "allenai", "arcee-ai"
]


# ============================================================
# Config Discovery
# ============================================================
def discover_copaw_config() -> tuple:
    """Find CoPaw global config and current agent config paths."""
    global COPAW_CONFIG_PATH, COPAW_AGENT_CONFIG_PATH, CACHE_FILE

    # Try env var first
    working_dir = os.environ.get("COPAW_WORKING_DIR")
    if not working_dir:
        working_dir = str(Path.home() / ".copaw")

    working_dir = Path(working_dir)
    global_config = working_dir / "config.json"

    # Find agent config: look for *.json in workspaces that have id field
    agent_config = None
    workspaces_dir = working_dir / "workspaces"
    if workspaces_dir.exists():
        # Check env var for current agent workspace
        agent_id = os.environ.get("COPAW_AGENT_ID")
        if agent_id:
            candidate = workspaces_dir / agent_id / "agent.json"
            if candidate.exists():
                agent_config = candidate

        # Fallback: scan workspaces for agent.json
        if not agent_config:
            for ws in workspaces_dir.iterdir():
                candidate = ws / "agent.json"
                if candidate.exists():
                    try:
                        data = json.loads(candidate.read_text("utf-8"))
                        if "id" in data:
                            agent_config = candidate
                            break
                    except (json.JSONDecodeError, OSError):
                        continue

    # If still no agent config, try global
    if not agent_config:
        agent_config = working_dir / "config.json"

    COPAW_CONFIG_PATH = global_config if global_config.exists() else None
    COPAW_AGENT_CONFIG_PATH = agent_config if agent_config.exists() else None

    # Cache path
    cache_dir = working_dir / ".cache" / "freeride"
    cache_dir.mkdir(parents=True, exist_ok=True)
    CACHE_FILE = cache_dir / "freeride-cache.json"

    return COPAW_CONFIG_PATH, COPAW_AGENT_CONFIG_PATH


def get_api_key() -> Optional[str]:
    """Get OpenRouter API key from environment or CoPaw config."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if api_key:
        return api_key

    # Try CoPaw global config
    if COPAW_CONFIG_PATH and COPAW_CONFIG_PATH.exists():
        try:
            config = json.loads(COPAW_CONFIG_PATH.read_text("utf-8"))
            # Check mcp providers or tools config for openrouter key
            mcp = config.get("mcp", {})
            for provider in mcp.values():
                key = provider.get("api_key") or provider.get("OPENROUTER_API_KEY")
                if key:
                    return key
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

    # Try agent config
    if COPAW_AGENT_CONFIG_PATH and COPAW_AGENT_CONFIG_PATH.exists():
        try:
            config = json.loads(COPAW_AGENT_CONFIG_PATH.read_text("utf-8"))
            env = config.get("env", {})
            if env.get("OPENROUTER_API_KEY"):
                return env["OPENROUTER_API_KEY"]
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

    return None


# ============================================================
# Model Fetching & Ranking (same logic as original)
# ============================================================
def fetch_all_models(api_key: str) -> list:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(OPENROUTER_API_URL, headers=headers, timeout=30, verify=False)
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])
    except requests.RequestException as e:
        print(f"Warning: SSL retry... ({e})")
        try:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            response = requests.get(OPENROUTER_API_URL, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except requests.RequestException as e2:
            print(f"Error fetching models: {e2}")
            return []


def filter_free_models(models: list) -> list:
    free_models = []
    for model in models:
        model_id = model.get("id", "")
        pricing = model.get("pricing", {})
        prompt_cost = pricing.get("prompt")
        if prompt_cost is not None:
            try:
                if float(prompt_cost) == 0:
                    free_models.append(model)
            except (ValueError, TypeError):
                pass
        if ":free" in model_id and model not in free_models:
            free_models.append(model)
    return free_models


def calculate_model_score(model: dict) -> float:
    score = 0.0
    context_length = model.get("context_length", 0)
    context_score = min(context_length / 1_000_000, 1.0)
    score += context_score * RANKING_WEIGHTS["context_length"]

    capabilities = model.get("supported_parameters", [])
    capability_count = len(capabilities) if capabilities else 0
    capability_score = min(capability_count / 10, 1.0)
    score += capability_score * RANKING_WEIGHTS["capabilities"]

    created = model.get("created", 0)
    if created:
        days_old = (time.time() - created) / 86400
        recency_score = max(0, 1 - (days_old / 365))
        score += recency_score * RANKING_WEIGHTS["recency"]

    model_id = model.get("id", "")
    provider = model_id.split("/")[0] if "/" in model_id else ""
    if provider in TRUSTED_PROVIDERS:
        trust_index = TRUSTED_PROVIDERS.index(provider)
        trust_score = 1 - (trust_index / len(TRUSTED_PROVIDERS))
        score += trust_score * RANKING_WEIGHTS["provider_trust"]

    return score


def rank_free_models(models: list) -> list:
    scored = []
    for model in models:
        score = calculate_model_score(model)
        scored.append({**model, "_score": score})
    scored.sort(key=lambda x: x["_score"], reverse=True)
    return scored


def get_cached_models() -> Optional[list]:
    if CACHE_FILE is None or not CACHE_FILE.exists():
        return None
    try:
        cache = json.loads(CACHE_FILE.read_text("utf-8"))
        cached_at = datetime.fromisoformat(cache.get("cached_at", ""))
        if datetime.now() - cached_at < timedelta(hours=CACHE_DURATION_HOURS):
            return cache.get("models", [])
    except (json.JSONDecodeError, ValueError):
        pass
    return None


def save_models_cache(models: list):
    if CACHE_FILE is None:
        return
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    cache = {"cached_at": datetime.now().isoformat(), "models": models}
    CACHE_FILE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")


def get_free_models(api_key: str, force_refresh: bool = False) -> list:
    if not force_refresh:
        cached = get_cached_models()
        if cached:
            return cached
    all_models = fetch_all_models(api_key)
    free_models = filter_free_models(all_models)
    ranked = rank_free_models(free_models)
    save_models_cache(ranked)
    return ranked


# ============================================================
# CoPaw Config Read/Write
# ============================================================
def load_agent_config() -> dict:
    if COPAW_AGENT_CONFIG_PATH is None or not COPAW_AGENT_CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(COPAW_AGENT_CONFIG_PATH.read_text("utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_agent_config(config: dict):
    if COPAW_AGENT_CONFIG_PATH is None:
        print(f"Error: No agent config path found.")
        sys.exit(1)
    COPAW_AGENT_CONFIG_PATH.write_text(
        json.dumps(config, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"Config saved to: {COPAW_AGENT_CONFIG_PATH}")


def get_current_model(config: dict = None) -> Optional[str]:
    if config is None:
        config = load_agent_config()
    am = config.get("active_model", {})
    provider = am.get("provider_id", "")
    model = am.get("model", "")
    if provider and model:
        return f"{provider}/{model}" if provider else model
    return None


def get_current_fallbacks(config: dict = None) -> list:
    if config is None:
        config = load_agent_config()
    am = config.get("active_model", {})
    return am.get("fallbacks", [])


def update_copaw_model(
    provider_id: str,
    model: str,
    fallbacks: Optional[list] = None,
    as_fallback_only: bool = False
) -> bool:
    """Update CoPaw agent config with model settings."""
    config = load_agent_config()

    # Preserve existing active_model fields, update only relevant ones
    current_am = config.get("active_model", {})

    if not as_fallback_only:
        current_am["provider_id"] = provider_id
        current_am["model"] = model

    if fallbacks is not None:
        current_am["fallbacks"] = fallbacks

    config["active_model"] = current_am

    # Also try to update llm_routing if available
    llm_routing = config.get("llm_routing", {})
    if llm_routing.get("mode") == "cloud_first" or llm_routing.get("mode") == "local_first":
        # Update routing local config
        if "local" not in llm_routing:
            llm_routing["local"] = {}
        llm_routing["local"]["provider_id"] = provider_id
        llm_routing["local"]["model"] = model
        config["llm_routing"] = llm_routing

    save_agent_config(config)
    return True


# ============================================================
# Commands
# ============================================================
def cmd_list(args):
    api_key = get_api_key()
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set")
        print("Set it via: set OPENROUTER_API_KEY=sk-or-v1-...")
        print("Or get a free key at: https://openrouter.ai/keys")
        sys.exit(1)

    print("Fetching free models from OpenRouter...")
    models = get_free_models(api_key, force_refresh=args.refresh if hasattr(args, 'refresh') else False)

    if not models:
        print("No free models available.")
        return

    current = get_current_model()
    fallbacks = get_current_fallbacks()
    limit = getattr(args, 'limit', 15) or 15

    print(f"\nTop {min(limit, len(models))} Free AI Models (ranked by quality):\n")
    print(f"{'#':<3} {'Model ID':<50} {'Context':<12} {'Score':<8} {'Status'}")
    print("-" * 90)

    for i, model in enumerate(models[:limit], 1):
        model_id = model.get("id", "unknown")
        context = model.get("context_length", 0)
        score = model.get("_score", 0)

        if context >= 1_000_000:
            ctx_str = f"{context // 1_000_000}M tokens"
        elif context >= 1_000:
            ctx_str = f"{context // 1_000}K tokens"
        else:
            ctx_str = f"{context} tokens"

        # Check status
        full_id = f"openrouter/{model_id}"
        status = ""
        if current:
            if current.endswith(model_id) or model_id in current:
                status = "[ACTIVE]"
        if full_id in fallbacks or model_id in fallbacks:
            status = "[FALLBACK]"

        print(f"{i:<3} {model_id:<50} {ctx_str:<12} {score:.3f}    {status}")

    if len(models) > limit:
        print(f"\n... and {len(models) - limit} more. Use -n to see more.")
    print(f"\nTotal free models available: {len(models)}")


def cmd_auto(args):
    api_key = get_api_key()
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set")
        sys.exit(1)

    config = load_agent_config()
    current = get_current_model()

    print("Finding best free model...")
    models = get_free_models(api_key, force_refresh=True)

    if not models:
        print("Error: No free models available.")
        sys.exit(1)

    # Skip openrouter/free (it's a smart router, use as fallback only)
    best = None
    for m in models:
        if "openrouter/free" not in m["id"]:
            best = m
            break
    if not best:
        best = models[0]

    model_id = best["id"]
    # Parse provider and model name for CoPaw format
    # OpenRouter model IDs look like: "qwen/qwen3-coder:free"
    # CoPaw provider_id should be "openrouter", model should be the full ID
    provider = "openrouter"
    model_name = model_id

    as_fallback = getattr(args, 'fallback_only', False)
    fallback_count = getattr(args, 'fallback_count', 5) or 5

    if not as_fallback:
        if current:
            print(f"Replacing current: {current}")
        print(f"\nBest free model: {model_name}")
        print(f"Context length: {best.get('context_length', 0):,} tokens")
        print(f"Quality score: {best.get('_score', 0):.3f}")
    else:
        print("Keeping current model, adding fallbacks only.")

    # Build fallback list
    fb_list = []
    fb_list.append("openrouter/free")  # smart router as first fallback
    for m in models[:fallback_count]:
        mid = m["id"]
        if "openrouter/free" in mid:
            continue
        if mid == model_id:
            continue
        fb_list.append(mid)
        if len(fb_list) >= fallback_count + 1:  # +1 for openrouter/free
            break

    update_copaw_model(
        provider_id=provider,
        model=model_name,
        fallbacks=fb_list,
        as_fallback_only=as_fallback
    )

    if not as_fallback:
        print(f"\nCoPaw config updated!")
        print(f"Active: openrouter/{model_name}")
    print(f"Fallbacks ({len(fb_list)}):")
    for fb in fb_list:
        print(f"  - {fb}")
    print("\nNote: Changes take effect on next session or after restarting CoPaw.")


def cmd_switch(args):
    api_key = get_api_key()
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set")
        sys.exit(1)

    model_id = args.model
    as_fallback = getattr(args, 'fallback_only', False)

    models = get_free_models(api_key)
    model_ids = [m["id"] for m in models]

    matched = None
    if model_id in model_ids:
        matched = model_id
    else:
        for mid in model_ids:
            if model_id.lower() in mid.lower():
                matched = mid
                break

    if not matched:
        print(f"Error: Model '{model_id}' not found in free models list.")
        print("Use 'copaw-freeride list' to see available models.")
        sys.exit(1)

    fb_count = getattr(args, 'fallback_count', 5) or 5
    fb_list = []
    fb_list.append("openrouter/free")
    for m in models[:fb_count]:
        mid = m["id"]
        if "openrouter/free" in mid or mid == matched:
            continue
        fb_list.append(mid)
        if len(fb_list) >= fb_count + 1:
            break

    update_copaw_model(
        provider_id="openrouter",
        model=matched,
        fallbacks=fb_list,
        as_fallback_only=as_fallback
    )

    print(f"Success! {'Added to fallbacks' if as_fallback else 'Set as active'}: {matched}")
    print(f"Fallbacks ({len(fb_list)}):")
    for fb in fb_list:
        print(f"  - {fb}")


def cmd_status(args):
    api_key = get_api_key()
    config = load_agent_config()
    current = get_current_model(config)
    fallbacks = get_current_fallbacks(config)

    print("CoPaw FreeRide Status")
    print("=" * 50)

    if api_key:
        masked = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        print(f"OpenRouter API Key: {masked}")
    else:
        print("OpenRouter API Key: NOT SET")
        print("  Set with: set OPENROUTER_API_KEY=sk-or-v1-...")

    print(f"\nActive Model: {current or 'Not configured'}")

    llm_routing = config.get("llm_routing", {})
    if llm_routing.get("enabled"):
        print(f"LLM Routing: enabled (mode: {llm_routing.get('mode', 'unknown')})")
    else:
        print("LLM Routing: disabled")

    if fallbacks:
        print(f"Fallback Models ({len(fallbacks)}):")
        for fb in fallbacks:
            print(f"  - {fb}")
    else:
        print("Fallback Models: None configured")

    if CACHE_FILE and CACHE_FILE.exists():
        try:
            cache = json.loads(CACHE_FILE.read_text("utf-8"))
            cached_at = datetime.fromisoformat(cache.get("cached_at", ""))
            age = datetime.now() - cached_at
            hours = age.seconds // 3600
            mins = (age.seconds % 3600) // 60
            print(f"\nModel Cache: {len(cache.get('models', []))} models (updated {hours}h {mins}m ago)")
        except:
            print("\nModel Cache: Invalid")
    else:
        print("\nModel Cache: Not created")

    if COPAW_AGENT_CONFIG_PATH:
        print(f"\nAgent Config: {COPAW_AGENT_CONFIG_PATH}")


def cmd_refresh(args):
    api_key = get_api_key()
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set")
        sys.exit(1)
    print("Refreshing free models cache...")
    models = get_free_models(api_key, force_refresh=True)
    print(f"Cached {len(models)} free models.")
    print(f"Cache expires in {CACHE_DURATION_HOURS} hours.")


def cmd_fallbacks(args):
    api_key = get_api_key()
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set")
        sys.exit(1)

    config = load_agent_config()
    current = get_current_model(config)
    count = getattr(args, 'count', 5) or 5

    print(f"Current active: {current or 'None'}")
    print(f"Setting up {count} fallback models...")

    models = get_free_models(api_key)
    fb_list = ["openrouter/free"]
    for m in models:
        mid = m["id"]
        if "openrouter/free" in mid:
            continue
        if current and (mid in current or current.endswith(mid.split("/")[-1])):
            continue
        if len(fb_list) > count:
            break
        fb_list.append(mid)

    # Update only fallbacks
    update_copaw_model(
        provider_id=config.get("active_model", {}).get("provider_id", "openrouter"),
        model=config.get("active_model", {}).get("model", ""),
        fallbacks=fb_list,
        as_fallback_only=True
    )

    print(f"\nConfigured {len(fb_list)} fallback models:")
    for i, fb in enumerate(fb_list, 1):
        print(f"  {i}. {fb}")


# ============================================================
# Main
# ============================================================
def main():
    # Discover config paths first
    global_path, agent_path = discover_copaw_config()

    parser = argparse.ArgumentParser(
        prog="copaw-freeride",
        description="CoPaw FreeRide - Free AI Models from OpenRouter for CoPaw"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    list_p = subparsers.add_parser("list", help="List available free models")
    list_p.add_argument("--limit", "-n", type=int, default=15)
    list_p.add_argument("--refresh", "-r", action="store_true")

    switch_p = subparsers.add_parser("switch", help="Switch to a specific model")
    switch_p.add_argument("model", help="Model ID")
    switch_p.add_argument("--fallback-only", "-f", action="store_true")
    switch_p.add_argument("--fallback-count", "-c", type=int, default=5)

    auto_p = subparsers.add_parser("auto", help="Auto-select best free model")
    auto_p.add_argument("--fallback-only", "-f", action="store_true")
    auto_p.add_argument("--fallback-count", "-c", type=int, default=5)

    subparsers.add_parser("status", help="Show current configuration")
    subparsers.add_parser("refresh", help="Force refresh model cache")

    fb_p = subparsers.add_parser("fallbacks", help="Configure fallback models")
    fb_p.add_argument("--count", "-c", type=int, default=5)

    args = parser.parse_args()

    cmds = {
        "list": cmd_list,
        "switch": cmd_switch,
        "auto": cmd_auto,
        "status": cmd_status,
        "refresh": cmd_refresh,
        "fallbacks": cmd_fallbacks,
    }

    if args.command in cmds:
        cmds[args.command](args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
