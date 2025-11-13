import logging
from typing import Any, Dict, List

from .utils_parser import MastodonClient, normalize_status

logger = logging.getLogger(__name__)

class TrendsExtractor:
    """
    Extracts trending hashtags/topics from a Mastodon instance.
    """

    def __init__(self, client: MastodonClient) -> None:
        self.client = client

    def fetch_trends(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Fetch trending tags and normalize them into the common schema.

        :param limit: Maximum number of trends to fetch.
        :return: List of normalized records.
        """
        logger.info("Fetching up to %d trends from Mastodon", limit)
        raw_trends = self.client.get("/api/v1/trends/tags", params={"limit": limit})
        records: List[Dict[str, Any]] = []

        if not isinstance(raw_trends, list):
            logger.warning("Unexpected trends format: %r", raw_trends)
            return records

        for trend in raw_trends[:limit]:
            name = trend.get("name")
            if not name:
                continue

            # Construct a pseudo-status object for schema compatibility
            pseudo_status = {
                "id": trend.get("id") or trend.get("name"),
                "account": {"acct": None, "username": None},
                "content": None,
                "created_at": None,
                "media_attachments": [],
                "url": trend.get("url"),
                "uri": trend.get("url"),
                "replies_count": None,
                "reblogs_count": trend.get("statuses_count"),
                "favourites_count": None,
            }

            record = normalize_status(
                pseudo_status,
                trend_name=name,
                tag=name.lstrip("#") if isinstance(name, str) else None,
                search_query=None,
            )
            records.append(record)

        logger.info("Fetched %d normalized trend records", len(records))
        return records