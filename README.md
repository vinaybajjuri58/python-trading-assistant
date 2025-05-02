# TradingView Chart Screenshot Tool

A Python script that automates taking screenshots of TradingView charts for specific tickers and intervals using Playwright.

## Features

- Capture screenshots of any ticker available on TradingView
- Set custom intervals (60 for 1H, 240 for 4H, D for 1D, etc.)
- Automatic handling of cookie/consent dialogs
- Timestamped filenames for easy organization

## Prerequisites

- Python 3.7+
- Playwright for Python

## Installation

1. Clone this repository or download the script.

2. Install the required dependencies:

```bash
pip install -r requirements.txt
playwright install
```

## Usage

Run the script with default parameters (OANDA:EURUSD on 1H timeframe):

```bash
python trading_view_screenshot.py
```

To modify the ticker or interval, edit the `main()` function in the script or import and use the function in your own code:

```python
import asyncio
from trading_view_screenshot import take_tradingview_screenshot

async def custom_screenshot():
    # Take a screenshot of Bitcoin on 4H timeframe
    await take_tradingview_screenshot(ticker="BINANCE:BTCUSDT", interval="240")

if __name__ == "__main__":
    asyncio.run(custom_screenshot())
```

## Common Ticker Formats

- US Stocks: `NASDAQ:AAPL`, `NYSE:BA`
- Crypto: `BINANCE:BTCUSDT`, `COINBASE:ETHUSD`
- Forex: `OANDA:EURUSD`, `FX:GBPUSD`
- Indices: `INDEX:SPX`, `INDEX:DXY`

## Common Interval Values

- 1 minute: `1`
- 5 minutes: `5`
- 15 minutes: `15`
- 1 hour: `60`
- 4 hours: `240`
- 1 day: `D`
- 1 week: `W`
- 1 month: `M`

## Notes

- The script uses headless mode by default. Set `headless=False` in the `launch()` method if you want to see the browser.
- Screenshot files are saved in a `screenshots` directory by default.
- The script uses TradingView's URL parameters to set the interval directly, avoiding UI interaction issues.
