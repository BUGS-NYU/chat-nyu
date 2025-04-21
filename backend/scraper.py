import requests
from bs4 import BeautifulSoup


def fetch_content(url, selector, user_agent=None):
    """
    Fetches and extracts the text content of a specific element from a web page.

    This function makes an HTTP request to the specified URL, parses the HTML content, and extracts text from the element matching the provided CSS selector. It handles proper formatting of the extracted text by preserving paragraph breaks and removing extra whitespace.

    Args:
        url (str): The URL of the web page to fetch content from.
        selector (str): The CSS selector for the target element on the page.
        user_agent (str, optional): Custom User-Agent string.

    Returns:
        str: The extracted text content with newlines between elements and whitespace trimmed.

    Raises:
        requests.HTTPError: If the HTTP request fails.
        requests.Timeout: If the request times out.
        requests.RequestException: For other request-related errors.
        ValueError: If the CSS selector does not match any elements on the page.
    """
    headers = {
        "User-Agent": user_agent
        or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
    }
    # Make an HTTP request with a timeout
    response = requests.get(url, headers=headers, timeout=10)

    # Raises an exception for 4XX/5XX status codes
    response.raise_for_status()

    # Parse the HTML content
    soup = BeautifulSoup(response.text, "html.parser")

    # Find the first element matching the CSS selector
    element = soup.select_one(selector)

    # Handle the case where the CSS selector does not match any elements
    if not element:
        raise ValueError(f"Selector '{selector}' not found on {url}")

    # Returns the extracted text content.
    return element.get_text(separator="\n", strip=True)
