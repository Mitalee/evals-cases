"""
Initialize SQLite database for Evals Demo
"""
import sqlite3
from pathlib import Path

def init_database(db_path: str = "data/evals_demo.db"):
    """
    Initialize the SQLite database with schema from schema.sql
    
    Args:
        db_path: Path to SQLite database file
    """
    # Create data directory if it doesn't exist
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Read schema
    with open('schema.sql', 'r') as f:
        schema_sql = f.read()
    
    # Connect and execute schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Execute schema (SQLite supports multiple statements)
    cursor.executescript(schema_sql)
    
    conn.commit()
    
    # Verify tables were created
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        ORDER BY name;
    """)
    tables = cursor.fetchall()
    
    print(f"✓ Database initialized at: {db_path}")
    print(f"✓ Created {len(tables)} tables:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Check views
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='view' 
        ORDER BY name;
    """)
    views = cursor.fetchall()
    print(f"✓ Created {len(views)} views:")
    for view in views:
        print(f"  - {view[0]}")
    
    conn.close()
    print("\n✓ Database ready!")

if __name__ == "__main__":
    init_database()
