"""Build an AgentDojo AgentPipeline backed by the remote Qwen endpoint."""

from __future__ import annotations

from agentdojo.agent_pipeline import AgentPipeline, LocalLLM, OpenAILLM
from agentdojo.agent_pipeline.agent_pipeline import PipelineConfig

from agentdojo_qwen.config import HarnessConfig, load_config
from agentdojo_qwen.llm_element import probe_tool_calls

# A FULL key from agentdojo.models.MODEL_NAMES. `get_model_name_from_pipeline` only
# matches full keys as substrings, so appending "GPT-4" would NOT work.
# Required because ImportantInstructionsAttack.__init__ calls it BEFORE any subclass
# can override model_name (important_instructions_attacks.py:43).
_MODEL_NAME_ANCHOR = "gpt-4o-2024-05-13"


def _use_native(config: HarnessConfig) -> bool:
    if config.llm_mode == "native":
        return True
    if config.llm_mode == "prompting":
        return False
    return probe_tool_calls(config.victim_endpoint, config.victim_api_key, config.victim_model)


def build_llm(config: HarnessConfig):
    import openai

    client = openai.OpenAI(base_url=config.victim_endpoint, api_key=config.victim_api_key)
    if _use_native(config):
        return OpenAILLM(client, config.victim_model)
    return LocalLLM(client, config.victim_model, tool_delimiter="tool")


def ensure_name_dependent_attack_compatible(pipeline: AgentPipeline) -> None:
    """Ensure get_model_name_from_pipeline() succeeds for name-dependent attacks."""
    from agentdojo.attacks.base_attacks import get_model_name_from_pipeline

    if _MODEL_NAME_ANCHOR not in (pipeline.name or ""):
        pipeline.name = f"{pipeline.name or 'pipeline'} {_MODEL_NAME_ANCHOR}"
    get_model_name_from_pipeline(pipeline)  # raises if still incompatible


def build_pipeline(
    config: HarnessConfig | None = None, *, name_anchor: bool = False
) -> AgentPipeline:
    config = config or load_config()
    llm = build_llm(config)
    pipeline = AgentPipeline.from_config(
        PipelineConfig(
            llm=llm,
            model_id=None,
            defense=None,
            tool_delimiter="tool",
            system_message_name=None,
            system_message=None,
        )
    )
    # OpenAILLM/LocalLLM have no .name, so from_config leaves pipeline.name as None.
    pipeline.name = f"{config.victim_model} [agentdojo-qwen]"
    if name_anchor:
        ensure_name_dependent_attack_compatible(pipeline)
    return pipeline
