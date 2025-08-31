#!/usr/bin/env python3
"""
Simple test to check if the driver is working.
"""

import logging
from scraper import TheresAnAIForThatScraper

# Set up logging
logging.basicConfig(level=logging.INFO)

def simple_test():
    """Simple test to check driver functionality."""
    print("Simple driver test...")
    
    try:
        # Create scraper instance
        scraper = TheresAnAIForThatScraper(debug_port=9222)
        
        print("✅ Scraper created successfully")
        print(f"Driver type: {type(scraper.driver)}")
        
        # Try to get page title
        try:
            title = scraper.driver.title
            print(f"✅ Driver title method works: {title}")
        except Exception as e:
            print(f"❌ Driver title method failed: {e}")
        
        # Try to navigate to a simple page
        try:
            scraper.driver.get("https://httpbin.org/html")
            print(f"✅ Navigation works: {scraper.driver.title}")
        except Exception as e:
            print(f"❌ Navigation failed: {e}")
        
        # Try to get page source
        try:
            source = scraper.driver.html
            print(f"✅ Page source works: {len(source)} characters")
        except Exception as e:
            print(f"❌ Page source failed: {e}")
        
        scraper.driver.quit()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logging.exception("Test failed")

if __name__ == "__main__":
    simple_test()
