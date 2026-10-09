from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import Any

HRSA_DATASET_NAME = "HRSA Health Center Service Delivery and Look-Alike Sites"


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def load_hrsa_csv(
    path: str,
    state: str | None = None,
    limit: int | None = 500,
) -> list[dict[str, Any]]:
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"HRSA CSV not found: {csv_path}")

    state_filter = state.strip().upper() if state else None
    rows: list[dict[str, Any]] = []

    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)

        required = {
            "Site Name",
            "Site Address",
            "Site City",
            "Site State Abbreviation",
            "Site Postal Code",
            "Geocoding Artifact Address Primary X Coordinate",
            "Geocoding Artifact Address Primary Y Coordinate",
        }
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(
                "Unexpected HRSA CSV format. Missing columns: "
                + ", ".join(sorted(missing))
            )

        for row in reader:
            if state_filter:
                row_state = (_clean(row.get("Site State Abbreviation")) or "").upper()
                if row_state != state_filter:
                    continue

            # For HelpMap v1, ingest only active sites when a status is provided.
            status = _clean(row.get("Site Status Description"))
            if status and status.lower() != "active":
                continue

            rows.append(row)
            if limit is not None and len(rows) >= limit:
                break

    return rows


def transform_hrsa(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []

    for index, row in enumerate(rows, start=1):
        title = _clean(row.get("Site Name"))
        site_number = _clean(row.get("Health Center Number"))
        bhcmis = _clean(row.get("BHCMIS Organization Identification Number"))
        bphc = _clean(row.get("BPHC Assigned Number"))
        location_id = _clean(row.get("Health Center Location Identification Number"))

        record_id = (
            bphc
            or location_id
            or site_number
            or bhcmis
            or title
            or f"row-{index}"
        )

        address = _clean(row.get("Site Address"))
        city = _clean(row.get("Site City"))
        state = _clean(row.get("Site State Abbreviation"))
        zip_code = _clean(row.get("Site Postal Code"))
        full_address = ", ".join(
            value for value in (address, city, state, zip_code) if value
        )

        # HRSA X = longitude, Y = latitude.
        lng = _clean(row.get("Geocoding Artifact Address Primary X Coordinate"))
        lat = _clean(row.get("Geocoding Artifact Address Primary Y Coordinate"))

        hours = _clean(row.get("Operating Hours per Week"))
        center_name = _clean(row.get("Health Center Name"))
        summary = "Health center resource from official HRSA public data."
        if center_name and center_name != title:
            summary += f" Health center organization: {center_name}."

        out.append(
            {
                "title": title,
                "summary": summary,
                "category": "Medical",
                "address": full_address,
                "city": city,
                "state": state,
                "zip": zip_code,
                "lat": lat,
                "lng": lng,
                "phone": _clean(row.get("Site Telephone Number")),
                "url": _clean(row.get("Site Web Address")),
                "working_hours": hours,
                "source_name": "HRSA",
                # Dataset identity rather than a guessed/dead API endpoint.
                "source_url": "https://data.hrsa.gov/",
                "source_record_id": str(record_id),
                "verification_date": date.today().isoformat(),
            }
        )

    return out
