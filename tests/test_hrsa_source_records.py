import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import db
from app.helpmap_ingest.core import import_records


class HRSASourceRecordsTests(unittest.TestCase):
    def test_same_location_preserves_distinct_source_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(db, 'DB_PATH', Path(tmp) / 'test.db'):
                base = {
                    'title': 'Example Health Center',
                    'category': 'Medical',
                    'address': '120 Main St, Chicago, IL',
                    'lat': 41.88,
                    'lng': -87.63,
                    'source_name': 'HRSA',
                }
                first = {**base, 'source_record_id': 'HRSA-001',
                         'phone': '312-111-1111'}
                second = {**base, 'source_record_id': 'HRSA-002',
                          'phone': '312-222-2222'}

                import_records([first, second])
                conn = db.get_conn()
                try:
                    locations = conn.execute(
                        'SELECT COUNT(*) FROM grants'
                    ).fetchone()[0]
                    sources = conn.execute(
                        'SELECT COUNT(*) FROM resource_source_records'
                    ).fetchone()[0]
                finally:
                    conn.close()

                self.assertEqual(locations, 1)
                self.assertEqual(sources, 2)


if __name__ == '__main__':
    unittest.main()
