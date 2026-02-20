from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('http://localhost:5173')
    page.wait_for_load_state('networkidle')
    
    print("Page title:", page.title())
    print("Page content:")
    print(page.content()[:1000])
    
    screenshot_path = r'C:\Users\Alan ZA Zhang\Desktop\newcode\code-insight\code-insight\screenshot.png'
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot saved to: {screenshot_path}")
    
    browser.close()
