#!/usr/bin/env python3
import sys
import asyncio
import json
from urllib.parse import urlparse
from functools import wraps
from playwright.async_api import async_playwright, TimeoutError

# Global variables
WEBSITE: str = sys.argv[1] if len(sys.argv) > 1 else "https://www.example.com"
SCREENSHOT_FILENAME: str = 'page.png'
BROWSER_CHOICE = 'chromium'

# Decorator to validate PNG filenames
def validate_png_filename(func):
    @wraps(func)
    def wrapper(filename, *args, **kwargs):
        if not filename.lower().endswith('.png'):
            filename = filename + '.png'
        return func(filename, *args, **kwargs)
    return wrapper

@validate_png_filename
def process_image_name(filename):
    print(f"Processing {filename}")

def get_cookie_filename(url):
    """Generate a cookie filename based on website domain"""
    parsed = urlparse(url)
    domain = parsed.netloc
    if not domain:  # Fallback for invalid URLs
        domain = "default"
    # Replace special characters to create safe filename
    domain = domain.replace(":", "_").replace(".", "_")
    return f"{domain}_cookies.json"

async def load_cookies(context, cookie_file):
    """Load cookies from file into browser context"""
    try:
        with open(cookie_file, "r") as f:
            cookies = json.load(f)
            await context.add_cookies(cookies)
            f.close()
            print(f"Loaded cookies from {cookie_file}")
    except FileNotFoundError:
        print(f"No existing cookie file: {cookie_file}")
    except Exception as e:
        print(f"Error loading cookies: {str(e)}")

async def save_cookies(context, cookie_file):
    """Save current context cookies to file"""
    cookies = await context.cookies()
    with open(cookie_file, "w") as f:
        json.dump(cookies, f, indent=2)
        f.close()
    print(f"Saved cookies to {cookie_file}")

async def close_cookie_banners(page):
    """Special handling for Amazon.de's complex cookie banner"""
    # Amazon-specific selectors
    amazon_selectors = [
        '#sp-cc-accept',  # Primary accept button ID
        'input[sp-cookie-accept="accept"]',  # Form input alternative
        'button:has-text("Akzeptieren")',  # Text-based fallback
        'div[data-cel-widget="sp-cc"] button:has-text("Akzeptieren")'  # Container-specific
    ]

    # First try with standard approach
    if await handle_amazon_banner(page, amazon_selectors):
        return True

    # Fallback to iframe check (though Amazon typically doesn't use iframes for this)
    frames = [page.main_frame] + page.frames
    for frame in frames:
        for selector in amazon_selectors:
            try:
                await frame.click(selector, timeout=450)
                print(f"Clicked Cookie banner using selector: {selector}")
                await page.wait_for_load_state('networkidle')
                return True
            except Exception as e:
                continue

    print("No Cookie banner found")
    return False

async def handle_amazon_banner(page, selectors):
    """Special handling for Amazon's layered consent dialog"""
    try:
        # Wait for banner container to appear
        await page.wait_for_selector('div[data-cel-widget="sp-cc"]', timeout=500)

        # Click the main accept button
        await page.click('#sp-cc-accept', timeout=450)
        print("Clicked primary accept button")
        await page.wait_for_load_state('networkidle')
        return True
    except Exception as e:
        print(f"Cookie banner handling failed: {str(e)}")
        return False

async def run(playwright):
    global SCREENSHOT_FILENAME, WEBSITE, BROWSER_CHOICE

    # Initialize browser
    browser_types = {
        "firefox": playwright.firefox,
        "chromium": playwright.chromium
    }
    browser = await browser_types[BROWSER_CHOICE].launch(headless=True)

    # Create context and load cookies
    context = await browser.new_context()
    cookie_file = get_cookie_filename(WEBSITE)
    await load_cookies(context, cookie_file)

    # Browser interactions
    page = await context.new_page()
    await page.goto(WEBSITE)

    # Handle cookie banner and save cookies if needed
    if await close_cookie_banners(page):
        await save_cookies(context, cookie_file)

    # Capture screenshot
    await page.screenshot(path=SCREENSHOT_FILENAME, full_page=True)
    print(f"Screenshot saved to {SCREENSHOT_FILENAME}")

    await browser.close()

async def main():
    async with async_playwright() as playwright:
        await run(playwright)

if __name__ == '__main__':
    try:
        process_image_name(SCREENSHOT_FILENAME)
        asyncio.run(main())
    except ValueError as e:
        print(f"Error: {e}")
