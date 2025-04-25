import re
import requests
import unicodedata
import markdownify
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def convert_relative_to_absolute(html, base_url):
    """
    Convert all relative links in the given HTML content to absolute URLs.

    Args:
        html (str): The HTML content containing <a> tags with relative or absolute links.
        base_url (str): The base URL to resolve relative links against.

    Returns:
        str: The modified HTML content with all <a> tags converted to absolute URls.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Iterate through all <a> tags with an href attribute
    for a_tag in soup.find_all("a", href=True):
        # Replace href with an absolute URL
        a_tag["href"] = urljoin(base_url, a_tag["href"])

    return str(soup)


def remove_inline_js(html):
    """
    Remove inline JavaScript code blocks and CDATA sections from HTML content.

    Args:
        html (str): The HTML content as a string.

    Returns:
        str: The HTML content with inline JavaScript and CDATA blocks removed.
    """
    # Remove //<![CDATA[ ... //]]> blocks
    html = re.sub(r"//<!\[CDATA\[(.*?)//\]\]>", "", html, flags=re.DOTALL)
    # Remove suspicious JS blocks
    html = re.sub(r"var\s+\w+\s*=\s*.*?;", "", html, flags=re.DOTALL)
    return html


def clean_markdown(text):
    """
    Clean and normalize Markdown text for LLM/RAG ingestion.

    Args:
        text (str): The Markdown-formatted text to clean.

    Returns:
        str: The cleaned and normalized Markdown text.
    """
    # Normalize Unicode
    text = unicodedata.normalize("NFKC", text)
    # Replace non-breaking spaces with regular spaces
    text = text.replace("\u00a0", " ")
    # Remove zero-width and other invisible chars
    text = re.sub(r"[\u200B-\u200D\uFEFF]", "", text)
    # Replace curly quotes with straight quotes
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    # Collapse multiple spaces
    text = re.sub(r"[ \t]+", " ", text)
    # Collapse 3+ line breaks to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove leading/trailing whitespace on each line
    text = "\n".join(line.strip() for line in text.splitlines())
    # Remove leading/trailing whitespace for the whole text
    text = text.strip()
    return text


def fetch_content(url, selector, user_agent=None):
    """
    Fetches content from a web page and extracts the target element as Markdown.

    Args:
        url (str): The URL of the web page to fetch.
        selector (str): The CSS selector that identifies the target element to extract.
        user_agent (str, optional): Custom User-Agent string for the HTTP request.

    Returns:
        str: The Markdown-formatted content of the selected element.

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

    # Convert all links to absolute
    html = convert_relative_to_absolute(str(element), url)

    # Remove inline JS/CDATA blocks
    html = remove_inline_js(html)

    # Convert to Markdown, ignoring common non-content elements
    markdown = markdownify.markdownify(
        html,
        heading_style="ATX",
        strip=["script", "style", "nav", "footer", "form", "button"],
    )

    # Clean and normalize markdown
    markdown = clean_markdown(markdown)

    return {"markdown": markdown}
