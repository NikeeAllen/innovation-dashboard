import sqlite3

conn = sqlite3.connect("legal_data.db")
cursor = conn.cursor()

# Create table: jurisdictions
cursor.execute("""
CREATE TABLE IF NOT EXISTS jurisdictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT
);
""")

# Create table: sectors
cursor.execute("""
CREATE TABLE IF NOT EXISTS sectors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT
);
""")

# Create table: laws
cursor.execute("""
CREATE TABLE IF NOT EXISTS laws (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jurisdiction_id INTEGER,
    name TEXT,
    type TEXT,
    summary TEXT,
    enforceability TEXT,
    FOREIGN KEY(jurisdiction_id) REFERENCES jurisdictions(id)
);
""")

# Create table: barriers
cursor.execute("""
CREATE TABLE IF NOT EXISTS barriers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    law_id INTEGER,
    sector_id INTEGER,
    risk_score INTEGER,
    description TEXT,
    FOREIGN KEY(law_id) REFERENCES laws(id),
    FOREIGN KEY(sector_id) REFERENCES sectors(id)
);
""")

conn.commit()
conn.close()
print("✅ Database tables created successfully.")
