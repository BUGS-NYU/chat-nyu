import os
import json
import time
import hashlib
from urllib.parse import urlparse
from scraper import fetch_content

LINKS_FILE = "links.json"  # File containing URLs to scrape
DATA_FILE = "data.jsonl"  # Output file for scraped data (formatted as JSON Lines)
ERROR_LOG = "errors.log"  # Log file for errors and blocked URLs


def is_allowed_by_robots(url):
    """
    Checks if scraping the given URL is allowed by the site's robots.txt.

    This function parses the website's robot.txt file to determine if the web scraper is permiited to access the specified URL based on the site's crawling policies.

    Args:
        url (str): The URL to check against robots.txt rules.

    Returns:
        bool: True if scraping is allowed, False if blocked or if robots.txt file cannot be fetched.
    """
    from urllib.robotparser import RobotFileParser

    # Extract the base domain to construct the robots.txt file
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    rp = RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch("*", url)
    except Exception:
        return False


def hash_content(text):
    """
    Computes a SHA-256 hash of the given text.

    Used to generate a unique indetifier for content to detect changes and avoid unnecessary re-scraping of identical content.

    Args:
        text (str): The text content to hash.

    Returns:
        str: the hexadecimal hash string.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_scraped_urls():
    """
    Loads previously scraped URLs and their content hashes from the data file.

    This prevents duplicate scraping and allows for change detection when the same URL is scraped multiple times.

    Returns:
        dict: Mapping of URL strings to content hash strings.
    """
    scraped = {}

    # Load the file if it exists
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    # Parse each JSON line
                    entry = json.loads(line)
                    # Store the URL and its content hash
                    scraped[entry["url"]] = entry.get("content_hash")
                except Exception:
                    continue
    return scraped


def main():
    """
    Main scraping workflow.

    Process:
    1. Loads the list of URLs and CSS selectors to scrape from links.json
    2. Checks which URLs have already been scraped to avoid duplicates
    3. Verifies each URL against the site's robots.txt rules
    4. Scrapes valid URLs and extracts content using the specified selectors
    5. Saves results to the data file in JSON Lines format
    6. Logs any errors to errors.log
    7. Implements a delay between requests to avoid overloading servers.
    """
    # Load the list of sites to scrape from the links file
    with open(LINKS_FILE, "r", encoding="utf-8") as f:
        sites = json.load(f)

    # Load previously scraped URLs to avoid duplicates
    scraped = load_scraped_urls()

    # Open output and error log files
    with open(DATA_FILE, "a", encoding="utf-8") as out, open(
        ERROR_LOG, "a", encoding="utf-8"
    ) as errlog:
        for site in sites:
            url = site["url"]
            selector = site["selector"]

            # Skip if already scraped
            if url in scraped:
                print(f"Already scraped: {url}")
                continue

            # Check robots.txt before scraping
            if not is_allowed_by_robots(url):
                print(f"Blocked by robots.txt: {url}")
                # Log blocked attempts
                errlog.write(
                    f"{time.strftime('%Y-%m-%dT%H:%M:%SZ')} | {url} | Blocked by robots.txt\n"
                )
                continue

            print(f"Scraping: {url}")
            try:
                # Fetch and extract the content using the provided CSS selector
                content = fetch_content(url, selector)

                # Hash the content for change detection in future runs
                content_hash = hash_content(content)

                # Create a data entry
                entry = {
                    "url": url,
                    "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "content_hash": content_hash,
                    "content": content,
                }

                # Write the result as a JSON line to the output file
                out.write(json.dumps(entry, ensure_ascii=False) + "\n")
                out.flush()

                # Sleep between requests
                time.sleep(1)
            except Exception as e:
                # Log any errors to the error log file
                print(f"Error scraping {url}: {e}")
                errlog.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ')} | {url} | {e}\n")


if __name__ == "__main__":
    main()
