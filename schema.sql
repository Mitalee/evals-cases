-- Evals Demo: Customer Pain Point Extractor
-- SQLite Schema Definition - Simple Start

-- Raw customer feedback (from Kaggle dataset)
CREATE TABLE IF NOT EXISTS feedback_submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clothing_id INTEGER,
    age INTEGER,
    title TEXT,
    review_text TEXT NOT NULL,
    rating INTEGER CHECK(rating BETWEEN 1 AND 5),
    recommended_ind INTEGER CHECK(recommended_ind IN (0, 1)),
    positive_feedback_count INTEGER DEFAULT 0,
    division_name TEXT,
    department_name TEXT,
    class_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for common queries
CREATE INDEX IF NOT EXISTS idx_feedback_rating ON feedback_submissions(rating);
