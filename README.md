# Previous Day VWAP Touch

## Hypothesis

Stocks tend to touch their previous day's VWAP (Volume Weighted Average Price) during the current trading day. If the stock opens below the previous VWAP, it will rise to touch it (LONG). If it opens above, it will fall to touch it (SHORT).

---

## Data

- **Universe:** Nifty 500 stocks
- **Source:** NSE historical price-volume-deliverable data
- **Period:** 01 Jan 2025 – 31 Aug 2026
- **Format:** Fetched as JSON → converted to CSV → transformed to clean CSV

---

## Pipeline

```
scripts/fetch_nse_data.py            # Fetch raw JSON from NSE (90-day chunks per symbol)
scripts/json_to_csv.py               # Convert JSON → CSV (raw NSE columns)
scripts/transform_csv.py             # Rename & clean columns → csv_transformed/
scripts/generate_trades_overall.py   # Generate trades for full period (1 Jan 2025 – 31 Aug 2026)
scripts/generate_trades_quarter.py   # Generate trades for recent period (1 Jun 2026 – 31 Aug 2026)
scripts/generate_results_overall.py  # Summarise overall trades → results/summary_overall.csv
scripts/generate_results_quarter.py  # Summarise quarter trades  → results/summary_quarter.csv
```

---

## Trade Logic

### Entry

| Condition | Trade |
|-----------|-------|
| Open < Previous day VWAP | LONG at open |
| Open > Previous day VWAP | SHORT at open |

### Skip

- If `|open − prev_vwap| <= 0.1%` of prev_vwap, the day is **skipped** (open too near to target).

### Target / Exit

- **Target:** Previous day's VWAP
- **Exit:** If the VWAP level was touched during the day (`low <= prev_vwap <= high`), exit at prev_vwap. Otherwise exit at close.

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

| Period | File |
|--------|------|
| 01 Jan 2025 – 31 Aug 2026 | `results/summary_overall.csv` |
| 01 Jun 2026 – 31 Aug 2026 | `results/summary_quarter.csv` |
