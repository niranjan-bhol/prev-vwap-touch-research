import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "data" / "backtests" / "30d_rolling" / "results"
TRADES_DIR = BASE_DIR / "data" / "backtests" / "trades" / "intraday"
OUTPUT_DIR = BASE_DIR / "data" / "backtests" / "30d_rolling" / "trades"

TOP_N = 10
METRICS = ["target_hit_percent", "average_pnl_percent"]

def read_csv(path):
    with open(path, "r") as f:
        return list(csv.DictReader(f))

def get_trade_fieldnames():
    sample_path = next(TRADES_DIR.glob("*.csv"))
    with open(sample_path, "r") as f:
        header = next(csv.reader(f))
    return ["symbol"] + [column for column in header if column != "date"]

def load_results():
    date_map = {}
    for path in sorted(RESULTS_DIR.glob("*.csv")):
        symbol = path.stem
        for row in read_csv(path):
            entry = {"symbol": symbol}
            entry.update({metric: float(row[metric]) for metric in METRICS})
            date_map.setdefault(row["date"], []).append(entry)
    return date_map

def load_trades():
    trades_map = {}
    for path in sorted(TRADES_DIR.glob("*.csv")):
        symbol = path.stem
        trades_map[symbol] = {row["date"]: row for row in read_csv(path)}
    return trades_map

def build_rows(top_entries, trades_map, current_date):
    rows = []
    for entry in top_entries:
        trade_row = trades_map.get(entry["symbol"], {}).get(current_date)
        if trade_row is None:
            continue
        row = {"symbol": entry["symbol"]}
        row.update({key: value for key, value in trade_row.items() if key != "date"})
        rows.append(row)
    return rows

def save_rows(rows, fieldnames, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def main():
    print("Loading 30d results ...")
    date_map = load_results()

    print("Loading intraday trades ...")
    trades_map = load_trades()
    fieldnames = get_trade_fieldnames()

    dates = sorted(date_map.keys())
    total = len(dates)
    width = len(str(total))

    print(f"\nFound {total} dates\n")

    success = 0
    for i, current_date in enumerate(dates, start=1):
        label = f"[{i:0{width}}/{total}]  {current_date}"

        entries = date_map[current_date]
        counts = []
        for metric in METRICS:
            top_entries = sorted(entries, key=lambda entry: entry[metric], reverse=True)[:TOP_N]
            rows = build_rows(top_entries, trades_map, current_date)

            if rows:
                output_path = OUTPUT_DIR / metric / f"{current_date}.csv"
                save_rows(rows, fieldnames, output_path)
                counts.append(f"{metric}={len(rows)}")

        if counts:
            print(f"{label}->  {', '.join(counts)}")
            success += 1
        else:
            print(f"{label}->  No data")

    print(f"\nSuccessfully processed {success}/{total} dates")
    relative_path = Path("/") / OUTPUT_DIR.relative_to(BASE_DIR.parent)
    print(f"Results saved to {relative_path}")

if __name__ == "__main__":
    main()
