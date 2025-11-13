import logging
from typing import Any, Dict, List, Optional

from .utils_parser import MastodonClient, normalize_status

logger = logging.getLogger(__name__)

class StatusesExtractor:
    """
    Extracts user statuses from a Mastodon instance by username.
    """

    def __init__(self, client: MastodonClient) -> None:
        self.client = client

    def _lookup_account_id(self, username: str) -> Optional[str]:
        """
        Look up a Mastodon account ID by username.

        :param username: Username or acct handle.
        :return: Account ID or None.
        """
        logger.info("Looking up account for username=%s", username)
        try:
            account = self.client.get("/api/v1/accounts/lookup", params={"acct": username})
        except Exception as exc:  # noqa: BLE001
            logger.error("Account lookup failed for %s: %s", username, exc)
            return None

        account_id = account.get("id") if isinstance(account, dict) else None
        if not account_id:
            logger.warning("No account found for username=%s", username)
        else:
            logger.debug("Found account_id=%s for username=%s", account_id, username)
        return account_id

    def fetch_statuses(
        self,
        username: str,
        from_id: Optional[str] = None,
        limit: int = 40,
    ) -> List[Dict[str, Any]]:
        """
        Fetch statuses for a given username.

        :param username: Mastodon username (acct).
        :param from_id: Optional status ID to fetch statuses since.
        :param limit: Maximum number of statuses to fetch.
        :return: List of normalized records.
        """
        account_id = self._lookup_account_id(username)
        if not account_id:
            return []

        params: Dict[str, Any] = {
            "limit": max(1, min(limit, 80)),
            "exclude_replies": False,
            "exclude_reblogs": False,
        }
        if from_id:
            params["since_id"] = from_id

        logger.info(
            "Fetching up to %d statuses for username=%s (account_id=%s)",
            limit,
            username,
            account_id,
        )

        try:
            raw_statuses = self.client.get(
                f"/api/v1/accounts/{account_id}/statuses",
                params=params,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to fetch statuses for %s: %s", username, exc)
            return []

        if not isinstance(raw_statuses, list):
            logger.warning("Unexpected statuses payload: %r", raw_statuses)
            return []

        records: List[Dict[str, Any]] = []
        for status in raw_statuses[:limit]:
            if not isinstance(status, dict):
                continue
            record = normalize_status(status)
            records.append(record)

        logger.info(
            "Fetched %d normalized statuses for username=%s",
            len(records),
            username,
        )
        return records