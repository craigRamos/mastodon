import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

DEFAULT_SETTINGS: Dict[str, Any] = {
    "base_url": "https://mastodon.social",
    "access_token": "",
    "user_agent": "MastodonScraper/1.0",
    "timeout": 10,
    "output_dir": str(Path(__file__).resolve().parents[2] / "data"),
    "log_level": "INFO",
}

def load_settings(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load scraper settings from JSON file or fall back to defaults.

    :param config_path: Optional path to JSON config file.
    :return: Settings dictionary with all required keys.
    """
    settings = DEFAULT_SETTINGS.copy()
    path: Optional[Path] = Path(config_path).resolve() if config_path else None

    if path and path.is_file():
        try:
            with path.open("r", encoding="utf-8") as f:
                file_settings = json.load(f)
            if not isinstance(file_settings, dict):
                raise ValueError("Settings JSON must be an object.")
            settings.update(file_settings)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load settings from %s: %s", path, exc)
    else:
        if path:
            logger.info("Settings file %s not found, using defaults.", path)

    # Normalize paths
    output_dir = Path(settings.get("output_dir", DEFAULT_SETTINGS["output_dir"]))
    settings["output_dir"] = str(output_dir)

    return settings

@dataclass
class MastodonClient:
    """
    Lightweight HTTP client for Mastodon API.
    """

    base_url: str
    access_token: str
    user_agent: str
    timeout: int = 10

    def __post_init__(self) -> None:
        self.base_url = self.base_url.rstrip("/")
        self.session = requests.Session()
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        self.session.headers.update(headers)
        logger.debug("Initialized MastodonClient with base_url=%s", self.base_url)

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Perform a GET request to the Mastodon API.

        :param path: API path starting with '/api/...'
        :param params: Query parameters dictionary.
        :return: Parsed JSON response.
        """
        url = self.base_url + path
        try:
            response = self.session.get(url, params=params or {}, timeout=self.timeout)
            response.raise_for_status()
            logger.debug(
                "GET %s succeeded with status=%s", response.url, response.status_code
            )
            return response.json()
        except requests.RequestException as exc:
            logger.error("GET request to %s failed: %s", url, exc)
            raise

    def close(self) -> None:
        self.session.close()

def create_client_from_settings(settings: Dict[str, Any]) -> MastodonClient:
    """
    Build a MastodonClient instance from settings dictionary.
    """
    return MastodonClient(
        base_url=settings.get("base_url", DEFAULT_SETTINGS["base_url"]),
        access_token=settings.get("access_token", DEFAULT_SETTINGS["access_token"]),
        user_agent=settings.get("user_agent", DEFAULT_SETTINGS["user_agent"]),
        timeout=int(settings.get("timeout", DEFAULT_SETTINGS["timeout"])),
    )

def normalize_status(
    status: Dict[str, Any],
    trend_name: Optional[str] = None,
    tag: Optional[str] = None,
    search_query: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Normalize a Mastodon status object into the unified schema used by this project.
    """
    account = status.get("account") or {}
    media_attachments = status.get("media_attachments") or []

    media_urls: List[str] = []
    for m in media_attachments:
        url = m.get("url") or m.get("preview_url") or m.get("remote_url")
        if url:
            media_urls.append(url)

    normalized: Dict[str, Any] = {
        "trend_name": trend_name,
        "status_id": status.get("id"),
        "username": account.get("acct") or account.get("username"),
        "content": status.get("content"),
        "created_at": status.get("created_at"),
        "media": media_urls,
        "tag": tag,
        "search_query": search_query,
        "url": status.get("url") or status.get("uri"),
        "replies_count": status.get("replies_count"),
        "reblogs_count": status.get("reblogs_count"),
        "favourites_count": status.get("favourites_count"),
    }
    return normalized