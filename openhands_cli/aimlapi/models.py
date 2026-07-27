"""AIMLAPI provider metadata for the CLI settings picker.

AIMLAPI (https://aimlapi.com) exposes 300+ models behind one OpenAI-compatible
key. LiteLLM routes them via its ``aiml`` provider, so a model saved as
``aiml/<catalog-id>`` reaches AIMLAPI. The provider already appears in the
picker via litellm/the SDK as the bare id ``aiml``; this module (1) presents it
under the AIMLAPI brand (label ``aimlapi.com``) and (2) supplies a curated
model list for it.

The list below is the flagship tool-calling chat set taken verbatim from
``GET /v1/models``; keep it in sync with the web integration's model list.
"""

# LiteLLM's registered provider id for AIMLAPI. This value MUST stay "aiml":
# litellm only knows the provider as "aiml" (there is no "aimlapi" alias), and
# the settings screen saves a basic-mode choice as ``{provider}/{model}`` — so a
# selection routes as ``aiml/<catalog-id>``. It is never shown to the user; the
# picker displays AIMLAPI_PROVIDER_LABEL instead.
AIML_LITELLM_PROVIDER = "aiml"
# How AIMLAPI is shown in the provider dropdown.
AIMLAPI_PROVIDER_LABEL = "aimlapi.com"

# Catalog ids as returned by AIMLAPI ``GET /v1/models`` (the picker adds the
# ``aiml/`` provider prefix when saving). Current flagship tool-calling chat
# models; keep in sync with the SDK's VERIFIED_MODELS["aiml"] list.
AIMLAPI_MODELS: list[str] = [
    # Anthropic
    "anthropic/claude-opus-5",
    "anthropic/claude-opus-4.8",
    "anthropic/claude-sonnet-5",
    "anthropic/claude-fable-5",
    # OpenAI
    "openai/gpt-5.6-luna-pro",
    "openai/gpt-5.6-sol-pro",
    "openai/gpt-5.6-terra-pro",
    # Google
    "google/gemini-3.6-flash",
    # xAI
    "x-ai/grok-4-5",
    # DeepSeek
    "deepseek/deepseek-v4-pro",
    # Alibaba Qwen
    "alibaba/qwen3.7-max",
    # Zhipu GLM
    "zhipu/glm-5.2",
    # Moonshot
    "moonshot/kimi-k3",
    # MiniMax
    "minimax/minimax-m3",
]
