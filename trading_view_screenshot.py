#!/usr/bin/env python3
import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright

async def take_tradingview_screenshot(ticker="OANDA:EURUSD", interval="60", output_dir="screenshots"):
    """
    Takes a screenshot of a TradingView chart for a specific ticker and interval.
    
    Args:
        ticker (str): The ticker symbol to capture (e.g., "NASDAQ:AAPL", "BINANCE:BTCUSDT")
        interval (str): The timeframe interval to set (e.g., "60" for 1H, "240" for 4H, "D" for 1D)
        output_dir (str): Directory to save screenshots
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Format current timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/{ticker.replace(':', '_')}_{interval}_{timestamp}.png"
    
    # Launch browser
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
        )
        
        # Create a new page
        page = await context.new_page()
        
        # Navigate to TradingView chart with the specified ticker and interval
        encoded_ticker = ticker.replace(":", "%3A")
        url = f"https://www.tradingview.com/chart/?symbol={encoded_ticker}&interval={interval}"
        
        print(f"Navigating to {url}")
        await page.goto(url, wait_until="networkidle")
        
        # Wait for chart to load
        print("Waiting for chart to load...")
        await page.wait_for_selector(".chart-container", timeout=60000)
        
        # Handle possible cookie consent dialog
        try:
            await page.click("button[data-name='close-button']", timeout=5000)
            print("Closed cookie dialog")
        except:
            print("No cookie dialog found or already closed")
        
        # Wait for chart to fully render
        await asyncio.sleep(3)
        
        # Take screenshot
        print(f"Taking screenshot and saving to {filename}...")
        await page.screenshot(path=filename)
        
        # Close browser
        await browser.close()
        
        print(f"Screenshot saved: {filename}")
        return filename

async def main():
    # You can modify these parameters as needed
    ticker = "OANDA:EURUSD"
    interval = "60"  # 60 = 1 hour, 240 = 4 hours, D = 1 day
    
    await take_tradingview_screenshot(ticker, interval)

if __name__ == "__main__":
    asyncio.run(main()) 