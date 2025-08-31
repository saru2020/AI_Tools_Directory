#!/usr/bin/env python3
"""
Simple test to verify Chrome connection.
"""

import logging
from scraper import TheresAnAIForThatScraper

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_connection():
    """Test connection to existing Chrome instance."""
    print("Testing Chrome connection...")
    
    try:
        # Try to connect to existing Chrome
        scraper = TheresAnAIForThatScraper(debug_port=9222)
        
        # This should connect to existing Chrome, not create new instance
        print("✅ Connection test completed")
        print("If you see 'Successfully connected to Chrome on port 9222', it worked!")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    test_connection()
