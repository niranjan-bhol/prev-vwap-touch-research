import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FILTERED_DIR = BASE_DIR / "data" / "historical" / "filtered"
VWAP_DIR = BASE_DIR / "data" / "nse" / "vwap"
OUTPUT_DIR = BASE_DIR / "data" / "backtests" / "trades" / "intraday"

SKIP_BAND_PERCENT = 0.001  # skip if |open - prev_vwap| <= 0.1% of prev_vwap

def read_csv(path):
    with open(path, "r") as f:
        return list(csv.DictReader(f))

def generate_trades(filtered_rows, vwap_rows):
    vwap_by_date = {row["date"]: row for row in vwap_rows}
    trades = []
    
    for row in filtered_rows:
        vwap_row = vwap_by_date.get(row["date"])
        if not vwap_row:
            continue
        
        prev_vwap_str = (vwap_row.get("prev_vwap") or "").strip()
        if not prev_vwap_str:
            continue
        
        prev_vwap = float(prev_vwap_str)
        open = float(row["0915_open"])
        high = float(row["session_high"])
        low = float(row["session_low"])
        close = float(row["1518_close"])
        
        band = prev_vwap * SKIP_BAND_PERCENT
        if abs(open - prev_vwap) <= band:
            trades.append({
                "date": row["date"],
                "open": f"{open:.2f}",
                "high": f"{high:.2f}",
                "low": f"{low:.2f}",
                "close": f"{close:.2f}",
                "prev_vwap": f"{prev_vwap:.2f}",
                "trade_type": "SKIP",
                "entry": "",
                "target": "",
                "exit": "",
                "target_hit": "",
                "pnl_absolute": "",
                "pnl_percent": "",
            })
            continue
        
        if open < prev_vwap:
            trade_type = "LONG"
        elif open > prev_vwap:
            trade_type = "SHORT"
        else:
            continue  # unreachable: skip-band check above already covers exact equality
        
        entry = open
        target = prev_vwap
        
        if low <= prev_vwap <= high:
            exit = prev_vwap
        else:
            exit = close
        
        target_hit = exit == prev_vwap
        
        if trade_type == "LONG":
            pnl_absolute = exit - entry
        else:
            pnl_absolute = entry - exit
        
        pnl_percent = (pnl_absolute / entry) * 100 if entry else 0
        
        trades.append({
            "date": row["date"],
            "open": f"{open:.2f}",
            "high": f"{high:.2f}",
            "low": f"{low:.2f}",
            "close": f"{close:.2f}",
            "prev_vwap": f"{prev_vwap:.2f}",
            "trade_type": trade_type,
            "entry": f"{entry:.2f}",
            "target": f"{target:.2f}",
            "exit": f"{exit:.2f}",
            "target_hit": str(target_hit).lower(),
            "pnl_absolute": f"{pnl_absolute:.2f}",
            "pnl_percent": f"{pnl_percent:.2f}",
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
            active = sum(1 for t in trades if t["trade_type"] != "SKIP")
            print(f"{label}->  {active} trades")
            success += 1
        except Exception:
            print(f"{label}->  Error")
    
    print(f"\nSuccessfully generated trades for {success}/{total} symbols")

if __name__ == "__main__":
    main()
