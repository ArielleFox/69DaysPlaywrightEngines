#!/usr/bin/env python3
import asyncio
import argparse
from playwright.async_api import async_playwright
from rich.console import Console
from rich.table import Table

console = Console()

async def amazon_search(query, max_results=10):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
            ]
        )

        context = await browser.new_context()
        page = await context.new_page()

        try:
            # Bypass bot detection with direct search URL
            await page.goto(f'https://www.amazon.de/s?k={query.replace(" ", "+")}', timeout=60000)

            # Accept cookies if popup exists
            try:
                await page.click('#sp-cc-accept', timeout=3000)
                console.print("[green]✓[/green] Cookies accepted")
            except:
                pass

            # Wait for core results
            await page.wait_for_selector('.s-result-item', timeout=15000)

            # Force load all results
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(2000)

            # Extract product data
            results = []
            items = await page.query_selector_all('.s-result-item:not(.s-ad-result)')

            for item in items[:max_results]:
                try:
                    # Title with multiple fallbacks
                    title = await item.evaluate('''el => {
                        return el.querySelector('h2 a span')?.textContent.trim() || 
                               el.querySelector('img.s-image')?.alt.trim() || 
                               'N/A';
                    }''')

                    # Price handling
                    price = await item.evaluate('''el => {
                        const priceEl = el.querySelector('.a-price .a-offscreen, .a-color-price');
                        return priceEl ? priceEl.textContent.trim().replace(/\\u00a0/g, ' ') : 'N/A';
                    }''')

                    # Rating handling
                    rating = await item.evaluate('''el => {
                        const ratingEl = el.querySelector('.a-icon-alt');
                        return ratingEl ? ratingEl.textContent.split(' ')[0].replace(',', '.') : 'N/A';
                    }''')

                    # Direct URL extraction
                    url = await item.evaluate('''el => {
                        const link = el.querySelector('h2 a');
                        return link ? link.href : 'N/A';
                    }''')

                    results.append({
                        'Title': title[:75] + '...' if len(title) > 75 else title,
                        'Price': price,
                        'Rating': rating,
                        'URL': url.split('?')[0]  # Clean URL
                    })
                except:
                    continue

            return [r for r in results if any(v != 'N/A' for v in r.values())]

        finally:
            await browser.close()

def display_results(results):
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Title", width=60)
    table.add_column("Price", justify="right")
    table.add_column("Rating", justify="center")
    table.add_column("URL", width=50)

    for item in results:
        table.add_row(
            item['Title'],
            item['Price'],
            item['Rating'],
            item['URL'][:55] + '...' if len(item['URL']) > 55 else item['URL']
        )
    
    console.print(table)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Amazon.de Search CLI')
    parser.add_argument('query', help='Search term')
    parser.add_argument('--max', type=int, default=5, help='Max results')
    args = parser.parse_args()

    console.print(f"\n🔍 Searching for [bold yellow]{args.query}[/bold yellow]...")
    results = asyncio.run(amazon_search(args.query, args.max + 2))
    display_results(results)
    console.print(f"\n[bold green]Found {len(results)} results[/bold green]")
