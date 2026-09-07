import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('http://localhost:3000/login', wait_until='networkidle')
    page.fill('input[type=" text\]', 'operator')
 page.fill('input[type=\password\]', 'RefineryPass2026!')
 page.click('button[type=\submit\]')
 page.wait_for_selector('textarea', timeout=15000)
 time.sleep(2)

 textarea = page.locator('textarea')
 textarea.fill('hi')
 textarea.press('Enter')
 time.sleep(6)

 body_text = page.inner_text('body')
 print('=== RESULT OF HI IN UI ===')
 for line in body_text.splitlines():
 if 'hello' in line.lower() or 'help' in line.lower():
 print('Captured line:', line)

 browser.close()
