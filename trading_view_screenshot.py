#!/usr/bin/env python3
import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright

async def take_tradingview_screenshot(ticker="OANDA:EURUSD", interval="60", output_dir="screenshots", 
                                      candles_to_show=40, zoom_method="both", debug_screenshots=False,
                                      zoom_intensity=1.5):
    """
    Takes a screenshot of a TradingView chart for a specific ticker and interval.
    
    Args:
        ticker (str): The ticker symbol to capture (e.g., "NASDAQ:AAPL", "BINANCE:BTCUSDT")
        interval (str): The timeframe interval to set (e.g., "60" for 1H, "240" for 4H, "D" for 1D)
        output_dir (str): Directory to save screenshots
        candles_to_show (int): Approximate number of candles to show in the view
        zoom_method (str): Specify which zoom method to use - "wheel", "keyboard", or "both"
        debug_screenshots (bool): Take screenshots after each zoom method to see which one works
        zoom_intensity (float): Multiplier for zoom intensity (1.0 = default, 2.0 = double zoom)
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Format current timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/{ticker.replace(':', '_')}_{interval}_{timestamp}.png"
    
    # Calculate zoom iterations based on intensity
    wheel_iterations = int(15 * zoom_intensity)  # Increased from 10 to 15 as baseline
    keyboard_iterations = int(12 * zoom_intensity)  # Increased from 8 to 12 as baseline
    wheel_delta = -150  # Increased from -120 for stronger zoom per iteration
    
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
        
        # Close any dialogs that might be present
        try:
            await page.click("button[data-name='close-button']", timeout=5000)
            print("Closed cookie/notification dialog")
        except:
            print("No dialog found or already closed")
        
        # Wait for chart to fully render
        await asyncio.sleep(5)
        
        # Find the chart area
        chart_area = await page.query_selector(".chart-container")
        if not chart_area:
            chart_area = await page.query_selector(".chart-markup-table")
        if not chart_area:
            chart_area = await page.query_selector(".chart-gui-wrapper")
            
        if chart_area:
            # Get the bounding box of the chart area
            chart_box = await chart_area.bounding_box()
            if chart_box:
                center_x = chart_box["x"] + chart_box["width"] / 2
                center_y = chart_box["y"] + chart_box["height"] / 2
                right_x = chart_box["x"] + chart_box["width"] * 0.9  # Right area of chart
                
                # First move to the end of the chart to ensure we're seeing recent candles
                # Click near the right edge of the chart
                await page.mouse.move(right_x, center_y)
                await page.mouse.click(right_x, center_y)
                await asyncio.sleep(1)
                
                # Press End key to ensure we're at the latest candles
                await page.keyboard.press("End")
                await asyncio.sleep(1.5)
                
                # Take a pre-zoom screenshot if in debug mode
                if debug_screenshots:
                    await page.screenshot(path=f"{output_dir}/{ticker.replace(':', '_')}_{interval}_{timestamp}_before_zoom.png")
                    print(f"Saved pre-zoom screenshot for comparison")
                
                print(f"Applying zoom to focus on recent candles (intensity: {zoom_intensity}x)...")
                
                # Method 1: Use mousewheel zoom
                if zoom_method in ["wheel", "both"]:
                    print(f"Trying MOUSE WHEEL method with {wheel_iterations} iterations...")
                    try:
                        # Move mouse to chart center
                        await page.mouse.move(center_x, center_y)
                        
                        # Use mouse wheel to zoom in (negative values zoom in)
                        for i in range(wheel_iterations):
                            await page.mouse.wheel(0, wheel_delta)
                            print(f"  Wheel zoom {i+1}/{wheel_iterations} applied")
                            
                            # Progressively increase delay between zooms to let chart respond
                            delay = 0.3 + (i / wheel_iterations * 0.2)  # 0.3 to 0.5 second
                            await asyncio.sleep(delay)
                            
                            # Every few iterations, click to ensure focus remains on chart
                            if i % 5 == 4:
                                await page.mouse.click(center_x, center_y)
                                await asyncio.sleep(0.5)
                                
                        print("✓ MOUSE WHEEL method completed successfully")
                        
                        # Take interim screenshot if in debug mode
                        if debug_screenshots:
                            await page.screenshot(path=f"{output_dir}/{ticker.replace(':', '_')}_{interval}_{timestamp}_after_wheel.png")
                            print(f"Saved post-wheel screenshot")
                    except Exception as e:
                        print(f"✗ MOUSE WHEEL method failed: {e}")
                
                # Method 2: Use keyboard shortcuts
                if zoom_method in ["keyboard", "both"]:
                    print(f"Trying KEYBOARD SHORTCUT method with {keyboard_iterations} iterations...")
                    try:
                        # Click to ensure chart has focus before keyboard shortcuts
                        await page.mouse.click(center_x, center_y)
                        await asyncio.sleep(0.5)
                        
                        await page.keyboard.down("Control")  # or Command on Mac
                        for i in range(keyboard_iterations):
                            await page.keyboard.press("+")
                            print(f"  Keyboard zoom {i+1}/{keyboard_iterations} applied")
                            
                            # Progressively increase delay between zooms
                            delay = 0.3 + (i / keyboard_iterations * 0.3)  # 0.3 to 0.6 second
                            await asyncio.sleep(delay)
                            
                        await page.keyboard.up("Control")
                        print("✓ KEYBOARD SHORTCUT method completed successfully")
                        
                        # Take interim screenshot if in debug mode
                        if debug_screenshots:
                            await page.screenshot(path=f"{output_dir}/{ticker.replace(':', '_')}_{interval}_{timestamp}_after_keyboard.png")
                            print(f"Saved post-keyboard screenshot")
                    except Exception as e:
                        print(f"✗ KEYBOARD SHORTCUT method failed: {e}")
        
        # Wait a moment for zoom actions to complete
        await asyncio.sleep(4)
        
        # Take screenshot
        print(f"Taking final screenshot and saving to {filename}...")
        await page.screenshot(path=filename)
        
        # Close browser
        await browser.close()
        
        print(f"Screenshot saved: {filename}")
        return filename

async def main():
    # You can modify these parameters as needed
    ticker = "OANDA:EURUSD"
    interval = "60"  # 60 = 1 hour, 240 = 4 hours, D = 1 day
    
    # Choose which zoom method to use:
    # zoom_method options: "wheel", "keyboard", or "both"
    await take_tradingview_screenshot(
        ticker=ticker, 
        interval=interval, 
        candles_to_show=40,
        zoom_method="both",  # Use both methods for best results
        debug_screenshots=False,  # Set to True to get before/after screenshots
        zoom_intensity=1.5  # Adjust this value to increase/decrease zoom (1.0 = default, 2.0 = double)
    )

if __name__ == "__main__":
    asyncio.run(main()) 