import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TRADES_DIR = BASE_DIR / "data" / "backtests" / "30d_rolling" / "trades"
OUTPUT_DIR = BASE_DIR / "data" / "results" / "30d_rolling"

STARTING_CAPITAL = 1_00_00_000  # 1 Cr
METRICS = ["target_hit_percent", "average_pnl_percent"]

def read_csv(path):
    with open(path, "r") as f:
        return list(csv.DictReader(f))

def simulate(metric):
    files = sorted((TRADES_DIR / metric).glob("*.csv"))  # filenames are ISO dates, sorted chronologically

    capital = STARTING_CAPITAL
    results = []

    for path in files:
        trades = read_csv(path)
        active_trades = [t for t in trades if t["trade_type"] != "SKIP"]

        capital_start = capital
        num_stocks = len(active_trades)

        if num_stocks:
            allocation = capital / num_stocks
            total_pnl = 0.0
            for t in active_trades:
                quantity = int(allocation // float(t["entry"]))
                total_pnl += quantity * float(t["pnl_absolute"])
            capital += total_pnl
        else:
            allocation = 0.0
            total_pnl = 0.0

        results.append({
            "date": path.stem,
            "trade_count": num_stocks,
            "capital_start": f"{capital_start:.2f}",
            "allocation_per_stock": f"{allocation:.2f}",
            "total_pnl": f"{total_pnl:.2f}",
            "capital_end": f"{capital:.2f}",
        })

    return results

def save_results(results, path):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

def main():
    for metric in METRICS:
        print(f"Processing {metric} ...")

        results = simulate(metric)
        if results:
            output_path = OUTPUT_DIR / f"{metric}.csv"
            save_results(results, output_path)
            print(f"  {len(results)} days processed, final capital = {results[-1]['capital_end']}")
        else:
            print("  No data")

if __name__ == "__main__":
    main()
