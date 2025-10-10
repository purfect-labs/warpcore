#!/usr/bin/env python3
"""
Quick check for white screen console errors
"""

import asyncio
from playwright.async_api import async_playwright
import time

async def check_console_errors():
    console_errors = []
    
    def log_console(msg):
        if msg.type in ['error', 'warning']:
            error_info = f"[{msg.type.upper()}] {msg.text}"
            console_errors.append(error_info)
            print(error_info)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        page.on('console', log_console)
        page.on('pageerror', lambda err: print(f"PAGE ERROR: {err}"))
        
        try:
            print("🔍 Loading WARPCORE page...")
            await page.goto('http://localhost:8000', timeout=30000)
            
            # Wait for page to load
            await asyncio.sleep(5)
            
            # Check if content is visible
            body_content = await page.evaluate("document.body.innerText.trim()")
            
            print(f"\n📊 Results:")
            print(f"Console errors: {len(console_errors)}")
            print(f"Body content length: {len(body_content)}")
            print(f"Page appears white: {len(body_content) < 10}")
            
            if console_errors:
                print(f"\n🚨 Console errors found:")
                for error in console_errors[:20]:  # First 20 errors
                    print(f"  {error}")
            
            if len(body_content) < 10:
                print(f"\n⚪ WHITE SCREEN DETECTED!")
                print("Checking DOM elements...")
                
                # Check if any major elements exist
                elements = await page.evaluate("""
                    ({
                        body: document.body.children.length,
                        header: document.querySelector('header') ? 'found' : 'missing',
                        main: document.querySelector('main') ? 'found' : 'missing',
                        scripts: document.scripts.length,
                        stylesheets: document.styleSheets.length
                    })
                """)
                
                print(f"DOM Analysis:")
                for key, value in elements.items():
                    print(f"  {key}: {value}")
            
            print(f"\n🌐 Browser open for inspection...")
            await asyncio.sleep(30)  # Keep open for inspection
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(check_console_errors())