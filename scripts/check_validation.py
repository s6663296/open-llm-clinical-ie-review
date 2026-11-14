"""Check validation records against individual search exports."""
import argparse
from pathlib import Path

from common import read_csv, write_csv
from record_matching import match_rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--validation', required=True)
    parser.add_argument('--records', action='append', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    rows = read_csv(args.validation)
    names = [Path(path).parent.name for path in args.records]
    if len(set(names)) != len(names):
        parser.error('records parent directory names must be unique')
    for name, path in zip(names, args.records):
        matches = match_rows(rows, read_csv(path))
        for row, match in zip(rows, matches):
            row[name] = 'yes' if match is not None else 'no'
        print(f'{name}: {sum(match is not None for match in matches)}')
    fields = list(rows[0]) if rows else ['val_id'] + names
    write_csv(args.out, rows, fields)


if __name__ == '__main__':
    main()
