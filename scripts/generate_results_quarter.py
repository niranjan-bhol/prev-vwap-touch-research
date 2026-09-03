import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "data" / "backtests" / "trades_quarter"
OUTPUT_DIR = BASE_DIR / "data" / "results"
OUTPUT_FILE = "summary_quarter.csv"

def read_trades(path):
    with open(path, "r") as f:
        return list(csv.DictReader(f))

def generate_summary(symbol, trades):
    if not trades:
        return None
    
    active_trades = [t for t in trades if t["trade_type"] != "SKIP"]
    
    trade_count = len(active_trades)
    target_hit_count = sum(1 for t in active_trades if t["target_hit"] == "true")
    target_hit_percent = (target_hit_count / trade_count) * 100 if trade_count else 0
    
    pnl_values = [float(t["pnl_percent"]) for t in active_trades]
    total_pnl_percent = sum(pnl_values)
    average_pnl_percent = total_pnl_percent / trade_count if trade_count else 0
    
    last_capital_trade = next((t for t in reversed(trades) if t["capital"] != ""), None)
    final_capital = float(last_capital_trade["capital"]) if last_capital_trade else 0
    
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
    print(f"\nProcessing trades ...\n")
    
    summaries = []
    success = 0
    
    for i, trade_path in enumerate(trade_files, start=1):
        symbol = trade_path.stem
        label = f"[{i:0{width}}/{total}]  {symbol:<12}"
        
        try:
            trades = read_trades(trade_path)
            summary = generate_summary(symbol, trades)
            if summary:
                summaries.append(summary)
                active = sum(1 for t in trades if t["trade_type"] != "SKIP")
                print(f"{label}->  {active} trades")
                success += 1
        except Exception:
            print(f"{label}->  Error")
    
    if summaries:
        output_path = OUTPUT_DIR / OUTPUT_FILE
        relative_path = Path("/") / output_path.relative_to(BASE_DIR.parent)
        save_summary(summaries, output_path)
        print(f"\nSuccessfully processed {success}/{total} symbols")
        print(f"Summary saved to {relative_path}")
    else:
        print("\nNo data to summarize")

if __name__ == "__main__":
    main()
