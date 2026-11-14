from fastapi import APIRouter, Depends, HTTPException
from ..db import get_conn
from ..security import require_admin
from ..program_publication import publication_issues

router = APIRouter(prefix="/v2/programs", tags=["programs"])

COST_WARNING = (
    "Free or discounted care is not guaranteed. "
    "Eligibility, covered services and possible charges "
    "must be confirmed with the provider before receiving "
    "non-emergency services."
)

def get_db():
    db = get_conn()
    try:
        yield db
    finally:
        db.close()


def verified_sources(db, program_id):
    rows = db.execute("""
        SELECT id, source_title, source_url, checked_at,
               evidence_note
        FROM verification_sources
        WHERE program_id = ?
          AND verification_status = 'verified'
        ORDER BY id
    """, (program_id,)).fetchall()
    return [dict(r) for r in rows]


def safe_cost(db, program_id, source_ids):
    if not source_ids:
        return {
            "status": "not_verified",
            "label": "Cost not verified",
            "warning": COST_WARNING
        }

    rows = db.execute("""
        SELECT cost_type, conditions, exclusions,
               possible_charges, source_id
        FROM cost_policies
        WHERE program_id = ?
          AND verification_status = 'verified'
        ORDER BY id
    """, (program_id,)).fetchall()

    verified = [
        dict(r) for r in rows
        if r["source_id"] in source_ids
    ]

    if not verified:
        return {
            "status": "not_verified",
            "label": "Cost not verified",
            "warning": COST_WARNING
        }

    labels = {
        "unknown": "Cost not verified",
        "free_if_eligible": "Free for eligible patients",
        "sliding_scale": "Income-based fees",
        "insurance_based": "Insurance-based coverage",
        "fixed_fee": "Fixed fee",
        "variable": "Costs may vary"
    }

    policies = []
    for item in verified:
        policy = {
            **item,
            "label": labels.get(
                item["cost_type"], "Cost not verified"
            )
        }
        policies.append(policy)

    return {
        "status": "source_verified",
        "policies": policies,
        "warning": COST_WARNING
    }


def get_program(db, program_id):
    row = db.execute("""
        SELECT id, slug, name, category, summary,
               verification_status, eligibility_summary,
               application_summary, last_reviewed_at
        FROM programs
        WHERE id = ? AND status = 'published'
    """, (program_id,)).fetchone()

    if row is None or publication_issues(db, program_id):
        raise HTTPException(
            status_code=404,
            detail="Program not available"
        )

    program = dict(row)
    sources = verified_sources(db, program_id)
    source_ids = {s["id"] for s in sources}

    trusted = (
        program["verification_status"]
        in ("source_verified", "provider_confirmed")
        and bool(source_ids)
    )

    rules = db.execute("""
        SELECT dimension, rule_text, source_id
        FROM eligibility_rules
        WHERE program_id = ?
          AND verification_status = 'verified'
        ORDER BY id
    """, (program_id,)).fetchall()

    benefits = db.execute("""
        SELECT service_name, coverage_status,
               limitations, source_id
        FROM program_benefits
        WHERE program_id = ?
        ORDER BY id
    """, (program_id,)).fetchall()

    steps = db.execute("""
        SELECT step_number, instruction, source_id
        FROM application_steps
        WHERE program_id = ?
        ORDER BY step_number
    """, (program_id,)).fetchall()

    locations = db.execute("""
        SELECT g.id, g.title, g.address, g.city,
               g.state, g.zip, g.lat, g.lng, g.phone
        FROM program_locations pl
        JOIN grants g ON g.id = pl.resource_id
        WHERE pl.program_id = ?
          AND pl.relationship_status = 'verified'
          AND g.status = 'published'
        ORDER BY g.title
    """, (program_id,)).fetchall()

    return {
        "id": program["id"],
        "slug": program["slug"],
        "name": program["name"],
        "category": program["category"],
        "verification_status": (
            program["verification_status"]
            if trusted else "insufficient_evidence"
        ),
        "summary": program["summary"] if trusted else None,
        "eligibility_summary": (
            program["eligibility_summary"] if trusted else None
        ),
        "application_summary": (
            program["application_summary"] if trusted else None
        ),
        "last_reviewed_at": program["last_reviewed_at"],
        "cost": safe_cost(db, program_id, source_ids)
            if trusted else {
                "status": "not_verified",
                "label": "Cost not verified",
                "warning": COST_WARNING
            },
        "eligibility_rules": [
            dict(r) for r in rules
            if trusted and r["source_id"] in source_ids
        ],
        "benefits": [
            dict(r) for r in benefits
            if trusted and r["source_id"] in source_ids
        ],
        "application_steps": [
            dict(r) for r in steps
            if trusted and r["source_id"] in source_ids
        ],
        "locations": [dict(r) for r in locations]
            if trusted else [],
        "sources": sources,
        "notice": (
            "Eligibility is not guaranteed. Confirm your "
            "approval, covered services, and possible costs "
            "directly with the program or provider."
        )
    }


@router.get("/")
def list_programs(db=Depends(get_db)):
    rows = db.execute("""
        SELECT id FROM programs
        WHERE status = 'published'
        ORDER BY name
    """).fetchall()

    return [
        get_program(db, r["id"])
        for r in rows
        if not publication_issues(db, r["id"])
    ]


@router.get("/{program_id}")
def program_detail(program_id: int, db=Depends(get_db)):
    return get_program(db, program_id)


@router.patch("/{program_id}/publish")
def publish_program(
    program_id: int,
    db=Depends(get_db),
    _=Depends(require_admin),
):
    """Admin-only publication, with validation under a write lock."""
    try:
        db.execute("BEGIN IMMEDIATE")

        program = db.execute(
            "SELECT id, status FROM programs WHERE id=?",
            (program_id,)
        ).fetchone()

        if program is None:
            db.rollback()
            raise HTTPException(404, "Program not found")

        if program["status"] == "archived":
            db.rollback()
            raise HTTPException(409, "Archived program cannot be published")

        issues = publication_issues(db, program_id)

        if issues:
            db.rollback()
            raise HTTPException(
                status_code=422,
                detail={"publication_blocked": True, "issues": issues}
            )

        db.execute("""
            UPDATE programs
            SET status='published',
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        """, (program_id,))

        db.execute("""
            INSERT INTO review_history
                (program_id, action, details)
            VALUES (?, 'published', 'Structural validation passed')
        """, (program_id,))

        db.commit()

        return {
            "ok": True,
            "id": program_id,
            "status": "published"
        }

    except Exception:
        db.rollback()
        raise
