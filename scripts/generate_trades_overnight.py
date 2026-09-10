import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FILTERED_DIR = BASE_DIR / "data" / "historical" / "filtered"
VWAP_DIR = BASE_DIR / "data" / "nse" / "vwap"
OUTPUT_DIR = BASE_DIR / "data" / "backtests" / "trades" / "overnight"

INITIAL_CAPITAL = 1_000_000
DP_CHARGE = 15.93
TAX_RATE = 0.11 / 100

def read_csv(path):
    with open(path, "r") as f:
        return list(csv.DictReader(f))

def generate_trades(filtered_rows, vwap_rows):
    vwap_by_date = {row["date"]: row for row in vwap_rows}
    trades = []
    capital = INITIAL_CAPITAL
    
    for i in range(len(filtered_rows) - 1):
        day1 = filtered_rows[i]
        day2 = filtered_rows[i + 1]
        
        vwap_row = vwap_by_date.get(day1["date"])
        if not vwap_row:
            continue
        
        vwap_str = (vwap_row.get("vwap") or "").strip()
        if not vwap_str:
            continue
        
        vwap = float(vwap_str)
        close_day1 = float(day1["1528_close"])
        high_day2 = float(day2["day_high"])
        low_day2 = float(day2["day_low"])
        close_day2 = float(day2["1528_close"])
        
        entry = close_day1
        quantity = int(capital / entry)
        
        if quantity == 0:
            continue
        
        target = vwap
        
        if low_day2 <= target <= high_day2:
            exit = target
        else:
            exit = close_day2
        
        target_hit = exit == target
        
        trade_turnover = (entry + exit) * quantity
        tax_charges = trade_turnover * TAX_RATE
        
        pnl_absolute = (exit - entry) * quantity - (DP_CHARGE + tax_charges)
        
        invested = entry * quantity
        pnl_percent = (pnl_absolute / invested) * 100 if invested else 0
        
        capital += pnl_absolute
        
        trades.append({
            "date": day1["date"],
            "close_day1": f"{close_day1:.2f}",
            "high_day2": f"{high_day2:.2f}",
            "low_day2": f"{low_day2:.2f}",
            "close_day2": f"{close_day2:.2f}",
            "vwap": f"{vwap:.2f}",
            "entry": f"{entry:.2f}",
            "quantity": quantity,
            "target": f"{target:.2f}",
            "exit": f"{exit:.2f}",
            "target_hit": str(target_hit).lower(),
            "dp_charge": f"{DP_CHARGE:.2f}",
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
    csv_files = sorted(FILTERED_DIR.glob("*.csv"))
    total = len(csv_files)
    width = len(str(total))
    
    print(f"Found {total} CSV files")
    relative_path = Path("/") / OUTPUT_DIR.relative_to(BASE_DIR.parent)
    print(f"Output directory: {relative_path}")
    print(f"\nGenerating trades ...\n")
    
    success = 0
    
    for i, filtered_path in enumerate(csv_files, start=1):
        symbol = filtered_path.stem
        vwap_path = VWAP_DIR / f"{symbol}.csv"
        output_path = OUTPUT_DIR / f"{symbol}.csv"
        label = f"[{i:0{width}}/{total}]  {symbol:<12}"
        
        try:
            filtered_rows = read_csv(filtered_path)
            vwap_rows = read_csv(vwap_path)
            trades = generate_trades(filtered_rows, vwap_rows)
            save_csv(trades, output_path)
            print(f"{label}->  {len(trades)} trades")
            success += 1
        except Exception:
            print(f"{label}->  Error")
    
    print(f"\nSuccessfully generated trades for {success}/{total} symbols")

if __name__ == "__main__":
    main()
