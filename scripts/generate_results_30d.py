import csv
from datetime import date, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "data" / "backtests" / "trades" / "intraday"
OUTPUT_DIR = BASE_DIR / "data" / "backtests" / "30d_rolling" / "results"

WINDOW_DAYS = 30

def read_trades(path):
    with open(path, "r") as f:
        return list(csv.DictReader(f))

def generate_summary(trades, start_date, end_date):
    ranged_trades = [t for t in trades if start_date <= t["date"] <= end_date]
    active_trades = [t for t in ranged_trades if t["trade_type"] != "SKIP"]

    trade_count = len(active_trades)
    target_hit_count = sum(1 for t in active_trades if t["target_hit"] == "true")
    target_hit_percent = (target_hit_count / trade_count) * 100 if trade_count else 0

    pnl_values = [float(t["pnl_percent"]) for t in active_trades]
    total_pnl_percent = sum(pnl_values)
    average_pnl_percent = total_pnl_percent / trade_count if trade_count else 0

    return {
        "trade_count": trade_count,
        "target_hit_count": target_hit_count,
        "target_hit_percent": f"{target_hit_percent:.2f}",
        "total_pnl_percent": f"{total_pnl_percent:.2f}",
        "average_pnl_percent": f"{average_pnl_percent:.2f}",
    }

def generate_rolling_results(trades):
    if not trades:
        return []

    first_date = date.fromisoformat(trades[0]["date"])
    cutoff_date = first_date + timedelta(days=WINDOW_DAYS)

    results = []
    for t in trades:
        current_date = t["date"]
        if date.fromisoformat(current_date) < cutoff_date:
            continue

        window_start = (date.fromisoformat(current_date) - timedelta(days=WINDOW_DAYS)).isoformat()
        summary = generate_summary(trades, window_start, current_date)
        results.append({"date": current_date, **summary})

    return results

def save_results(results, path):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

def main():
    trade_files = sorted(INPUT_DIR.glob("*.csv"))
    total = len(trade_files)
    width = len(str(total))

    print(f"Found {total} trade files")

    success = 0
    for i, trade_path in enumerate(trade_files, start=1):
        symbol = trade_path.stem
        label = f"[{i:0{width}}/{total}]  {symbol:<12}"

        try:
            trades = read_trades(trade_path)
            results = generate_rolling_results(trades)
            if results:
                output_path = OUTPUT_DIR / trade_path.name
                save_results(results, output_path)
                print(f"{label}->  {len(results)} rows")
                success += 1
            else:
                print(f"{label}->  No data")
        except Exception:
            print(f"{label}->  Error")

    print(f"\nSuccessfully processed {success}/{total} symbols")
    relative_path = Path("/") / OUTPUT_DIR.relative_to(BASE_DIR.parent)
    print(f"Results saved to {relative_path}")

if __name__ == "__main__":
    main()
