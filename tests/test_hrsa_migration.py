import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import db
from app.helpmap_ingest.core import import_records


class HRSAMigrationTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.patch = patch.object(
            db, "DB_PATH", Path(self.tmp.name) / "test.db"
        )
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def record(self, source_id="HRSA-001"):
        return {
            "title": "Example Clinic",
            "category": "Medical",
            "address": "1 Main St, Chicago, IL",
            "lat": 41.88,
            "lng": -87.63,
            "source_name": "HRSA",
            "source_record_id": source_id,
            "phone": "312-111-1111",
        }

    def count(self, table):
        conn = db.get_conn()
        try:
            return conn.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]
        finally:
            conn.close()

    def test_existing_legacy_record(self):
        db.init_db()
        conn = db.get_conn()
        conn.execute(
            "INSERT INTO grants "
            "(title, category, address, lat, lng, "
            "source_name, source_record_id, status) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (
                "Example Clinic", "Medical",
                "1 Main St, Chicago, IL",
                41.88, -87.63, "HRSA",
                "HRSA-001", "published"
            ),
        )
        conn.commit()
        conn.close()

        result = import_records([self.record()])

        self.assertEqual(result.inserted, 0)
        self.assertEqual(self.count("grants"), 1)
        self.assertEqual(self.count("resource_source_records"), 1)

    def test_changed_address_does_not_duplicate(self):
        import_records([self.record()])

        changed = {
            **self.record(),
            "address": "2 Main St, Chicago, IL",
        }

        result = import_records([changed])

        self.assertEqual(result.inserted, 0)
        self.assertEqual(self.count("grants"), 1)

        conn = db.get_conn()
        try:
            flagged = conn.execute(
                "SELECT needs_review "
                "FROM resource_source_records"
            ).fetchone()[0]
            self.assertEqual(flagged, 1)
        finally:
            conn.close()

    def test_original_csv_fields_preserved(self):
        record = {
            **self.record(),
            "_source_raw": {
                "Site Name": "Example Clinic",
                "Additional HRSA Field": "original value",
            },
        }

        import_records([record])

        conn = db.get_conn()
        try:
            raw = conn.execute(
                "SELECT raw_data "
                "FROM resource_source_records"
            ).fetchone()[0]
            self.assertEqual(
                json.loads(raw)["Additional HRSA Field"],
                "original value",
            )
        finally:
            conn.close()

    def test_dry_run_does_not_write_resources(self):
        import_records([self.record()], dry_run=True)

        self.assertEqual(self.count("grants"), 0)
        self.assertEqual(
            self.count("resource_source_records"), 0
        )


if __name__ == "__main__":
    unittest.main()
