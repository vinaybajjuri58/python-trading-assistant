#!/usr/bin/env python3
import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright

async def take_tradingview_screenshot(ticker="OANDA:EURUSD", timeframe="1H", output_dir="screenshots",interval=60):
    """
    Takes a screenshot of a TradingView chart for a specific ticker and timeframe.
    
    Args:
        ticker (str): The ticker symbol to capture (e.g., "NASDAQ:AAPL", "BINANCE:BTCUSDT")
        timeframe (str): The timeframe to set (e.g., "1H", "4H", "1D")
        output_dir (str): Directory to save screenshots
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Format current timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/{ticker.replace(':', '_')}_{timeframe}_{timestamp}.png"
    
    # Launch browser
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
        )
        
        # Create a new page
        page = await context.new_page()
        
        # Navigate to TradingView chart with the specified ticker
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
        
        # Set timeframe
        print(f"Setting timeframe to {timeframe}...")
        try:
            # Click on the current timeframe button
            await page.click("button.menuButton-Hj6U1eUe.button-Hj6U1eUe.apply-common-tooltip.common-tooltip-vertical", timeout=10000)
            
            # Wait for the dropdown to appear
            await page.wait_for_selector("div.menuBoxContainer-Hj6U1eUe", timeout=10000)
            
            # Click on the specified timeframe
            await page.click(f"div[data-value='{timeframe}']", timeout=10000)
            
            # Wait for the chart to update
            await asyncio.sleep(3)
        except Exception as e:
            print(f"Error setting timeframe: {e}")
            # Try alternative method
            try:
                # Some versions of TradingView have different UI elements
                await page.click(f"div[data-role='button']:has-text('{timeframe}')")
                await asyncio.sleep(3)
            except:
                print("Could not set timeframe, using default")
        
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
    timeframe = "1H"
    interval = "60"
    await take_tradingview_screenshot(ticker, timeframe, interval)

if __name__ == "__main__":
    asyncio.run(main()) 