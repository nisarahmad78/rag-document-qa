"""LLM client for answer generation (any OpenAI-compatible API).

Configure with environment variables:
    OPENAI_API_KEY   - your API key
    OPENAI_BASE_URL  - endpoint base URL (default: https://api.openai.com/v1)
    LLM_MODEL        - model name (default: gpt-4o-mini)

If OPENAI_API_KEY is not set, LLMNotConfigured is raised so the API layer
can return a clear message while still returning the retrieved sources.
"""
from .config import settings

SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions strictly from the "
    "provided document excerpts. If the answer is not in the excerpts, say "
    "you could not find it in the uploaded documents. Be concise and cite "
    "the source filename when you use information from an excerpt."
)


class LLMNotConfigured(RuntimeError):
    """Raised when no LLM API key has been configured."""


def build_context(sources: list[dict]) -> str:
    parts = []
    for i, src in enumerate(sources, start=1):
        parts.append(f"[{i}] Source: {src['filename']} (chunk {src['chunk_index']})\n{src['text']}")
    return "\n\n".join(parts)


def generate_answer(question: str, sources: list[dict]) -> str:
    if not settings.llm_configured:
        raise LLMNotConfigured(
            "LLM is not configured. Set OPENAI_API_KEY (and optionally "
            "OPENAI_BASE_URL / LLM_MODEL) in your environment or .env file "
            "to enable answer generation. Retrieval results are still returned."
        )

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Document excerpts:\n\n{build_context(sources)}\n\nQuestion: {question}",
            },
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()
