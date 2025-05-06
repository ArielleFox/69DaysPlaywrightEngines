#!/usr/bin/env python3
import asyncio
import argparse
from playwright.async_api import async_playwright
from rich.console import Console
from rich.table import Table
from urllib.parse import urljoin
import random

console = Console()

async def amazon_search(query, max_results=10):
    async with async_playwright() as p:
        # Configure browser with anti-detection measures
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(90,120)}.0.0.0 Safari/537.36'
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='de-DE',
            timezone_id='Europe/Berlin'
        )
        
        page = await context.new_page()
        
        try:
            # Navigate with randomized patterns
            await page.goto('https://www.amazon.de', timeout=50000, wait_until="domcontentloaded")
            await page.wait_for_timeout(random.uniform(1, 3)*1000)

            # Handle cookie banner with multiple selectors
            cookie_selectors = [
                '#sp-cc-accept', 
                '#acceptCookiesButton',
                'button:has-text("Acceptieren")'
            ]
            for selector in cookie_selectors:
                try:
                    await page.click(selector, timeout=3000)
                    console.print(f"[green]✓[/green] Accepted cookies via {selector}")
                    break
                except:
                    continue

            # Perform human-like search interaction
            await page.type('#twotabsearchtextbox', query, delay=random.uniform(50, 100))
            await page.wait_for_timeout(random.uniform(0.5, 1.5)*500)
            await page.click('#nav-search-submit-button')
            
            # Wait for core results with multiple fallbacks
            try:
                await page.wait_for_selector('div.s-main-slot.s-result-list', timeout=5000)
            except:
                await page.wait_for_selector('.s-result-item', timeout=5000)

            # Scroll through page progressively
            for _ in range(3):
                await page.mouse.wheel(0, random.randint(200, 500))
                await page.wait_for_timeout(random.uniform(0.5, 2)*1000)

            # Extract product data with modern selectors
            results = []
            items = await page.query_selector_all('div.s-result-item:not(.s-ad-result)')
            
            for item in items[:max_results]:
                data = {'Title': 'N/A', 'Price': 'N/A', 'Rating': 'N/A', 'URL': 'N/A'}
                
                try:
                    # Title with multiple fallbacks
                    title_elem = await item.query_selector('h2 a span, .a-size-base-plus.a-color-base')
                    if title_elem:
                        data['Title'] = (await title_elem.text_content()).strip()[:80]

                    # Price handling with currency detection
                    price_elem = await item.query_selector('.a-price .a-offscreen, .a-price-fraction, .a-color-price')
                    if price_elem:
                        price_text = await price_elem.text_content()
                        data['Price'] = price_text.replace('\xa0', ' ').strip()

                    # Rating with decimal conversion
                    rating_elem = await item.query_selector('.a-icon-star-small .a-icon-alt, i.a-icon-star-small')
                    if rating_elem:
                        rating_text = await rating_elem.text_content()
                        data['Rating'] = rating_text.split()[0].replace(',', '.')

                    # URL validation and cleaning
                    link_elem = await item.query_selector('h2 a.a-link-normal')
                    if link_elem:
                        rel_url = await link_elem.get_attribute('href')
                        data['URL'] = urljoin('https://www.amazon.de', rel_url).split('/ref=')[0]

                    results.append(data)
                
                except Exception as e:
                    continue

            return [r for r in results if any(v != 'N/A' for v in r.values())]

        finally:
            await browser.close()

def display_results(results):
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Title", width=60)
    table.add_column("Price", justify="right")
    table.add_column("Rating", justify="center")
    table.add_column("URL", width=40)

    for item in results:
        table.add_row(
            item['Title'],
            item['Price'],
            item['Rating'],
            (item['URL'][:35] + '...') if len(item['URL']) > 35 else item['URL']
        )
    
    console.print(table)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Amazon.de Search CLI')
    parser.add_argument('query', help='Search term')
    parser.add_argument('--max', type=int, default=5, help='Max results')
    args = parser.parse_args()

    console.print(f"\n🔍 Searching Amazon.de for [bold cyan]{args.query}[/bold cyan]...")
    results = asyncio.run(amazon_search(args.query, args.max + 2))
    display_results(results)
    console.print(f"\n[bold green]Found {len(results)} valid results[/bold green]")
