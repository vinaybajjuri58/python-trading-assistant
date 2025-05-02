#!/usr/bin/env python3
import asyncio
import os
import base64
import json
import requests
from datetime import datetime
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

# Set your OpenAI API key here or use environment variable
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")  # Replace with your API key if not using env var

async def take_tradingview_screenshot(ticker="OANDA:EURUSD", interval="60", output_dir="screenshots", 
                                      candles_to_show=40, debug_screenshots=False,
                                      zoom_intensity=1.5, filename_suffix=""):
    """
    Takes a screenshot of a TradingView chart for a specific ticker and interval.
    
    Args:
        ticker (str): The ticker symbol to capture (e.g., "NASDAQ:AAPL", "BINANCE:BTCUSDT")
        interval (str): The timeframe interval to set (e.g., "60" for 1H, "240" for 4H, "D" for 1D)
        output_dir (str): Directory to save screenshots
        candles_to_show (int): Approximate number of candles to show in the view
        debug_screenshots (bool): Take screenshots after each zoom method to see which one works
        zoom_intensity (float): Multiplier for zoom intensity (1.0 = default, 2.0 = double zoom)
        filename_suffix (str): Optional suffix to add to the filename
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Format current timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if filename_suffix:
        filename = f"{output_dir}/{ticker.replace(':', '_')}_{interval}_{timestamp}_{filename_suffix}.png"
    else:
        filename = f"{output_dir}/{ticker.replace(':', '_')}_{interval}_{timestamp}.png"
    
    # Calculate zoom iterations based on intensity
    wheel_iterations = int(12 * zoom_intensity)  # Increased from 10 to 15 as baseline
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
                
                print(f"Applying mouse wheel zoom to focus on recent candles (intensity: {zoom_intensity}x)...")
                
                # Use mousewheel zoom
                print(f"Applying mouse wheel zoom with {wheel_iterations} iterations...")
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
                            
                    print("✓ Mouse wheel zoom completed successfully")
                    
                    # Take interim screenshot if in debug mode
                    if debug_screenshots:
                        await page.screenshot(path=f"{output_dir}/{ticker.replace(':', '_')}_{interval}_{timestamp}_after_wheel.png")
                        print(f"Saved post-wheel screenshot")
                except Exception as e:
                    print(f"✗ Mouse wheel zoom failed: {e}")
        
        # Wait a moment for zoom actions to complete
        await asyncio.sleep(4)
        
        # Take screenshot
        print(f"Taking final screenshot and saving to {filename}...")
        await page.screenshot(path=filename)
        
        # Close browser
        await browser.close()
        
        print(f"Screenshot saved: {filename}")
        return filename

def analyze_chart_with_openai(image_path, timeframe):
    """
    Send the chart image to OpenAI API for analysis, specifically checking for FVG (Fair Value Gap).
    
    Args:
        image_path (str): Path to the screenshot image
        timeframe (str): Timeframe of the chart (e.g., "1H", "4H")
        
    Returns:
        dict: The API response containing the analysis
    """
    if not OPENAI_API_KEY:
        print("Warning: OpenAI API key not found. Set OPENAI_API_KEY environment variable or update the script.")
        return {"error": "API key not set"}
    
    # Read and encode the image
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
    
    # Set up the API request
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    
    # Prepare the prompt for FVG analysis
    prompt = f"""
    Analyze this TradingView chart ({timeframe} timeframe) and identify if there are any Fair Value Gaps (FVGs) visible.
    Then determine if the recent price action has tapped or filled any FVG.
    
    A Fair Value Gap (FVG) is formed when the low of a candle is higher than the high of the candle two positions before it (bullish FVG),
    or when the high of a candle is lower than the low of the candle two positions before it (bearish FVG).
    
    Please provide:
    1. Whether you can identify any FVGs on the chart
    2. If there are FVGs, whether the recent price has tapped into or filled any of them
    3. The direction of the FVG (bullish or bearish)
    4. The approximate price level of the identified FVG
    """
    
    # Build the API request payload
    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{encoded_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 500
    }
    
    # Make the API request
    try:
        print(f"Sending chart to OpenAI for FVG analysis ({timeframe} timeframe)...")
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response_data = response.json()
        
        if "error" in response_data:
            print(f"API Error: {response_data['error']['message']}")
            return response_data
        
        # Extract and print the analysis
        analysis = response_data["choices"][0]["message"]["content"]
        print(f"\n=== FVG ANALYSIS FOR {timeframe} TIMEFRAME ===")
        print(analysis)
        print("=" * 50)
        
        return {"timeframe": timeframe, "analysis": analysis, "full_response": response_data}
    
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return {"error": str(e)}

async def main():
    # Base parameters
    ticker = "OANDA:EURUSD"
    zoom_intensity = 1.5  # Adjust this value to increase/decrease zoom
    
    # Array of intervals to capture
    intervals = ["60", "240"]
    interval_names = {
        "60": "1H",
        "240": "4H",
    }
    
    # Store screenshots and analyses
    screenshot_paths = []
    analysis_results = []
    
    # Capture screenshots for each interval
    for interval in intervals:
        print(f"\n=== TAKING SCREENSHOT FOR {interval_names[interval]} TIMEFRAME ===")
        screenshot_path = await take_tradingview_screenshot(
            ticker=ticker, 
            interval=interval, 
            zoom_intensity=zoom_intensity,
            filename_suffix=interval_names[interval]
        )
        screenshot_paths.append((screenshot_path, interval_names[interval]))
    
    print("\nAll screenshots have been saved.")
    
    # Analyze each screenshot with OpenAI
    if OPENAI_API_KEY:
        print("\n=== ANALYZING SCREENSHOTS FOR FVG PATTERNS ===")
        for path, timeframe in screenshot_paths:
            # Analyze one screenshot at a time
            result = analyze_chart_with_openai(path, timeframe)
            analysis_results.append(result)
            
            # Wait a bit between API calls to avoid rate limits
            await asyncio.sleep(2)
        
        # Save the analysis results to a JSON file
        results_file = f"screenshots/fvg_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, "w") as f:
            json.dump(analysis_results, f, indent=2)
        print(f"\nAnalysis results saved to {results_file}")
    else:
        print("\nSkipping OpenAI analysis because API key is not set.")
        print("Set your OpenAI API key in the script or as an environment variable (OPENAI_API_KEY).")

if __name__ == "__main__":
    asyncio.run(main()) 