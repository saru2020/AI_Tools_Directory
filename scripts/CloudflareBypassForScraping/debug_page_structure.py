#!/usr/bin/env python3
"""
Debug script to inspect the actual page structure.
"""

import logging
from scraper import TheresAnAIForThatScraper

# Set up logging
logging.basicConfig(level=logging.INFO)

def debug_page_structure():
    """Debug the actual page structure to find correct selectors."""
    print("Debugging page structure...")
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
        print(f"📄 URL: {scraper.driver.url}")
        
        # Wait for page to load
        import time
        time.sleep(5)
        
        # Check for different possible selectors
        print("\n🔍 Checking for letter categories...")
        
        # Try different selectors for letter categories
        selectors_to_try = [
            "div.letter",
            ".letter",
            "[id^='a']",  # Elements with ID starting with 'a'
            "[id^='b']",  # Elements with ID starting with 'b'
            "[id^='c']",  # Elements with ID starting with 'c'
            "div[id]",
            ".tasks",
            ".task"
        ]
        
        for selector in selectors_to_try:
            try:
                elements = scraper.driver.eles(selector)
                if elements:
                    print(f"✅ Selector '{selector}': Found {len(elements)} elements")
                    for i, elem in enumerate(elements[:3]):  # Show first 3
                        try:
                            elem_id = elem.attr("id") or "no-id"
                            elem_class = elem.attr("class") or "no-class"
                            elem_text = elem.text[:100] if elem.text else "no-text"
                            print(f"   Element {i+1}: id='{elem_id}', class='{elem_class}', text='{elem_text}'...")
                        except Exception as e:
                            print(f"   Element {i+1}: Error reading: {e}")
                else:
                    print(f"❌ Selector '{selector}': No elements found")
            except Exception as e:
                print(f"❌ Selector '{selector}': Error - {e}")
        
        # Check for task links directly
        print("\n🔍 Checking for task links...")
        task_selectors = [
            "a.task_name",
            ".task_name",
            "a[href*='/']",
            "a"
        ]
        
        for selector in task_selectors:
            try:
                elements = scraper.driver.eles(selector)
                if elements:
                    print(f"✅ Selector '{selector}': Found {len(elements)} elements")
                    for i, elem in enumerate(elements[:5]):  # Show first 5
                        try:
                            href = elem.attr("href") or "no-href"
                            text = elem.text[:50] if elem.text else "no-text"
                            print(f"   Link {i+1}: href='{href}', text='{text}'...")
                        except Exception as e:
                            print(f"   Link {i+1}: Error reading: {e}")
                else:
                    print(f"❌ Selector '{selector}': No elements found")
            except Exception as e:
                print(f"❌ Selector '{selector}': Error - {e}")
        
        # Get page source for manual inspection
        print("\n📄 Getting page source preview...")
        try:
            page_source = scraper.driver.html
            # Look for specific patterns in the HTML
            if "letter" in page_source.lower():
                print("✅ Found 'letter' in page source")
            if "task" in page_source.lower():
                print("✅ Found 'task' in page source")
            if "ai_link" in page_source.lower():
                print("✅ Found 'ai_link' in page source")
            
            # Save page source for manual inspection
            with open("debug_page_source.html", "w", encoding="utf-8") as f:
                f.write(page_source)
            print("💾 Page source saved to 'debug_page_source.html'")
            
        except Exception as e:
            print(f"❌ Error getting page source: {e}")
        
        scraper.driver.quit()
        
    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        logging.exception("Debug failed")

if __name__ == "__main__":
    debug_page_structure()
