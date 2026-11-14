import sqlite3
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data" / "data.db"
BACKUPS = ROOT / "data" / "backups"

if not DB.is_file():
    raise SystemExit("STOP: database not found")

BACKUPS.mkdir(parents=True, exist_ok=True)
BACKUPS.chmod(0o700)

timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
backup_path = BACKUPS / f"helpmap-before-v2-{timestamp}.db"

conn = sqlite3.connect(DB)
conn.execute("PRAGMA foreign_keys=ON")

try:
    original = {
        name: conn.execute(
            f'SELECT COUNT(*) FROM "{name}"'
        ).fetchone()[0]
        for name in ("grants", "resource_source_records")
    }

    with sqlite3.connect(backup_path) as backup:
        conn.backup(backup)

    backup_path.chmod(0o600)
    print("BACKUP:", backup_path)
    print("ORIGINAL COUNTS:", original)

    conn.executescript("""
    BEGIN IMMEDIATE;

    CREATE TABLE IF NOT EXISTS programs (
        id INTEGER PRIMARY KEY,
        slug TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        summary TEXT,
        status TEXT NOT NULL DEFAULT 'draft'
            CHECK(status IN ('draft','published','archived')),
        verification_status TEXT NOT NULL DEFAULT 'unverified'
            CHECK(verification_status IN
                ('unverified','source_verified','provider_confirmed')),
        eligibility_summary TEXT,
        cost_warning TEXT,
        application_summary TEXT,
        last_reviewed_at TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS program_locations (
        id INTEGER PRIMARY KEY,
        program_id INTEGER NOT NULL REFERENCES programs(id),
        resource_id INTEGER NOT NULL REFERENCES grants(id),
        relationship_status TEXT NOT NULL DEFAULT 'unverified'
            CHECK(relationship_status IN
                ('unverified','verified','inactive')),
        notes TEXT,
        UNIQUE(program_id, resource_id)
    );

    CREATE TABLE IF NOT EXISTS verification_sources (
        id INTEGER PRIMARY KEY,
        program_id INTEGER NOT NULL REFERENCES programs(id),
        source_url TEXT NOT NULL,
        source_title TEXT,
        source_type TEXT NOT NULL DEFAULT 'official_website',
        checked_at TEXT,
        evidence_note TEXT,
        verification_status TEXT NOT NULL DEFAULT 'pending'
            CHECK(verification_status IN
                ('pending','verified','rejected'))
    );

    CREATE TABLE IF NOT EXISTS eligibility_rules (
        id INTEGER PRIMARY KEY,
        program_id INTEGER NOT NULL REFERENCES programs(id),
        dimension TEXT NOT NULL CHECK(dimension IN (
            'income','household_size','residency','age',
            'citizenship','immigration_status','insurance',
            'housing_status','other'
        )),
        rule_text TEXT NOT NULL,
        verification_status TEXT NOT NULL DEFAULT 'unverified'
            CHECK(verification_status IN ('unverified','verified')),
        source_id INTEGER REFERENCES verification_sources(id)
    );

    CREATE TABLE IF NOT EXISTS program_benefits (
        id INTEGER PRIMARY KEY,
        program_id INTEGER NOT NULL REFERENCES programs(id),
        service_name TEXT NOT NULL,
        coverage_status TEXT NOT NULL DEFAULT 'unknown'
            CHECK(coverage_status IN
                ('unknown','covered','partially_covered','excluded')),
        limitations TEXT,
        source_id INTEGER REFERENCES verification_sources(id)
    );

    CREATE TABLE IF NOT EXISTS cost_policies (
        id INTEGER PRIMARY KEY,
        program_id INTEGER NOT NULL REFERENCES programs(id),
        cost_type TEXT NOT NULL DEFAULT 'unknown'
            CHECK(cost_type IN (
                'unknown','free_if_eligible','sliding_scale',
                'insurance_based','fixed_fee','variable'
            )),
        conditions TEXT,
        exclusions TEXT,
        possible_charges TEXT,
        verification_status TEXT NOT NULL DEFAULT 'unverified'
            CHECK(verification_status IN ('unverified','verified')),
        source_id INTEGER REFERENCES verification_sources(id)
    );

    CREATE TABLE IF NOT EXISTS application_steps (
        id INTEGER PRIMARY KEY,
        program_id INTEGER NOT NULL REFERENCES programs(id),
        step_number INTEGER NOT NULL,
        instruction TEXT NOT NULL,
        source_id INTEGER REFERENCES verification_sources(id),
        UNIQUE(program_id, step_number)
    );

    CREATE TABLE IF NOT EXISTS review_history (
        id INTEGER PRIMARY KEY,
        program_id INTEGER NOT NULL REFERENCES programs(id),
        action TEXT NOT NULL,
        details TEXT,
        reviewed_by TEXT,
        reviewed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_programs_category_status
        ON programs(category,status);

    CREATE INDEX IF NOT EXISTS idx_program_locations_resource
        ON program_locations(resource_id);

    CREATE INDEX IF NOT EXISTS idx_eligibility_program
        ON eligibility_rules(program_id);

    CREATE INDEX IF NOT EXISTS idx_sources_program
        ON verification_sources(program_id);

    COMMIT;
    """)

    current = {
        name: conn.execute(
            f'SELECT COUNT(*) FROM "{name}"'
        ).fetchone()[0]
        for name in ("grants", "resource_source_records")
    }

    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    foreign_keys = conn.execute("PRAGMA foreign_key_check").fetchall()

    if current != original or integrity != "ok" or foreign_keys:
        raise RuntimeError(
            f"VALIDATION FAILED: counts={current}, "
            f"integrity={integrity}, foreign_keys={foreign_keys}"
        )

    tables = [
        row[0] for row in conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
    ]

    print("\nSUCCESS: HelpMap 2.0 foundation created")
    print("TABLES:", ", ".join(tables))
    print("RESOURCE COUNTS PRESERVED:", current)
    print("INTEGRITY:", integrity)
    print("FOREIGN KEYS: OK")
    print("PROGRAMS ADDED: 0 (safe default)")

finally:
    conn.close()
