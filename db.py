import sqlite3
import uuid
import os

# Get database name from environment variables
DB_NAME = os.getenv('DB_NAME', 'data.db')

def setup_db():
    # Connect to SQLite database (or create one if it doesn't exist)
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Create a table for advertisements (if not exists)
    c.execute('''
        CREATE TABLE IF NOT EXISTS advertisements (
            id TEXT PRIMARY KEY,
            title TEXT,
            url TEXT,
            price INT,
            negotiable TEXT,
            location TEXT,
            date DATE,
            size INT,
            age INT,
            kilometers INT,
            listing_type TEXT
        )
    ''')

    # Create a table for AI ratings
    c.execute('''
        CREATE TABLE IF NOT EXISTS ai_ratings (
            id TEXT PRIMARY KEY,
            ad_id TEXT UNIQUE,
            rating REAL,
            reasoning_low TEXT,
            reasoning_high TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ad_id) REFERENCES advertisements(id)
        )
    ''')

    return conn, c

def insert_ad(c, title, url, price, negotiable, location, date, size, age=None, kilometers=None, listing_type="apartment"):
    try:
        ad_id = str(uuid.uuid4())
        c.execute('''
            INSERT INTO advertisements (id, title, url, price, negotiable, location, date, size, age, kilometers, listing_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (ad_id, title, url, price, negotiable, location, date, size, age, kilometers, listing_type))
        c.connection.commit()  # Commit after each insert
        return True
    except Exception as e:
        print(f"Error inserting ad into database: {str(e)}")
        return False

# Function to check if an ad already exists in the database
def is_duplicate_ad(c, ad_url):
    c.execute("SELECT 1 FROM advertisements WHERE url = ?", (ad_url,))
    return c.fetchone() is not None

def load_listings_from_db(db_path: str = DB_NAME):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM advertisements')
    listings = cursor.fetchall()
    conn.close()
    return listings

def save_rating(conn, cursor, ad_id: str, rating: float, reasoning_low: str, reasoning_high: str):
    rating_id = str(uuid.uuid4())
    cursor.execute('''
        INSERT OR REPLACE INTO ai_ratings (id, ad_id, rating, reasoning_low, reasoning_high)
        VALUES (?, ?, ?, ?, ?)
    ''', (rating_id, ad_id, rating, reasoning_low, reasoning_high))
    conn.commit()

def get_rating(cursor, ad_id: str):
    cursor.execute('''
        SELECT rating, reasoning_low, reasoning_high 
        FROM ai_ratings 
        WHERE ad_id = ?
    ''', (ad_id,))
    return cursor.fetchone()

def close_db(conn):
    conn.commit()
    conn.close()