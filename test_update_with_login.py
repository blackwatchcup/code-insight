#!/usr/bin/env python3
"""Test project update with authentication"""
from playwright.sync_api import sync_playwright
import os
import time

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Create output directory
        os.makedirs('C:/tmp/screenshots', exist_ok=True)

        # Navigate to login page first
        print("1. Navigating to login page...")
        page.goto('http://127.0.0.1:5173/login', timeout=30000)
        page.wait_for_load_state('networkidle', timeout=30000)

        # Screenshot login page
        page.screenshot(path='C:/tmp/screenshots/01_login_page.png', full_page=True)

        # Fill in login form
        print("2. Filling login form...")
        page.fill('input[type="email"]', 'alan')
        page.fill('input[type="password"]', '123456')

        # Screenshot after filling
        page.screenshot(path='C:/tmp/screenshots/02_login_filled.png', full_page=True)

        # Submit login
        print("3. Submitting login...")
        page.locator('button[type="submit"]').click()
        page.wait_for_load_state('networkidle', timeout=10000)
        page.wait_for_timeout(2000)

        # Screenshot after login
        page.screenshot(path='C:/tmp/screenshots/03_after_login.png', full_page=True)
        print(f"Current URL: {page.url()}")

        # Navigate to projects list
        print("4. Navigating to projects...")
        page.goto('http://127.0.0.1:5173', timeout=30000)
        page.wait_for_load_state('networkidle', timeout=30000)

        # Screenshot projects list
        page.screenshot(path='C:/tmp/screenshots/04_projects_list.png', full_page=True)

        # Wait for project cards
        print("5. Waiting for projects to load...")
        page.wait_for_timeout(3000)

        # Find and click on project
        print("6. Finding project card...")
        try:
            # Try clicking on the project
            selectors = [
                'a[href*="/project/"]',
                'div[class*="group"]',
                '[class*="bg-white"]',
            ]

            clicked = False
            for selector in selectors:
                print(f"Trying selector: {selector}")
                elements = page.locator(selector).all()
                if elements:
                    print(f"Found {len(elements)} elements with selector {selector}")
                    elements[0].click()
                    clicked = True
                    break

            if not clicked:
                print("Could not find project to click")
                page.screenshot(path='C:/tmp/screenshots/05_no_project.png', full_page=True)
                return

            # Wait for navigation to project detail
            page.wait_for_load_state('networkidle', timeout=10000)
            page.wait_for_timeout(2000)

            # Screenshot project detail page
            page.screenshot(path='C:/tmp/screenshots/06_project_detail.png', full_page=True)
            print(f"Project detail URL: {page.url()}")

            # Look for update button
            print("7. Looking for update button...")
            update_selectors = [
                'button:has-text("更新项目")',
                'text=更新项目',
                'button[class*="update"]',
            ]

            update_button = None
            for selector in update_selectors:
                print(f"Trying update button selector: {selector}")
                btn = page.locator(selector).first
                if btn.count() > 0:
                    print(f"Found update button with selector: {selector}")
                    update_button = btn
                    break

            if not update_button:
                print("Update button not found")
                page.screenshot(path='C:/tmp/screenshots/07_no_update_button.png', full_page=True)
            else:
                # Screenshot before clicking
                page.screenshot(path='C:/tmp/screenshots/08_before_update.png', full_page=True)

                print("8. Clicking update button...")
                update_button.click()

                # Wait for alert and handle it
                page.wait_for_timeout(3000)
                try:
                    page.on("dialog", lambda dialog: dialog.accept())
                    print("Accepted alert dialog")
                except:
                    pass

                # Wait and screenshot
                page.wait_for_timeout(5000)
                page.screenshot(path='C:/tmp/screenshots/09_after_update.png', full_page=True)

                # Check for loading spinner
                loading_spenters = page.locator('[class*="animate-spin"]').all()
                if loading_spenters:
                    print(f"Found {len(loading_spenters)} loading spinner(s)")
                    page.wait_for_timeout(3000)
                    page.screenshot(path='C:/tmp/screenshots/10_during_loading.png', full_page=True)

                # Final screenshot
                page.wait_for_timeout(3000)
                page.screenshot(path='C:/tmp/screenshots/11_final_state.png', full_page=True)

                print("\n✅ Test completed successfully!")
                print("Screenshots saved to C:/tmp/screenshots/")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            page.screenshot(path='C:/tmp/screenshots/error_screenshot.png', full_page=True)

        print("\nPress Enter to close browser...")
        input()
        browser.close()

if __name__ == '__main__':
    main()
