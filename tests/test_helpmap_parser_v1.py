import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import db
from app.helpmap_ingest.core import import_records


class ParserV1Tests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_patch = patch.object(db, 'DB_PATH', Path(self.temp_dir.name) / 'parser-test.db')
        self.db_patch.start()

    def tearDown(self):
        self.db_patch.stop()
        self.temp_dir.cleanup()

    def test_dedup_validation_and_draft(self):
        record = {
            'title': 'Example Training Resource', 'category': 'Employment',
            'address': '123 Example Street, Chicago, IL',
            'lat': 41.88, 'lng': -87.63, 'source_name': 'FIXTURE',
            'source_record_id': '123',
        }
        bad = {'title': 'Missing Coordinates', 'category': 'Employment', 'source_name': 'FIXTURE', 'source_record_id': 'bad'}
        result = import_records([record, record, bad])
        self.assertEqual(result.to_dict(), {'received': 3, 'valid': 2, 'inserted': 1, 'duplicates': 1, 'errors': 1})
        self.assertEqual(import_records([record]).duplicates, 1)
        conn = db.get_conn()
        self.assertEqual(conn.execute('SELECT status FROM grants').fetchone()['status'], 'draft')
        conn.close()

    def test_dry_run_does_not_write_and_dedupes_batch(self):
        record = {
            'title': 'Example Resource', 'category': 'Medical', 'address': '45 Main St',
            'lat': 41.0, 'lng': -87.0, 'source_name': 'FIXTURE', 'source_record_id': 'abc',
        }
        result = import_records([record, record], dry_run=True)
        self.assertEqual(result.inserted, 1)
        self.assertEqual(result.duplicates, 1)
        conn = db.get_conn()
        self.assertEqual(conn.execute('SELECT COUNT(*) FROM grants').fetchone()[0], 0)
        conn.close()


if __name__ == '__main__':
    unittest.main()
