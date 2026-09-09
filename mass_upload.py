import os
import time

import requests


API_URL = os.getenv(
    "HELPMAP_API_URL",
    "http://127.0.0.1:8000/api/v2/grants/",
)

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

if not ADMIN_TOKEN:
    raise RuntimeError(
        "ADMIN_TOKEN environment variable is required "
        "before running mass_upload.py."
    )


def upload_points(count=100):
    headers = {"x-admin-token": ADMIN_TOKEN}

    print(f"Starting bulk upload test for {count} simulated records...")

    for i in range(1, count + 1):
        data = {
            "title": f"Humanitarian Point #{i}",
            "summary": "Simulated scalability test record for HelpMap.",
            "status": "draft",
            "lat": 41.8781 + (i * 0.001),
            "lng": -87.6298 + (i * 0.001),
            "category": "Emergency",
            "working_hours": "24/7",
        }

        try:
            response = requests.post(
                API_URL,
                json=data,
                headers=headers,
                timeout=10,
            )

            if response.status_code == 200:
                print(f"Accepted simulated record {i}")
            else:
                print(
                    f"Request rejected ({response.status_code}): "
                    f"{response.text}"
                )

                if i == 1:
                    break

        except requests.RequestException as exc:
            print(f"Request failed: {exc}")
            break

        time.sleep(0.5)


if __name__ == "__main__":
    upload_points(100)
