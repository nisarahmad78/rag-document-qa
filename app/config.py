"""Application configuration, read from environment variables.

Copy .env.example to .env for local development, or export the variables
in your shell / container runtime.
"""
import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_dotenv() -> None:
    """Minimal .env loader so we don't need an extra dependency."""
    env_file = BASE_DIR / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()


@dataclass
class Settings:
    # LLM (any OpenAI-compatible endpoint)
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")

    # Embeddings (local model, no API key needed)
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # Storage
    data_dir: Path = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
    chroma_dir: Path = Path(os.getenv("CHROMA_DIR", BASE_DIR / "data" / "chroma"))

    @property
    def llm_configured(self) -> bool:
        return bool(self.openai_api_key)


settings = Settings()
