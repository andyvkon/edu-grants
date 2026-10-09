from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.helpmap_ingest.core import import_records
from app.helpmap_ingest.hrsa import load_hrsa_csv, transform_hrsa


def load_json(path: str):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("JSON input must contain a list of records")
    return data


def main():
    parser = argparse.ArgumentParser(description="HelpMap Parser v1")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--hrsa-csv",
        help="Import official HRSA Health Center Service Delivery and Look-Alike Sites CSV",
    )
    source.add_argument("--json", help="Import already-normalized JSON records")
    parser.add_argument("--state", help="Optional two-letter state filter, e.g. IL")
    parser.add_argument("--limit", type=int, default=500, help="Maximum source records to process")
    parser.add_argument("--dry-run", action="store_true", help="Validate/deduplicate without writing")
    args = parser.parse_args()

    if args.limit < 1:
        parser.error("--limit must be at least 1")

    if args.hrsa_csv:
        rows = load_hrsa_csv(args.hrsa_csv, state=args.state, limit=args.limit)
        records = transform_hrsa(rows)
    else:
        records = load_json(args.json)
        if args.limit:
            records = records[: args.limit]

    stats = import_records(records, dry_run=args.dry_run)
    print(json.dumps(stats.to_dict(), indent=2))


if __name__ == "__main__":
    main()
