"""URL rewriter — makes scraped HTML self-contained for iframe preview."""

from bs4 import BeautifulSoup


def rewrite_urls_with_base_tag(raw_html: str, base_url: str) -> str:
    """
    Insert a <base> tag so all relative URLs resolve to the original domain.
    Also handles lazy-loaded images (data-src → src).

    This is the simplest approach for read-only preview — it doesn't rewrite
    every URL, it just tells the browser where to resolve relative paths from.
    """
    soup = BeautifulSoup(raw_html, "lxml")

    # Remove any existing <base> tag to avoid conflicts
    existing_base = soup.find("base")
    if existing_base:
        existing_base.decompose()

    # Insert <base> as first child of <head>
    head = soup.find("head")
    if head:
        base_tag = soup.new_tag("base", href=base_url)
        head.insert(0, base_tag)
    else:
        # No <head> — create a minimal one
        html_tag = soup.find("html")
        if html_tag:
            head_tag = soup.new_tag("head")
            base_tag = soup.new_tag("base", href=base_url)
            head_tag.append(base_tag)
            html_tag.insert(0, head_tag)

    # Handle lazy-loaded images: copy data-src → src if src is missing
    for img in soup.find_all("img"):
        if not img.get("src"):
            data_src = img.get("data-src") or img.get("data-lazy-src")
            if data_src:
                img["src"] = data_src

    return str(soup)
