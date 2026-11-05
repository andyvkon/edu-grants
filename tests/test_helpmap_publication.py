
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("ADMIN_TOKEN", "local-test-token")

from fastapi.testclient import TestClient
from app import db
from app.main import app
from app.helpmap_ingest.core import import_records


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_patch = patch.object(
            db, "DB_PATH", Path(self.temp_dir.name) / "test.db"
        )
        self.db_patch.start()
        self.client = TestClient(app)

        import_records([{
            "title": "Publication Test Resource",
            "category": "Medical",
            "address": "123 Test Street, Chicago, IL",
            "lat": 41.88,
            "lng": -87.63,
            "source_name": "TEST",
            "source_record_id": "publication-001",
        }])

        conn = db.get_conn()
        self.item_id = conn.execute(
            "SELECT id FROM grants"
        ).fetchone()[0]
        conn.close()

    def tearDown(self):
        self.client.close()
        self.db_patch.stop()
        self.temp_dir.cleanup()

    def test_publication_lifecycle(self):
        url = f"/v2/grants/{self.item_id}"

        # Draft is hidden from public access
        self.assertEqual(self.client.get(url).status_code, 404)

        # Publishing without authorization is forbidden
        self.assertEqual(
            self.client.patch(url + "/publish").status_code, 401
        )

        headers = {"X-Admin-Token": os.environ["ADMIN_TOKEN"]}

        # Authorized publication
        response = self.client.patch(
            url + "/publish", headers=headers
        )
        self.assertEqual(response.status_code, 200)

        # Published record is publicly accessible
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "published")

        # Remove from publication
        response = self.client.patch(
            url + "/unpublish", headers=headers
        )
        self.assertEqual(response.status_code, 200)

        # Record is hidden again
        self.assertEqual(self.client.get(url).status_code, 404)

    
    def test_publish_nonexistent_resource(self):
        headers = {"X-Admin-Token": os.environ["ADMIN_TOKEN"]}

        response = self.client.patch(
            "/v2/grants/999999999/publish",
            headers=headers
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["detail"],
            "Resource not found"
        )

    def test_unpublish_nonexistent_resource(self):
        headers = {"X-Admin-Token": os.environ["ADMIN_TOKEN"]}

        response = self.client.patch(
            "/v2/grants/999999999/unpublish",
            headers=headers
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["detail"],
            "Resource not found"
        )


if __name__ == "__main__":
    unittest.main()

            
if __name__ == "__main__":
    unittest.main()
