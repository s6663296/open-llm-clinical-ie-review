"""Export records for manual reading, without generating decisions."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import read_csv


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--records', required=True)
    parser.add_argument('--out-dir', required=True)
    parser.add_argument('--size', type=int, default=50)
    args = parser.parse_args()
    if args.size < 1:
        parser.error('--size must be positive')
    rows = read_csv(args.records)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for start in range(0, len(rows), args.size):
        lines = []
        for row in rows[start:start + args.size]:
            lines.append(f"{row['record_id']}\nTITLE: {row['title']}\nABSTRACT: {row['abstract']}\n")
        (out / f'batch_{start // args.size + 1:03}.txt').write_text('\n'.join(lines), encoding='utf-8')
    print(f'{len(rows)} records, {(len(rows) + args.size - 1) // args.size} batches')


if __name__ == '__main__':
    main()
