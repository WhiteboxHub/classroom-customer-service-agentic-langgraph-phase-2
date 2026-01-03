import asyncio
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://xyz_user:xyz_password@localhost:5432/xyz_db")

async def seed_db():
    print("Connecting to database...")
    try:
        conn = await asyncpg.connect(POSTGRES_URL)
    except Exception as e:
        print(f"Failed to connect to DB: {e}")
        return

    print("Creating tables...")
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS members (
            member_id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100),
            plan_type VARCHAR(50)
        );
        
        CREATE TABLE IF NOT EXISTS claims (
            claim_id VARCHAR(50) PRIMARY KEY,
            member_id VARCHAR(50),
            status VARCHAR(20),
            amount DECIMAL(10, 2),
            service_date DATE,
            denial_code VARCHAR(10),
            description TEXT
        );
    """)

    print("Seeding members...")
    await conn.execute("""
        INSERT INTO members (member_id, name, plan_type) VALUES
        ('MRN-12345', 'John Doe', 'Gold PPO'),
        ('MRN-67890', 'Jane Smith', 'Silver HMO'),
        ('MRN-11223', 'Bob Johnson', 'Bronze HMO')
        ON CONFLICT (member_id) DO NOTHING;
    """)

    print("Seeding claims...")
    await conn.execute("""
        INSERT INTO claims (claim_id, member_id, status, amount, service_date, denial_code, description) VALUES
        ('CLM-1001', 'MRN-12345', 'Paid', 150.00, '2025-01-10', NULL, 'Dental Cleaning'),
        ('CLM-1002', 'MRN-12345', 'Denied', 5000.00, '2025-01-15', 'E45', 'Cosmetic Surgery'),
        ('CLM-2001', 'MRN-67890', 'Paid', 200.00, '2025-02-01', NULL, 'Urgent Care Visit'),
        ('CLM-2002', 'MRN-67890', 'Denied', 100.00, '2025-02-05', 'D01', 'Duplicate Checkup'),
        ('CLM-3001', 'MRN-11223', 'Processing', 1200.00, '2025-03-01', NULL, 'ER Visit')
        ON CONFLICT (claim_id) DO NOTHING;
    """)
    
    print("Database seeded successfully.")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(seed_db())
