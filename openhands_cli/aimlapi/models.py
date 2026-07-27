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

# Catalog ids WITHOUT the ``aiml/`` prefix (the picker adds the provider prefix
# when saving). Keep in sync with the web integration's AIMLAPI_MODELS.
AIMLAPI_MODELS: list[str] = [
    # OpenAI
    "openai/gpt-5.2-codex",
    "openai/gpt-5-codex",
    "openai/gpt-4.1",
    "openai/gpt-4.1-mini",
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    # Anthropic
    "anthropic/claude-opus-4.8",
    "anthropic/claude-sonnet-4.6",
    "anthropic/claude-sonnet-4.5",
    "anthropic/claude-haiku-4.5",
    # Google
    "google/gemini-2.5-pro",
    "google/gemini-2.5-flash",
    # DeepSeek
    "deepseek/deepseek-v4-pro",
    "deepseek/deepseek-chat-v3.1",
    # Alibaba Qwen
    "Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8",
    "Qwen/Qwen3-235B-A22B-Thinking-2507",
    # Meta Llama
    "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    # Mistral
    "mistralai/mistral-large-2512",
    "mistralai/mistral-medium-3.1",
    # Moonshot
    "moonshot/kimi-k2-7-code",
]
