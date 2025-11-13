import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

# Ensure src/ is on sys.path so "extractors" and "outputs" can be imported
CURRENT_FILE = Path(__file__).resolve()
SRC_DIR = CURRENT_FILE.parent
REPO_ROOT = SRC_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from extractors.utils_parser import (  # type: ignore[import]
    load_settings,
    create_client_from_settings,
)
from extractors.trends_extractor import TrendsExtractor  # type: ignore[import]
from extractors.statuses_extractor import StatusesExtractor  # type: ignore[import]
from extractors.timeline_extractor import TimelineExtractor  # type: ignore[import]
from extractors.search_handler import SearchHandler  # type: ignore[import]
from outputs.data_exporter import DataExporter  # type: ignore[import]

def _configure_logging(level_name: str) -> None:
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

def run_trends(args: argparse.Namespace, settings: Dict[str, Any]) -> None:
    logger = logging.getLogger("Mastodon.trends")
    client = create_client_from_settings(settings)
    exporter = DataExporter(settings["output_dir"])

    extractor = TrendsExtractor(client)
    records: List[Dict[str, Any]] = extractor.fetch_trends(limit=args.limit)

    output_path = exporter.export_json(records, "trends")
    logger.info("Fetched %d trend records", len(records))
    logger.info("Output saved to %s", output_path)

def run_statuses(args: argparse.Namespace, settings: Dict[str, Any]) -> None:
    logger = logging.getLogger("Mastodon.statuses")
    client = create_client_from_settings(settings)
    exporter = DataExporter(settings["output_dir"])

    extractor = StatusesExtractor(client)
    records: List[Dict[str, Any]] = extractor.fetch_statuses(
        username=args.username,
        from_id=args.from_id,
        limit=args.limit,
    )

    output_path = exporter.export_json(records, "statuses")
    logger.info("Fetched %d status records for username=%s", len(records), args.username)
    logger.info("Output saved to %s", output_path)

def run_timeline(args: argparse.Namespace, settings: Dict[str, Any]) -> None:
    logger = logging.getLogger("Mastodon.timeline")
    client = create_client_from_settings(settings)
    exporter = DataExporter(settings["output_dir"])

    extractor = TimelineExtractor(client)
    records: List[Dict[str, Any]] = extractor.fetch_timeline(
        tag=args.tag,
        from_id=args.from_id,
        limit=args.limit,
    )

    output_path = exporter.export_json(records, "timeline")
    logger.info("Fetched %d timeline records for tag=%s", len(records), args.tag)
    logger.info("Output saved to %s", output_path)

def run_search(args: argparse.Namespace, settings: Dict[str, Any]) -> None:
    logger = logging.getLogger("Mastodon.search")
    client = create_client_from_settings(settings)
    exporter = DataExporter(settings["output_dir"])

    handler = SearchHandler(client)

    if args.type == "accounts":
        records = handler.search_accounts(args.query, limit=args.limit)
        prefix = "search_accounts"
    elif args.type == "hashtags":
        records = handler.search_hashtags(args.query, limit=args.limit)
        prefix = "search_hashtags"
    else:
        records = handler.search_statuses(args.query, limit=args.limit)
        prefix = "search_statuses"

    output_path = exporter.export_json(records, prefix)
    logger.info(
        "Fetched %d search records for type=%s query=%r",
        len(records),
        args.type,
        args.query,
    )
    logger.info("Output saved to %s", output_path)

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mastodon Trends, Statuses & Timeline Scraper"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=str(SRC_DIR / "config" / "settings.example.json"),
        help="Path to JSON settings file (default: src/config/settings.example.json)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Trends
    p_trends = subparsers.add_parser("trends", help="Fetch trending tags")
    p_trends.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of trends to fetch (default: 20)",
    )

    # Statuses
    p_statuses = subparsers.add_parser("statuses", help="Fetch user statuses")
    p_statuses.add_argument(
        "--username",
        type=str,
        required=True,
        help="Mastodon username (without instance domain, e.g. 'example_user')",
    )
    p_statuses.add_argument(
        "--from-id",
        type=str,
        default=None,
        help="Fetch statuses since this status ID (optional)",
    )
    p_statuses.add_argument(
        "--limit",
        type=int,
        default=40,
        help="Maximum number of statuses to fetch (default: 40)",
    )

    # Timeline
    p_timeline = subparsers.add_parser("timeline", help="Fetch hashtag timeline")
    p_timeline.add_argument(
        "--tag",
        type=str,
        required=True,
        help="Hashtag (without #, e.g. 'technology')",
    )
    p_timeline.add_argument(
        "--from-id",
        type=str,
        default=None,
        help="Fetch timeline items since this status ID (optional)",
    )
    p_timeline.add_argument(
        "--limit",
        type=int,
        default=40,
        help="Maximum number of statuses in timeline (default: 40)",
    )

    # Search
    p_search = subparsers.add_parser("search", help="Search accounts, hashtags, or statuses")
    p_search.add_argument(
        "--query",
        type=str,
        required=True,
        help="Text query to search",
    )
    p_search.add_argument(
        "--type",
        type=str,
        choices=["accounts", "hashtags", "statuses"],
        default="statuses",
        help="Search type (default: statuses)",
    )
    p_search.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of results (default: 20)",
    )

    return parser

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    settings = load_settings(args.config)
    _configure_logging(settings.get("log_level", "INFO"))

    if args.command == "trends":
        run_trends(args, settings)
    elif args.command == "statuses":
        run_statuses(args, settings)
    elif args.command == "timeline":
        run_timeline(args, settings)
    elif args.command == "search":
        run_search(args, settings)
    else:
        parser.error(f"Unknown command: {args.command!r}")

if __name__ == "__main__":
    main()