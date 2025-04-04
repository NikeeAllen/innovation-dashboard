import sqlite3
import pandas as pd

# Load the Excel data
df = pd.read_excel("laws_import.xlsx", sheet_name=0)

# Normalize column names
df.columns = [col.strip() for col in df.columns]

# Clean nulls
df = df.dropna(subset=["Jurisdiction", "Law/Subprovision", "Significance"])

# Connect to DB
conn = sqlite3.connect("legal_data.db")
cur = conn.cursor()

# Step 1: Insert unique jurisdictions
jurisdictions = df["Jurisdiction"].unique()
for name in jurisdictions:
    cur.execute("INSERT OR IGNORE INTO jurisdictions (name) VALUES (?)", (name.strip(),))

# Step 2: Insert unique sectors
all_sectors = set()
for s in df["Relevant Industry"]:
    if pd.notna(s):
        for sec in map(str.strip, s.split(",")):
            all_sectors.add(sec)
for sector in all_sectors:
    cur.execute("INSERT OR IGNORE INTO sectors (name) VALUES (?)", (sector,))

# Step 3: Insert each law and link to jurisdiction
for _, row in df.iterrows():
    juris_name = row["Jurisdiction"].strip()
    law_name = row["Law/Subprovision"].strip()
    summary = row["Significance"].strip()
    industries = str(row["Relevant Industry"]).split(",") if pd.notna(row["Relevant Industry"]) else []
    innovation_stage = str(row["Innovation Stage"]) if pd.notna(row["Innovation Stage"]) else "General"

    # Get jurisdiction ID
    cur.execute("SELECT id FROM jurisdictions WHERE name = ?", (juris_name,))
    juris_id = cur.fetchone()
    if not juris_id:
        continue
    juris_id = juris_id[0]

    # Insert law
    cur.execute("""
        INSERT INTO laws (jurisdiction_id, name, type, summary, enforceability)
        VALUES (?, ?, ?, ?, ?)""",
        (juris_id, law_name, "Mixed", summary, "Unrated"))
    
    law_id = cur.lastrowid

    # For each industry sector, insert a barrier (rough scoring placeholder)
    for industry in industries:
        industry = industry.strip()
        cur.execute("SELECT id FROM sectors WHERE name = ?", (industry,))
        result = cur.fetchone()
        if result:
            sector_id = result[0]
            cur.execute("""
                INSERT INTO barriers (law_id, sector_id, risk_score, description)
                VALUES (?, ?, ?, ?)""",
                (law_id, sector_id, 5, f"Relevant to {innovation_stage} stage in {industry}"))
    
conn.commit()
conn.close()
print("✅ Real law data imported from Excel.")
