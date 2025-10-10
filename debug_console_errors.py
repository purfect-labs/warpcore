#!/usr/bin/env python3
"""
Debug console errors in WARPCORE UI
Captures all console errors and analyzes their sources
"""

import asyncio
from playwright.async_api import async_playwright
import json
from collections import defaultdict, Counter
import sys
import time

async def debug_console_errors():
    """Capture and analyze console errors from the WARPCORE UI"""
    
    console_messages = []
    error_count = defaultdict(int)
    error_sources = defaultdict(list)
    
    def handle_console_message(msg):
        """Handle console messages"""
        console_messages.append({
            'type': msg.type,
            'text': msg.text,
            'location': msg.location,
            'timestamp': time.time()
        })
        
        if msg.type in ['error', 'warning']:
            error_count[msg.type] += 1
            error_sources[msg.text].append(msg.location)
            
        # Print real-time for serious errors
        if msg.type == 'error':
            print(f"ERROR: {msg.text}")
            if msg.location:
                print(f"  Location: {msg.location}")
    
    async with async_playwright() as p:
        print("🔍 Starting console error analysis...")
        
        browser = await p.chromium.launch(
            headless=False,
            devtools=True,
            slow_mo=500  # Slow down for observation
        )
        
        context = await browser.new_context()
        page = await context.new_page()
        
        # Set up console message handler
        page.on('console', handle_console_message)
        
        # Also capture page errors
        page.on('pageerror', lambda error: print(f"PAGE ERROR: {error}"))
        
        try:
            print("📱 Navigating to WARPCORE UI...")
            await page.goto('http://localhost:8000', wait_until='networkidle')
            
            print("⏱️  Waiting 10 seconds to capture initial errors...")
            await asyncio.sleep(10)
            
            # Try to interact with problematic elements
            print("🖱️  Attempting to interact with UI elements...")
            
            # Try clicking license manage button
            try:
                license_button = await page.query_selector('[onclick*="showLicenseModal"]')
                if license_button:
                    print("Clicking license manage button...")
                    await license_button.click()
                    await asyncio.sleep(2)
                else:
                    print("License button not found")
            except Exception as e:
                print(f"License button click failed: {e}")
            
            # Try clicking environment buttons  
            try:
                env_buttons = await page.query_selector_all('[onclick*="switchEnvironment"]')
                if env_buttons:
                    print(f"Found {len(env_buttons)} environment buttons")
                    for i, button in enumerate(env_buttons[:2]):  # Try first 2
                        try:
                            await button.click()
                            await asyncio.sleep(1)
                        except Exception as e:
                            print(f"Environment button {i} click failed: {e}")
                else:
                    print("No environment buttons found")
            except Exception as e:
                print(f"Environment button interaction failed: {e}")
            
            print("⏱️  Waiting additional 5 seconds for error capture...")
            await asyncio.sleep(5)
            
        except Exception as e:
            print(f"Navigation or interaction error: {e}")
        
        finally:
            print("\n" + "="*60)
            print("📊 CONSOLE ERROR ANALYSIS RESULTS")
            print("="*60)
            
            print(f"Total console messages: {len(console_messages)}")
            
            for msg_type, count in error_count.items():
                print(f"{msg_type.upper()}: {count}")
            
            if error_count['error'] > 0:
                print(f"\n🚨 TOP ERROR MESSAGES:")
                error_counter = Counter([msg['text'] for msg in console_messages if msg['type'] == 'error'])
                for error_text, count in error_counter.most_common(10):
                    print(f"  ({count}x) {error_text}")
            
            if error_count['warning'] > 0:
                print(f"\n⚠️  TOP WARNING MESSAGES:")
                warning_counter = Counter([msg['text'] for msg in console_messages if msg['type'] == 'warning'])
                for warning_text, count in warning_counter.most_common(5):
                    print(f"  ({count}x) {warning_text}")
            
            # Save detailed log
            log_file = '/tmp/warpcore_console_debug.json'
            with open(log_file, 'w') as f:
                json.dump(console_messages, f, indent=2, default=str)
            print(f"\n📝 Detailed console log saved to: {log_file}")
            
            print(f"\n🌐 Keeping browser open for manual inspection...")
            print("Press Enter to close browser and exit...")
            input()
            
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_console_errors())