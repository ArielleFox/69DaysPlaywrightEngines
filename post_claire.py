#!/bin/env python3.13
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

    infos = page.get_by_label("Ergebnis Sendungsverfolgung").locator("div.tracking__details")
    # help(infos)

    # print(f"{infos.all_inner_texts()=}")
    # print(f"{infos.all_text_contents()=}")
    # print(f"{infos.inner_html()=}")

    txt = "\n\n\n".join(infos.all_inner_texts())
    txt = txt.replace(" H\n", " H ")
    txt = txt.replace(" L\n", " L ")
    txt = txt.replace("\n\n", "\n")
    print(txt)

    context.close()
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
