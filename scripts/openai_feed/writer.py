"""Feed file + exclusions-report writer.

Format choice: csv.gz. The spec (docs/integrations/openai-product-feed-spec.md
"Delivery and file requirements") prefers parquet but explicitly also
supports jsonl.gz, csv.gz, and tsv.gz. We chose csv.gz over parquet to avoid
pulling the pandas/pyarrow ML dependency stack (`ml` extra in pyproject.toml)
into a lightweight ops script — csv.gz is on the spec's supported list and
needs only the stdlib `csv` + `gzip` modules. None of our current data
populates the schema's nested/list fields (variant_dict, q_and_a, reviews,
ads_metadata), so CSV's inability to nest costs nothing today; if that
changes, switch to jsonl.gz.
"""

from __future__ import annotations

import csv
import gzip
import json
from pathlib import Path
from typing import Any

from scripts.openai_feed.constants import CSV_COLUMNS

FEED_FILENAME = "openai-product-feed.csv.gz"
EXCLUSIONS_FILENAME = "openai-feed-exclusions.json"


def write_csv_feed(items: list[dict[str, Any]], path: Path) -> None:
    """Write valid feed items to a gzip-compressed CSV file, UTF-8 encoded."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(CSV_COLUMNS), extrasaction="ignore")
        writer.writeheader()
        for item in items:
            writer.writerow(item)


def write_exclusions(excluded: list[dict[str, Any]], path: Path) -> None:
    """Write the excluded-items report as pretty-printed JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(excluded, fh, indent=2, sort_keys=False)
        fh.write("\n")
