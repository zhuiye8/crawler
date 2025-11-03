"""HTML cleaning utilities to extract clean text from HTML content"""

from bs4 import BeautifulSoup
import re


def clean_html(html_content: str) -> str:
    """
    Clean HTML content and extract plain text

    Args:
        html_content: Raw HTML string

    Returns:
        Cleaned plain text string
    """
    if not html_content:
        return ""

    # Parse HTML
    soup = BeautifulSoup(html_content, 'lxml')

    # Remove script and style elements
    for element in soup(["script", "style", "nav", "footer", "header"]):
        element.decompose()

    # Get text
    text = soup.get_text(separator="\n")

    # Clean up whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)

    # Remove excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def extract_main_content(html_content: str, selectors: list[str] = None) -> str:
    """
    Extract main content from HTML using CSS selectors

    Args:
        html_content: Raw HTML string
        selectors: List of CSS selectors to try (in order of priority)

    Returns:
        Extracted content as clean text
    """
    if not html_content:
        return ""

    default_selectors = [
        ".article-content",
        ".post-content",
        "article",
        ".content",
        "main",
        "#content"
    ]

    selectors = selectors or default_selectors
    soup = BeautifulSoup(html_content, 'lxml')

    # Try each selector
    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            return clean_html(str(element))

    # Fallback to full clean
    return clean_html(html_content)
