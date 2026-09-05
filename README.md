# Previous Day VWAP Touch

## Hypothesis

Stocks tend to touch their previous day's VWAP (Volume Weighted Average Price) during the current trading day. If the stock opens below the previous VWAP, it will rise to touch it (LONG). If it opens above, it will fall to touch it (SHORT).

---

## Data

- **Universe:** Nifty 500 stocks
- **VWAP source:** NSE historical price-volume-deliverable data (daily)
- **OHLC source:** Zerodha Kite historical API (1-minute candles), used for entry/exit prices and day high/low
- **Period:** 01 Jan 2025 – 31 Aug 2026
- **Format:** Fetched as JSON → converted to CSV → transformed/filtered to clean CSV

---

## Pipeline

```
# Auth & symbol setup
scripts/fetch_access_token.py         # Log in to Zerodha Kite → data/auth/access_token.txt
scripts/fetch_instruments.py          # Download Kite instruments list → data/instruments/instruments.csv
scripts/generate_symbols.py           # Map Nifty 500 symbols → instrument tokens → data/symbols/symbols.json

# NSE data → previous day VWAP
scripts/fetch_nse_data.py             # Fetch raw JSON from NSE (90-day chunks per symbol)
scripts/json_to_csv_nse.py            # Convert JSON → CSV (+ corporate actions → csv_ca/)
scripts/transform_csv.py              # Rename & clean columns → csv_transformed/
scripts/extract_vwap.py               # Carry forward each day's VWAP as next day's prev_vwap → nse/vwap/

# Zerodha data → intraday OHLC
scripts/fetch_historical_data.py --interval minute   # Fetch 1-minute candles from Kite → historical/json/
scripts/json_to_csv_zerodha.py        # Convert JSON → CSV → historical/csv/
scripts/filter_data.py                # Extract 09:15 & 15:18 snapshots + day high/low → historical/filtered/

# Trades & results
scripts/generate_trades.py            # Combine filtered OHLC + prev_vwap → backtests/trades/<symbol>.csv
scripts/generate_results.py           # Summarise trades by month/quarter/year → results/*.csv
```

---

## Trade Logic

### Entry

| Condition | Trade |
|-----------|-------|
| 09:15 open < Previous day VWAP | LONG at 09:15 open |
| 09:15 open > Previous day VWAP | SHORT at 09:15 open |

- Entry price is the open of the 09:15 1-minute candle (falls back to the next available candle if 09:15 is missing).

### Skip

- If `|open − prev_vwap| <= 0.1%` of prev_vwap, the day is **skipped** (open too near to target).

### Target / Exit

- **Target:** Previous day's VWAP
- **Exit:** If the VWAP level was touched between 09:15 and 15:18 (`day_low <= prev_vwap <= day_high`), exit at prev_vwap. Otherwise exit at the 15:18 close (falls back to the previous available candle if 15:18 is missing).

### Position Sizing

- Full capital deployed each trade: `quantity = floor(capital / entry_price)`

---

## Costs

| Cost | Value |
|------|-------|
| Initial capital | ₹10,00,000 per symbol |
| Brokerage | ₹40 flat per trade (buy & sell combined) |
| Tax & charges | 0.02% of total trade turnover |

`turnover = (entry_price + exit_price) × quantity`

`net P&L = gross P&L − brokerage − tax_charges`

---

## Results

| Period | Range | File |
|--------|-------|------|
| Year | 01 Sep 2025 – 31 Aug 2026 | `results/year.csv` |
| Quarter | 01 Jun 2026 – 31 Aug 2026 | `results/quarter.csv` |
| Month | 01 Aug 2026 – 31 Aug 2026 | `results/month.csv` |
