# Advertisement Listing Scraper and Analyzer

This script scrapes car listings from classified ads websites, stores them in a SQLite database, and uses AI to analyze and rate the listings based on user preferences.

## Features

- Scrapes car listings from classified ads websites
- Stores listing data in SQLite database
- Uses AI to analyze and rate listings
- Filters listings based on price range
- Avoids duplicate listings
- Provides detailed reasoning for ratings

## Prerequisites

- Python 3.x
- LM Studio -> LLM of your choosing
- Python packages (install via pip):
  ```
  pip install -r requirements.txt
  ```

## Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your settings:

```env
# LM Studio settings
LM_STUDIO_URL=http://localhost:1234/v1
LM_STUDIO_API_KEY=lm-studio
LM_STUDIO_MODEL=your-model-name-here

# Scraping settings
BASE_URL=website-URL-ending-in-&page=-or-similar
MAX_PAGES=5

# Database settings
DB_NAME=data.db

# Price range settings
MIN_PRICE=2500
MAX_PRICE=4000

# User preferences
USE_CHROME=false
PREFERENCES=Enter your car preferences here
```

## Usage

1. Run the script:
   ```
   python app.py
   ```

2. The script will:
   - Scrape car listings
   - Store them in the database
   - Analyze and rate each listing
   - Save ratings to the database

## Database Structure

The script uses two main tables:

1. `advertisements` - Stores the car listings
2. `ai_ratings` - Stores the AI analysis and ratings

## Querying the Database

You can use [DB Browser for SQLite](https://sqlitebrowser.org/).
To view all listings with their ratings, use this SQL query:

```sql
SELECT 
    a.id,
    a.title,
    a.url,
    a.price,
    a.negotiable,
    a.location,
    a.date,
    a.size,
    a.age,
    a.kilometers,
    a.listing_type,
    r.rating,
    r.reasoning_low,
    r.reasoning_high,
    r.created_at
FROM advertisements a
LEFT JOIN ai_ratings r ON a.id = r.ad_id
ORDER BY r.rating DESC;
```

## Notes

- The script includes delays between page loads to avoid being blocked
- It handles various date formats and international text
- Duplicate listings are automatically skipped
- Listings outside the configured price range are skipped
- The AI rating system provides both high and low reasoning for each rating

## Troubleshooting

If you encounter issues:
1. Check your internet connection
2. Verify the website structure matches what the script is looking for
3. Ensure your WebDriver is properly configured, have Chrome or Firefox on your system installed

## Important Notice

Please ensure you comply with the terms of service and robots.txt of any website you scrape. This tool is for educational purposes only.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 