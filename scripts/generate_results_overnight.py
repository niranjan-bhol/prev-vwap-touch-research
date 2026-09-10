import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "data" / "backtests" / "trades" / "overnight"
OUTPUT_DIR = BASE_DIR / "data" / "results" / "overnight"

INITIAL_CAPITAL = 1_000_000

TIMEFRAMES = {
    "year": ("2025-09-01", "2026-08-31"),
    "quarter": ("2026-06-01", "2026-08-31"),
    "month": ("2026-08-01", "2026-08-31"),
}

def read_trades(path):
    with open(path, "r") as f:
        return list(csv.DictReader(f))

def generate_summary(symbol, trades, start_date, end_date):
    ranged_trades = [t for t in trades if start_date <= t["date"] <= end_date]
    if not ranged_trades:
        return None
    
    trade_count = len(ranged_trades)
    target_hit_count = sum(1 for t in ranged_trades if t["target_hit"] == "true")
    target_hit_percent = (target_hit_count / trade_count) * 100 if trade_count else 0
    
    pnl_values = [float(t["pnl_percent"]) for t in ranged_trades]
    total_pnl_percent = sum(pnl_values)
    average_pnl_percent = total_pnl_percent / trade_count if trade_count else 0
    
    total_pnl_absolute = sum(float(t["pnl_absolute"]) for t in ranged_trades)
    final_capital = INITIAL_CAPITAL + total_pnl_absolute
    
    return {
        "symbol": symbol,
        "trade_count": trade_count,
        "target_hit_count": target_hit_count,
        "target_hit_percent": f"{target_hit_percent:.2f}",
        "total_pnl_percent": f"{total_pnl_percent:.2f}",
        "average_pnl_percent": f"{average_pnl_percent:.2f}",
        "capital": f"{final_capital:.2f}",
    }

def save_summary(summaries, path):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=summaries[0].keys())
        writer.writeheader()
        writer.writerows(summaries)

def main():
    trade_files = sorted(INPUT_DIR.glob("*.csv"))
    total = len(trade_files)
    width = len(str(total))
    
    print(f"Found {total} trade files")
    
    all_trades = {}
    for trade_path in trade_files:
        symbol = trade_path.stem
        try:
            all_trades[symbol] = read_trades(trade_path)
        except Exception:
            continue
    
    for timeframe, (start_date, end_date) in TIMEFRAMES.items():
        print(f"\nProcessing {timeframe} ({start_date} to {end_date}) ...\n")
        
        summaries = []
        success = 0
        
        for i, trade_path in enumerate(trade_files, start=1):
            symbol = trade_path.stem
            label = f"[{i:0{width}}/{total}]  {symbol:<12}"
            
            try:
                trades = all_trades.get(symbol)
                if trades is None:
                    print(f"{label}->  Error")
                    continue
                summary = generate_summary(symbol, trades, start_date, end_date)
                if summary:
                    summaries.append(summary)
                    print(f"{label}->  {summary['trade_count']} trades")
                    success += 1
            except Exception:
                print(f"{label}->  Error")
        
        if summaries:
            output_path = OUTPUT_DIR / f"{timeframe}.csv"
            relative_path = Path("/") / output_path.relative_to(BASE_DIR.parent)
            save_summary(summaries, output_path)
            print(f"\nSuccessfully processed {success}/{total} symbols")
            print(f"Summary saved to {relative_path}")
        else:
            print("\nNo data to summarize")

if __name__ == "__main__":
    main()
