"""Probe the remote endpoints and (later) build the LLM element."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import openai

from agentdojo_qwen.config import HarnessConfig, load_config

_PROBE_TOOL = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get the weather for a city",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    },
}


def _client(endpoint: str, api_key: str) -> openai.OpenAI:
    return openai.OpenAI(base_url=endpoint, api_key=api_key)


def list_models(endpoint: str, api_key: str) -> list[str]:
    """Return served model ids, or [] if /models is unavailable."""
    try:
        return [m.id for m in _client(endpoint, api_key).models.list().data]
    except Exception:
        return []


def probe_tool_calls(endpoint: str, api_key: str, model: str) -> bool:
    """True if the model emits native OpenAI tool calls."""
    response = _client(endpoint, api_key).chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "What's the weather in Zurich? Use the tool."}],
        tools=[_PROBE_TOOL],
    )
    return bool(response.choices[0].message.tool_calls)


def _probe_one(endpoint: str, api_key: str, model: str) -> dict[str, Any]:
    result: dict[str, Any] = {"endpoint": endpoint, "model": model}
    discovered = list_models(endpoint, api_key)
    result["available_models"] = discovered
    result["model_source"] = "discovered" if model in discovered else "env"
    try:
        result["native_tool_calls"] = probe_tool_calls(endpoint, api_key, model)
    except Exception as exc:  # keep probing the other endpoint
        result["native_tool_calls"] = None
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def run_probe(config: HarnessConfig) -> dict[str, Any]:
    payload = {
        "victim": _probe_one(config.victim_endpoint, config.victim_api_key, config.victim_model),
        "attacker": _probe_one(
            config.attacker_endpoint, config.attacker_api_key, config.attacker_model
        ),
    }
    out_dir = Path(config.log_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "probe.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe Qwen endpoints for tool-call support.")
    parser.add_argument("--probe", action="store_true", help="Probe endpoints and write probe.json")
    parser.parse_args()
    print(json.dumps(run_probe(load_config()), indent=2))


if __name__ == "__main__":
    main()
