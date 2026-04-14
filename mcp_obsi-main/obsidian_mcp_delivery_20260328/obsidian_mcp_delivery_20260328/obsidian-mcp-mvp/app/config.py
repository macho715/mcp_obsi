from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "obsidian-mcp-mvp"
    host: str = "127.0.0.1"
    port: int = 8765
    vault_path: Path = Field(alias="VAULT_PATH")
    index_db_path: Path = Field(default=Path("data/memory_index.sqlite3"), alias="INDEX_DB_PATH")
    mcp_api_token: str | None = Field(default=None, alias="MCP_API_TOKEN")
    timezone: str = Field(default="Asia/Dubai", alias="TIMEZONE")

    def normalize(self) -> None:
        self.vault_path.mkdir(parents=True, exist_ok=True)
        self.index_db_path.parent.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.normalize()
