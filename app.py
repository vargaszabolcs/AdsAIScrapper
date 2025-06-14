from bs4 import BeautifulSoup
import db
from datetime import datetime
import ai  # Import the ai module
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time as time_module
import os
from dotenv import load_dotenv
from web_drivers import web_driver

# Load environment variables
load_dotenv()

conn, c = db.setup_db()

# Base URL without the page number
base_url = os.getenv('BASE_URL')

# Define the number of pages you want to scrape
max_pages = int(os.getenv('MAX_PAGES', '5'))

def wait_for_page_load(driver, timeout=30):
    try:
        # Wait for the page to be fully loaded
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        return True
    except Exception as e:
        print(f"Timeout waiting for page load: {str(e)}")
        return False

def romanian_to_standard_date(romanian_date):
    # Define Romanian month names and their numeric equivalents
    romanian_months = {
        'ianuarie': '01', 'februarie': '02', 'martie': '03', 'aprilie': '04',
        'mai': '05', 'iunie': '06', 'iulie': '07', 'august': '08',
        'septembrie': '09', 'octombrie': '10', 'noiembrie': '11', 'decembrie': '12'
    }
    
    # Split the Romanian date into day, month name, and year
    parts = romanian_date.split()
    if len(parts) != 3:
        raise ValueError("Date must be in the format 'dd month yyyy'")
    
    day, month_name, year = parts
    
    # Convert month name to numeric month
    month = romanian_months.get(month_name.lower())
    if not month:
        raise ValueError(f"Unknown month: {month_name}")
    
    # Format the date in standard format
    standard_date = f'{day}-{month}-{year} 00:00'
    
    return standard_date

def scrape_listings():
    driver = web_driver.get_driver()
    try:
        # Loop through each page
        for page in range(1, max_pages + 1):
            print(f"Scraping page {page}...")

            # Construct the URL for the current page
            url = base_url + str(page)
            
            try:
                # Load the page with Selenium
                driver.get(url)
                print("Page loaded, waiting for content...")
                
                # Wait for the page to be fully loaded
                if not wait_for_page_load(driver):
                    print("Page load timeout, trying to refresh...")
                    driver.refresh()
                    if not wait_for_page_load(driver):
                        print("Failed to load page after refresh, skipping...")
                        continue
                
                # Try to find any element that indicates the page has loaded
                page_loaded = False
                for selector in [
                    '[data-cy="l-card"]',
                    '[data-testid="l-card"]',
                    '.css-l9drzq'
                ]:
                    try:
                        element = WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        if element:
                            page_loaded = True
                            print(f"Found content with selector: {selector}")
                            break
                    except:
                        continue
                
                if not page_loaded:
                    print("Could not find any content on the page, trying to refresh...")
                    driver.refresh()
                    time_module.sleep(10)
                    continue

                # Get the page source and parse with BeautifulSoup
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                # Try different selectors for ads
                ads = []
                for selector in [
                    {'data-cy': 'l-card'},
                    {'data-testid': 'l-card'},
                    {'class': 'css-l9drzq'}
                ]:
                    ads = soup.find_all('div', selector)
                    if ads:
                        print(f"Found {len(ads)} ads with selector {selector}")
                        break

                if not ads:
                    print("No ads found on the page, might be blocked or page structure changed")
                    continue

                # Process each ad
                for ad in ads:
                    try:
                        # Get the title
                        title = None
                        title_element = ad.find('h4', class_='css-1g61gc2')
                        if title_element:
                            title = title_element.text.strip()

                        if not title:
                            print("Could not find title, skipping ad...")
                            continue

                        # Get the price
                        price = None
                        price_element = ad.find('p', {'data-testid': 'ad-price'})
                        if price_element:
                            price = price_element.text.strip()

                        if not price:
                            print("Could not find price, skipping ad...")
                            continue

                        # Process price
                        if "Prețul e negociabil" in price:
                            price = price.replace("Prețul e negociabil", "").strip()
                            negotiable = "Negotiable"
                        else:
                            negotiable = "Fix"

                        price = price.replace(" ", "").replace("€", "").replace(",", ".")

                        # Get the URL
                        ad_url = None
                        url_element = ad.find('a', class_='css-1tqlkj0')
                        if url_element and 'href' in url_element.attrs:
                            ad_url = url_element['href']
                            if not ad_url.startswith('http'):
                                ad_url = 'https://www.olx.ro' + ad_url

                        if not ad_url:
                            print("Could not find URL, skipping ad...")
                            continue

                        # Get location and date
                        location = "N/A"
                        date_str = datetime.now().strftime("%d-%m-%Y 00:00")
                        
                        location_date_element = ad.find('p', {'data-testid': 'location-date'})
                        if location_date_element:
                            location_date = location_date_element.text.strip()
                            parts = location_date.split(" - ")
                            if len(parts) >= 2:
                                location = parts[0].strip()
                                date_str = parts[1].strip()
                                date_str = date_str.replace("Reactualizat ", "")
                                if "Azi la" in date_str:
                                    date_str = date_str.replace("Azi la ", datetime.now().strftime("%d-%m-%Y "))
                                else:
                                    date_str = date_str.replace("la", "")
                                    try:
                                        date_str = romanian_to_standard_date(date_str)
                                    except:
                                        pass

                        # Get car details
                        age = None
                        kilometers = None
                        size = "N/A"
                        listing_type = "car"

                        # Try to find car details
                        details_element = ad.find('span', class_='css-6as4g5')
                        if details_element:
                            details_text = details_element.text.strip()
                            # Extract year and kilometers
                            parts = details_text.split()
                            if len(parts) >= 2:
                                try:
                                    # First part is the year
                                    age = int(parts[0])
                                    # Everything after the year until 'km' is the kilometers
                                    km_text = ' '.join(parts[1:-1])  # Join all parts except the last 'km'
                                    kilometers = int(km_text.replace(' ', '').replace('.', ''))
                                except:
                                    pass

                        # Check for duplicates
                        if db.is_duplicate_ad(c, ad_url):
                            print("Ad already exists in the database. Skipping...")
                            continue

                        # Print and store the data
                        print(f"Title: {title}")
                        print(f"URL: {ad_url}")
                        print(f"Price: {price} EUR")
                        print(f"Negotiable: {negotiable}")
                        print(f"Location: {location}")
                        print(f"Date: {date_str}")
                        print(f"Age: {age} years")
                        print(f"Kilometers: {kilometers} km")
                        print("-" * 40)

                        # Insert into database and check result
                        if db.insert_ad(c, title, ad_url, price, negotiable, location, date_str, size, age, kilometers, listing_type):
                            print("Successfully saved to database")
                        else:
                            print("Failed to save to database")
                        
                    except Exception as e:
                        print(f"Error processing ad: {str(e)}")
                        continue
                    
            except Exception as e:
                print(f"Error processing page {page}: {str(e)}")
                continue
                    
            # Add a delay between pages
            time_module.sleep(5)
            
    except Exception as e:
        print(f"Error during scraping: {str(e)}")
    finally:
        # Commit any remaining changes and close the database connection
        conn.commit()
        driver.quit()

