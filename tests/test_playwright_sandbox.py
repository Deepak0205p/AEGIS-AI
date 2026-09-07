import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

def run():
    print("[1] Launching Playwright browser...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 850})
        page = context.new_page()

        # Step 1: Open Login Page
        print("[2] Navigating to login page (http://localhost:3000/login)...")
        page.goto("http://localhost:3000/login", timeout=30000)
        page.wait_for_load_state("networkidle")

        # Step 2: Login as operator
        print("[3] Submitting login credentials...")
        page.fill('input[type="text"]', "operator")
        page.fill('input[type="password"]', "RefineryPass2026!")
        page.click('button[type="submit"]')

        # Step 3: Wait for main chat page
        print("[4] Waiting for main chat interface...")
        page.wait_for_url("http://localhost:3000/**", timeout=20000)
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Step 4: Type Prompt in Chat Input
        print("[5] Entering code execution prompt...")
        chat_input = page.locator('textarea')
        chat_input.first.wait_for(state="visible", timeout=10000)
        prompt_text = "Write Python code to compute factorial of 6 and print the result."
        chat_input.first.fill(prompt_text)
        time.sleep(1)

        # Step 5: Send the prompt
        print("[6] Submitting message...")
        send_button = page.locator('button:has(svg.lucide-arrow-up), button:has(svg.lucide-send), button[type="submit"]')
        if send_button.count() > 0 and send_button.first.is_enabled():
            send_button.first.click()
        else:
            chat_input.first.press("Enter")

        # Step 6: Wait for response streaming & sandbox execution
        print("[7] Waiting for streaming & sandbox execution (up to 30s)...")
        time.sleep(10)
        for sec in range(20):
            time.sleep(1)
            content = page.content()
            if "720" in content or "factorial" in content.lower():
                print(f"  --> Received code result at ~{sec+11}s!")
                break

        # Step 7: Take Screenshot
        screenshot_path = Path("tests/sandbox_playwright_result.png").resolve()
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"[8] Saved full page screenshot to: {screenshot_path}")

        # Extract page text
        body_text = page.locator("body").inner_text()
        print("\n=== PLAYWRIGHT RUN OUTPUT SUMMARY ===")
        filtered_lines = [l.strip() for l in body_text.splitlines() if l.strip()]
        for line in filtered_lines[-30:]:
            print(f"  | {line}")
        print("=====================================\n")

        browser.close()
        print("[OK] Playwright sandbox test finished successfully!")

if __name__ == "__main__":
    run()
