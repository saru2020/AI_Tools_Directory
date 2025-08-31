#!/usr/bin/env python3
"""
Debug script to check href attributes.
"""

import logging
from scraper import TheresAnAIForThatScraper

# Set up logging
logging.basicConfig(level=logging.INFO)

def debug_href():
    """Debug why href attributes are not being found."""
    print("Debugging href attributes...")
    print("=" * 40)
    
    try:
        # Create scraper instance
        scraper = TheresAnAIForThatScraper(debug_port=9222)
        
        # Navigate to the page
        start_url = "https://theresanaiforthat.com/alphabetical/"
        if not scraper._bypass_cloudflare(start_url):
            print("❌ Failed to bypass Cloudflare")
            return
        
        print(f"✅ Page loaded: {scraper.driver.title}")
        
        # Wait for page to load
        import time
        time.sleep(5)
        
        # Check task elements more carefully
        print("\n🔍 Checking task elements...")
        task_elements = scraper.driver.eles(".task_name")
        print(f"Found {len(task_elements)} task elements")
        
        # Check first few elements in detail
        for i in range(min(5, len(task_elements))):
            elem = task_elements[i]
            try:
                print(f"\nElement {i+1}:")
                print(f"  Tag: {elem.tag}")
                print(f"  Text: {elem.text[:100] if elem.text else 'no-text'}")
                
                # Check all attributes
                attrs = elem.attrs
                print(f"  All attributes: {attrs}")
                
                # Check href specifically
                href = elem.attr("href")
                print(f"  Href: {href}")
                
                # Check if it's actually a link
                if elem.tag == "a":
                    print(f"  Is link: ✅")
                else:
                    print(f"  Is link: ❌ (tag is {elem.tag})")
                    
            except Exception as e:
                print(f"  Error reading element: {e}")
        
        # Check parent elements
        print("\n🔍 Checking parent elements...")
        if task_elements:
            first_elem = task_elements[0]
            try:
                parent = first_elem.parent
                print(f"Parent tag: {parent.tag}")
                print(f"Parent class: {parent.attr('class')}")
                print(f"Parent HTML: {parent.html[:200]}...")
            except Exception as e:
                print(f"Error checking parent: {e}")
        
        scraper.driver.quit()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logging.exception("Debug failed")

if __name__ == "__main__":
    debug_href()