def main():
    # Scrape listings first
    scrape_listings()
    
    # Then use ai.py to rate the listings and save results to DB
    print("\nStarting AI rating process...")
    
    # Create preferences object
    preferences = ai.Preferences(
        description=os.getenv('PREFERENCES')
    )
    
    # Get all listings from the database using db module
    listings = db.load_listings_from_db()
    
    # Process listings with ai.py
    llm = ai.get_llm()
    
    total_listings = len(listings)
    processed_listings = 0
    skipped_listings = 0
    
    for idx, listing in enumerate(listings, 1):
        try:
            # Check if the listing already has a rating
            existing_rating = db.get_rating(c, listing[0])  # listing[0] is the ID
            if existing_rating:
                print(f"Listing {listing[0]} already has a rating of {existing_rating[0]}. Skipping...")
                continue
                
            price = float(listing[3])  # Price is in the fourth column
            if price < float(os.getenv('MIN_PRICE', '0')) or price > float(os.getenv('MAX_PRICE', '100000')):
                skipped_listings += 1
                continue
                
            processed_listings += 1
            print(f"\nProcessing listing {processed_listings}/{total_listings} (Total skipped: {skipped_listings})")
            url = listing[2]  # URL is in the third column
            details = ai.scrape_detailed_data(url)
            
            if not details:
                print(f"Skipping listing due to scraping issues: {url}")
                continue
            
            rating, lowest_rated, highest_rated = ai.calculate_rating(listing, details, preferences, llm)
                
            print(f"\nListing: {url}")
            print(f"Title: {listing[1]}")  # Title is now in the second column
            print(f"Price: {price} EUR")
            print(f"Rating: {rating}/10")
            print(f"Reasoning (Low): {lowest_rated}")
            print(f"Reasoning (High): {highest_rated}")
            print("-" * 50)
            
            # Save the rating to the database
            db.save_rating(conn, c, listing[0], rating, lowest_rated, highest_rated)
            
        except (ValueError, TypeError) as e:
            print(f"Error processing listing price: {e}")
            skipped_listings += 1
            continue
    
    # Close the database connection
    db.close_db(conn)

if __name__ == "__main__":
    main()