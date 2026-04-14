from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_name: str = "obsidian-mcp"
    vault_path: Path = Field(default=Path("./vault"), alias="VAULT_PATH")
    index_db_path: Path = Field(default=Path("./data/memory_index.sqlite3"), alias="INDEX_DB_PATH")
    mcp_api_token: str = Field(default="dev-change-me", alias="MCP_API_TOKEN")
    chatgpt_mcp_write_token: str = Field(default="", alias="CHATGPT_MCP_WRITE_TOKEN")
    claude_mcp_write_token: str = Field(default="", alias="CLAUDE_MCP_WRITE_TOKEN")
    mcp_allowed_hosts: str = Field(default="", alias="MCP_ALLOWED_HOSTS")
    mcp_allowed_origins: str = Field(default="", alias="MCP_ALLOWED_ORIGINS")
    mcp_hmac_secret: str = Field(default="", alias="MCP_HMAC_SECRET")
    railway_public_domain: str = Field(default="", alias="RAILWAY_PUBLIC_DOMAIN")
    railway_static_url: str = Field(default="", alias="RAILWAY_STATIC_URL")
    railway_service_mcp_server_url: str = Field(default="", alias="RAILWAY_SERVICE_MCP_SERVER_URL")
    timezone: str = Field(default="Asia/Dubai", alias="TIMEZONE")
    obs_vault_name: str = Field(default="mcp_obsidian_vault", alias="OBS_VAULT_NAME")
    wiki_overlay_dirname: str = Field(default="wiki", alias="WIKI_OVERLAY_DIRNAME")

    @staticmethod
    def _csv(value: str) -> list[str]:
        return [item.strip() for item in value.split(",") if item.strip()]

    @property
    def mcp_allowed_hosts_list(self) -> list[str]:
        return self._csv(self.mcp_allowed_hosts)

    @property
    def mcp_allowed_origins_list(self) -> list[str]:
        return self._csv(self.mcp_allowed_origins)

    @property
    def runtime_allowed_hosts_list(self) -> list[str]:
        hosts = self.mcp_allowed_hosts_list.copy()
        for candidate in [
            self.railway_public_domain,
            self.railway_static_url,
            self.railway_service_mcp_server_url,
        ]:
            if candidate and candidate not in hosts:
                hosts.append(candidate)
        return hosts

    @property
    def runtime_allowed_origins_list(self) -> list[str]:
        origins = self.mcp_allowed_origins_list.copy()
        for candidate in [
            self.railway_public_domain,
            self.railway_static_url,
            self.railway_service_mcp_server_url,
        ]:
            if not candidate:
                continue
            origin = candidate if candidate.startswith("http") else f"https://{candidate}"
            if origin not in origins:
                origins.append(origin)
        return origins

    @property
    def mcp_hmac_enabled(self) -> bool:
        return bool(self.mcp_hmac_secret.strip())

    @property
    def effective_chatgpt_mcp_write_token(self) -> str:
        return self.chatgpt_mcp_write_token.strip() or self.mcp_api_token.strip()

    @property
    def effective_claude_mcp_write_token(self) -> str:
        return self.claude_mcp_write_token.strip() or self.mcp_api_token.strip()


settings = Settings()
