#!/usr/bin/env python3
import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright

async def take_tradingview_screenshot(ticker="OANDA:EURUSD", interval="60", output_dir="screenshots", candles_to_show=40):
    """
    Takes a screenshot of a TradingView chart for a specific ticker and interval.
    
    Args:
        ticker (str): The ticker symbol to capture (e.g., "NASDAQ:AAPL", "BINANCE:BTCUSDT")
        interval (str): The timeframe interval to set (e.g., "60" for 1H, "240" for 4H, "D" for 1D)
        output_dir (str): Directory to save screenshots
        candles_to_show (int): Approximate number of candles to show in the view
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
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
            has_touch=True  # Enable touch events for pinch-to-zoom
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
                await asyncio.sleep(1)
                
                # Simulate pinch-to-zoom gesture
                print("Applying zoom to focus on recent candles...")
                
                # Try multiple zooming methods
                
                # Method 1: Use touchscreen pinch-to-zoom
                try:
                    # Start with fingers together at center
                    await page.touchscreen.tap(center_x, center_y)
                    await asyncio.sleep(0.5)
                    
                    # Perform multiple pinch-out gestures to zoom in
                    for i in range(8):  # Adjust number based on testing
                        # Simulate pinch-to-zoom gesture (spreading two fingers)
                        await page.evaluate("""() => {
                            const chartElement = document.querySelector('.chart-container') || 
                                               document.querySelector('.chart-markup-table') || 
                                               document.querySelector('.chart-gui-wrapper');
                            if (chartElement) {
                                const rect = chartElement.getBoundingClientRect();
                                const centerX = rect.left + rect.width / 2;
                                const centerY = rect.top + rect.height / 2;
                                
                                // Create touch events
                                const touchStart = new TouchEvent('touchstart', {
                                    bubbles: true,
                                    touches: [
                                        new Touch({identifier: 0, target: chartElement, clientX: centerX - 20, clientY: centerY}),
                                        new Touch({identifier: 1, target: chartElement, clientX: centerX + 20, clientY: centerY})
                                    ]
                                });
                                
                                const touchMove = new TouchEvent('touchmove', {
                                    bubbles: true,
                                    touches: [
                                        new Touch({identifier: 0, target: chartElement, clientX: centerX - 100, clientY: centerY}),
                                        new Touch({identifier: 1, target: chartElement, clientX: centerX + 100, clientY: centerY})
                                    ]
                                });
                                
                                const touchEnd = new TouchEvent('touchend', {
                                    bubbles: true,
                                    touches: []
                                });
                                
                                // Dispatch the events
                                chartElement.dispatchEvent(touchStart);
                                chartElement.dispatchEvent(touchMove);
                                chartElement.dispatchEvent(touchEnd);
                            }
                        }""")
                        await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"Pinch-to-zoom gesture failed: {e}")
                
                # Method 2: Use mousewheel zoom as backup
                try:
                    # Move mouse to chart center
                    await page.mouse.move(center_x, center_y)
                    
                    # Use mouse wheel to zoom in (negative values zoom in)
                    for i in range(10):
                        await page.mouse.wheel(0, -120)
                        await asyncio.sleep(0.3)
                except Exception as e:
                    print(f"Mouse wheel zoom failed: {e}")
                
                # Method 3: Use keyboard shortcuts as a last resort
                try:
                    await page.keyboard.down("Control")  # or Command on Mac
                    for i in range(8):
                        await page.keyboard.press("+")
                        await asyncio.sleep(0.3)
                    await page.keyboard.up("Control")
                except Exception as e:
                    print(f"Keyboard zoom failed: {e}")
        
        # Wait a moment for zoom actions to complete
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
    
    await take_tradingview_screenshot(ticker, interval, candles_to_show=40)

if __name__ == "__main__":
    asyncio.run(main()) 