# TradingView Chart Screenshot Tool

A Python script that automates taking screenshots of TradingView charts for specific tickers and timeframes using Playwright.

## Features

- Capture screenshots of any ticker available on TradingView
- Set custom timeframes (1H, 4H, 1D, etc.)
- Automatic handling of cookie/consent dialogs
- Timestamped filenames for easy organization

## Prerequisites

- Python 3.7+
- Playwright for Python

## Installation

1. Clone this repository or download the script.

2. Install the required dependencies:

```bash
pip install playwright
playwright install
```

## Usage

Run the script with default parameters (NASDAQ:AAPL on 1H timeframe):

```bash
python trading_view_screenshot.py
```

To modify the ticker or timeframe, edit the `main()` function in the script or import and use the function in your own code:

```python
import asyncio
from trading_view_screenshot import take_tradingview_screenshot

async def custom_screenshot():
    # Take a screenshot of Bitcoin on 4H timeframe
    await take_tradingview_screenshot(ticker="BINANCE:BTCUSDT", timeframe="4H")

if __name__ == "__main__":
    asyncio.run(custom_screenshot())
```

## Common Ticker Formats

- US Stocks: `NASDAQ:AAPL`, `NYSE:BA`
- Crypto: `BINANCE:BTCUSDT`, `COINBASE:ETHUSD`
- Forex: `OANDA:EURUSD`, `FX:GBPUSD`
- Indices: `INDEX:SPX`, `INDEX:DXY`

## Notes

- The script uses headless mode by default. Set `headless=False` in the `launch()` method if you want to see the browser.
- Screenshot files are saved in a `screenshots` directory by default.
- If you encounter issues with timeframe selection, TradingView's UI might have changed - you may need to update the selectors.
