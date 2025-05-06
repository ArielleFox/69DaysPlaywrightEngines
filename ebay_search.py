#!/usr/bin/env python3
import asyncio
import argparse
import json
import csv
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from rich.console import Console
from rich.table import Table

console = Console()

async def ebay_search(query, max_results=10, headless=False, auction_only=False):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
            ]
        )

        context = await browser.new_context()
        page = await context.new_page()

        try:
            base_url = f"https://www.ebay.at/sch/i.html?_nkw={query.replace(' ', '+')}&_sacat=0&_from=R40"
            if auction_only:
                base_url += "&LH_Auction=1&_sop=1&rt=nc&LH_PrefLoc=3"  # Auction + Newly Listed
            else:
                base_url += "&rt=nc&rt=nc&LH_PrefLoc=3"  # Default sort

            await page.goto(base_url, timeout=60000)

            # Handle cookie banner
            try:
                await page.click('button#gdpr-banner-accept', timeout=3000)
                console.print("[green]✓[/green] Cookies accepted")
            except PlaywrightTimeoutError:
                pass

            await page.wait_for_selector('.s-item', timeout=15000)
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(2000)
            
            results = []
            items = await page.query_selector_all('.s-item:not(.s-ad)')

            for item in items:
                try:
                    if await item.query_selector('.s-item__title--tag'):
                        continue  # Skip promoted or header items

                    title = await item.evaluate('el => el.querySelector(".s-item__title")?.textContent.trim() || "N/A"')
                    if 'new listing' in title.lower():
                        continue

                    price_text = await item.evaluate('el => el.querySelector(".s-item__price")?.textContent.trim() || "N/A"')
                    clean_price = price_text.replace('EUR', '').replace('€', '').replace(',', '.').replace(' ', '')
                    if 'bis' in clean_price:
                        clean_price = clean_price.split('bis')[0].strip()
                    try:
                        price_value = float(clean_price)
                    except ValueError:
                        price_value = 0.0

                    condition = await item.evaluate('el => el.querySelector(".s-item__subtitle")?.textContent.trim() || "N/A"')
                    shipping = await item.evaluate('el => el.querySelector(".s-item__shipping")?.textContent.trim() || "N/A"')
                    url = await item.evaluate('''
                        el => {
                            const link = el.querySelector(".s-item__link");
                            return link ? link.href.split("?")[0] : "N/A";
                        }
                    ''')

                    bids = await item.evaluate('el => el.querySelector(".s-item__bids")?.textContent.trim() || "N/A"')
                    time_left = await item.evaluate('el => el.querySelector(".s-item__time-left")?.textContent.trim() || "N/A"')
                    location = await item.evaluate('el => el.querySelector(".s-item__location")?.textContent.trim() || "N/A"')

                    results.append({
                        'Title': title,
                        'Price': price_text,
                        'PriceValue': price_value,
                        'Condition': condition,
                        'Shipping': shipping,
                        'Bids': bids,
                        'TimeLeft': time_left,
                        'Location': location,
                        'URL': url
                    })

                    if len(results) >= max_results:
                        break

                except Exception as e:
                    console.print(f"[red]Error parsing item: {e}[/red]")
                    continue

               
            sorted_results = sorted(results, key=lambda x: x['PriceValue'], reverse=True)
            return sorted_results

        finally:
            await browser.close()

def display_results(results):
    table = Table(
        show_header=True,
        header_style="bold cyan",
        box=None,
        show_lines=False,
        padding=(0, 1)
    )

    table.add_column("Price", justify="right", width=15)
    table.add_column("Title", width=50)
    table.add_column("Condition", width=18)
    table.add_column("Shipping", width=18)
    table.add_column("Bids", width=8, justify="center")
    table.add_column("Time Left", width=18)
    table.add_column("Location", width=18)
    table.add_column("URL", width=40, no_wrap=True)

    for item in results:
        table.add_row(
            item['Price'],
            item['Title'],
            item['Condition'],
            item['Shipping'],
            item['Bids'],
            item['TimeLeft'],
            item['Location'],
            item['URL'][:40] + '...' if len(item['URL']) > 40 else item['URL']
        )

    console.print(table)

def export_results(results, output_path, fmt='json'):
    path = Path(output_path)
    if fmt == 'json':
        with path.open('w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
            f.close()
        console.print(f"[blue]✓ Exported results to[/blue] {path.resolve()}")
    elif fmt == 'csv':
        with path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
            f.close()

        console.print(f"[blue]✓ Exported results to[/blue] {path.resolve()}")
    else:
        console.print(f"[red]✗ Unsupported export format: {fmt}[/red]")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='eBay.at Search CLI')
    parser.add_argument('query', help='Search term')
    parser.add_argument('--max', type=int, default=5, help='Max number of results')
    parser.add_argument('--headless', action='store_true', help='Run browser headlessly')
    parser.add_argument('--export', help='Export results to file (JSON or CSV)')
    parser.add_argument('--auction-only', action='store_true', help='Only show auction listings (newest first)')

    args = parser.parse_args()

    console.print(f"\n🔍 Searching eBay.at for [bold yellow]{args.query}[/bold yellow]...")
    results = asyncio.run(ebay_search(
        query=args.query,
        max_results=args.max + 2,
        headless=args.headless,
        auction_only=args.auction_only
    ))
    display_results(results)
    console.print(f"\n[bold green]✓ Found {len(results)} results (sorted by price)[/bold green]")

    if args.export:
        fmt = 'csv' if args.export.endswith('.csv') else 'json'
        export_results(results, args.export, fmt=fmt)

