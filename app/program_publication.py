from datetime import date, timedelta
from urllib.parse import urlparse


def publication_issues(db, program_id):
    """Return reasons why a program is not ready for publication."""
    issues = []

    program = db.execute("""
        SELECT * FROM programs WHERE id = ?
    """, (program_id,)).fetchone()

    if program is None:
        return ["Program does not exist"]

    if program["verification_status"] not in (
        "source_verified", "provider_confirmed"
    ):
        issues.append("Program verification is incomplete")

    if not program["summary"]:
        issues.append("Program summary is missing")

    if not program["eligibility_summary"]:
        issues.append("Eligibility summary is missing")

    if not program["application_summary"]:
        issues.append("Application instructions are missing")

    sources = db.execute("""
        SELECT * FROM verification_sources
        WHERE program_id = ?
          AND verification_status = 'verified'
    """, (program_id,)).fetchall()

    valid_sources = set()

    for source in sources:
        parsed = urlparse(source["source_url"])
        if parsed.scheme != "https" or not parsed.hostname:
            continue

        try:
            checked = date.fromisoformat(source["checked_at"])
            if not (
                checked <= date.today()
                and checked >= date.today() - timedelta(days=180)
            ):
                continue
        except (ValueError, TypeError):
            continue

        valid_sources.add(source["id"])

    if not valid_sources:
        issues.append("No recently reviewed HTTPS evidence source")

    costs = db.execute("""
        SELECT * FROM cost_policies
        WHERE program_id = ?
          AND verification_status = 'verified'
    """, (program_id,)).fetchall()

    valid_costs = [
        c for c in costs
        if c["source_id"] in valid_sources
        and c["cost_type"] != "unknown"
        and c["conditions"]
    ]

    if not valid_costs:
        issues.append("No verified cost policy with conditions")

    steps = db.execute("""
        SELECT * FROM application_steps
        WHERE program_id = ?
    """, (program_id,)).fetchall()

    if not any(
        step["instruction"] and
        step["source_id"] in valid_sources
        for step in steps
    ):
        issues.append("No source-backed application instructions")

    rules = db.execute("""
        SELECT * FROM eligibility_rules
        WHERE program_id = ?
          AND verification_status = 'verified'
    """, (program_id,)).fetchall()

    if not any(
        rule["source_id"] in valid_sources
        for rule in rules
    ):
        issues.append("No verified eligibility rules")

    return issues
