"""Write extraction batch lists (record_id<TAB>title) for the included studies.

Usage: python scripts/agent_extraction/make_batches.py [--size 10] [--out-dir extraction/ai_batches]
"""
import argparse, csv
from pathlib import Path

def main():
    p = argparse.ArgumentParser(); p.add_argument('--size', type=int, default=10)
    p.add_argument('--src', default='screening/full_text.csv'); p.add_argument('--out-dir', default='extraction/ai_batches')
    a = p.parse_args()
    rows = [r for r in csv.DictReader(open(a.src, encoding='utf-8-sig')) if r['final_decision'] == 'include']
    rows.sort(key=lambda r: r['record_id'])
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    for i in range(0, len(rows), a.size):
        (out / f'batch_{i // a.size + 1:02}.list').write_text(
            ''.join(f"{r['record_id']}\t{r['title']}\n" for r in rows[i:i + a.size]), encoding='utf-8')
    print(f'{len(rows)} studies, {(len(rows) + a.size - 1) // a.size} batches -> {out}')

if __name__ == '__main__': main()
