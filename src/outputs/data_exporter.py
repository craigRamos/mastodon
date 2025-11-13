import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

logger = logging.getLogger(__name__)

class DataExporter:
    """
    Handles exporting scraped data to JSON and NDJSON files.
    """

    def __init__(self, output_dir: str) -> None:
        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.debug("DataExporter initialized with output_dir=%s", self.output_dir)

    def _build_path(self, prefix: str, ext: str) -> Path:
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        filename = f"{prefix}_{timestamp}.{ext}"
        return self.output_dir / filename

    def export_json(self, items: Iterable[Dict[str, Any]], prefix: str) -> str:
        """
        Export iterable of dictionaries to a pretty-printed JSON array.

        :param items: Iterable of dictionaries.
        :param prefix: Filename prefix.
        :return: String path to created file.
        """
        data: List[Dict[str, Any]] = list(items)
        path = self._build_path(prefix, "json")
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("Exported %d records to %s", len(data), path)
        return str(path)

    def export_ndjson(self, items: Iterable[Dict[str, Any]], prefix: str) -> str:
        """
        Export iterable of dictionaries to newline-delimited JSON (NDJSON).

        :param items: Iterable of dictionaries.
        :param prefix: Filename prefix.
        :return: String path to created file.
        """
        path = self._build_path(prefix, "ndjson")
        count = 0
        with path.open("w", encoding="utf-8") as f:
            for item in items:
                json_line = json.dumps(item, ensure_ascii=False)
                f.write(json_line + "\n")
                count += 1
        logger.info("Exported %d records to %s (NDJSON)", count, path)
        return str(path)