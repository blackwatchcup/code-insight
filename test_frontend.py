from playwright.sync_api import sync_playwright
import time
import random

# Generate unique username for testing
unique_suffix = str(random.randint(1000, 9999))
TEST_USERNAME = f"testuser{unique_suffix}"
TEST_EMAIL = f"test{unique_suffix}@example.com"
TEST_PASSWORD = "password123"

print(f"Testing with user: {TEST_USERNAME}")
print(f"Email: {TEST_EMAIL}")

def test_full_flow():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            # Step 1: Go to login page
            print("\n=== Step 1: Navigating to login page ===")
            page.goto('http://localhost:5175/login')
            page.wait_for_load_state('networkidle')
            
            # Take screenshot of login page
            page.screenshot(path='login_page.png', full_page=True)
            print("✓ Login page loaded successfully")
            
            # Step 2: Switch to register mode
            print("\n=== Step 2: Switching to register mode ===")
            register_tab = page.locator('button:has-text("注册")')
            register_tab.wait_for()
            register_tab.click()
            page.wait_for_timeout(500)
            print("✓ Switched to register mode")
            
            # Step 3: Fill register form
            print("\n=== Step 3: Filling register form ===")
            page.locator('input[placeholder="输入用户名"]').fill(TEST_USERNAME)
            page.locator('input[placeholder="your@email.com"]').fill(TEST_EMAIL)
            page.locator('input[placeholder="输入密码"]').fill(TEST_PASSWORD)
            print("✓ Filled register form")
            
            # Step 4: Submit register form
            print("\n=== Step 4: Submitting register form ===")
            register_button = page.locator('button:has-text("注册")').last()
            register_button.wait_for()
            register_button.click()
            
            # Wait for navigation to projects page
            page.wait_for_load_state('networkidle')
            
            # Check if we're on projects page
            current_url = page.url
            print(f"Current URL after register: {current_url}")
            
            if '/login' in current_url:
                # Check for error message
                error_message = page.locator('.bg-red-50').first()
                if error_message.is_visible():
                    error_text = error_message.inner_text()
                    print(f"⚠️  Registration failed with error: {error_text}")
                else:
                    print("⚠️  Registration failed without error message")
            else:
                print("✓ Registration successful, navigated to projects page")
                
                # Take screenshot of projects page
                page.screenshot(path='projects_page.png', full_page=True)
                
                # Step 5: Test navbar and sidebar
                print("\n=== Step 5: Testing navbar and sidebar ===")
                
                # Check if navbar is visible
                navbar = page.locator('.flex-1 overflow-y-auto').first()
                if navbar.is_visible():
                    print("✓ Navbar is visible")
                else:
                    print("⚠️  Navbar is not visible")
                
                # Check if sidebar is visible
                sidebar = page.locator('.flex-1 overflow-hidden').first()
                if sidebar.is_visible():
                    print("✓ Sidebar is visible")
                else:
                    print("⚠️  Sidebar is not visible")
                
                # Step 6: Test logout
                print("\n=== Step 6: Testing logout ===")
                
                # Find logout button (usually in user dropdown)
                # First, check if there's a user menu button
                user_menu = page.locator('button').filter(has_text=TEST_USERNAME)
                if user_menu.is_visible():
                    user_menu.click()
                    page.wait_for_timeout(500)
                    
                    logout_button = page.locator('button:has-text("退出")')
                    if logout_button.is_visible():
                        logout_button.click()
                        page.wait_for_load_state('networkidle')
                        
                        if '/login' in page.url:
                            print("✓ Logout successful, returned to login page")
                        else:
                            print("⚠️  Logout failed, not returned to login page")
                    else:
                        print("⚠️  Logout button not found")
                else:
                    print("⚠️  User menu button not found")
                    
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
            # Take screenshot on failure
            page.screenshot(path='failure.png', full_page=True)
        finally:
            # Close browser
            browser.close()
            print("\n=== Test completed ===")

if __name__ == "__main__":
    test_full_flow()