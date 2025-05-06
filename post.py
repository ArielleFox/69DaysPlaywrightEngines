import re
import sys
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    trackingNumber: str = sys.argv[1]
    print(f'Connecting To Server')
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://www.post.at/en")
    print('Connection Successfully')
    page.get_by_role("button", name="Use website with required").click()
    print('Ignoring US Cookies')
    page.get_by_label("", exact=True).click()
    print('Closing Login Window')
    page.get_by_label("", exact=True).fill(trackingNumber)
    page.get_by_role("button", name="Submit query").click()
    print(f'Requesting Number: {trackingNumber}')
    page.get_by_role("button", name="Close dialogue box").click()
    info = page.get_by_label("Ergebnis Sendungsverfolgung").locator("div").filter(has_text="Item detailsTracking number:").all_text_contents()
    #page.get_by_label("Ergebnis Sendungsverfolgung").locator("div").filter(has_text="Item detailsTracking number:")
    # ---------------------
    context.close()
    browser.close()

    for i in info:
        print(i.replace(',', '\n').replace('Show senderDestination postcode:', '\n  ').replace('Sender:', ' ').replace('Postal code 2005', 'Postal code 2005 ').replace('Item detailsTracking number:', 'Item detailsTracking number: ').replace('cm', 'cm ').replace('kg', 'kg\n  ').replace('The sender has provided electronic shipment information', ' The sender has provided electronic shipment information ').replace('AT', '').replace(f'Item detailsTracking number: {trackingNumber}', '').replace('Item delivered to consignee', '\n  [Item delivered] to consignee ').replace('Postal code 1700', 'Postal code 1700 ').replace('Postal code 1220', 'Postal code 1220 ').replace('Item is out for delivery', ' Item is out for delivery ').replace('Item distributed', ' Item distributed ').replace('Item delivered', ' Item delivered').replace('Show destination postcode', 'Show destination postcode INSERT-VARIABLE-HERE ').replace('Weight', 'Weight ').replace('May', ' May').replace('Jun', 'Jun ').replace('Jul', 'Jul ').replace('Aug', 'Aug ').replace('Sep', 'Sep ').replace('Oct', 'Oct ').replace('Nov', 'Nov ').replace('Dec', 'Dec '))

with sync_playwright() as playwright:
    run(playwright)
