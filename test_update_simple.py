#!/usr/bin/env python3
"""Test project update and version control functionality"""
from playwright.sync_api import sync_playwright
import time
import os

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Create output directory
        os.makedirs('C:/tmp/screenshots', exist_ok=True)

        # Navigate to projects list
        print("Navigating to projects page...")
        page.goto('http://127.0.0.1:5173', timeout=30000)
        page.wait_for_load_state('networkidle', timeout=30000)

        # Screenshot initial state
        page.screenshot(path='C:/tmp/screenshots/01_projects_list.png', full_page=True)
        print("Screenshot taken: projects_list.png")

        # Look for project card - wait for it to load
        print("Waiting for project cards to load...")
        page.wait_for_timeout(3000)

        # Take screenshot to see available projects
        page.screenshot(path='C:/tmp/screenshots/02_project_card.png', full_page=True)

        # Try to find clickable element that leads to project detail
        print("Looking for project link or card...")
        try:
            # Try multiple selectors to find project
            selectors = [
                'a[href*="/project/"]',
                'div[class*="group"]',
                'div.rounded-xl',
            ]

            for selector in selectors:
                print(f"Trying selector: {selector}")
                elements = page.locator(selector).all()
                print(f"Found {len(elements)} elements with selector {selector}")
                if elements:
                    print("Clicking on first element...")
                    elements[0].click()
                    break
            else:
                print("No elements found with any selector")
                # Debug: print page content
                print(f"Page URL: {page.url}")
                print(f"Page title: {page.title()}")

            # Wait for navigation
            page.wait_for_load_state('networkidle', timeout=10000)
            page.wait_for_timeout(2000)

            # Screenshot project detail page
            page.screenshot(path='C:/tmp/screenshots/03_project_detail.png', full_page=True)
            print("Screenshot taken: project_detail.png")

            # Look for update button
            print("Looking for update button...")
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
                page.screenshot(path='C:/tmp/screenshots/04_no_update_button.png', full_page=True)
            else:
                # Screenshot before clicking
                page.screenshot(path='C:/tmp/screenshots/05_before_update.png', full_page=True)
                print("Found update button, clicking...")
                update_button.click()

                # Wait for alert and handle it
                page.wait_for_timeout(2000)
                try:
                    page.on("dialog", lambda dialog: dialog.accept())
                except:
                    pass

                # Wait and screenshot during/after update
                page.wait_for_timeout(5000)
                page.screenshot(path='C:/tmp/screenshots/06_during_update.png', full_page=True)
                page.screenshot(path='C:/tmp/screenshots/07_after_update.png', full_page=True)

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            page.screenshot(path='C:/tmp/screenshots/error_screenshot.png', full_page=True)

        print("\nTest completed. Screenshots saved to C:/tmp/screenshots/")
        print("Press Enter to close browser...")
        input()

        browser.close()

if __name__ == '__main__':
    main()
