"""Run licensing migration directly."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, create_engine
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.begin() as conn:
    # 1. Create super_admins table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS super_admins (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            display_name VARCHAR(255) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            is_active BOOLEAN DEFAULT true NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
        )
    """))
    print("Created super_admins table")

    # 2. Add license columns to firms
    for col, typ in [
        ("license_key", "VARCHAR(255)"),
        ("license_key_hash", "VARCHAR(64)"),
        ("license_tier", "VARCHAR(50)"),
        ("license_expires_at", "TIMESTAMP WITH TIME ZONE"),
        ("license_activated_at", "TIMESTAMP WITH TIME ZONE"),
    ]:
        try:
            conn.execute(text(f"ALTER TABLE firms ADD COLUMN IF NOT EXISTS {col} {typ}"))
            print(f"Added column: {col}")
        except Exception as e:
            print(f"Column {col}: {e}")

    # 3. Create index
    try:
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_firms_license_key_hash ON firms (license_key_hash)"))
        print("Created index on license_key_hash")
    except Exception as e:
        print(f"Index: {e}")

    # 4. Auto-license existing firms
    result = conn.execute(text("""
        UPDATE firms
        SET
            license_key_hash = encode(sha256('LEGACY-PERPETUAL'::bytea), 'hex'),
            license_tier = 'enterprise',
            license_activated_at = now()
        WHERE license_key_hash IS NULL
    """))
    print(f"Licensed {result.rowcount} existing firms")

    # 5. Create invitations table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS invitations (
            id SERIAL PRIMARY KEY,
            firm_id INTEGER NOT NULL REFERENCES firms(id) ON DELETE CASCADE,
            email VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL DEFAULT 'viewer',
            invited_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            token VARCHAR(255) UNIQUE NOT NULL,
            is_used BOOLEAN DEFAULT false NOT NULL,
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
        )
    """))
    print("Created invitations table")

    # 6. Create firm_business_roles table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS firm_business_roles (
            id SERIAL PRIMARY KEY,
            firm_id INTEGER NOT NULL REFERENCES firms(id) ON DELETE CASCADE,
            role_code VARCHAR(50) NOT NULL,
            is_enabled BOOLEAN DEFAULT true NOT NULL,
            rate_type VARCHAR(10),
            rate_value NUMERIC(10, 2),
            currency VARCHAR(10) DEFAULT 'INR' NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            UNIQUE (firm_id, role_code)
        )
    """))
    print("Created firm_business_roles table")

    # 7. Seed default business roles for existing firms
    default_roles = [
        ("partner", True, "daily", 15000),
        ("director", True, "daily", 12000),
        ("ca_manager", True, "daily", 8000),
        ("paid_assistant", True, "daily", 5000),
        ("staff", True, "daily", 5000),
        ("article", True, "daily", 3000),
        ("data_analyst", True, "daily", 6000),
    ]
    
    firms = conn.execute(text("SELECT id FROM firms")).fetchall()
    for firm_row in firms:
        firm_id = firm_row[0]
        for role_code, enabled, rate_type, rate_value in default_roles:
            conn.execute(text("""
                INSERT INTO firm_business_roles (firm_id, role_code, is_enabled, rate_type, rate_value)
                VALUES (:firm_id, :role_code, :is_enabled, :rate_type, :rate_value)
                ON CONFLICT (firm_id, role_code) DO NOTHING
            """), {
                "firm_id": firm_id,
                "role_code": role_code,
                "is_enabled": enabled,
                "rate_type": rate_type,
                "rate_value": rate_value,
            })
    print(f"Seeded default business roles for {len(firms)} firms")

    # 8. Add system settings for reporting
    conn.execute(text("""
        INSERT INTO system_settings (key, value, description)
        VALUES ('hours_per_work_day', '8', 'Hours per working day for cost calculations')
        ON CONFLICT (key) DO NOTHING
    """))
    conn.execute(text("""
        INSERT INTO system_settings (key, value, description)
        VALUES ('default_currency', 'INR', 'Default currency for cost rates')
        ON CONFLICT (key) DO NOTHING
    """))
    print("Added system settings for reporting")
    
    # 9. Update alembic_version
    conn.execute(text("UPDATE alembic_version SET version_num = 'a1b2c3d4e5f6'"))
    print("Updated alembic_version")

print("\nMigration complete!")
