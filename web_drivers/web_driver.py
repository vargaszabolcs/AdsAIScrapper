import os
from dotenv import load_dotenv
from . import firefox_driver
from . import chrome_driver

# Load environment variables
load_dotenv()

# Get browser preference from environment variables
USE_CHROME = os.getenv('USE_CHROME', 'false').lower() == 'true'

def get_headers():
    if USE_CHROME:
        return chrome_driver.get_headers()
    return firefox_driver.get_headers()

def get_driver():
    if USE_CHROME:
        return chrome_driver.get_driver()
    return firefox_driver.get_driver()