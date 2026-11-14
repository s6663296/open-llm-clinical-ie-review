"""Compare incoming records against the existing deduplicated collection."""
import argparse
from pathlib import Path
from common import FIELDS, read_csv, write_csv
from import_records import deduplicate


def main():
    """Write new records and matched existing-record identifiers."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--new', required=True)
    parser.add_argument('--existing', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--matches', required=True)
    args = parser.parse_args()
    existing = read_csv(args.existing)
    incoming = read_csv(args.new)
    groups, _, _ = deduplicate(existing + incoming)
    fresh = []
    matches = []
    for group in groups:
        old = [i for i in group if i < len(existing)]
        new = [i - len(existing) for i in group if i >= len(existing)]
        for i in new:
            if old:
                matches.append({'new_index': i + 1, 'existing_record_ids': '; '.join(existing[j].get('record_id', '') for j in old), 'new_title': incoming[i].get('title', '')})
            else:
                fresh.append(incoming[i])
    fields = list(incoming[0]) if incoming else FIELDS
    write_csv(args.out, fresh, fields)
    write_csv(args.matches, matches, ['new_index', 'existing_record_ids', 'new_title'])
    print(f'new={len(fresh)}, matched={len(matches)}')


if __name__ == '__main__':
    main()
