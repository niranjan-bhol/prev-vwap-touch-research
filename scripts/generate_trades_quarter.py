import csv
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "data" / "nse" / "csv_transformed"
OUTPUT_DIR = BASE_DIR / "data" / "backtests" / "trades_quarter"

INITIAL_CAPITAL = 1_000_000
BROKERAGE = 40.0
TAX_RATE = 0.02 / 100

START_DATE = date(2026, 6, 1)
END_DATE = date(2026, 8, 31)

def read_csv(path):
    with open(path, "r") as f:
        return list(csv.DictReader(f))

def parse_date(date_str):
    return date.fromisoformat(date_str)

def generate_trades(rows):
    trades = []
    capital = INITIAL_CAPITAL
    
    for i, row in enumerate(rows):
        if i == 0:
            continue
        
        row_date = parse_date(row["date"])
        if row_date < START_DATE or row_date > END_DATE:
            continue
        
        prev_vwap = float(rows[i - 1]["vwap"])
        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        
        band = prev_vwap * 0.001
        if abs(open_price - prev_vwap) <= band:
            trades.append({
                "date": row["date"],
                "open": f"{open_price:.2f}",
                "high": f"{high:.2f}",
                "low": f"{low:.2f}",
                "close": f"{close:.2f}",
                "prev_vwap": f"{prev_vwap:.2f}",
                "trade_type": "SKIP",
                "entry": "",
                "quantity": "",
                "target": "",
                "exit": "",
                "target_hit": "",
                "brokerage": "",
                "tax_charges": "",
                "pnl_absolute": "",
                "pnl_percent": "",
                "capital": f"{capital:.2f}",
            })
            continue
        
        if open_price < prev_vwap:
            trade_type = "LONG"
        elif open_price > prev_vwap:
            trade_type = "SHORT"
        else:
            continue
        
        entry = open_price
        quantity = int(capital / entry)
        
        if quantity == 0:
            continue
        
        target = prev_vwap
        
        if low <= prev_vwap <= high:
            exit_price = prev_vwap
        else:
            exit_price = close
        
        target_hit = exit_price == prev_vwap
        
        trade_turnover = (entry + exit_price) * quantity
        tax_charges = trade_turnover * TAX_RATE
        
        if trade_type == "LONG":
            pnl_absolute = (exit_price - entry) * quantity - (BROKERAGE + tax_charges)
        else:
            pnl_absolute = (entry - exit_price) * quantity - (BROKERAGE + tax_charges)
        
        invested = entry * quantity
        pnl_percent = (pnl_absolute / invested) * 100 if invested else 0
        
        capital += pnl_absolute
        
        trades.append({
            "date": row["date"],
            "open": f"{open_price:.2f}",
            "high": f"{high:.2f}",
            "low": f"{low:.2f}",
            "close": f"{close:.2f}",
            "prev_vwap": f"{prev_vwap:.2f}",
            "trade_type": trade_type,
            "entry": f"{entry:.2f}",
            "quantity": quantity,
            "target": f"{target:.2f}",
            "exit": f"{exit_price:.2f}",
            "target_hit": str(target_hit).lower(),
            "brokerage": f"{BROKERAGE:.2f}",
            "tax_charges": f"{tax_charges:.2f}",
            "pnl_absolute": f"{pnl_absolute:.2f}",
            "pnl_percent": f"{pnl_percent:.2f}",
            "capital": f"{capital:.2f}",
        })
    
    return trades

def save_csv(trades, path):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=trades[0].keys())
        writer.writeheader()
        writer.writerows(trades)

def main():
    csv_files = sorted(INPUT_DIR.glob("*.csv"))
    total = len(csv_files)
    width = len(str(total))
    
    print(f"Found {total} CSV files")
    relative_path = Path("/") / OUTPUT_DIR.relative_to(BASE_DIR.parent)
    print(f"Output directory: {relative_path}")
    print(f"Date range: {START_DATE} to {END_DATE}")
    print(f"\nGenerating trades ...\n")
    
    success = 0
    
    for i, csv_path in enumerate(csv_files, start=1):
        symbol = csv_path.stem
        output_path = OUTPUT_DIR / f"{symbol}.csv"
        label = f"[{i:0{width}}/{total}]  {symbol:<12}"
        
        try:
            rows = read_csv(csv_path)
            trades = generate_trades(rows)
            if not trades:
                print(f"{label}->  0 trades")
                continue
            save_csv(trades, output_path)
            active = sum(1 for t in trades if t["trade_type"] != "SKIP")
            print(f"{label}->  {active} trades")
            success += 1
        except Exception:
            print(f"{label}->  Error")
    
    print(f"\nSuccessfully generated trades for {success}/{total} symbols")

if __name__ == "__main__":
    main()
