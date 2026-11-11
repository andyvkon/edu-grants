import json

from app.helpmap_ingest.core import import_records



with open("web/helpmap/data/resources.sample.json", encoding="utf-8") as f:

    resources = json.load(f)



records = [

    {

        "title": r["name"],

        "summary": r.get("notes", ""),

        "category": r["type"],

        "lat": r["lat"],

        "lng": r["lng"],

        "address": r["address"],

        "city": r.get("city", ""),

        "state": "IL",

        "zip": r.get("zip", ""),

        "phone": r.get("phone", ""),

        "url": r.get("website", ""),

        "source_name": "HelpMap Initial Dataset",

        "source_record_id": str(r["id"]),

    }

    for r in resources

]



if __name__ == "__main__":

    stats = import_records(records, dry_run=False)

    print(stats.to_dict())
