"""Custom AgentDojo attack: generate injections with PyRIT driving the abliterated Qwen."""

from __future__ import annotations

import asyncio

from agentdojo.attacks.attack_registry import register_attack
from agentdojo.attacks.base_attacks import BaseAttack
from agentdojo.base_tasks import BaseInjectionTask, BaseUserTask

from agentdojo_qwen.attacks_qwen_client import INJECTION_TEMPLATE, sanitize_injection
from agentdojo_qwen.config import load_config

_pyrit_ready = False


def _ensure_pyrit_initialized() -> None:
    """Initialize PyRIT exactly once, and ONLY before an OpenAIChatTarget is built."""
    global _pyrit_ready
    if _pyrit_ready:
        return
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        pass  # no running loop -> safe to asyncio.run
    else:
        raise RuntimeError(
            "PyRITInjectionAttack cannot initialize PyRIT from inside a running event loop."
        )
    from pyrit.setup import IN_MEMORY, initialize_pyrit_async

    asyncio.run(initialize_pyrit_async(memory_db_type=IN_MEMORY, silent=True))
    _pyrit_ready = True


@register_attack
class PyRITInjectionAttack(BaseAttack):
    """Generate injection strings with a PyRIT PromptSendingAttack against the attacker LLM."""

    name = "pyrit_qwen_attacker"

    def __init__(self, task_suite, target_pipeline) -> None:
        super().__init__(task_suite, target_pipeline)
        # CRITICAL: PyRIT must be initialized BEFORE OpenAIChatTarget is constructed,
        # or it raises "Central memory instance has not been set".
        _ensure_pyrit_initialized()

        from pyrit.executor.attack import PromptSendingAttack
        from pyrit.prompt_target import OpenAIChatTarget

        cfg = load_config()
        attacker_target = OpenAIChatTarget(  # keyword args only
            endpoint=cfg.attacker_endpoint,
            api_key=cfg.attacker_api_key,
            model_name=cfg.attacker_model,
        )
        self._attack = PromptSendingAttack(objective_target=attacker_target)

    def _generate(self, prompt: str) -> str:
        result = asyncio.run(self._attack.execute_async(objective=prompt))
        piece = result.last_response
        raw = (piece.converted_value if piece else "") or (piece.original_value if piece else "")
        return sanitize_injection(raw)

    def attack(self, user_task: BaseUserTask, injection_task: BaseInjectionTask) -> dict[str, str]:
        prompt = INJECTION_TEMPLATE.format(goal=injection_task.GOAL, user_task=user_task.PROMPT)
        text = self._generate(prompt)
        if not text:
            raise ValueError(
                f"PyRIT attacker returned empty injection for user_task={user_task.ID}, "
                f"injection_task={injection_task.ID}"
            )
        return {placeholder: text for placeholder in self.get_injection_candidates(user_task)}
