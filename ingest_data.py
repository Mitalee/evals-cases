"""
Ingest Kaggle Women's E-Commerce Clothing Reviews into SQLite
"""
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

def clean_text(text):
    """Clean text fields"""
    if pd.isna(text):
        return None
    return str(text).strip()

def ingest_reviews(csv_path: str, db_path: str = "data/evals_demo.db", sample_size: int = None):
    """
    Load Kaggle reviews CSV into SQLite database
    
    Args:
        csv_path: Path to the downloaded CSV file
        db_path: Path to SQLite database
        sample_size: Optional - load only N random reviews (for testing)
    """
    print(f"📂 Reading CSV from: {csv_path}")
    
    # Read CSV
    df = pd.read_csv(csv_path)
    
    print(f"✓ Loaded {len(df)} reviews")
    print(f"✓ Columns: {list(df.columns)}")
    
    # Sample if requested
    if sample_size and sample_size < len(df):
        df = df.sample(n=sample_size, random_state=42)
        print(f"✓ Sampled {sample_size} reviews for testing")
    
    # Clean and prepare data
    print("\n🧹 Cleaning data...")
    
    # Map CSV columns to our schema
    # Expected CSV columns from Kaggle:
    # ['Clothing ID', 'Age', 'Title', 'Review Text', 'Rating', 
    #  'Recommended IND', 'Positive Feedback Count', 'Division Name', 
    #  'Department Name', 'Class Name']
    
    df_clean = pd.DataFrame({
        'clothing_id': df['Clothing ID'],
        'age': df['Age'],
        'title': df['Title'].apply(clean_text),
        'review_text': df['Review Text'].apply(clean_text),
        'rating': df['Rating'],
        'recommended_ind': df['Recommended IND'],
        'positive_feedback_count': df['Positive Feedback Count'].fillna(0).astype(int),
        'division_name': df['Division Name'].apply(clean_text),
        'department_name': df['Department Name'].apply(clean_text),
        'class_name': df['Class Name'].apply(clean_text)
    })
    
    # Remove rows with no review text
    df_clean = df_clean.dropna(subset=['review_text'])
    print(f"✓ {len(df_clean)} reviews after removing empty text")
    
    # Data quality checks
    print("\n📊 Data Quality Summary:")
    print(f"  Rating distribution:")
    print(df_clean['rating'].value_counts().sort_index())
    print(f"\n  Reviews with text: {df_clean['review_text'].notna().sum()}")
    print(f"  Average review length: {df_clean['review_text'].str.len().mean():.0f} chars")
    print(f"  Department breakdown:")
    print(df_clean['department_name'].value_counts())
    
    # Connect to database
    print(f"\n💾 Writing to database: {db_path}")
    conn = sqlite3.connect(db_path)
    
    # Insert data
    df_clean.to_sql(
        'feedback_submissions',
        conn,
        if_exists='append',  # append to existing table
        index=False
    )
    
    # Verify insertion
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM feedback_submissions")
    total_count = cursor.fetchone()[0]
    
    print(f"✓ Successfully inserted {len(df_clean)} reviews")
    print(f"✓ Total reviews in database: {total_count}")
    
    # Show some sample data
    print("\n📝 Sample Reviews:")
    cursor.execute("""
        SELECT id, rating, department_name, 
               substr(review_text, 1, 100) || '...' as preview
        FROM feedback_submissions
        ORDER BY RANDOM()
        LIMIT 3
    """)
    
    for row in cursor.fetchall():
        print(f"\n  ID: {row[0]} | Rating: {row[1]} | Dept: {row[2]}")
        print(f"  Preview: {row[3]}")
    
    conn.close()
    print("\n✅ Ingestion complete!")
    
    return len(df_clean)

def get_stats(db_path: str = "data/evals_demo.db"):
    """Show database statistics"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("DATABASE STATISTICS")
    print("="*60)
    
    # Total reviews
    cursor.execute("SELECT COUNT(*) FROM feedback_submissions")
    total = cursor.fetchone()[0]
    print(f"\nTotal Reviews: {total}")
    
    # By rating
    print("\nBy Rating:")
    cursor.execute("""
        SELECT rating, COUNT(*) as count
        FROM feedback_submissions
        GROUP BY rating
        ORDER BY rating
    """)
    for row in cursor.fetchall():
        bar = "█" * (row[1] // 100)
        print(f"  {row[0]} stars: {row[1]:>5} {bar}")
    
    # By department
    print("\nBy Department:")
    cursor.execute("""
        SELECT department_name, COUNT(*) as count
        FROM feedback_submissions
        WHERE department_name IS NOT NULL
        GROUP BY department_name
        ORDER BY count DESC
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")
    
    conn.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ingest_data.py <path_to_csv> [sample_size]")
        print("\nExample:")
        print("  python ingest_data.py data/reviews.csv")
        print("  python ingest_data.py data/reviews.csv 100  # Load only 100 reviews")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    sample_size = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    if not Path(csv_path).exists():
        print(f"❌ File not found: {csv_path}")
        sys.exit(1)
    
    # Ingest data
    ingest_reviews(csv_path, sample_size=sample_size)
    
    # Show stats
    get_stats()
