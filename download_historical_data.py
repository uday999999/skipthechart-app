#!/usr/bin/env python3
"""
Download real historical NSE market data for NIFTY 50 and BANK NIFTY using yfinance.
Saves data into ./data/ directory for local backtesting on localhost:8888.
"""
import os
import json
import yfinance as yf
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

TICKERS = {
    "nifty50": {
        "symbol": "^NSEI",
        "name": "NIFTY 50",
        "description": "NSE India Benchmark Index"
    },
    "banknifty": {
        "symbol": "^NSEBANK",
        "name": "BANK NIFTY",
        "description": "NSE Banking Sector Index"
    }
}

def download_data():
    summary = {}
    for key, info in TICKERS.items():
        symbol = info["symbol"]
        print(f"Downloading historical data for {info['name']} ({symbol})...")
        
        # Download 1 Year of daily candles
        df = yf.download(symbol, period="1y", interval="1d", progress=False)
        
        if df.empty:
            print(f"Failed to download data for {symbol}")
            continue

        # Flatten multi-index columns if present in newer pandas/yfinance
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]

        # Clean NaN values
        df = df.dropna()

        records = []
        for idx, row in df.iterrows():
            date_str = idx.strftime("%Y-%m-%d") if hasattr(idx, 'strftime') else str(idx)[:10]
            records.append({
                "date": date_str,
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row.get("Volume", 0))
            })

        # Save as JSON
        json_path = os.path.join(DATA_DIR, f"{key}_1y.json")
        with open(json_path, "w") as f:
            json.dump({
                "symbol": symbol,
                "name": info["name"],
                "total_candles": len(records),
                "start_date": records[0]["date"],
                "end_date": records[-1]["date"],
                "candles": records
            }, f, indent=2)

        # Save as CSV
        csv_path = os.path.join(DATA_DIR, f"{key}_1y.csv")
        df.to_csv(csv_path)

        summary[key] = {
            "name": info["name"],
            "total_candles": len(records),
            "start_date": records[0]["date"],
            "end_date": records[-1]["date"],
            "latest_close": records[-1]["close"],
            "file": json_path
        }
        print(f"Saved {len(records)} records for {info['name']} to {json_path}")

    # Write metadata manifest
    manifest_path = os.path.join(DATA_DIR, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(summary, f, indent=2)

    print("Historical data download complete!")
    return summary

if __name__ == "__main__":
    download_data()
