import time
import csv
import logging
import os
from typing import List, Dict, Any
from urllib.parse import urljoin, urlparse
from CloudflareBypasser import CloudflareBypasser
from DrissionPage import ChromiumPage, ChromiumOptions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scraper.log', mode='w')
    ]
)

class TheresAnAIForThatScraper:
    def __init__(self, headless: bool = False, browser_path: str = None, debug_port: int = None):
        """
        Initialize the scraper with browser configuration.
        
        :param headless: Whether to run browser in headless mode
        :param browser_path: Path to Chrome/Chromium executable
        :param debug_port: Port to connect to existing Chrome instance (e.g., 9222)
        """
        self.headless = headless
        self.browser_path = browser_path or self._get_default_browser_path()
        self.debug_port = debug_port
        self.driver = None
        self.cf_bypasser = None
        self.data = []
        
        # Setup browser immediately
        self._setup_browser()
        
    def _get_default_browser_path(self) -> str:
        """Get default browser path based on OS."""
        if os.name == 'nt':  # Windows
            return r"C:/Program Files/Google/Chrome/Application/chrome.exe"
        elif os.name == 'posix':  # macOS and Linux
            # Check macOS first
            macos_chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            if os.path.exists(macos_chrome):
                return macos_chrome
            # Fallback to Linux path
            return "/usr/bin/google-chrome"
        else:
            return "/usr/bin/google-chrome"
    
    def _setup_browser(self):
        """Setup and configure the browser."""
        if self.headless:
            try:
                from pyvirtualdisplay import Display
                display = Display(visible=0, size=(1920, 1080))
                display.start()
            except ImportError:
                logging.warning("pyvirtualdisplay not available, running in non-headless mode")
                self.headless = False
        
        try:
            # If debug port is specified, connect to existing Chrome instance
            if self.debug_port:
                logging.info(f"Connecting to existing Chrome instance on port {self.debug_port}...")
                try:
                    # Connect to existing Chrome instance using the correct API
                    self.driver = ChromiumPage(addr_or_opts=f"127.0.0.1:{self.debug_port}")
                    self.cf_bypasser = CloudflareBypasser(self.driver, max_retries=5)
                    logging.info(f"Successfully connected to Chrome on port {self.debug_port}")
                    return
                except Exception as e:
                    logging.error(f"Failed to connect to Chrome on port {self.debug_port}: {e}")
                    logging.error(f"Make sure Chrome is running with --remote-debugging-port={self.debug_port}")
                    raise
            
            # If no debug port, try to detect existing Chrome processes
            logging.info("Attempting to connect to existing Chrome instance...")
            
            try:
                # Look for existing Chrome processes with debugging enabled
                import psutil
                chrome_processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                            cmdline = proc.info['cmdline']
                            if cmdline and any('--remote-debugging-port=' in arg for arg in cmdline):
                                chrome_processes.append(proc)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                if chrome_processes:
                    logging.info(f"Found {len(chrome_processes)} existing Chrome processes with debugging enabled")
                    # Try to connect to the first one
                    self.driver = ChromiumPage()
                    self.cf_bypasser = CloudflareBypasser(self.driver, max_retries=5)
                    logging.info("Connected to existing Chrome instance")
                    return
                else:
                    logging.info("No existing Chrome instance with debugging found")
            except ImportError:
                logging.warning("psutil not available, skipping existing Chrome detection")
            except Exception as e:
                logging.warning(f"Error detecting existing Chrome: {e}")
            
            # If no existing instance, create new one with minimal arguments
            logging.info("Creating new Chrome instance...")
            
            # Minimal arguments to avoid warnings and maintain stability
            arguments = [
                "--no-first-run",
                "--disable-background-mode",
                "--disable-extensions",
                "--disable-plugins",
                "--disable-images",  # Speed up loading
                "--disable-javascript",  # Disable JS initially to avoid login redirects
                "--accept-lang=en-US",
                "--remote-debugging-port=0"  # Let DrissionPage choose port
            ]
            
            options = ChromiumOptions().auto_port()
            options.set_paths(browser_path=self.browser_path)
            
            # Add arguments
            for argument in arguments:
                options.set_argument(argument)
            
            # Create driver with options
            self.driver = ChromiumPage(addr_or_opts=options)
            self.cf_bypasser = CloudflareBypasser(self.driver, max_retries=5)
            
            logging.info("New browser instance created")
            
        except Exception as e:
            logging.error(f"Error setting up browser: {e}")
            # Fallback: try without custom options
            try:
                logging.info("Trying fallback browser setup...")
                self.driver = ChromiumPage()
                self.cf_bypasser = CloudflareBypasser(self.driver, max_retries=5)
                logging.info("Fallback browser setup completed")
            except Exception as fallback_error:
                logging.error(f"Fallback browser setup also failed: {fallback_error}")
                raise
    
    def _bypass_cloudflare(self, url: str) -> bool:
        """
        Navigate to URL and bypass Cloudflare protection if present.
        
        :param url: URL to navigate to
        :return: True if bypass successful or not needed, False otherwise
        """
        try:
            logging.info(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Check if Cloudflare protection is present
            if self.cf_bypasser.is_bypassed():
                logging.info("No Cloudflare protection detected")
                return True
            
            logging.info("Cloudflare protection detected, attempting to bypass...")
            self.cf_bypasser.bypass()
            
            # Wait for page to load after bypass
            time.sleep(3)
            
            if self.cf_bypasser.is_bypassed():
                logging.info("Cloudflare bypass successful")
                return True
            else:
                logging.error("Cloudflare bypass failed")
                return False
                
        except Exception as e:
            logging.error(f"Error during Cloudflare bypass: {e}")
            return False
    
    def _extract_task_links(self) -> List[str]:
        """Extract task links from the alphabetical page."""
        try:
            logging.info("Extracting task links...")
            task_links = []
            
            # Wait a bit for page to fully load after Cloudflare bypass
            time.sleep(3)
            
            # Find all task links directly using the correct selector
            task_elements = self.driver.eles(".task_name")
            logging.info(f"Found {len(task_elements)} task elements")
            
            if task_elements:
                for task_element in task_elements:
                    try:
                        href = task_element.attr("href")
                        text = task_element.text.strip()
                        if href and text:
                            # href is already a full URL, no need for urljoin
                            task_links.append(href)
                            logging.info(f"Found task: {text} -> {href}")
                    except Exception as e:
                        logging.warning(f"Error processing task element: {e}")
                        continue
            
            logging.info(f"Found {len(task_links)} total task links")
            return task_links
            
        except Exception as e:
            logging.error(f"Error extracting task links: {e}")
            return []
    
    def _extract_gpt_links(self, task_url: str) -> List[str]:
        """Extract GPT tool links from a task page."""
        try:
            logging.info(f"Extracting GPT links from: {task_url}")
            gpt_links = []
            
            # Navigate to task page and bypass Cloudflare if needed
            if not self._bypass_cloudflare(task_url):
                return []
            
            # Try multiple selectors to find GPT tool links based on sitemap
            selectors_to_try = [
                ".d a.ai_link",           # Original sitemap selector
                "a.ai_link",              # Simplified selector
                "a[href*='/tool/']",      # Links containing '/tool/'
                "a[href*='/ai/']",        # Links containing '/ai/'
                "a[href*='/gpt/']",       # Links containing '/gpt/'
                ".tool_list a",           # Tool list links
                ".ai_tools a"             # AI tools links
            ]
            
            for selector in selectors_to_try:
                gpt_elements = self.driver.eles(selector)
                if gpt_elements:
                    logging.info(f"Found {len(gpt_elements)} GPT links with selector '{selector}'")
                    
                    for element in gpt_elements:
                        href = element.attr("href")
                        text = element.text.strip()
                        if href and text:
                            full_url = urljoin(self.driver.url, href)
                            gpt_links.append(full_url)
                            logging.info(f"Found GPT tool: {text} -> {full_url}")
                    
                    if gpt_links:
                        break
            
            logging.info(f"Found {len(gpt_links)} total GPT links")
            return gpt_links
            
        except Exception as e:
            logging.error(f"Error extracting GPT links: {e}")
            return []
    
    def _extract_tool_data(self, tool_url: str) -> Dict[str, Any]:
        """Extract detailed tool data from a GPT tool page."""
        try:
            logging.info(f"Extracting tool data from: {tool_url}")
            
            # Navigate to tool page and bypass Cloudflare if needed
            if not self._bypass_cloudflare(tool_url):
                return {}
            
            tool_data = {
                'tool_url': tool_url,
                'tool_name': '',
                'tool_logo': '',
                'tool_description': '',
                'tool_link': '',
                'impacted_jobs': '',
                'impacted_jobs_percentage': ''
            }
            
            # Extract tool name
            try:
                title_element = self.driver.ele(".title_wrap h1")
                if title_element:
                    tool_data['tool_name'] = title_element.text.strip()
            except Exception as e:
                logging.warning(f"Could not extract tool name: {e}")
            
            # Extract tool logo
            try:
                logo_element = self.driver.ele(".icon_wrap img")
                if logo_element:
                    tool_data['tool_logo'] = logo_element.attr("src") or ""
            except Exception as e:
                logging.warning(f"Could not extract tool logo: {e}")
            
            # Extract tool description
            try:
                desc_element = self.driver.ele("div#use_case")
                if desc_element:
                    tool_data['tool_description'] = desc_element.text.strip()
            except Exception as e:
                logging.warning(f"Could not extract tool description: {e}")
            
            # Extract tool link
            try:
                link_element = self.driver.ele("a#ai_top_link_breadcrumbs")
                if link_element:
                    tool_data['tool_link'] = link_element.attr("href") or ""
            except Exception as e:
                logging.warning(f"Could not extract tool link: {e}")
            
            # Extract impacted jobs
            try:
                jobs_element = self.driver.ele("span.related_job_name")
                if jobs_element:
                    tool_data['impacted_jobs'] = jobs_element.text.strip()
            except Exception as e:
                logging.warning(f"Could not extract impacted jobs: {e}")
            
            # Extract impacted jobs percentage
            try:
                percentage_element = self.driver.ele("span.related_impact")
                if percentage_element:
                    tool_data['impacted_jobs_percentage'] = percentage_element.text.strip()
            except Exception as e:
                logging.warning(f"Could not extract impacted jobs percentage: {e}")
            
            logging.info(f"Successfully extracted data for: {tool_data.get('tool_name', 'Unknown')}")
            return tool_data
            
        except Exception as e:
            logging.error(f"Error extracting tool data: {e}")
            return {}
    
    def _save_to_csv(self, filename: str = "theresanaiforthat_data.csv"):
        """Save scraped data to CSV file."""
        try:
            if not self.data:
                logging.warning("No data to save")
                return
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'tool_name', 'tool_logo', 'tool_description', 'tool_link',
                    'impacted_jobs', 'impacted_jobs_percentage', 'tool_url'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for row in self.data:
                    # Only write rows that have at least some data
                    if any(row.get(field) for field in fieldnames):
                        writer.writerow(row)
            
            logging.info(f"Data saved to {filename}")
            
        except Exception as e:
            logging.error(f"Error saving to CSV: {e}")
    
    def scrape(self, max_tools: int = None):
        """
        Main scraping method that follows the sitemap structure.
        
        :param max_tools: Maximum number of tools to scrape (None for all)
        """
        try:
            self._setup_browser()
            
            # Start with the main alphabetical page
            start_url = "https://theresanaiforthat.com/alphabetical/"
            
            if not self._bypass_cloudflare(start_url):
                logging.error("Failed to bypass Cloudflare on main page")
                return
            
            # Extract task links from the alphabetical page
            task_links = self._extract_task_links()
            
            # Debug: show page title and some content
            logging.info(f"Page title: {self.driver.title}")
            logging.info(f"Page URL: {self.driver.url}")
            
            # Try to get some page content for debugging
            try:
                body_text = self.driver.ele("tag:body").text[:500]
                logging.info(f"Page content preview: {body_text}...")
            except Exception as e:
                logging.warning(f"Could not get page content: {e}")
            
            tools_scraped = 0
            
            # Process each task
            for task_url in task_links:
                if max_tools and tools_scraped >= max_tools:
                    break
                
                logging.info(f"Processing task: {task_url}")
                
                # Extract GPT tool links from this task page
                gpt_links = self._extract_gpt_links(task_url)
                
                # Process each GPT tool
                for tool_url in gpt_links:
                    if max_tools and tools_scraped >= max_tools:
                        break
                    
                    tool_data = self._extract_tool_data(tool_url)
                    if tool_data:
                        self.data.append(tool_data)
                        tools_scraped += 1
                        
                        # Add delay to be respectful
                        time.sleep(1)
                
                # Add delay between tasks
                time.sleep(1)
            
            logging.info(f"Scraping completed. Total tools scraped: {len(self.data)}")
            
            # Save data to CSV
            self._save_to_csv()
            
        except Exception as e:
            logging.error(f"Error during scraping: {e}")
        
        finally:
            if self.driver:
                self.driver.quit()
                logging.info("Browser closed")

def main():
    """Main function to run the scraper."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape TheresAnAIForThat.com using Cloudflare bypass')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser.add_argument('--browser-path', type=str, help='Path to Chrome/Chromium executable')
    parser.add_argument('--max-tools', type=int, help='Maximum number of tools to scrape')
    parser.add_argument('--debug-port', type=int, help='Port to connect to existing Chrome instance (e.g., 9222)')
    
    args = parser.parse_args()
    
    # Create scraper instance
    scraper = TheresAnAIForThatScraper(
        headless=args.headless,
        browser_path=args.browser_path,
        debug_port=args.debug_port
    )
    
    # Start scraping
    scraper.scrape(max_tools=args.max_tools)

if __name__ == '__main__':
    main()
