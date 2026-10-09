# HelpMap Parser v1

This is a first-stage **draft-only** ingestion pipeline. It does not publish records or certify that they are current. A source dataset may be public while its accuracy or reuse conditions still need review.

## Install

From the repository root, using the project's Python environment:

```bash
pip install -r requirements.txt
```

## HRSA source (network required)

The adapter follows the HRSA Socrata endpoint already referenced by the repository's older `web/helpmap/us_aid_data/parser.py`. Confirm the endpoint's current availability, fields, and terms before production use.

```bash
python -m app.parser_v1 --hrsa --limit 100 --dry-run
python -m app.parser_v1 --hrsa --limit 100
```

## Import normalized JSON (offline)

```bash
python -m app.parser_v1 --json path/to/records.json --dry-run
python -m app.parser_v1 --json path/to/records.json
```

The JSON must be an array of objects with at least `title`, `category`, `source_name`, valid `lat`/`lng`, and either `source_record_id` or `address`. Optional fields include `summary`, `address`, `city`, `state`, `zip`, `phone`, `url`, `working_hours`, `source_url`, and `verification_date`.

Results report `received`, `valid`, `inserted` (would-insert during dry-run), `duplicates`, and `errors`. Duplicate detection checks source name + source record ID, then normalized title + address. No fuzzy geographic deduplication yet. All imported records are **draft**, invisible to the default public API until reviewed and explicitly published.

## Tests

```bash
python -m unittest discover -s tests -p 'test_helpmap_parser_v1.py' -v
```

## Important limits

- HRSA fetch is not validated live in this package; it requires network access.
- No automatic geocoding. Records without valid coordinates are rejected.
- No automatic publication, refresh, record expiration, or source-level licensing audit.
- Legacy `app/ingest/` is a separate older grants/course ingestion implementation and is not used by this HelpMap parser.
- Back up your local `data/data.db` before the first real import. Existing rows are preserved; `init_db()` adds metadata columns if needed.
