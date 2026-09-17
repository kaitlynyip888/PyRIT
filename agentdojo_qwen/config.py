"""Environment-based configuration for the AgentDojo + Qwen harness."""

from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
except ImportError:  # dotenv is optional; shell env is the primary source
    load_dotenv = None

_ENV_FILES = (
    os.path.expanduser("~/.pyrit/.env"),
    os.path.expanduser("~/.pyrit/.env.local"),
)


def _load_env_files() -> None:
    """Best-effort: load ~/.pyrit env files without overriding shell vars."""
    if load_dotenv is None:
        return
    for path in _ENV_FILES:
        if os.path.exists(path):
            load_dotenv(path)  # override=False -> shell exports win


def _mask(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 6:
        return "***"
    return f"{value[:2]}***{value[-2:]}"


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"{name} must be set")
    return value


@dataclass(frozen=True, repr=False)
class HarnessConfig:
    victim_endpoint: str
    victim_api_key: str
    victim_model: str
    attacker_endpoint: str
    attacker_api_key: str
    attacker_model: str
    benchmark_version: str
    log_dir: str
    llm_mode: str

    def __repr__(self) -> str:
        return (
            "HarnessConfig("
            f"victim_endpoint={self.victim_endpoint!r}, "
            f"victim_api_key={_mask(self.victim_api_key)!r}, "
            f"victim_model={self.victim_model!r}, "
            f"attacker_endpoint={self.attacker_endpoint!r}, "
            f"attacker_api_key={_mask(self.attacker_api_key)!r}, "
            f"attacker_model={self.attacker_model!r}, "
            f"benchmark_version={self.benchmark_version!r}, "
            f"log_dir={self.log_dir!r}, "
            f"llm_mode={self.llm_mode!r})"
        )

    __str__ = __repr__


def load_config() -> HarnessConfig:
    _load_env_files()
    return HarnessConfig(
        victim_endpoint=os.environ.get("AGENTDOJO_QWEN_ENDPOINT", "https://llm.oasishpc.hk/v1"),
        victim_api_key=_require("AGENTDOJO_QWEN_API_KEY"),
        victim_model=os.environ.get("AGENTDOJO_QWEN_MODEL", "Qwen3.8-27B-FP8"),
        attacker_endpoint=os.environ.get(
            "AGENTDOJO_ATTACKER_ENDPOINT", "https://oac500-qwen25ablite.oasishpc.hk/v1"
        ),
        attacker_api_key=os.environ.get("AGENTDOJO_ATTACKER_API_KEY", "EMPTY"),
        attacker_model=_require("AGENTDOJO_ATTACKER_MODEL"),
        benchmark_version=os.environ.get("AGENTDOJO_BENCHMARK_VERSION", "v1.2.2"),
        log_dir=os.environ.get("AGENTDOJO_LOG_DIR", "agentdojo_qwen/runs"),
        llm_mode=os.environ.get("AGENTDOJO_LLM_MODE", "auto"),
    )
