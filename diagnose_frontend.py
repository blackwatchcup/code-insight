#!/usr/bin/env python3
"""Diagnose frontend rendering and git endpoint issues"""
from playwright.sync_api import sync_playwright
import os
import json

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Enable console logging
        console_messages = []
        page.on("console", lambda msg: console_messages.append({
            'type': msg.type,
            'text': msg.text
        }))

        # Create output directory
        os.makedirs('C:/tmp/screenshots', exist_ok=True)

        # Navigate to login page
        print("=== 1. Login ===")
        page.goto('http://127.0.0.1:5173/login', timeout=30000)
        page.wait_for_load_state('networkidle', timeout=30000)

        # Fill and submit login
        page.fill('input[type="email"]', 'alan')
        page.fill('input[type="password"]', '123456')
        page.screenshot(path='C:/tmp/screenshots/01_login_filled.png', full_page=True)

        page.locator('button[type="submit"]').click()
        page.wait_for_load_state('networkidle', timeout=10000)
        page.wait_for_timeout(2000)
        page.screenshot(path='C:/tmp/screenshots/02_after_login.png', full_page=True)

        # Navigate to project detail directly
        print("\n=== 2. Navigate to Project Detail ===")
        project_id = "de84cb3a"
        page.goto(f'http://127.0.0.1:5173/project/{project_id}', timeout=30000)
        page.wait_for_load_state('networkidle', timeout=30000)
        page.wait_for_timeout(3000)

        # Screenshot the entire page
        page.screenshot(path='C:/tmp/screenshots/03_project_detail_full.png', full_page=True)
        print(f"Current URL: {page.url()}")

        # Check page title
        title = page.title()
        print(f"Page title: {title}")

        # Check for errors in console
        if console_messages:
            print("\n=== Console Errors ===")
            for msg in console_messages:
                if msg['type'] == 'error':
                    print(f"ERROR: {msg['text']}")

        # Look for update button
        print("\n=== 3. Looking for Update Button ===")
        update_button = None

        # Try multiple selectors
        selectors = [
            'button:has-text("更新项目")',
            'text=更新项目',
            'button:has(svg)',  # Any button with icon
            '[onclick*="update"]',
            'button[class*="update"]',
        ]

        for i, selector in enumerate(selectors, 1):
            print(f"Trying selector {i}: {selector}")
            try:
                btn = page.locator(selector).first
                count = btn.count()
                print(f"  Found {count} element(s)")
                if count > 0:
                    # Get bounding box
                    box = btn.bounding_box()
                    print(f"  Position: {box}")
                    print(f"  Text: {btn.text_content()}")
                    print(f"  Visible: {btn.is_visible()}")
                    if not update_button:
                        update_button = btn
                        break
            except Exception as e:
                print(f"  Error: {e}")

        if not update_button:
            print("\n❌ Update button NOT FOUND")
            # Try to list all buttons
            all_buttons = page.locator('button').all()
            print(f"\nTotal buttons found: {len(all_buttons)}")
            for i, btn in enumerate(all_buttons[:10], 1):
                print(f"  Button {i}: {btn.text_content()}")
        else:
            print("\n✅ Update button found!")
            page.screenshot(path='C:/tmp/screenshots/04_update_button_highlighted.png', full_page=True)

            # Click update button
            print("\n=== 4. Clicking Update Button ===")
            update_button.click()

            # Wait for alert
            page.wait_for_timeout(3000)
            try:
                page.on("dialog", lambda dialog: dialog.accept())
                print("Alert accepted")
            except:
                pass

            page.wait_for_timeout(3000)
            page.screenshot(path='C:/tmp/screenshots/05_after_update_click.png', full_page=True)

            # Navigate to versions tab
            print("\n=== 5. Testing Git Version Retrieval ===")
            version_tab = page.locator('button:has-text("版本对比")')
            if version_tab.count() > 0:
                version_tab.click()
                page.wait_for_load_state('networkidle', timeout=10000)
                page.wait_for_timeout(2000)

                page.screenshot(path='C:/tmp/screenshots/06_version_tab.png', full_page=True)

                # Look for commits
                commits = page.locator('span:has-text("作者:")')
                commits_count = commits.count()
                print(f"Found {commits_count} commit entries")

                if commits_count == 0:
                    print("\n❌ No commits found")
                else:
                    print("\n✅ Commits are displayed")
                    page.screenshot(path='C:/tmp/screenshots/07_commits_shown.png', full_page=True)

                # Check console for git endpoint errors
                print("\n=== Console Messages After Version Tab ===")
                git_errors = [msg for msg in console_messages if 'git' in msg['text'].lower() and msg['type'] == 'error']
                if git_errors:
                    print(f"Git-related errors:")
                    for err in git_errors:
                        print(f"  {err['type']}: {err['text']}")
                else:
                    print("No git-related errors in console")
            else:
                print("\n❌ Version tab not found")

        # Final check
        print("\n=== 6. Final Checks ===")
        print(f"Current URL: {page.url()}")
        print(f"Page title: {page.title()}")
        print(f"Total console messages: {len(console_messages)}")
        print(f"Console errors: {len([msg for msg in console_messages if msg['type'] == 'error'])}")

        # Save console log
        with open('C:/tmp/screenshots/console_log.json', 'w', encoding='utf-8') as f:
            json.dump(console_messages, f, indent=2, ensure_ascii=False)

        page.screenshot(path='C:/tmp/screenshots/08_final_state.png', full_page=True)

        print("\n=== Test Complete ===")
        print("Screenshots saved to C:/tmp/screenshots/")
        print("Console log saved to C:/tmp/screenshots/console_log.json")
        print("Press Enter to close browser...")
        input()

        context.close()
        browser.close()

if __name__ == '__main__':
    main()
