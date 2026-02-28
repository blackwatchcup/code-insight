#!/usr/bin/env python3
"""Test project update and version control functionality"""
from playwright.sync_api import sync_playwright
import time

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Navigate to projects list
        print("Navigating to projects page...")
        page.goto('http://127.0.0.1:5173', timeout=30000)
        page.wait_for_load_state('networkidle', timeout=30000)

        # Screenshot initial state
        page.screenshot(path='C:/tmp/01_projects_list.png', full_page=True)
        print("Screenshot taken: projects_list.png")

        # Look for project card - wait for it to load
        print("Waiting for project cards to load...")
        page.wait_for_timeout(3000)

        # Take screenshot to see available projects
        page.screenshot(path='C:/tmp/02_project_card.png', full_page=True)

        # Find and click on the project (code-insight)
        print("Looking for project card...")

        # Try multiple selectors
        selectors_to_try = [
            'div[class*="group"]',
            'a[href*="/project/"]',
            'text=code-insight',
            'div.rounded-xl',
            '[class*="bg-white"]',
        ]

        project_card = None
        for selector in selectors_to_try:
            try:
                print(f"Trying selector: {selector}")
                card = page.locator(selector).first
                if card.count() > 0:
                    print(f"Found element with selector: {selector}")
                    project_card = card
                    break
            except:
                continue

        if not project_card:
            print("No project card found with any selector")
            # Debug: Print page content
            print(f"Page URL: {page.url}")
            print(f"Page title: {page.title()}")
            return

            # Click on the project
            print("Clicking on project...")
            first_card.click()
            page.wait_for_load_state('networkidle')
            page.wait_for_timeout(2000)

            # Screenshot project detail page
            page.screenshot(path='/tmp/03_project_detail.png', full_page=True)
            print("Screenshot taken: project_detail.png")

            # Look for update button
            print("Looking for update button...")
            update_button = page.get_by_text("更新项目")
            if update_button.count() == 0:
                print("Update button not found")
                # Take screenshot to debug
                page.screenshot(path='/tmp/04_no_update_button.png', full_page=True)
            else:
                print(f"Found update button")
                # Screenshot before clicking
                page.screenshot(path='/tmp/05_before_update.png', full_page=True)

                # Click update button
                print("Clicking update button...")
                update_button.click()

                # Wait for alert or loading state
                page.wait_for_timeout(3000)

                # Screenshot during update
                page.screenshot(path='/tmp/06_during_update.png', full_page=True)

                # Handle alert dialog
                page.on("dialog", lambda dialog: dialog.accept())
                page.wait_for_timeout(2000)

                # Screenshot after update
                page.screenshot(path='/tmp/07_after_update.png', full_page=True)

                # Look for loading spinner
                loading_spenters = page.locator('[class*="animate-spin"]').all()
                print(f"Loading spinners found: {len(loading_spenters)}")

                # Wait a bit more to see the result
                page.wait_for_timeout(5000)

                # Final screenshot
                page.screenshot(path='/tmp/08_final_state.png', full_page=True)

        except Exception as e:
            print(f"Error during navigation: {e}")
            page.screenshot(path='/tmp/error_screenshot.png', full_page=True)
            import traceback
            traceback.print_exc()

        # Check console for errors
        print("\n=== Console Errors ===")
        page.on("console", lambda msg: print(f"Console: {msg.type} - {msg.text}"))

        print("\nTest completed. Screenshots saved to /tmp/")
        print("Press Enter to close browser...")
        input()

        browser.close()

if __name__ == '__main__':
    main()
