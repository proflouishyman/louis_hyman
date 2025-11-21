# 2025-11-21 10:20 ET
# Purpose: Crawl a Wix site with a headless browser, execute JS on each page,
# and mirror HTML + assets (images, CSS, JS, fonts) into a local folder
# suitable for static hosting (e.g., GitHub Pages).

import os
import re
from urllib.parse import urlparse, urljoin, urldefrag

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

START_URL = "https://www.louishyman.com/"
OUTPUT_DIR = "mirror"


def safe_join(*parts):
    """Join path parts and normalize, avoiding accidental leading slashes."""
    path = os.path.join(*parts)
    return os.path.normpath(path.lstrip(os.sep))


def url_to_local_html_path(root_url, current_url):
    """
    Map a page URL to a local HTML file path.
    Examples:
      https://site.com/           -> mirror/index.html
      https://site.com/about      -> mirror/about/index.html
      https://site.com/about/     -> mirror/about/index.html
      https://site.com/blog/post  -> mirror/blog/post/index.html
      https://site.com/file.html  -> mirror/file.html
    """
    root = urlparse(root_url)
    u = urlparse(current_url)

    # Remove query/fragment
    path = u.path or "/"
    if path.endswith("/"):
        rel = safe_join(OUTPUT_DIR, path[1:], "index.html")
    else:
        # If there is no dot in last segment, treat as directory
        last_part = os.path.basename(path)
        if "." not in last_part:
            rel = safe_join(OUTPUT_DIR, path[1:], "index.html")
        else:
            rel = safe_join(OUTPUT_DIR, path[1:])

    return rel


def url_to_local_asset_path(asset_url):
    """
    Map an asset URL to a local file path inside OUTPUT_DIR/assets/...
    Keeps the URL path, drops scheme/host.
    """
    u = urlparse(asset_url)
    path = u.path or "/unnamed"
    rel = safe_join(OUTPUT_DIR, "assets", path.lstrip("/"))
    return rel


def is_same_site(root_url, candidate_url):
    """Check if candidate_url is on the same site (same netloc) as root_url."""
    root = urlparse(root_url)
    c = urlparse(candidate_url)
    if not c.scheme.startswith("http"):
        return False
    return c.netloc == root.netloc


def normalize_url(base_url, link_href):
    """Resolve relative link to absolute, strip fragments."""
    abs_url = urljoin(base_url, link_href)
    abs_url, _ = urldefrag(abs_url)
    return abs_url


def crawl_site():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    visited_pages = set()
    queued_pages = [START_URL]

    downloaded_assets = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()

        while queued_pages:
            current_url = queued_pages.pop(0)
            if current_url in visited_pages:
                continue
            visited_pages.add(current_url)

            print(f"[PAGE] {current_url}")

            page = context.new_page()
            responses = []

            def handle_response(response):
                try:
                    req = response.request
                    rtype = req.resource_type
                    url = response.url

                    # Only keep certain resource types
                    if rtype in ("image", "stylesheet", "script", "font"):
                        responses.append((url, rtype))
                except Exception:
                    pass

            page.on("response", handle_response)

            try:
                page.goto(current_url, wait_until="networkidle", timeout=60000)
            except Exception as e:
                print(f"  ! Error loading {current_url}: {e}")
                page.close()
                continue

            # Get the fully rendered HTML
            html = page.content()

            # Save HTML
            html_path = url_to_local_html_path(START_URL, current_url)
            html_dir = os.path.dirname(html_path)
            os.makedirs(html_dir, exist_ok=True)
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)

            # Parse links from HTML and queue internal pages
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith("mailto:") or href.startswith("tel:"):
                    continue
                target = normalize_url(current_url, href)
                if is_same_site(START_URL, target) and target not in visited_pages and target not in queued_pages:
                    queued_pages.append(target)

            # Download assets seen on this page
            for asset_url, rtype in responses:
                if asset_url in downloaded_assets:
                    continue
                downloaded_assets.add(asset_url)

                asset_path = url_to_local_asset_path(asset_url)
                asset_dir = os.path.dirname(asset_path)
                os.makedirs(asset_dir, exist_ok=True)

                print(f"  [ASSET] {rtype}: {asset_url}")
                try:
                    # Use Playwright's request context to fetch the asset
                    resp = context.request.get(asset_url, timeout=60000)
                    if not resp.ok:
                        print(f"    ! Failed ({resp.status})")
                        continue

                    content = resp.body()
                    # Decide binary vs text by extension (rough heuristic)
                    if re.search(r"\.(css|js|json|txt|html?|xml)$", asset_path, re.IGNORECASE):
                        mode = "w"
                        with open(asset_path, mode, encoding="utf-8", errors="ignore") as f:
                            f.write(content.decode("utf-8", errors="ignore"))
                    else:
                        mode = "wb"
                        with open(asset_path, mode) as f:
                            f.write(content)

                except Exception as e:
                    print(f"    ! Error downloading {asset_url}: {e}")

            page.close()

        browser.close()


if __name__ == "__main__":
    crawl_site()
