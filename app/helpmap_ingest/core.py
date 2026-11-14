from __future__ import annotations

import re
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Iterable

from app import db


@dataclass
class ImportStats:
    received: int = 0
    valid: int = 0
    inserted: int = 0
    duplicates: int = 0
    errors: int = 0

    def to_dict(self):
        return asdict(self)


def clean(value: Any) -> str:
    if value is None:
        return ''
    return re.sub(r'\s+', ' ', str(value)).strip()


def normalize_key(value: Any) -> str:
    return re.sub(r'[^a-z0-9]+', '', clean(value).lower())


def normalize_record(raw: dict[str, Any]) -> dict[str, Any]:
    record = {
        'title': clean(raw.get('title')),
        'summary': clean(raw.get('summary')),
        'category': clean(raw.get('category')),
        'address': clean(raw.get('address')),
        'city': clean(raw.get('city')),
        'state': clean(raw.get('state')),
        'zip': clean(raw.get('zip')),
        'phone': clean(raw.get('phone')),
        'url': clean(raw.get('url')),
        'working_hours': clean(raw.get('working_hours')),
        'weekly_service_hours': raw.get('weekly_service_hours'),
        'source_name': clean(raw.get('source_name')),
        'source_url': clean(raw.get('source_url')),
        'source_record_id': clean(raw.get('source_record_id')),
        'verification_date': clean(raw.get('verification_date')),
        'status': 'draft',
    }
    try:
        record['lat'] = float(raw.get('lat')) if raw.get('lat') not in (None, '') else None
        record['lng'] = float(raw.get('lng')) if raw.get('lng') not in (None, '') else None
    except (TypeError, ValueError):
        record['lat'] = record['lng'] = None
    return record


def validate_record(record: dict[str, Any]) -> list[str]:
    errors = []
    for field in ('title', 'category', 'source_name'):
        if not record.get(field):
            errors.append(f'missing {field}')
    lat, lng = record.get('lat'), record.get('lng')
    if lat is None or lng is None:
        errors.append('missing/invalid coordinates')
    elif not (-90 <= lat <= 90 and -180 <= lng <= 180):
        errors.append('coordinates out of range')
    if not record.get('source_record_id') and not record.get('address'):
        errors.append('need source_record_id or address for deduplication')
    return errors


def _is_duplicate(conn, record: dict[str, Any]) -> bool:
    if record.get('source_record_id'):
        row = conn.execute(
            'SELECT 1 FROM grants WHERE source_name=? AND source_record_id=? LIMIT 1',
            (record['source_name'], record['source_record_id'])
        ).fetchone()
        if row:
            return True

    title_key = normalize_key(record.get('title'))
    address_key = normalize_key(record.get('address'))
    if title_key and address_key:
        candidates = conn.execute(
            'SELECT title, address FROM grants WHERE address IS NOT NULL AND title IS NOT NULL'
        ).fetchall()
        return any(
            normalize_key(row['title']) == title_key and normalize_key(row['address']) == address_key
            for row in candidates
        )
    return False



def import_records(records: Iterable[dict[str, Any]], dry_run: bool = False) -> ImportStats:
    db.init_db()
    stats = ImportStats()
    conn = db.get_conn()
    imported_at = datetime.now(timezone.utc).isoformat(timespec='seconds')

    sql = """INSERT INTO grants (
        title, summary, status, lat, lng, category, working_hours, weekly_service_hours, url, address,
        source_name, source_url, source_record_id, phone, city, state, zip,
        verification_date, imported_at
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""

    source_index = {}
    location_index = {}
    original_location = {}
    primary_source_id = {}
    stored_snapshots = {}

    for row in conn.execute(
        'SELECT id, title, address, source_name, source_record_id FROM grants'
    ):
        rid = row['id']
        name = clean(row['source_name'])
        sid = clean(row['source_record_id'])
        title = normalize_key(row['title'])
        address = normalize_key(row['address'])

        if sid:
            source_index.setdefault((name, sid), rid)

        if title and address:
            key = (name, title, address)
            location_index.setdefault(key, rid)
            original_location[rid] = key

        primary_source_id[rid] = sid

    for row in conn.execute(
        'SELECT resource_id, source_name, source_record_id, raw_data '
        'FROM resource_source_records'
    ):
        key = (row['source_name'], row['source_record_id'])
        source_index[key] = row['resource_id']
        stored_snapshots[key] = row['raw_data']

    next_virtual_id = -1

    try:
        for raw in records:
            stats.received += 1
            record = normalize_record(raw)

            if validate_record(record):
                stats.errors += 1
                continue

            stats.valid += 1

            name = record['source_name']
            sid = record['source_record_id']
            source_key = (name, sid) if sid else None

            title = normalize_key(record['title'])
            address = normalize_key(record['address'])
            location_key = (
                (name, title, address)
                if title and address else None
            )

            if source_key and source_key in source_index:
                rid = source_index[source_key]
                match_type = 'source'

            elif location_key and location_key in location_index:
                rid = location_index[location_key]
                match_type = 'location'

            else:
                match_type = 'new'

                if dry_run:
                    rid = next_virtual_id
                    next_virtual_id -= 1
                else:
                    cur = conn.execute(sql, (
                        record['title'], record['summary'], 'draft',
                        record['lat'], record['lng'], record['category'],
                        record['working_hours'],
                        record['weekly_service_hours'],
                        record['url'], record['address'],
                        name, record['source_url'], sid,
                        record['phone'], record['city'],
                        record['state'], record['zip'],
                        record['verification_date'], imported_at,
                    ))
                    rid = cur.lastrowid

                stats.inserted += 1
                primary_source_id[rid] = sid

                if location_key:
                    location_index[location_key] = rid
                    original_location[rid] = location_key

            if match_type != 'new':
                stats.duplicates += 1

            if source_key:
                source_index[source_key] = rid

                if not dry_run:
                    snapshot = json.dumps(
                        raw.get('_source_raw', raw),
                        ensure_ascii=False,
                        sort_keys=True,
                        default=str,
                    )

                    if source_key not in stored_snapshots:
                        review = (
                            (
                                match_type == 'location'
                                and primary_source_id.get(rid) != sid
                            )
                            or (
                                match_type == 'source'
                                and location_key
                                and original_location.get(rid)
                                and original_location[rid] != location_key
                            )
                        )

                        conn.execute(
                            'INSERT INTO resource_source_records '
                            '(resource_id, source_name, source_record_id, '
                            'raw_data, needs_review) VALUES (?,?,?,?,?)',
                            (
                                rid, name, sid, snapshot,
                                int(bool(review)),
                            ),
                        )
                        stored_snapshots[source_key] = snapshot

                    elif stored_snapshots[source_key] != snapshot:
                        # Preserve the first snapshot; flag changes for review.
                        conn.execute(
                            'UPDATE resource_source_records '
                            'SET needs_review=1 '
                            'WHERE source_name=? AND source_record_id=?',
                            source_key,
                        )

        if dry_run:
            conn.rollback()
        else:
            conn.commit()

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return stats
