from __future__ import annotations

import re
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
    seen_in_batch = set()
    sql = '''INSERT INTO grants (
        title, summary, status, lat, lng, category, working_hours, url, address,
        source_name, source_url, source_record_id, phone, city, state, zip,
        verification_date, imported_at
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''

    try:
        for raw in records:
            stats.received += 1
            record = normalize_record(raw)
            if validate_record(record):
                stats.errors += 1
                continue
            stats.valid += 1
            source_key = ('source', record['source_name'], record['source_record_id']) if record['source_record_id'] else None
            location_key = ('location', normalize_key(record['title']), normalize_key(record['address'])) if record['address'] else None
            if ((source_key and source_key in seen_in_batch)
                    or (location_key and location_key in seen_in_batch)
                    or _is_duplicate(conn, record)):
                stats.duplicates += 1
                continue
            if source_key:
                seen_in_batch.add(source_key)
            if location_key:
                seen_in_batch.add(location_key)
            if not dry_run:
                conn.execute(sql, (
                    record['title'], record['summary'], 'draft', record['lat'], record['lng'],
                    record['category'], record['working_hours'], record['url'], record['address'],
                    record['source_name'], record['source_url'], record['source_record_id'],
                    record['phone'], record['city'], record['state'], record['zip'],
                    record['verification_date'], imported_at,
                ))
            stats.inserted += 1
        if dry_run:
            conn.rollback()
        else:
            conn.commit()
    finally:
        conn.close()
    return stats
