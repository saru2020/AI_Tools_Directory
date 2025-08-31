#!/usr/bin/env python3
"""
Test script for the updated TheresAnAIForThat scraper.
"""

import logging
from scraper import TheresAnAIForThatScraper

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_scraper():
    """Test the updated scraper with task-based structure."""
    print("Testing Updated TheresAnAIForThat Scraper...")
    print("=" * 50)
    
    try:
        # Create scraper instance with debug port
        scraper = TheresAnAIForThatScraper(debug_port=9222)
        
        # Test with very limited scraping (just 3 tools)
        print("Starting test scrape (max 2 tools)...")
        scraper.scrape(max_tools=2)
        
        # Check results
        if scraper.data:
            print(f"\n✅ Success! Scraped {len(scraper.data)} tools:")
            for i, tool in enumerate(scraper.data, 1):
                print(f"\nTool {i}:")
                print(f"  Name: {tool.get('tool_name', 'N/A')}")
                print(f"  Description: {tool.get('tool_description', 'N/A')[:100]}...")
                print(f"  Logo: {tool.get('tool_logo', 'N/A')}")
                print(f"  Link: {tool.get('tool_link', 'N/A')}")
                print(f"  Impacted Jobs: {tool.get('impacted_jobs', 'N/A')}")
                print(f"  Impact %: {tool.get('impacted_jobs_percentage', 'N/A')}")
                print(f"  URL: {tool.get('tool_url', 'N/A')}")
            
            # Check if CSV was created
            csv_file = "theresanaiforthat_data.csv"
            if os.path.exists(csv_file):
                print(f"\n✅ CSV file created: {csv_file}")
                file_size = os.path.getsize(csv_file)
                print(f"   File size: {file_size} bytes")
            else:
                print(f"\n❌ CSV file not found: {csv_file}")
                
        else:
            print("\n❌ No data was scraped")
            return False
            
        return True
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        logging.exception("Test failed")
        return False

if __name__ == "__main__":
    import os
    
    print("Updated TheresAnAIForThat Scraper Test")
    print("======================================")
    print("This scraper now follows the correct structure:")
    print("1. Alphabetical page → Letter categories (A, B, C, etc.)")
    print("2. Letter category → Task links (e.g., 'A/B testing', 'Academic research')")
    print("3. Task page → GPT tool links")
    print("4. GPT tool page → Tool details")
    print()
    
    if test_scraper():
        print("\n🎉 All tests passed! The updated scraper is working correctly.")
        print("\nYou can now run the full scraper:")
        print("  python scraper.py --debug-port=9222 --max-tools 100")
    else:
        print("\n❌ Scraper test failed. Check the logs for details.")
