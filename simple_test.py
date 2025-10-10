#!/usr/bin/env python3
"""
Simple test to check console errors
"""

import asyncio
from playwright.async_api import async_playwright

async def simple_test():
    errors = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Collect console messages
        page.on('console', lambda msg: errors.append(msg.text) if msg.type == 'error' else None)
        
        try:
            await page.goto('http://localhost:8000', timeout=5000)
            await asyncio.sleep(3)
            
            print(f"Errors in 3 seconds: {len(errors)}")
            if len(errors) < 10:
                print("✅ Console errors are under control!")
                
                # Check if page content loaded
                content = await page.evaluate("document.body.innerText.length")
                print(f"Body content length: {content}")
                
                if content > 100:
                    print("✅ Page content is visible - white screen fixed!")
                else:
                    print("⚠️ Page might still be white")
                    
            else:
                print("⚠️ Still too many console errors")
                for i, error in enumerate(errors[:10]):
                    print(f"  {i+1}. {error}")
                    
        except Exception as e:
            print(f"Test failed: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(simple_test())