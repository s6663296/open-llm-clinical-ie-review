"""Create the extraction workbook from the codebook."""
import argparse
import re
from pathlib import Path
from openpyxl import Workbook, load_workbook
from form_common import ROOT, codebook_tables, format_sheet, validation


def main():
    """Build an empty or full-text-prefilled extraction form."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default=str(ROOT / 'extraction/extraction.xlsx'))
    parser.add_argument('--from-fulltext')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    out = Path(args.out)
    if out.exists() and not args.force:
        parser.error('output exists; use --force')
    tables = codebook_tables()
    wb = Workbook()
    wb.remove(wb.active)
    excluded = set('study_id record_ids primary_report extractor verifier verified note limitations'.split())
    for name, rows in tables.items():
        ws = wb.create_sheet(name)
        fields = []
        definitions = []
        options = {}
        for field, definition, allowed in rows:
            if field == '*_src':
                continue
            for col in (x.strip() for x in field.split(',')):
                fields.append(col)
                definitions.append(definition + ('；允許值：' + allowed if allowed else ''))
                if ' / ' in allowed and not re.search('例|整數|數值|可複選|…', allowed):
                    options[col] = allowed.split(' / ')
                if name == 'studies' and col not in excluded:
                    fields.append(col + '_src')
                    definitions.append('出處頁碼、表格或圖號')
        ws.append(fields)
        ws.append(definitions)
        format_sheet(ws)
        for field, choices in options.items():
            validation(ws, fields.index(field) + 1, choices)
    codebook = wb.create_sheet('codebook')
    codebook.append(['sheet', '欄位', '定義', '允許值'])
    for name, rows in tables.items():
        for row in rows:
            codebook.append([name] + row)
    if args.from_fulltext:
        source = load_workbook(args.from_fulltext, read_only=True, data_only=True)
        it = source['screening'].iter_rows(values_only=True)
        headers = next(it)
        included = [dict(zip(headers, row)) for row in it]
        included = [r for r in included if str(r.get('final_decision') or '').strip().lower() == 'include']
        ws = wb['studies']
        for i, record in enumerate(included, 1):
            ws.cell(i + 2, 1, f'S{i:03d}')
            ws.cell(i + 2, 2, record.get('record_id'))
        source.close()
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    print(out)


if __name__ == '__main__':
    main()
