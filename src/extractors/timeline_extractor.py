import logging
from typing import Any, Dict, List, Optional

from .utils_parser import MastodonClient, normalize_status

logger = logging.getLogger(__name__)

class TimelineExtractor:
    """
    Extracts hashtag timelines from a Mastodon instance.
    """

    def __init__(self, client: MastodonClient) -> None:
        self.client = client

    def fetch_timeline(
        self,
        tag: str,
        from_id: Optional[str] = None,
        limit: int = 40,
    ) -> List[Dict[str, Any]]:
        """
        Fetch a hashtag timeline.

        :param tag: Hashtag (without #).
        :param from_id: Optional status ID to fetch since.
        :param limit: Maximum number of statuses to fetch.
        :return: List of normalized records.
        """
        params: Dict[str, Any] = {
            "limit": max(1, min(limit, 80)),
        }
        if from_id:
            params["since_id"] = from_id

        normalized_tag = tag.lstrip("#")
        logger.info(
            "Fetching up to %d timeline statuses for tag=%s",
            limit,
            normalized_tag,
        )

        try:
            raw_statuses = self.client.get(
                f"/api/v1/timelines/tag/{normalized_tag}",
                params=params,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to fetch timeline for tag=%s: %s", normalized_tag, exc)
            return []

        if not isinstance(raw_statuses, list):
            logger.warning("Unexpected timeline payload: %r", raw_statuses)
            return []

        records: List[Dict[str, Any]] = []
        for status in raw_statuses[:limit]:
            if not isinstance(status, dict):
                continue
            record = normalize_status(
                status,
                tag=normalized_tag,
                search_query=None,
            )
            records.append(record)

        logger.info(
            "Fetched %d normalized timeline statuses for tag=%s",
            len(records),
            normalized_tag,
        )
        return records