import logging
from typing import Any, Dict, List

from .utils_parser import MastodonClient, normalize_status

logger = logging.getLogger(__name__)

class SearchHandler:
    """
    Provides search capabilities for accounts, hashtags, and statuses.
    """

    def __init__(self, client: MastodonClient) -> None:
        self.client = client

    def _search(self, query: str, search_type: str, limit: int) -> Dict[str, Any]:
        logger.info(
            "Performing search type=%s query=%r limit=%d",
            search_type,
            query,
            limit,
        )
        params: Dict[str, Any] = {
            "q": query,
            "type": search_type,
            "limit": max(1, min(limit, 40)),
        }
        return self.client.get("/api/v2/search", params=params)

    def search_accounts(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        payload = self._search(query, "accounts", limit)
        accounts = payload.get("accounts") or []
        results: List[Dict[str, Any]] = []

        if not isinstance(accounts, list):
            logger.warning("Unexpected accounts payload: %r", accounts)
            return results

        for account in accounts[:limit]:
            if not isinstance(account, dict):
                continue

            pseudo_status = {
                "id": account.get("id"),
                "account": account,
                "content": account.get("note"),
                "created_at": account.get("created_at"),
                "media_attachments": [],
                "url": account.get("url"),
                "uri": account.get("url"),
                "replies_count": None,
                "reblogs_count": None,
                "favourites_count": None,
            }
            record = normalize_status(
                pseudo_status,
                trend_name=None,
                tag=None,
                search_query=query,
            )
            results.append(record)

        logger.info("Search accounts returned %d records", len(results))
        return results

    def search_hashtags(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        payload = self._search(query, "hashtags", limit)
        hashtags = payload.get("hashtags") or []
        results: List[Dict[str, Any]] = []

        if not isinstance(hashtags, list):
            logger.warning("Unexpected hashtags payload: %r", hashtags)
            return results

        for tag in hashtags[:limit]:
            if not isinstance(tag, dict):
                continue

            name = tag.get("name")
            pseudo_status = {
                "id": tag.get("id") or name,
                "account": {"acct": None, "username": None},
                "content": None,
                "created_at": None,
                "media_attachments": [],
                "url": tag.get("url"),
                "uri": tag.get("url"),
                "replies_count": None,
                "reblogs_count": tag.get("history"),
                "favourites_count": None,
            }
            record = normalize_status(
                pseudo_status,
                trend_name=name,
                tag=name.lstrip("#") if isinstance(name, str) else None,
                search_query=query,
            )
            results.append(record)

        logger.info("Search hashtags returned %d records", len(results))
        return results

    def search_statuses(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        payload = self._search(query, "statuses", limit)
        statuses = payload.get("statuses") or []
        results: List[Dict[str, Any]] = []

        if not isinstance(statuses, list):
            logger.warning("Unexpected statuses payload: %r", statuses)
            return results

        for status in statuses[:limit]:
            if not isinstance(status, dict):
                continue
            record = normalize_status(
                status,
                trend_name=None,
                tag=None,
                search_query=query,
            )
            results.append(record)

        logger.info("Search statuses returned %d records", len(results))
        return results