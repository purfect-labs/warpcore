#!/usr/bin/env python3
"""
Quick test to verify WARPCORE UI is working after fixes
"""

import asyncio
from playwright.async_api import async_playwright
import time

async def test_ui_functionality():
    """Test basic UI functionality after console error fixes"""
    
    console_messages = []
    error_count = 0
    
    def handle_console_message(msg):
        console_messages.append(msg.text)
        if msg.type == 'error':
            global error_count
            error_count += 1
            print(f"ERROR: {msg.text}")
    
    async with async_playwright() as p:
        print("🧪 Testing WARPCORE UI functionality after fixes...")
        
        browser = await p.chromium.launch(headless=False, devtools=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        page.on('console', handle_console_message)
        
        try:
            print("📱 Loading WARPCORE page...")
            await page.goto('http://localhost:8000', wait_until='networkidle', timeout=10000)
            
            # Wait for page to load
            await asyncio.sleep(3)
            
            # Check if content is visible
            body_content = await page.evaluate("document.body.innerText")
            visible_text_length = len(body_content.strip())
            
            print(f"\n📊 Results after fixes:")
            print(f"✅ Page loaded successfully")
            print(f"✅ Body content length: {visible_text_length} characters")
            print(f"✅ Console errors in first 3 seconds: {error_count}")
            
            if visible_text_length > 100:
                print("✅ Page is NOT white screen - content is visible!")
            else:
                print("⚠️ Page might still be showing white screen")
            
            # Test clicking buttons
            print("\n🖱️ Testing button functionality...")
            
            try:
                # Test license manage button
                license_button = await page.query_selector('[onclick*="showLicenseModal"]')
                if license_button:
                    print("✅ Found license manage button")
                    await license_button.click()
                    await asyncio.sleep(1)
                    print("✅ License button click successful")
                else:
                    print("⚠️ License button not found")
                
                # Test environment buttons
                env_buttons = await page.query_selector_all('[onclick*="switchEnvironment"]')
                if env_buttons:
                    print(f"✅ Found {len(env_buttons)} environment buttons")
                    if len(env_buttons) > 0:
                        await env_buttons[0].click()
                        await asyncio.sleep(1)
                        print("✅ Environment button click successful")
                else:
                    print("⚠️ No environment buttons found")
                
                # Test profile dropdown
                profile_button = await page.query_selector('[onclick*="toggleProfileDropdown"]')
                if profile_button:
                    print("✅ Found profile dropdown button")
                    await profile_button.click()
                    await asyncio.sleep(1)
                    print("✅ Profile button click successful")
                else:
                    print("⚠️ Profile button not found")
                    
            except Exception as e:
                print(f"⚠️ Button interaction error: {e}")
            
            # Wait a bit more and check for runaway errors
            print("\n⏱️ Monitoring for runaway console errors...")
            initial_error_count = error_count
            await asyncio.sleep(5)
            final_error_count = error_count
            
            error_increase = final_error_count - initial_error_count
            print(f"Console errors in last 5 seconds: {error_increase}")
            
            if error_increase < 10:
                print("✅ No runaway console error loop detected!")
            else:
                print(f"⚠️ Still {error_increase} errors in 5 seconds - may need more fixes")
            
            print(f"\n🎯 SUMMARY:")
            print(f"✅ UI is {'FUNCTIONAL' if visible_text_length > 100 and error_increase < 50 else 'NEEDS MORE WORK'}")
            print(f"✅ Total console errors: {final_error_count}")
            print(f"✅ White screen issue: {'FIXED' if visible_text_length > 100 else 'STILL PRESENT'}")
            
            await asyncio.sleep(10)  # Keep browser open for inspection
            
        except Exception as e:
            print(f"Test error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_ui_functionality())